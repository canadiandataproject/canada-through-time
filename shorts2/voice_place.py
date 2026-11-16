"""Place narration lines from a (processed) take onto the Short's timeline.
  python3 shorts2/voice_place.py <cues.json> <take.wav> <out.wav>
cues["cuts"] = [[t, [[start, end], gap_s, [start, end], ...]], ...]: take times in seconds, placed at t."""
import json, subprocess, sys
import numpy as np
cues = json.load(open(sys.argv[1])); SR = 48000
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[2], "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
def clip(s, e):
    x = a[int(s * SR):int(e * SR)].copy(); f = int(0.03 * SR); r = np.linspace(0, 1, f); x[:f] *= r; x[-f:] *= r[::-1]; return x
out = np.zeros(int(cues["duration"] * SR), np.float32)
for t, parts in cues["cuts"]:
    x = np.concatenate([clip(*p) if isinstance(p, list) else np.zeros(int(p * SR), np.float32) for p in parts])
    v = x[np.abs(x) > 0.01]; x = x * (0.08 / np.sqrt((v ** 2).mean()))         # per-line level match
    i = int(t * SR); assert i + len(x) <= len(out), "line runs past the end"; out[i:i + len(x)] += x
out /= np.abs(out).max() / 0.9
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", sys.argv[3]], input=out.tobytes(), check=True)
print("placed", len(cues["cuts"]), "lines ->", sys.argv[3])
