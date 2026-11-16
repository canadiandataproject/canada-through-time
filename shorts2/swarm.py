"""Short #15 — Temporary residents as a particle swarm that assembles itself into the numbers.

  python3 shorts2/swarm.py <cues.json> <out.mp4> [--stills t1,...]

Data: web/data/more/npr.json (Statistics Canada 17-10-0121-01, non-permanent residents on July 1; 2026 preliminary) and
web/data/population.json (MB + SK, July 1, 2025). One dot = 2,000 people, coloured by permit type.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]; FONTS = Path("/home/claude/fonts")
W, H, FPS = 1080, 1920, 30
PER = 2000

n = json.loads((ROOT / "web/data/more/npr.json").read_text())["data"]["CAN"]
pop = json.loads((ROOT / "web/data/population.json").read_text()); i25 = pop["dates"].index("2025-07-01")
MBSK = pop["series"]["MB"][i25] + pop["series"]["SK"][i25]
T = {y: n[str(y)]["total"] for y in (2021, 2024, 2025, 2026)}
assert round(T[2021] / 1e6, 1) == 1.3 and round(T[2025] / 1e6, 1) == 2.9 and round(T[2026] / 1e6, 1) == 2.8 and T[2025] > MBSK
assert round(n["2024"]["study"], -3) == 649000 and n["2026"]["study"] < 400000 and n["2026"]["asylum"] > n["2025"]["asylum"] and n["2026"]["work"] > n["2025"]["work"]
TYPES = ["work", "study", "asylum", "work_study", "other"]
COL = {"work": (255, 178, 64), "study": (64, 210, 255), "asylum": (255, 82, 110), "work_study": (150, 230, 120), "other": (170, 170, 190)}
NAME = {"work": "WORK PERMIT", "study": "STUDY PERMIT", "asylum": "ASYLUM CLAIMANT", "work_study": "WORK + STUDY", "other": "OTHER"}
cnt = lambda y, k: int(round(n[str(y)][k] / PER))
NMAX = {k: max(cnt(y, k) for y in range(2021, 2027)) for k in TYPES}
TYPE = np.concatenate([[j] * NMAX[k] for j, k in enumerate(TYPES)]); RANK = np.concatenate([np.arange(NMAX[k]) for k in TYPES]); N = len(TYPE)
def active(y): return np.array([RANK[i] < cnt(y, TYPES[TYPE[i]]) for i in range(N)])

f_glyph = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 470)
f_cap = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 76)
f_lab = ImageFont.truetype(str(FONTS / "oswald-latin-400-normal.ttf"), 40)
f_src = ImageFont.truetype(str(FONTS / "share-tech-mono-latin-400-normal.ttf"), 24)

def glyph_targets(text, k, cy=880, seed=0):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text((W // 2, cy), text, font=f_glyph, fill=255, anchor="mm")
    ys, xs = np.nonzero(np.array(m) > 128); rng = np.random.default_rng(seed)
    idx = rng.choice(len(xs), k, replace=len(xs) < k)
    return np.stack([xs[idx], ys[idx]], 1).astype(np.float32) + rng.normal(0, 1.2, (k, 2))

def column_targets(act, y):
    """Dots stacked into one column per type (a bar chart made of people)."""
    out = np.zeros((N, 2), np.float32); x0s = np.linspace(140, W - 140, len(TYPES))
    for j, k in enumerate(TYPES):
        ids = np.where((TYPE == j) & act)[0]
        for q, i in enumerate(ids):
            out[i] = (x0s[j] + (q % 12 - 5.5) * 13.5, 1380 - (q // 12) * 13.5)
    return out

def build_targets(cues):
    """Targets per phase: [(t, year, kind, payload)] -> (positions, active mask)."""
    res = []
    for p in cues["phases"]:
        act = active(p["year"])
        if p["kind"] == "glyph":
            pos = np.full((N, 2), np.nan, np.float32); ids = np.where(act)[0]; pos[ids] = glyph_targets(p["text"], len(ids), seed=p["year"])
        else: pos = column_targets(act, p["year"])
        res.append((p["t"], act, pos, p))
    return res

def simulate(cues, upto_frame):
    """Deterministic spring + noise simulation; yields (frame_index, positions, alive_alpha)."""
    rng = np.random.default_rng(11); tg = build_targets(cues)
    ang = rng.uniform(0, 2 * math.pi, N); rad = rng.uniform(260, 620, N)
    P = np.stack([W / 2 + np.cos(ang) * rad, H * 0.46 + np.sin(ang) * rad], 1).astype(np.float32)
    V = np.zeros_like(P); A = np.zeros(N, np.float32); phase_off = rng.uniform(0, 2 * math.pi, N)
    exit_dir = np.stack([np.cos(ang), np.sin(ang)], 1) * 2000
    for f in range(-20, upto_frame + 1):          # 20-frame pre-roll so frame 1 is already mid-assembly
        t = max(0, f) / FPS; cur = [x for x in tg if x[0] <= t] or tg[:1]
        _, act, pos, p = cur[-1]
        tgt = np.where(np.isnan(pos), np.array([W / 2, H * 0.46]) + exit_dir, pos)
        tgt = np.where(act[:, None], tgt, np.array([W / 2, H * 0.46]) + exit_dir)      # inactive dots fly off
        wob = np.stack([np.sin(t * 1.3 + phase_off), np.cos(t * 1.1 + phase_off * 1.7)], 1) * 5
        k = p.get("stiff", 0.06); V = V * 0.80 + (tgt + wob - P) * k + rng.normal(0, 0.6, P.shape); P = P + V
        A = A + (act.astype(np.float32) - A) * 0.08
        if f >= 0: yield f, P, A, V, p

def frame_img(P, A, V, p, t, cues):
    base = Image.new("RGB", (W, H), (6, 10, 18)); d = ImageDraw.Draw(base, "RGBA")
    # faint aurora gradient band
    for yy in range(0, H, 6):
        g = math.exp(-((yy - 600 - 80 * math.sin(t * 0.2)) / 520) ** 2)
        d.rectangle([0, yy, W, yy + 6], fill=(10, int(30 * g), int(40 * g), 255))
    glow = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(glow)
    for i in np.argsort(TYPE):
        if A[i] < 0.03: continue
        x, y = P[i]; c = COL[TYPES[TYPE[i]]]; a = A[i]
        sp = min(10, float(np.hypot(*V[i])))
        if sp > 2: d.line([(x - V[i][0] * 1.6, y - V[i][1] * 1.6), (x, y)], fill=(*c, int(110 * a)), width=4)   # motion trail
        d.ellipse([x - 5.5, y - 5.5, x + 5.5, y + 5.5], fill=(*c, int(255 * a)))
        gd.ellipse([x - 9, y - 9, x + 9, y + 9], fill=tuple(int(v * a * 0.5) for v in c))
    out = Image.fromarray(np.clip(np.array(base, np.int16) + np.array(glow.filter(ImageFilter.GaussianBlur(10)), np.int16), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    for cap in cues.get("captions", []):
        if cap["t0"] <= t < cap["t1"]:
            d.multiline_text((W // 2, cap.get("y", 300)), cap["text"], font=ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), cap.get("size", 76)),
                             fill=tuple(cap.get("color", (245, 245, 250))), anchor="mm", align="center", spacing=8)
    if p["kind"] == "columns":
        xs = np.linspace(140, W - 140, len(TYPES))
        for j, k in enumerate(TYPES):
            d.text((xs[j], 1430), NAME[k].replace(" ", "\n", 1), font=f_lab, fill=COL[k], anchor="ma", align="center")
            d.text((xs[j], 1530), f"{n[str(p['year'])][k]/1000:,.0f}K", font=f_lab, fill=(230, 230, 236), anchor="ma")
    # legend (glyph phases)
    else:
        x = 60
        for k in TYPES[:3]:
            d.ellipse([x, 1406, x + 22, 1428], fill=COL[k]); d.text((x + 34, 1417), NAME[k].split()[0], font=f_lab, fill=COL[k], anchor="lm"); x += 320
    d.text((W // 2, 1480 if p["kind"] != "columns" else 1600), f"1 dot = {PER:,} people · July 1 · Statistics Canada 17-10-0121 (2026 preliminary)", font=f_src, fill=(120, 130, 150), anchor="mm")
    return out

def render(cp, out, stills=None):
    cues = json.loads(Path(cp).read_text()); nfr = int(round(cues["duration"] * FPS))
    want = set(int(round(s * FPS)) for s in stills) if stills else None
    if stills:
        for f, P, A, V, p in simulate(cues, max(want)):
            if f in want: frame_img(P, A, V, p, f / FPS, cues).save(f"{out}_{f / FPS:05.1f}.png")
        return
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f, P, A, V, p in simulate(cues, nfr - 1): pr.stdin.write(frame_img(P, A, V, p, f / FPS, cues).tobytes())
    pr.stdin.close(); pr.wait(); print("wrote", out, nfr)

if __name__ == "__main__":
    st = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")] if "--stills" in sys.argv else None
    render(sys.argv[1], sys.argv[2], st)
