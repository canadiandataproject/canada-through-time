"""Calm bed for the Shorts (v4 audio). Synthesized from scratch: no samples, no third-party audio.
Slow warm pad (detuned soft saws through a low-pass), a quiet sine bass, and a few soft felt-piano notes. No drums.
Chords change every 4 s: Dmaj9 - Bm9 - Gmaj7 - Aadd9. Seeded, so the same length gives the same file.
Usage: make_bed_calm.py <seconds> <out.wav> [steady]
"steady": chords and bass cross-fade with equal-power curves so the level never swells or dips (no "breathing")."""
import sys, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
SR = 48000; DUR = float(sys.argv[1]); OUT = sys.argv[2]; STEADY = len(sys.argv) > 3 and sys.argv[3] == 'steady'; XF = 1.6
rng = np.random.default_rng(5); n = int(SR * (DUR + 3)); t = np.arange(n) / SR
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
L = np.zeros(n); R = np.zeros(n)
CH = [[50, 57, 61, 64, 66], [47, 54, 57, 61, 62], [43, 50, 54, 57, 62], [45, 52, 57, 59, 64]]
SEC = 4.0
def pad(m, ln):
    k = int(ln * SR); tt = np.arange(k) / SR; f = mtof(m); s = np.zeros(k)
    for det in ((0.0, 0.0, 0.0) if STEADY else (-0.12, 0.0, 0.11)):   # steady: no detune, so no slow beating between voices
        ph = 2 * np.pi * f * (1 + det / 100) * tt + rng.uniform(0, 6.28)
        s += np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    if STEADY:   # equal-power fade in and out over XF seconds; neighbours overlap by exactly XF, so sin²+cos² keeps power constant
        a = np.sin(np.pi / 2 * np.clip(tt / XF, 0, 1)); r = np.sin(np.pi / 2 * np.clip((ln - tt) / XF, 0, 1))
        return s * a * r / 3
    a = np.minimum(tt / 1.4, 1); r = np.minimum((ln - tt) / 1.6, 1)
    return s * a * np.clip(r, 0, 1) / 3
nb = int(np.ceil((DUR + 1) / SEC))
if STEADY:
    # Each pitch is ONE continuous tone for the whole bed; its level is the equal-power sum of the chords it belongs to.
    # A note shared by two neighbouring chords never restarts (no phase cancellation); others cross-fade over XF seconds.
    w = []
    for b_ in range(nb):
        a0, a1 = b_ * SEC - XF / 2, (b_ + 1) * SEC + XF / 2
        w.append(np.clip(np.minimum((t - a0) / XF, (a1 - t) / XF), 0, 1) if b_ else np.clip((a1 - t) / XF, 0, 1))
    tones = {}
    for b_ in range(nb):
        for m in CH[b_ % 4] + [CH[b_ % 4][0] - 12]: tones.setdefault(m, np.zeros(n))
    for b_ in range(nb):
        for m in set(CH[b_ % 4] + [CH[b_ % 4][0] - 12]): tones[m] += w[b_]
    for idx, (m, e) in enumerate(sorted(tones.items())):
        f = mtof(m); ph = 2 * np.pi * f * t + (m * 0.618) % 6.28
        bass = m < 48
        s = (np.sin(ph) * (0.10 if bass else 0.06)) if bass else (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)) * 0.06 / 1.2
        s = s * np.sqrt(np.clip(e, 0, 1)); pan = 0.5 if bass else 0.3 + 0.4 * (idx % 5) / 4
        L += (1 - pan) * s; R += pan * s
else:
    for b in range(nb):
        t0 = b * SEC - (XF / 2 if STEADY else 0); ch = CH[b % 4]
        for i, m in enumerate(ch):
            s = pad(m, SEC + XF if STEADY else SEC + 1.8) * 0.06; i0 = max(0, int(t0 * SR)); s = s[int(max(0, -t0) * SR):]; pan = 0.3 + 0.4 * i / 4; j = min(n, i0 + len(s))
            L[i0:j] += (1 - pan) * s[: j - i0]; R[i0:j] += pan * s[: j - i0]
        k = int(((SEC + XF) if STEADY else (SEC + 0.5)) * SR); tt = np.arange(k) / SR; f = mtof(ch[0] - 12)
        env = np.sin(np.pi / 2 * np.clip(tt / XF, 0, 1)) * np.sin(np.pi / 2 * np.clip((k / SR - tt) / XF, 0, 1)) if STEADY else np.minimum(tt / 0.6, 1) * np.clip((SEC + 0.5 - tt) / 0.8, 0, 1)
        bs = np.sin(2 * np.pi * f * tt) * env * 0.10
        if STEADY and t0 < 0: bs = bs[int(-t0 * SR):]
        i0 = max(0, int(t0 * SR)); j = min(n, i0 + len(bs)); L[i0:j] += bs[: j - i0]; R[i0:j] += bs[: j - i0]

# a few soft felt-piano notes (fundamental + quiet octave, slow decay), well spaced
NOTES = [74, 76, 78, 81, 83]
for b in range(1, nb):
    if not STEADY and rng.random() < 0.6:
        st = b * SEC + rng.choice([0.5, 1.5, 2.5]); m = NOTES[rng.integers(len(NOTES))]
        k = int(3.0 * SR); tt = np.arange(k) / SR; f = mtof(m)
        s = (np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(4 * np.pi * f * tt)) * np.minimum(tt / 0.012, 1) * np.exp(-tt * 1.6) * 0.035
        i0 = int(st * SR); j = min(n, i0 + k)
        if i0 >= n: continue
        L[i0:j] += 0.45 * s[: j - i0]; R[i0:j] += 0.55 * s[: j - i0]
sos = butter(2, 2200, btype="low", fs=SR, output="sos"); L = sosfilt(sos, L); R = sosfilt(sos, R)
ir = rng.standard_normal(int(1.8 * SR)) * np.exp(-np.arange(int(1.8 * SR)) / SR * 3.2) * 0.012     # soft room
L = L + fftconvolve(L, ir)[:n]; R = R + fftconvolve(R, ir[::-1].copy())[:n]
if STEADY:   # hold the level even: divide by a slow (1.5 s) loudness envelope, gain kept within 0.4x-2.5x
    k = int(1.5 * SR); e = np.sqrt(np.convolve((L ** 2 + R ** 2) / 2, np.ones(k) / k, "same")) + 1e-9
    g = np.clip(np.median(e[int(2 * SR):-int(3 * SR)]) / e, 0.4, 2.5); g = np.convolve(g, np.ones(int(0.3 * SR)) / int(0.3 * SR), "same")
    L = L * g; R = R * g
m = int(DUR * SR); L = L[:m]; R = R[:m]
fade = np.ones(m); fi = int(0.8 * SR); fo = int(1.5 * SR); fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0.3, fo)
x = np.stack([L * fade, R * fade], 1); x = x / np.abs(x).max() * 0.8
wavfile.write(OUT, SR, (x * 32767).astype(np.int16))
