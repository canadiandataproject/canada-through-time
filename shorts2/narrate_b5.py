"""Narration batch 5 (Shorts #17-22, recorded 2026-11-17 as one take): cut lines from the processed take, lay them on
each Short's timeline, and return the beat times the visuals are timed to.

  python3 shorts2/narrate_b5.py <processed_take.wav> <outdir>     -> <outdir>/v17.wav ... v22.wav, <outdir>/beats.json

Line times are in the raw take (seconds). Cuts removed from the take (claims the data doesn't support):
  #18 "the biggest jump in the country" (data covers 33 cities), #19 "in the prairies" (Manitoba went the other way),
  #20 "on average" (figures are medians).
Pacing (narration rules): pauses inside a line longer than 0.7 s become 0.55 s; speed 1.04x.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

SR = 48000; SPEED = 1.04; GAP = 0.32
src, outdir = sys.argv[1], Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
# speed first (pitch kept), so all raw times scale by 1/SPEED
sped = outdir / "take_sped.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"rubberband=tempo={SPEED}:pitchq=quality:formant=preserved", "-ac", "1", "-ar", str(SR), str(sped)], check=True)
A = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(sped), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout, np.float32)
S = lambda t: t / SPEED
hop = int(0.01 * SR); env = np.sqrt(np.convolve(A ** 2, np.ones(hop * 3) / (hop * 3), "same"))[::hop]   # 10 ms RMS
floor = np.percentile(env, 20); thr = max(floor * 3.5, np.percentile(env, 60) * 0.12)

def snap(t, w=0.25, side=0):  # line edge at the first quiet 10 ms frame outward from the cut (side -1 start: search earlier; +1 end: later), so no word is clipped
    i = int(t * 100); step = -1 if side < 0 else 1
    for k in range(int(w * 100)):
        j = i + step * k
        if 0 <= j < len(env) and env[j] < thr: return j / 100
    return (i + step * int(w * 100)) / 100

def line(a, b, hard=""):
    """Cut raw [a, b] with quiet edges; shorten inner pauses > 0.7 s to 0.55 s. Returns audio and a raw->line-time map."""
    s = S(a) if "s" in hard else snap(S(a), side=-1); e = S(b) if "e" in hard else snap(S(b), side=1); x = A[int(s * SR):int(e * SR)].copy()   # hard edges: exact cut between touching words
    q = env[int(s * 100):int(e * 100)] < thr; segs, i = [], 0
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]: j += 1
            if (j - i) / 100 > 0.7: segs.append((i / 100, j / 100))
            i = j
        else: i += 1
    parts, removed, last = [], [], 0.0
    for u, v in segs:
        cut0, cut1 = u + 0.275, v - 0.275; parts.append(x[int(last * SR):int(cut0 * SR)]); removed.append((cut0, cut1 - cut0)); last = cut1
    parts.append(x[int(last * SR):]); y = np.concatenate(parts)
    f = int(0.025 * SR); r = np.linspace(0, 1, f); y[:f] *= r; y[-f:] *= r[::-1]
    def tmap(raw):  # raw take time -> seconds from the start of this line
        u = S(raw) - s; return u - sum(d for c, d in removed if c < u)
    return y, tmap

def join(lines, gaps=None):
    """lines: list of (a, b). Returns audio and a function raw->timeline seconds, plus each line's start."""
    out, starts, maps, t = [], [], [], 0.15
    out.append(np.zeros(int(t * SR), np.float32))
    for k, (a, b, *h) in enumerate(lines):
        y, m = line(a, b, h[0] if h else ""); starts.append(t); maps.append((a, b, t, m)); out.append(y); t += len(y) / SR
        g = (gaps or {}).get(k, GAP); out.append(np.zeros(int(g * SR), np.float32)); t += g
    def at(raw):
        for a, b, t0, m in maps:   # first line whose range holds the time
            if a - 0.05 <= raw <= b + 0.05: return round(t0 + m(raw), 3)
        raise ValueError(raw)
    return np.concatenate(out), at, starts

beats = {}
def save(n, y, extra):
    y = y / max(1e-9, np.abs(y).max()) * 0.9
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(outdir / f"v{n}.wav")], input=y.astype(np.float32).tobytes(), check=True)
    extra["voice_end"] = round(len(y) / SR, 3); beats[n] = extra; print(n, extra)

# 17 Alberta: "Then 2 / to 3 / to 4" are split so each lands on its year
y, at, st = join([(4.25, 6.40), (7.10, 11.82), (12.50, 13.45, "e"), (13.50, 14.24, "se"), (14.27, 14.92, "se"), (14.92, 17.95, "s"), (18.05, 21.65), (23.20, 25.36), (26.0, 26.9)],
                 gaps={1: 0.45, 2: 0.75, 3: 0.75, 4: 0.6, 5: 0.25, 6: 0.35, 7: 0.45})
save(17, y, dict(q_end=at(6.36), l2_start=st[1], y1971=at(7.30), l2_end=at(11.76), two=at(13.01), three=at(13.82), four=at(14.54), now=st[5],
                 five=at(15.66), summary=st[5], double_end=at(25.32), links=st[8]))
# 18 Rent ("the biggest jump in the country" cut)
y, at, st = join([(29.00, 31.30, "s"), (31.85, 34.10), (34.30, 35.80), (36.55, 41.05), (44.45, 48.35), (49.50, 50.40)], gaps={0: 0.4, 2: 0.45, 3: 0.4, 4: 0.5})
save(18, y, dict(q_end=at(31.20), van=st[1], n73=at(32.80), kel=st[3], low=st[4], low_end=at(48.30), links=st[5]))
# 19 Gas ("in the prairies" cut)
y, at, st = join([(53.20, 57.10), (57.75, 62.05), (62.55, 66.66), (66.90, 68.76), (70.80, 71.70)], gaps={0: 0.4, 1: 0.4, 2: 0.3, 3: 0.5})
save(19, y, dict(q_end=at(57.04), counted=st[1], n39=at(59.70), canada=st[2], sask=at(65.18), wages_end=at(68.72), links=st[4]))
# 20 Montréal ("on average" cut)
y, at, st = join([(73.45, 74.92), (75.00, 77.00), (77.58, 79.92, "e"), (80.43, 83.72, "s"), (84.45, 90.30), (91.25, 94.10), (94.35, 99.10), (99.90, 100.60)],
                 gaps={1: 0.4, 2: 0.12, 3: 0.4, 4: 0.4, 5: 0.45, 6: 0.4})
save(20, y, dict(q_end=at(74.88), city=st[1], nb=at(75.54), lo0=st[2], hi0=at(81.18), lo1=st[4], hi1=at(88.34), lo2=st[5], hi2=at(93.30), same=st[6], links=st[7]))
# 21 Edmonton
y, at, st = join([(102.65, 104.62), (105.05, 107.72), (108.22, 110.86), (111.28, 114.45), (115.08, 118.50), (119.22, 123.46), (123.46, 125.62), (126.08, 126.75)],
                 gaps={1: 0.4, 2: 0.2, 3: 0.4, 4: 0.4, 5: 0.35, 6: 0.4})
save(21, y, dict(q_end=at(104.58), city=st[1], nb=at(105.78), lo0=st[2], hi0=st[3], lo1=st[4], hi1=at(117.82), lo2=st[5], hi2=at(122.04), same=st[6], links=st[7]))
# 22 Vancouver (keeps "Seems kind of low.")
y, at, st = join([(128.85, 130.65), (131.00, 132.95), (134.05, 136.72), (136.90, 138.98), (139.25, 140.32), (140.68, 147.22), (147.22, 150.34), (151.88, 154.00)],
                 gaps={1: 0.4, 2: 0.2, 3: 0.2, 4: 0.35, 5: 0.3, 6: 0.45})
save(22, y, dict(q_end=at(130.60), city=st[1], nb=at(131.28), lo0=st[2], hi0=st[3], lo1=st[5], hi1=at(145.76), lo2=st[6], hi2=at(149.44), same=st[7], links=at(153.02)))
(outdir / "beats.json").write_text(json.dumps(beats, indent=1))
