"""Make the same Short with different music: one MP4 per style in exports/<subdir>/music/.
Video is copied untouched; only the audio changes. Reveal times come from the page's own cue log.

  python3 tools/music_variants.py <timelapse-id> <exports-subdir> pulse,cinematic,keys,calm
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ID, SUB, STYLES = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
E = ROOT / "exports/timelapses" / ID; OUT = ROOT / "exports" / SUB / "music"; OUT.mkdir(parents=True, exist_ok=True)
V = E / f"{ID}_1080x1920.mp4"
cfg = json.loads((E / "config.json").read_text()); log = json.loads((E / f"{ID}.frames.json").read_text()); fps = cfg["fps"]
dur = len(log) / fps
run = lambda *a: subprocess.run(list(a), check=True)
cues = [(r["frame"], r["cue"]) for r in log if r.get("cue")]
hits = [f / fps for f, c in cues if c == "hit"]
run("python3", str(ROOT / "tools/make_sfx.py"), str(OUT / "sfx"))
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "2", "-ar", "48000", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)
LUFS = {"pulse": -16, "cinematic": -16, "keys": -18, "calm": -21}
HITG = {"pulse": 0.30, "cinematic": 0.0, "keys": 0.25, "calm": 0.35}       # cinematic has its own boom on reveals
for st in STYLES:
    bed_p = OUT / f"bed_{st}.wav"
    if st == "calm": run("python3", str(ROOT / "tools/make_bed_calm.py"), f"{dur:.3f}", str(bed_p))
    else: run("python3", str(ROOT / "tools/make_music.py"), st, f"{dur:.3f}", str(bed_p), ",".join(f"{h:.3f}" for h in hits))
    bed = load(bed_p); bed = bed / max(1e-9, np.abs(bed).max()) * 0.5; mix = bed.copy()
    sfx = {"hit": load(OUT / "sfx/soft_hit.wav"), "riser": load(OUT / "sfx/swell.wav")}
    for fr, kind in cues:
        if kind not in sfx: continue                                          # no per-year ticks in any style
        g = HITG[st] if kind == "hit" else 0.15
        x = sfx[kind] * g; i0 = int(fr / fps * 48000); n = min(len(x), len(mix) - i0)
        if n > 0 and g > 0: mix[i0:i0 + n] += x[:n]
    k = int(0.25 * 48000); mix[-k:] *= np.linspace(1, 0.35, k)[:, None]; mix[:k] *= np.linspace(0.35, 1, k)[:, None]
    raw = OUT / "mix_raw.f32"; raw.write_bytes(mix.astype(np.float32).tobytes())
    wav = OUT / f"mix_{st}.wav"
    run("ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", str(raw), "-af", f"loudnorm=I={LUFS[st]}:TP=-1.5:LRA=9", "-ar", "48000", str(wav)); raw.unlink()
    run("ffmpeg", "-y", "-v", "error", "-i", str(V), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(OUT / f"{ID}_{st}.mp4"))
    print("wrote", (OUT / f"{ID}_{st}.mp4").relative_to(ROOT))
