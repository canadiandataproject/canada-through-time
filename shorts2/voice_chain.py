"""Studio voice chain for narration takes: clean -> reshape -> finish.

  python3 shorts2/voice_chain.py <take.m4a|wav> <out.wav> [--formant 0.94] [--pitch 98] [--clean-only]

1. Clean: DeepFilterNet3 (runs in /home/claude/dfenv) removes room noise and some room echo, with the
   attenuation capped at 15 dB so the voice keeps its air instead of sounding gated or "AI".
2. Reshape (optional): Praat "Change gender" (PSOLA). --formant scales the vocal-tract resonances
   (<1 = bigger, deeper-sounding; >1 = smaller, lighter); --pitch sets the new median pitch in Hz.
   Your delivery, timing and pitch movement are kept; only voice size and centre pitch move.
3. Finish: rumble cut, low-mid mud cut, presence and air lift, de-esser, gentle 2.5:1 compression,
   peak ceiling. The final loudness is set in mix.py (-16 LUFS).
"""
import subprocess, sys, tempfile
from pathlib import Path
import numpy as np, parselmouth as pm
from parselmouth.praat import call

args = sys.argv[1:]; src, out = args[0], args[1]
opt = lambda k, d: float(args[args.index(k) + 1]) if k in args else d
formant, pitch, clean_only = opt("--formant", 1.0), opt("--pitch", 0.0), "--clean-only" in args
SR = 48000; tmp = Path(tempfile.mkdtemp())

# 0. decode to 48 kHz mono
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", str(SR), str(tmp / "in.wav")], check=True)
# 1. clean
subprocess.run(["/home/claude/dfenv/bin/python", "-c", f"""
import soundfile as sf, torch
from df.enhance import init_df, enhance
m, s, _ = init_df('/home/claude/dfmodel'); a, _ = sf.read('{tmp/'in.wav'}', dtype='float32')
y = enhance(m, s, torch.from_numpy(a)[None], atten_lim_db=15)
sf.write('{tmp/'clean.wav'}', y[0].numpy(), s.sr())"""], check=True)
x = tmp / "clean.wav"
# 2. reshape
if not clean_only and (formant != 1.0 or pitch):
    s = pm.Sound(str(x))
    y = call(s, "Change gender", 60, 300, formant, pitch, 1.0, 1.0)
    y.save(str(tmp / "shape.wav"), "WAV"); x = tmp / "shape.wav"
# 3. finish
chain = ",".join([
    "highpass=f=75:poles=2",
    "equalizer=f=280:t=q:w=1.1:g=-2.5",      # low-mid mud (phone/room boxiness)
    "equalizer=f=3800:t=q:w=1.0:g=2",         # presence: words cut through the music
    "highshelf=f=9500:g=2.5",                 # air
    "deesser=i=0.35:m=0.5:f=0.5",
    "acompressor=threshold=-22dB:ratio=2.5:attack=12:release=150:makeup=3",
    "alimiter=limit=0.89:attack=3:release=60",
])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(x), "-af", chain, "-ar", str(SR), out], check=True)
print("wrote", out, f"(formant {formant}, pitch {pitch or 'unchanged'})")
