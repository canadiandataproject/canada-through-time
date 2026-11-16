"""Mix narration + calm bed + engine-specific sound effects onto a rendered Short.

  python3 shorts2/mix.py <engine> <cues.json> <video.mp4> <out.mp4>

engine: receipt | splitflap | zoom | swarm. The voice path comes from cues["voice"] (relative to the cues file's dir or absolute).
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]; SR = 48000
eng, cp, vid, out = sys.argv[1:5]
cues = json.loads(Path(cp).read_text()); dur = cues["duration"]; N = int(dur * SR)
rng = np.random.default_rng(1)

def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2); b = np.zeros((N, 2), np.float32); b[:min(N, len(a))] = a[:N]; return b
def lp(x, k):            # fast moving-average low-pass
    return np.convolve(x, np.ones(k) / k, "same")
def place(buf, snd, t, g=1.0):
    i = int(t * SR); n = min(len(snd), N - i)
    if n > 0 and i >= 0: buf[i:i + n] += snd[:n, None] * g if snd.ndim == 1 else snd[:n] * g

voice = load(Path(cues["voice"]) if Path(cues["voice"]).is_absolute() else Path("/home/claude/audio/b4") / cues["voice"])
voice = voice / max(1e-9, np.abs(voice).max()) * 0.9
bedf = Path("/tmp") / f"bed_{eng}.wav"
subprocess.run(["python3", str(ROOT / "tools/make_bed_calm.py"), f"{dur:.3f}", str(bedf)], check=True)
bed = load(bedf); bed = bed / max(1e-9, np.abs(bed).max()) * 0.30
fx = np.zeros((N, 2), np.float32)
t_ = np.arange(int(0.6 * SR)) / SR

if eng == "receipt":
    for c in cues["print"]:
        d = max(0.12, c.get("dur", 0.3))
        if c["t"] - d < 0.05: continue
        tt = np.arange(int(d * SR)) / SR
        motor = (rng.normal(0, 1, len(tt)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 180 * tt)))) ; motor = lp(motor, 6) * 0.10
        motor *= np.minimum(1, tt / 0.02) * np.minimum(1, (d - tt) / 0.03)
        place(fx, motor, c["t"] - d)
    for s in cues.get("stamps", []):
        th = np.arange(int(0.35 * SR)) / SR; thump = np.sin(2 * np.pi * 70 * th) * np.exp(-th * 18) * 0.55 + lp(rng.normal(0, 1, len(th)), 3) * np.exp(-th * 40) * 0.25
        place(fx, thump, s["t"])
    for c in cues.get("circles", []):
        tt = np.arange(int(0.6 * SR)) / SR; scr = lp(rng.normal(0, 1, len(tt)), 2) * 0.05 * np.sin(np.pi * tt / 0.6) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * tt))
        place(fx, scr, c["t"])
elif eng == "splitflap":
    clk = lambda: (lp(rng.normal(0, 1, int(0.012 * SR)), 2) * np.exp(-np.arange(int(0.012 * SR)) / SR * 400))
    for p in cues["phases"]:
        for k in range(0, int(3.2 / 0.011)):          # a burst of clacks that thins out as rows settle
            t0 = p["t"] + k * 0.011 + rng.uniform(0, 0.01)
            dens = max(0, 1 - k * 0.011 / 3.2)
            if rng.random() < 0.85 * dens: place(fx, clk(), t0, 0.16 * (0.5 + rng.random() * 0.5))
elif eng == "zoom":
    cam = cues["camera"]
    for a, b in zip(cam, cam[1:]):
        if b["t"] - a["t"] > 0.4 and (a["at"] != b["at"] or a["zoom"] != b["zoom"]):
            d = b["t"] - a["t"]; tt = np.arange(int(d * SR)) / SR
            w = lp(rng.normal(0, 1, len(tt)), 30) * np.sin(np.pi * tt / d) ** 2 * 0.22
            place(fx, w, a["t"])
elif eng == "swarm":
    for p in cues["phases"]:
        d = 1.6; tt = np.arange(int(d * SR)) / SR
        sh = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f in (880, 1320, 1760, 2640)) * 0.012 * np.exp(-tt * 2.2) * np.minimum(1, tt / 0.05)
        place(fx, sh + lp(rng.normal(0, 1, len(tt)), 4) * 0.02 * np.exp(-tt * 3), p["t"])

# duck bed and effects under the voice
env = lp(np.abs(voice).mean(1), int(0.25 * SR)); talk = np.clip(env / max(1e-9, np.percentile(env[env > 0], 60)), 0, 1)[:, None]
mix = bed * (0.45 - 0.27 * talk) + fx * (1 - 0.35 * talk) + voice
k = int(0.25 * SR); mix[-k:] *= np.linspace(1, 0.3, k)[:, None]
raw = Path("/tmp") / f"mix_{eng}.f32"; raw.write_bytes(mix.astype(np.float32).tobytes())
wav = Path("/tmp") / f"mix_{eng}.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", str(SR), str(wav)], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
print("mixed", out)
