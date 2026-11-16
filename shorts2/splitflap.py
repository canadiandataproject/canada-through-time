"""Short #13 — Biggest federal contracts on a split-flap departures board, timed to a cue file.

  python3 shorts2/splitflap.py <cues.json> <out.mp4> [--stills t1,t2,...]

Data: web/data/money/contracts.json (Treasury Board proactive disclosure of contracts over $10,000; each contract counted
once at its latest total value, including amendments). Asserts keep the narration true.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]; FONTS = Path("/home/claude/fonts")
W, H, FPS = 1080, 1920, 30

c = json.loads((ROOT / "web/data/money/contracts.json").read_text())
tv = {k: sum(v[0] for v in d.values()) for k, d in c["by_proc"].items()}; TOT = sum(tv.values())
NCON = sum(sum(v[1] for v in d.values()) for d in c["by_proc"].values())
TN, NS = tv["TN"], tv["?"]
assert NCON > 1.1e6 and round(TN / 1e9) == 62 and round(NS / 1e9) == 69 and round(7 * TN / TOT) == 1
top = c["largest"][:8]
assert top[0]["name"].startswith("SkyAlyne") and round(top[0]["v"] / 1e9, 1) == 11.2 and top[1]["name"].startswith("Irving") and round(top[1]["v"] / 1e9, 1) == 10.8
SHORT = {"SkyAlyne Canada Limited Partnership": "SKYALYNE", "Irving Shipbuilding Inc.": "IRVING SHIPS", "Lockheed Martin Canada Inc.": "LOCKHEED MRTN",
         "Bgis Global Integrated Solutions Ca": "BGIS", "GROUPE SIGNATURE SUR LE SAINT LAURENT": "SIGNATURE SL", "Vancouver Shipyards Co Ltd": "VANCOUVER SHP",
         "CAE Military Aviation Training Inc.": "CAE MILITARY", "ESAP PROJECT CO LIMITED PARTNERSHIP": "ESAP PROJECT"}
DEPT = {"National Defence": "DEFENCE", "Public Services and Procurement Canada": "PSPC", "Department of Housing, Infrastructure and Communities": "INFRA",
        "Fisheries and Oceans Canada": "DFO"}
WHAT = {"Ships and boats": "SHIPS", "Aircraft": "AIRCRAFT"}
PROC = {"TC": "COMPETED", "OB": "COMPETED", "ST": "COMPETED", "AC": "ACAN", "TN": "NO COMP", "?": "NOT STATED"}

COLS = [("NO", 2), ("VENDOR", 13), ("$ BIL", 5)]   # chars per column; award type shown as a lamp
ROWS = [[f"{i+1:>2}", SHORT.get(x["name"], x["name"][:13].upper()), f"{x['v']/1e9:4.1f}"] for i, x in enumerate(top)]
LAMP = ["red" if x["proc"] == "TN" else "green" for x in top]

# summary board (end)
SUMMARY = [
    ["", "CONTRACTS", f"{NCON/1e6:.2f}M"],
    ["", "TOTAL VALUE", f"${TOT/1e9:.0f}B"],
    ["", "", ""],
    ["", "NO COMPETITN", f"${TN/1e9:.0f}B"],
    ["", " 1 DOLLAR IN", "7"],
    ["", "", ""],
    ["", "HOW AWARDED", f"${NS/1e9:.0f}B"],
    ["", " NOT STATED", "?"],
]

CHARS = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.$-=?#/&'"
CW, CH, GAP = 46, 86, 4
f_flap = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 58)
f_head = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 30)
f_title = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 96)
f_small = ImageFont.truetype(str(FONTS / "share-tech-mono-latin-400-normal.ttf"), 24)

def cell_img(ch, color=(240, 236, 220)):
    im = Image.new("RGB", (CW, CH), (22, 22, 24)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, CW - 1, CH - 1], 5, fill=(28, 28, 31))
    d.text((CW // 2, CH // 2 + 2), ch, font=f_flap, fill=color, anchor="mm")
    d.line([(0, CH // 2), (CW, CH // 2)], fill=(8, 8, 9), width=2)          # the hinge
    a = np.array(im, np.float32); a[:CH // 2] *= 1.06; a[CH // 2:] *= 0.92    # top half lit, bottom half shaded
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
CACHE = {}
def cimg(ch, col): k = (ch, col); CACHE.setdefault(k, cell_img(ch, col)); return CACHE[k]

NCH = sum(n for _, n in COLS) + len(COLS) - 1
BW = NCH * (CW + GAP) + 60 + 70; BH = 8 * (CH + 18) + 200

def text_at(rows, r, i):
    """Character i of row r's padded line (columns separated by a blank cell)."""
    s = ""
    for (name, n), v in zip(COLS, rows[r]):
        s += (v.rjust(n) if name in ("NO", "$ BIL") else v.ljust(n))[:n] + " "
    return s[i] if i < len(s) else " "

def flap_char(target, prev, t, t0, seed):
    """Flip through characters from prev to target starting at t0; each flip 0.05 s."""
    if t < t0: return prev, 0.0
    a, b = CHARS.find(prev), CHARS.find(target)
    if a < 0: a = 0
    if b < 0: b = 0
    steps = (b - a) % len(CHARS); steps = steps + len(CHARS) * (seed % 2) if steps < 6 else steps
    k = (t - t0) / 0.045
    if k >= steps: return target, 0.0
    return CHARS[(a + int(k)) % len(CHARS)], k - int(k)

def board(t, cues):
    im = Image.new("RGB", (BW, BH), (12, 12, 13)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, BW - 6, BH - 6], 18, outline=(52, 52, 56), width=4)
    title = "DEPARTURES" if t < cues["title_switch"] else ("BIGGEST CONTRACTS" if t < cues["phases"][-1]["t"] else "ALL CONTRACTS")
    d.text((40, 80), title, font=f_title, fill=(250, 200, 40), anchor="lm")
    x = 30
    for name, n in COLS:
        d.text((x + 4, 168), name, font=f_head, fill=(150, 150, 156), anchor="lm"); x += (n + 1) * (CW + GAP)
    phase = [p for p in cues["phases"] if p["t"] <= t]
    for r in range(8):
        for i in range(NCH):
            prev = " "; ch, sub = " ", 0.0
            for j, p in enumerate(phase):
                src = ROWS if p["board"] == "top" else SUMMARY if p["board"] == "summary" else None
                tgt = text_at(src, r, i) if src and r < p.get("rows", 8) else " "
                t0 = p["t"] + r * p.get("row_delay", 0.25) + (i * 0.013)
                ch, sub = flap_char(tgt, prev, t, t0, r * 31 + i)
                if t >= t0: prev = tgt if sub == 0 and ch == tgt else ch
            col = (240, 236, 220)
            for hl in cues.get("highlights", []):
                if hl["t0"] <= t < hl["t1"] and r == hl["row"] and (math.sin(t * 9) > -0.3 or not hl.get("blink")): col = tuple(hl["color"])
            ci = cimg(ch, col)
            if i == NCH - 1 and any(p["board"] == "top" for p in phase) and not any(p["board"] == "summary" for p in phase):
                lx, ly = 30 + NCH * (CW + GAP) + 32, 200 + r * (CH + 18) + CH // 2
                on = t > phase[0]["t"] + r * 0.18 + 1.0
                lc = {"green": (60, 220, 110), "red": (255, 60, 50)}[LAMP[r]] if on else (40, 40, 44)
                d.ellipse([lx - 20, ly - 20, lx + 20, ly + 20], fill=lc)
            px, py = 30 + i * (CW + GAP), 200 + r * (CH + 18)
            if sub > 0:      # mid-flip: squash the top half
                top = ci.crop((0, 0, CW, CH // 2)).resize((CW, max(1, int(CH // 2 * (1 - sub)))))
                im.paste(ci.crop((0, CH // 2, CW, CH)), (px, py + CH // 2)); im.paste(top, (px, py + CH // 2 - top.height))
            else: im.paste(ci, (px, py))
    return im

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def bg():
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - W / 2) / W, (yy - H * 0.45) / H)
    a = np.stack([34 - r * 34, 36 - r * 34, 42 - r * 36], -1) + np.random.default_rng(2).normal(0, 1.8, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
BG = bg()

def frame(t, cues):
    b = board(t, cues)
    # camera: perspective tilt + slow push; keyframes {t, z, tilt, pan}
    k = cues["camera"]; z, tilt, pan = k[0]["z"], k[0]["tilt"], k[0]["pan"]
    for a_, b_ in zip(k, k[1:]):
        if a_["t"] <= t <= b_["t"]:
            e = ease((t - a_["t"]) / (b_["t"] - a_["t"])); z = a_["z"] + (b_["z"] - a_["z"]) * e; tilt = a_["tilt"] + (b_["tilt"] - a_["tilt"]) * e; pan = a_["pan"] + (b_["pan"] - a_["pan"]) * e
        elif t > b_["t"]: z, tilt, pan = b_["z"], b_["tilt"], b_["pan"]
    sw = int(W * 0.94 * z * 1.0); sh = int(sw * BH / BW)
    bi = b.resize((sw, sh), Image.BICUBIC)
    # fake perspective: shrink the top edge by `tilt`
    dx = int(sw * tilt)
    coeffs = _persp([(0, 0), (sw, 0), (sw, sh), (0, sh)], [(dx, 0), (sw - dx, 0), (sw, sh), (0, sh)])
    bi = bi.transform((sw, sh), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    mask = Image.new("L", (sw, sh), 0); ImageDraw.Draw(mask).polygon([(dx, 0), (sw - dx, 0), (sw, sh), (0, sh)], fill=255)
    out = BG.copy(); x0 = W // 2 - sw // 2 + int(pan); y0 = int(H * 0.47 - sh / 2)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); glow.paste((250, 200, 40), (x0, y0, x0 + sw, y0 + sh)); glow = glow.filter(ImageFilter.GaussianBlur(60))
    out = Image.blend(out, Image.fromarray(np.clip(np.array(out, np.int16) + np.array(glow, np.int16) // 7, 0, 255).astype(np.uint8)), 1)
    out.paste(bi, (x0, y0), mask)
    d = ImageDraw.Draw(out)
    for cap in cues.get("captions", []):
        if cap["t0"] <= t < cap["t1"]:
            d.multiline_text((W // 2, 300), cap["text"], font=ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), cap.get("size", 84)), fill=(250, 246, 236),
                             anchor="mm", align="center", spacing=8, stroke_width=5, stroke_fill=(12, 12, 13))
    d.multiline_text((W // 2, H - 500), "Source: Treasury Board proactive disclosure,\ncontracts over $10,000. Value = total committed.\nLamp: green = competed, red = no competition.", font=f_small, fill=(150, 150, 156), anchor="mm", align="center", spacing=6)
    return out

def _persp(src, dst):
    m = []
    for (x, y), (X, Y) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); m.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    A = np.array(m, float); bb = np.array([v for p in src for v in p], float)
    return np.linalg.solve(A, bb).tolist()

def render(cp, out, stills=None):
    cues = json.loads(Path(cp).read_text()); n = int(round(cues["duration"] * FPS))
    if stills:
        for t in stills: frame(t, cues).save(f"{out}_{t:05.1f}.png")
        return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(frame(i / FPS, cues).tobytes())
    p.stdin.close(); p.wait(); print("wrote", out, n)

if __name__ == "__main__":
    st = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")] if "--stills" in sys.argv else None
    render(sys.argv[1], sys.argv[2], st)
