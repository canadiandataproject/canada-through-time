"""Short #12 — Ottawa's $493B receipt. A thermal receipt prints out of a printer, line by line, timed to a cue file.

  python3 shorts2/receipt.py <cues.json> <out.mp4> [--stills t1,t2,...]

Every amount comes from web/data/money/public_accounts.json (Public Accounts of Canada, Vol. II, gross expenditures by
standard object, fiscal year ending 2026) and web/data/population.json (Statistics Canada, July 1, 2025). Asserts stop
the build if the data no longer matches the narration.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = Path("/home/claude/fonts")
W, H, FPS = 1080, 1920, 30

# ---------------- data
pa = json.loads((ROOT / "web/data/money/public_accounts.json").read_text())
vals = dict(zip(pa["objects"], pa["totals"]["2026"]))            # thousands of dollars
TOTAL = sum(vals.values()) * 1000
pop = json.loads((ROOT / "web/data/population.json").read_text())
POP = pop["series"]["CAN"][pop["dates"].index("2025-07-01")]
PER = TOTAL / POP
B = lambda k: vals[k] * 1000 / 1e9
assert round(TOTAL / 1e9) == 493 and round(B("Transfer payments")) == 294 and round(B("Personnel")) == 67
assert round(B("Public debt charges")) == 48 and round(B("Professional and special services")) == 23 and round(PER, -1) == 11860

LABEL = {"Transfer payments": "TRANSFER PAYMENTS", "Personnel": "FEDERAL EMPLOYEES", "Public debt charges": "DEBT CHARGES",
         "Professional and special services": "CONSULTANTS & PROF. SERVICES", "Other subsidies and payments": "OTHER SUBSIDIES & PAYMENTS",
         "Acquisition of machinery and equipment": "MACHINERY & EQUIPMENT", "Rentals": "RENTALS", "Repair and maintenance": "REPAIR & MAINTENANCE",
         "Utilities, materials and supplies": "UTILITIES & SUPPLIES", "Acquisition of land, buildings and works": "LAND & BUILDINGS",
         "Transportation and communications": "TRAVEL & PHONES", "Information": "INFORMATION"}
order = sorted(vals, key=lambda k: -vals[k])
money = lambda b: f"${b:,.1f}B"

# ---------------- receipt layout (paper coordinates)
PW = 860; M = 54
f_mono = ImageFont.truetype(str(FONTS / "space-mono-latin-400-normal.ttf"), 30)
f_monob = ImageFont.truetype(str(FONTS / "space-mono-latin-700-normal.ttf"), 34)
f_big = ImageFont.truetype(str(FONTS / "space-mono-latin-700-normal.ttf"), 64)
f_huge = ImageFont.truetype(str(FONTS / "space-mono-latin-700-normal.ttf"), 92)
f_small = ImageFont.truetype(str(FONTS / "space-mono-latin-400-normal.ttf"), 22)

lines = []   # (key, kind, left, right, font, height)
def L(key, left="", right="", font=f_mono, h=46, kind="row"): lines.append(dict(key=key, kind=kind, left=left, right=right, font=font, h=h))
L("h0", "GOVERNMENT OF CANADA", font=f_monob, h=58, kind="center")
L("h1", "OTTAWA, ON  ·  RECEIPT 2025-26", font=f_small, h=34, kind="center")
L("h2", "APR 1 2025 – MAR 31 2026", font=f_small, h=40, kind="center")
L("d0", kind="dash", h=40)
for k in order:
    big = k in ("Transfer payments", "Personnel", "Public debt charges", "Professional and special services")
    L(k, LABEL[k], money(B(k)), font=f_monob if big else f_mono, h=78 if big else 46)
L("d1", kind="dash", h=40)
L("total", "TOTAL", f"${TOTAL/1e9:,.1f}B", font=f_big, h=104)
L("per", "PER PERSON (41.6M)", f"${PER:,.0f}", font=f_monob, h=64)
L("day", "PER PERSON, PER DAY", f"${PER/365:,.2f}", font=f_mono, h=52)
L("d2", kind="dash", h=40)
L("thx", "THANK YOU, TAXPAYER", font=f_monob, h=58, kind="center")
L("src", "Public Accounts of Canada 2025-26, Vol. II", font=f_small, h=30, kind="center")
L("src2", "Gross expenditures by type. Items may not add (rounding).", font=f_small, h=30, kind="center")
L("pad", kind="blank", h=90)
y = 70
for l in lines: l["y0"] = y; y += l["h"]; l["y1"] = y
PH = y + 40
ROW = {l["key"]: l for l in lines}

def paper_texture(w, h, seed=3):
    rng = np.random.default_rng(seed)
    base = np.full((h, w, 3), (246, 243, 236), np.float32)
    n = rng.normal(0, 1, (h // 2 + 1, w // 2 + 1)).astype(np.float32)
    n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255
    base -= (n[..., None] - 0.5) * 10
    x = np.linspace(-1, 1, w)[None, :, None]; base -= (x ** 6) * 26          # curl shading at the edges
    return np.clip(base, 0, 255).astype(np.uint8)

def build_paper():
    img = Image.fromarray(paper_texture(PW, PH)); d = ImageDraw.Draw(img)
    ink = (38, 36, 40)
    for l in lines:
        f = l["font"]; cy = l["y0"] + l["h"] // 2
        if l["kind"] == "center": d.text((PW // 2, cy), l["left"], font=f, fill=ink, anchor="mm")
        elif l["kind"] == "dash": d.text((PW // 2, cy), "-" * 38, font=f_mono, fill=ink, anchor="mm")
        elif l["kind"] == "row":
            d.text((M, cy), l["left"], font=f, fill=ink, anchor="lm"); d.text((PW - M, cy), l["right"], font=f, fill=ink, anchor="rm")
            lw = d.textlength(l["left"], font=f); rw = d.textlength(l["right"], font=f)
            dots = int((PW - 2 * M - lw - rw - 24) / d.textlength(".", font=f_mono))
            if dots > 2: d.text((M + lw + 12, cy), "." * dots, font=f_mono, fill=(120, 116, 120), anchor="lm")
    # thermal unevenness: faint horizontal banding
    a = np.array(img, np.float32); band = (np.sin(np.arange(PH) / 3.1) * 2.5)[:, None, None]; a += band
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # torn zig-zag top edge
    mask = Image.new("L", (PW, PH), 255); md = ImageDraw.Draw(mask)
    pts = [(x, 6 + (10 if (x // 18) % 2 else 0)) for x in range(0, PW + 18, 18)]
    md.polygon([(0, 0)] + pts + [(PW, 0)], fill=0)
    img.putalpha(mask)
    return img

PAPER = build_paper()

# ---------------- background, printer
def build_bg():
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W / 2) / W, (yy - H * 0.55) / H)
    base = np.stack([50 - r * 52, 44 - r * 47, 39 - r * 43], -1)           # warm dark counter, light pool
    base += rng.normal(0, 2.2, (H, W, 1))
    grain = (np.sin(xx / 7.0 + np.sin(yy / 90.0) * 3) * 3)[..., None]       # wood-ish grain
    return Image.fromarray(np.clip(base + grain, 0, 255).astype(np.uint8))
BG = build_bg()
MOUTH = 1470            # screen y of the printer slot (paper emerges upward from here)

def draw_printer(img, shake):
    d = ImageDraw.Draw(img)
    x0, x1 = W // 2 - 520, W // 2 + 520; top = MOUTH - 6 + shake
    d.rounded_rectangle([x0, top, x1, H + 40], 36, fill=(24, 24, 27))
    d.rounded_rectangle([x0 + 10, top + 8, x1 - 10, top + 40], 14, fill=(36, 36, 40))
    d.rectangle([W // 2 - PW // 2 - 14, top - 2, W // 2 + PW // 2 + 14, top + 12], fill=(10, 10, 12))   # slot
    d.ellipse([x1 - 120, top + 90, x1 - 84, top + 126], fill=(60, 200, 110) if shake else (40, 120, 70))   # status LED
    d.text((x0 + 60, top + 108), "FISCAL-O-MATIC 2026", font=f_small, fill=(90, 90, 96), anchor="lm")

# ---------------- timeline
def load_cues(p):
    c = json.loads(Path(p).read_text())
    return c
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def printed_y(t, cues):
    """Paper y printed so far. Each cue {key, t} finishes printing that row at t (0.35 s per row, chained)."""
    y = 0.0
    for c in cues["print"]:
        row = ROW[c["key"]]; t1 = c["t"]; t0 = t1 - c.get("dur", 0.35)
        if t >= t1: y = max(y, row["y1"])
        elif t > t0: y = max(y, row["y0"] + (row["y1"] - row["y0"]) * (t - t0) / (t1 - t0))
    return y

def camera(t, cues):
    """zoom and rotation keyframes; pullback at the end."""
    k = cues["camera"]; py = printed_y(t, cues); pyy = MOUTH - py
    fyk = lambda kf: (pyy + (ROW[kf["focus"]]["y0"] + ROW[kf["focus"]]["y1"]) / 2) if kf.get("focus") else MOUTH - 470
    z, rot, fy = k[0]["z"], k[0]["rot"], fyk(k[0])
    for a, b in zip(k, k[1:]):
        if a["t"] <= t <= b["t"]:
            e = ease((t - a["t"]) / (b["t"] - a["t"])); z = a["z"] + (b["z"] - a["z"]) * e; rot = a["rot"] + (b["rot"] - a["rot"]) * e; fy = fyk(a) + (fyk(b) - fyk(a)) * e
        elif t > b["t"]: z, rot, fy = b["z"], b["rot"], fyk(b)
    return z, rot + 0.6 * math.sin(t * 0.7), fy

f_hand = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 64)
def frame(t, cues):
    py = printed_y(t, cues)
    z, rot, fyc = camera(t, cues)
    feeding = any(c["t"] - c.get("dur", 0.35) < t < c["t"] for c in cues["print"])
    # world canvas: printer slot at MOUTH; paper bottom (printed edge) sits at slot
    strip = PAPER.crop((0, 0, PW, int(max(py, 1)) + 1))
    world = BG.copy().convert("RGBA")
    px = W // 2 - PW // 2; pyy = MOUTH - strip.height
    shadow = Image.new("RGBA", strip.size, (0, 0, 0, 0)); shadow.putalpha(strip.getchannel("A").point(lambda v: v * 0.45))
    world.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)), (px + 14, pyy + 18))
    world.alpha_composite(strip, (px, pyy))
    # pen circle and stamp annotations (paper coordinates)
    d = ImageDraw.Draw(world)
    for a in cues.get("circles", []):
        if t > a["t"]:
            row = ROW[a["key"]]; prog = ease((t - a["t"]) / 0.6)
            cy = pyy + (row["y0"] + row["y1"]) / 2; bx = [px + 22, cy - row["h"] * 0.62, px + PW - 22, cy + row["h"] * 0.62]
            pts = [((bx[0] + bx[2]) / 2 + (bx[2] - bx[0]) / 2 * math.cos(-math.pi / 2 + th) * (1 + 0.02 * math.sin(th * 3)),
                    (bx[1] + bx[3]) / 2 + (bx[3] - bx[1]) / 2 * math.sin(-math.pi / 2 + th)) for th in np.linspace(0, 2 * math.pi * 1.06 * prog, 90)]
            if len(pts) > 1: d.line(pts, fill=(200, 30, 36, 235), width=7, joint="curve")
            if a.get("note") and prog >= 1: d.text(((bx[0] + bx[2]) / 2 + 40, cy), a["note"], font=ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 46), fill=(200, 30, 36, 245), anchor="mm", stroke_width=5, stroke_fill=(246, 243, 236, 255))
    for s in cues.get("stamps", []):
        if t > s["t"]:
            k = min(1, (t - s["t"]) / 0.18); sc = 1.6 - 0.6 * k
            st = Image.new("RGBA", (760, 220), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
            sd.rounded_rectangle([8, 8, 752, 212], 18, outline=(190, 24, 32, 230), width=12)
            sd.text((380, 112), s["text"], font=ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 118), fill=(190, 24, 32, 230), anchor="mm")
            rng = np.random.default_rng(5); a = np.array(st); holes = rng.random(a.shape[:2]) < 0.10; a[..., 3][holes] = 0
            st = Image.fromarray(a).rotate(-9, expand=True, resample=Image.BICUBIC)
            st = st.resize((int(st.width * sc), int(st.height * sc)))
            row = ROW[s["key"]]; cy = pyy + (row["y0"] + row["y1"]) / 2
            world.alpha_composite(st, (int(W / 2 - st.width / 2), int(cy - st.height / 2)))
    draw_printer(world, 2 if feeding else 0)
    # camera: zoom about a focus point that follows the newest line, rotate slightly
    fx, fy = W / 2, fyc
    cam = world.transform(world.size, Image.AFFINE, _affine(z, rot, fx, fy), resample=Image.BILINEAR, fillcolor=(14, 12, 11, 255))
    out = cam.convert("RGB")
    # hook caption (top), stays readable
    for cap in cues.get("captions", []):
        if cap["t0"] <= t < cap["t1"]:
            a = min(1 if cap["t0"] == 0 else (t - cap["t0"]) / 0.25, (cap["t1"] - t) / 0.25, 1)
            ov = Image.new("RGBA", out.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.multiline_text((W // 2, 230), cap["text"], align="center", spacing=10, font=ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), cap.get("size", 92)),
                    fill=(250, 246, 236, int(255 * a)), anchor="mm", stroke_width=6, stroke_fill=(20, 18, 16, int(220 * a)))
            out = Image.alpha_composite(out.convert("RGBA"), ov).convert("RGB")
    return out

def _affine(z, rot_deg, fx, fy):
    """Inverse map for PIL: output pixel -> input pixel. Zoom z and rotate about (fx, fy), placing (fx, fy) at screen (W/2, H*0.52)."""
    r = math.radians(rot_deg); c, s = math.cos(r) / z, math.sin(r) / z
    ox, oy = W / 2, H * 0.52
    return (c, s, fx - c * ox - s * oy, -s, c, fy + s * ox - c * oy)

def render(cues_path, out, stills=None):
    cues = load_cues(cues_path); dur = cues["duration"]; n = int(round(dur * FPS))
    if stills:
        for t in stills: frame(t, cues).save(f"{out}_{t:05.1f}.png")
        return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(frame(i / FPS, cues).tobytes())
    p.stdin.close(); p.wait()
    print("wrote", out, n, "frames")

if __name__ == "__main__":
    st = None
    if "--stills" in sys.argv: st = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]
    render(sys.argv[1], sys.argv[2], st)
