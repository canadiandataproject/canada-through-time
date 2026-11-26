"""Synthetic narration for a Short: Kokoro-82M (Apache-2.0, runs locally, free; a stock voice, not a clone of anyone).

  python3 shorts2/tts.py <cues.json> [--voice am_michael] [--speed 1.0] [--out path.wav]

Reads the burned-in captions (cues["captions"]: t0, t1, text) and places each spoken line at its caption start, so
voice, caption and on-screen card stay in sync. A line that runs past its slot is re-read faster (up to 1.3×); if it
still doesn't fit it may run into the gap before the next caption but never overlaps it. Writes cues["voice"] (or --out).
Model files: /home/claude/tts/kokoro-v1.0.onnx + voices-v1.0.bin from github.com/thewh1teagle/kokoro-onnx releases.
"""
import json, re, sys
from pathlib import Path
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

MODEL = Path("/home/claude/tts")
SR = 24000
# spoken forms: things the phonemizer reads badly. Captions keep the written form.
SAY = {"×": "times ", "W9": "W nine", "Wîhkwêntôwin": "Wee-kwen-toe-win", "Jogeshwari": "Joe-gesh-wuh-ree", "Girgaon": "Gir-gown",
       "Haymarket": "Hay-market", "St. James": "Saint James", "CBD": "C B D", "N.B.": "New Brunswick", "vada pav": "vahda pahv",
       "Whyte Ave": "White Avenue", "Maida Hill": "May-da Hill", "M4": "M-four"}


def num_words(m):
    n = int(m.group(0).replace(",", ""))
    from num2words import num2words
    return num2words(n)


def spoken(t):
    for k, v in SAY.items(): t = t.replace(k, v)
    t = re.sub(r"\b(\d+)\.0 million", r"\1 million", t)               # "11.0 million" is said "eleven million"
    t = re.sub(r"\b\d{1,3}(,\d{3})+\b", num_words, t)          # 35,018 -> thirty-five thousand and eighteen
    return t


def build(cues, voice="am_michael", speed=1.0):
    k = Kokoro(str(MODEL / "kokoro-v1.0.onnx"), str(MODEL / "voices-v1.0.bin"))
    lang = "en-gb" if voice.startswith("b") else "en-us"
    caps = cues["captions"]; N = int(cues["duration"] * SR) + SR; out = np.zeros(N, np.float32); log = []; vend = 0.0
    for i, c in enumerate(caps):
        nxt = caps[i + 1]["t0"] if i + 1 < len(caps) else cues["duration"]
        # earliest start: just after the previous line ends and the previous caption leaves (a line may start in that gap)
        early = max(vend + 0.25, (caps[i - 1]["t1"] + 0.15) if i else 0.0, c["t0"] - 3.0)
        slot = c["t1"] - c["t0"]; room = c["t1"] - early; hard = nxt - early - 0.12
        sp = speed
        while True:
            a, sr = k.create(spoken(c["text"]), voice=voice, speed=sp, lang=lang); assert sr == SR
            a = np.trim_zeros(np.where(np.abs(a) < 1e-3, 0, a)) if np.abs(a).max() > 0 else a
            L = len(a) / SR
            if L <= room or sp >= 1.25: break
            sp = min(1.25, sp * L / room + 0.02)
        t0 = c["t0"] + 0.05 if L <= slot else max(early, c["t1"] - L)   # fits: on the caption; else start early so it ends with it
        t0 = max(t0, vend + 0.25)                                       # a long line before may push this one a little later
        # a line may run up to 1.2 s past its caption (the next, shorter line then waits); never past the next caption's end
        nend = caps[i + 1]["t1"] - 1.2 if i + 1 < len(caps) else cues["duration"] - 0.3
        assert t0 + L <= min(c["t1"] + 1.2, nend) + 0.05, f"line {i} ({c['text']!r}) is {L:.2f} s, room {room:.2f} s: shorten the line"
        s = int(t0 * SR); out[s:s + len(a)] += a[:N - s]; vend = t0 + L
        log.append(f"  {t0:5.1f}s  {L:4.1f}/{slot:3.1f}s  ×{sp:.2f}  {c['text']}")
    return out, log


if __name__ == "__main__":
    cp = Path(sys.argv[1]); cues = json.loads(cp.read_text())
    arg = lambda n, d: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
    voice, speed = arg("--voice", "am_michael"), float(arg("--speed", "1.08"))
    out = Path(arg("--out", cues["voice"])); out.parent.mkdir(parents=True, exist_ok=True)
    a, log = build(cues, voice, speed); sf.write(out, a, SR); print(f"wrote {out} ({voice})"); print("\n".join(log))
