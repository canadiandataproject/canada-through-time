"""Original music beds for The Canadian Data Project Shorts, in three styles common on data/explainer Shorts.
Synthesized from scratch with numpy: no samples, no third-party audio, no melodies borrowed from existing songs.

  pulse      — upbeat electronic: 120 bpm, four-on-the-floor soft kick, claps, hats, side-chained pad, pluck arpeggio,
               sub bass. vi–IV–I–V in A minor. Filtered intro; full groove from bar 3; energy steps up after the first reveal.
  cinematic  — documentary build: 90 bpm, string-like drone, piano ostinato, low "boom" hits on reveals, growing toms.
               i–VI–III–VII in D minor.
  keys       — chill keys: 84 bpm, electric-piano chords, soft brushed beat, round bass. Fmaj7–Em7–Dm7–Cmaj7.

Usage: make_music.py <style> <seconds> <out.wav> [reveal times in seconds, comma-separated]
Seeded, so the same inputs give the same file."""
import sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

STYLE, DUR, OUT = sys.argv[1], float(sys.argv[2]), sys.argv[3]
HITS = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] else []
SR = 48000
rng = np.random.default_rng({"pulse": 11, "cinematic": 23, "keys": 37}[STYLE])
N = int(SR * (DUR + 2)); L = np.zeros(N); R = np.zeros(N)
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def add(sig, t0, pan=0.5, gain=1.0):
    i0 = int(round(t0 * SR))
    if i0 >= N or i0 + len(sig) <= 0: return
    a, b = max(0, i0), min(N, i0 + len(sig)); s = sig[a - i0:b - i0] * gain
    L[a:b] += s * np.sqrt(1 - pan); R[a:b] += s * np.sqrt(pan)


def env(n, a, d, s=0.0, r=0.0, hold=None):
    t = np.arange(n) / SR; e = np.minimum(t / max(a, 1e-4), 1.0)
    if hold is None: return e * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    e = e * (s + (1 - s) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4)))
    rel = np.clip((hold + r - t) / max(r, 1e-4), 0, 1); return e * np.where(t > hold, rel, 1)


def lp(x, f, order=2): return sosfilt(butter(order, min(f, SR / 2 - 100), btype="low", fs=SR, output="sos"), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)
def bp(x, f1, f2): return sosfilt(butter(2, [f1, f2], btype="band", fs=SR, output="sos"), x)


def saw(f, n, det=(0.0,)):
    t = np.arange(n) / SR; out = np.zeros(n)
    for d in det:
        ph = (f * (1 + d / 1200) * t + rng.random()) % 1.0; out += 2 * ph - 1
    return out / len(det)


def kick(n=int(0.35 * SR), f0=95, f1=42, punch=0.9):
    t = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16) * punch + np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.002) * 0.05


def noise_hit(n, f1, f2, dec): return bp(rng.normal(0, 1, n), f1, f2) * np.exp(-np.arange(n) / SR / dec)


def epiano(m, n, vel=1.0):
    t = np.arange(n) / SR; f = mtof(m)
    mod = np.sin(2 * np.pi * f * 2 * t) * 1.2 * np.exp(-t / 0.35)          # gentle FM tine
    car = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 1.6)
    return (car + 0.12 * np.sin(2 * np.pi * f * 3 * t) * np.exp(-t / 0.4)) * np.minimum(t / 0.004, 1) * vel * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))


def piano(m, n, vel=1.0):
    t = np.arange(n) / SR; f = mtof(m); s = np.zeros(n)
    for h, a in ((1, 1), (2, .45), (3, .22), (4, .12), (5, .06)):
        s += a * np.sin(2 * np.pi * f * h * (1 + .0004 * h * h) * t) * np.exp(-t * (1.1 + .9 * h))
    return s * np.minimum(t / 0.003, 1) * vel


def intensity(t):
    """0..1 energy curve: builds toward the first reveal, steps up after it, holds; dips briefly right after each reveal."""
    if not HITS: return min(1, 0.4 + t / DUR)
    first = HITS[0]; e = 0.45 + 0.35 * min(1, t / max(first, 1)) if t < first else 0.9
    for h in HITS:
        if 0 <= t - h < 0.6: e *= 0.75
    return e


# ------------------------------------------------------------------------------------------------ styles
if STYLE == "pulse":
    BPM = 120; beat = 60 / BPM; bar = 4 * beat
    PROG = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]          # Am F C G
    BASS = [45, 41, 36, 43]
    nbar = int(np.ceil(DUR / bar)) + 1
    side = np.ones(N)                                                         # side-chain envelope from the kick
    for b in range(nbar):
        t0 = b * bar; ch = PROG[b % 4]; full = b >= 1; e = intensity(t0)
        for q in range(4):
            tq = t0 + q * beat
            if full:
                add(kick(), tq, 0.5, 0.5); i0 = int(tq * SR); k = int(0.22 * SR)
                if i0 < N: side[i0:i0 + k] = np.minimum(side[i0:i0 + k], 1 - 0.65 * np.exp(-np.arange(min(k, N - i0)) / SR / 0.09))
            if full and q in (1, 3): add(noise_hit(int(.25 * SR), 900, 4000, .07), tq, 0.5, 0.5 * e)
            for e8 in (0, 0.5):
                if True: add(hp(rng.normal(0, 1, int(.05 * SR)), 7000) * np.exp(-np.arange(int(.05 * SR)) / SR / .012), tq + e8 * beat, 0.62 if e8 else 0.4, (0.16 if e8 else 0.09) * e)
        # pad (side-chained later), plucks, sub bass
        n = int((bar + 0.4) * SR)
        pad = sum(saw(mtof(m), n, (-7, 0, 7)) for m in ch) / 3 * env(n, 0.05, 9, 1, 0.3, hold=bar)
        add(lp(pad, 1200 + 2600 * e), t0, 0.4, 0.24); add(lp(pad, 1200 + 2600 * e), t0 + 0.012, 0.6, 0.24)
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24]
        for s16 in range(16):
            if not full and s16 % 2: continue
            m = arp[s16 % 4]; nn = int(0.18 * SR); pl = lp(saw(mtof(m), nn, (-4, 4)) * env(nn, 0.002, 0.07), 2600 + 1800 * e)
            add(pl, t0 + s16 * beat / 4, 0.3 + 0.4 * ((s16 * 5) % 7) / 6, 0.18 * (0.6 + 0.4 * e))
        for e8 in range(8):
            if not full: break
            nn = int(beat / 2 * SR * 0.9); f = mtof(BASS[b % 4]); tt = np.arange(nn) / SR
            add(np.sin(2 * np.pi * f * tt) * env(nn, 0.005, 0.25) * (0.9 if e8 % 2 == 0 else 0.6), t0 + e8 * beat / 2, 0.5, 0.14)
    L *= side; R *= side
    lpf = np.array([600 + 14000 * min(1, (i / SR) / bar) ** 2 for i in range(0, N, 480)])   # intro filter sweep
    cut = np.repeat(lpf, 480)[:N]
    for ch_ in (L, R):
        lo = lp(ch_, 700); ch_[:] = np.where(np.arange(N) / SR < bar, lo + (ch_ - lo) * np.clip((cut - 600) / 14000, 0, 1), ch_)

elif STYLE == "cinematic":
    BPM = 90; beat = 60 / BPM; bar = 4 * beat
    PROG = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64]]   # Dm Bb F C
    nbar = int(np.ceil(DUR / bar)) + 1
    for b in range(nbar):
        t0 = b * bar; ch = PROG[b % 4]; e = intensity(t0)
        n = int((bar + 1.5) * SR)                                            # strings: slow swells, detuned saws, dark filter
        for m in ch:
            st = lp(saw(mtof(m), n, (-9, -3, 4, 10)), 700 + 1500 * e) * env(n, 0.9, 9, 1, 1.2, hold=bar)
            add(st, t0, 0.3 + 0.4 * rng.random(), 0.065)
        add(lp(saw(mtof(ch[0] - 12), n, (-5, 5)), 300) * env(n, 0.6, 9, 1, 1.0, hold=bar), t0, 0.5, 0.12)
        ost = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12]                # piano ostinato, 8ths
        for e8 in range(8):
            add(piano(ost[e8 % 4], int(1.6 * SR), 0.55 + 0.25 * (e8 % 2 == 0)), t0 + e8 * beat / 2, 0.35 + 0.3 * (e8 % 2), 0.17 * (0.7 + 0.3 * e))
        if t0 > (HITS[0] - 4 * bar if HITS else DUR / 3):                     # toms grow in as the story builds
            for q, g in ((0, 1), (2.5, .6), (3, .8)):
                add(kick(int(.5 * SR), 120, 60, 1) * 0.8 + noise_hit(int(.5 * SR), 80, 400, .12) * 0.3, t0 + q * beat, 0.5, 0.22 * e * g)
    for h in HITS:                                                            # deep boom on each reveal
        n = int(3 * SR); t = np.arange(n) / SR; f = 34 + 60 * np.exp(-t / .05)
        boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .9) + lp(rng.normal(0, 1, n), 200) * np.exp(-t / .25) * 0.4
        add(boom, h, 0.5, 0.4)

elif STYLE == "keys":
    BPM = 84; beat = 60 / BPM; bar = 4 * beat; swing = 0.08
    PROG = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]   # Fmaj7 Em7 Dm7 Cmaj7
    BASS = [41, 40, 38, 36]
    nbar = int(np.ceil(DUR / bar)) + 1
    for b in range(nbar):
        t0 = b * bar; ch = PROG[b % 4]; e = intensity(t0)
        for hit_t in (0, 1.5 * beat, 2.5 * beat):                            # syncopated chord stabs
            for i, m in enumerate(ch): add(epiano(m, int(2.2 * SR), 0.8 if hit_t == 0 else 0.55), t0 + hit_t + i * 0.008, 0.35 + 0.1 * i, 0.12)
        for q in range(4):
            tq = t0 + q * beat
            if b >= 1 and q in (0, 2): add(kick(int(.3 * SR), 80, 45, .8), tq, 0.5, 0.3 * e)
            if b >= 1 and q in (1, 3): add(noise_hit(int(.3 * SR), 1200, 6000, .09), tq, 0.55, 0.18 * e)
            for e8 in (0, 1):
                tt = tq + e8 * beat / 2 + (swing * beat if e8 else 0)
                add(hp(rng.normal(0, 1, int(.06 * SR)), 6000) * np.exp(-np.arange(int(.06 * SR)) / SR / .02), tt, 0.65, 0.05 * e)
        nn = int(bar * SR); tt = np.arange(nn) / SR; f = mtof(BASS[b % 4])
        add(np.sin(2 * np.pi * f * tt) * env(nn, 0.01, 1.4) + 0.2 * np.sin(4 * np.pi * f * tt) * env(nn, 0.01, .4), t0, 0.5, 0.16)
        if b % 2 == 1:                                                        # a few soft melody notes (pentatonic)
            for k_ in range(3):
                m = [72, 74, 77, 79, 81][int(rng.integers(5))]; add(epiano(m, int(2 * SR), .6), t0 + (0.5 + k_ * 1.25) * beat, 0.6, 0.05)
else:
    raise SystemExit("unknown style " + STYLE)

# ------------------------------------------------------------------------------------------------ master
ir = rng.normal(0, 1, int(1.4 * SR)) * np.exp(-np.arange(int(1.4 * SR)) / SR / 0.35) * 0.010
L2 = L + fftconvolve(L, ir)[:N] * 0.6; R2 = R + fftconvolve(R, ir[::-1].copy())[:N] * 0.6
x = np.stack([hp(L2, 30), hp(R2, 30)], 1)[: int(DUR * SR)]
x = np.tanh(x / (np.percentile(np.abs(x), 99.9) + 1e-9) * 1.1) * 0.85                  # gentle soft clip
fi, fo = int(0.05 * SR), int(0.6 * SR); x[:fi] *= np.linspace(0, 1, fi)[:, None]; x[-fo:] *= np.linspace(1, 0.4, fo)[:, None]
wavfile.write(OUT, SR, (x * 32767).astype(np.int16))
