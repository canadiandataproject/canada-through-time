"""Short #16 — a city spreading out, 1975–2020, drawn from the explorer's own city picture (web/data/sprawl/<slug>.png) and
totals (web/data/sprawl/sprawl.json), with the cards and timings from a cue file.

  python3 shorts2/sprawl.py <cues.json> <out.mp4> [--stills t1,t2,...]

Data: European Commission JRC, GHS-BUILT-S R2023A (100 m), reprojected by pipeline/ingest_sprawl.py. Each 100 m square belongs to
the first satellite snapshot (1975, 1985, 1990, 2000, 2010, 2020) in which buildings covered 20% of it. The year counter ticks one
year at a time; at each snapshot year the picture is exactly that snapshot. Between snapshots, that snapshot's new squares appear
outward from land already built (nearest first): the order is illustrative, the description says so. Backdrop: shaded relief
(Copernicus DEM GLO-30) and water (ESA WorldCover 2021) from pipeline/ingest_terrain.py, for orientation only.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]; FONTS = Path("/home/claude/fonts")
W, H, FPS = 1080, 1920, 30
PAPER = (251, 248, 241); LAND = (240, 234, 222); WATER = (138, 178, 205); INK = (29, 35, 38); ACC = (194, 64, 42); MUTE = (92, 96, 98)
EPC = [(52, 48, 42), (104, 92, 76), (146, 128, 98), (196, 164, 104), (222, 132, 78), ACC]   # oldest dark → newest the accent (as in the explorer)
f_big = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 128)
f_mid = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 84)
f_lab = ImageFont.truetype(str(FONTS / "oswald-latin-400-normal.ttf"), 44)
f_year = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 96)
f_src = ImageFont.truetype(str(FONTS / "share-tech-mono-latin-400-normal.ttf"), 25)
f_leg = ImageFont.truetype(str(FONTS / "oswald-latin-400-normal.ttf"), 32)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import MODE as STYLE, font

def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def use_route(mode):
    """New identity (2026-11-17): Blue hour (dark) or Whiteout (light), Funnel Display/Sans + Martian Mono. No paper, no orange.
    Then = dim, now = lit: snapshots run from a muted steel blue (1975) to the brightest tone (2020)."""
    global PAPER, LAND, WATER, INK, ACC, MUTE, EPC, OFF, GLASS, f_big, f_mid, f_lab, f_year, f_src, f_leg
    M = STYLE[mode]
    PAPER = hexrgb(M["bg"]); INK = hexrgb(M["ink"]); ACC = hexrgb(M["accent"]); MUTE = hexrgb(M["ink3"]); GLASS = M["glass"]
    if mode == "dark":
        LAND = (30, 52, 94); WATER = (8, 20, 50)
        EPC = [hexrgb(x) for x in ("#5F80B8", "#7493C8", "#8EAED9", "#ADCBEB", "#D3EAFB", "#FFFFFF")]; OFF = (40, 60, 102)
    else:
        LAND = hexrgb(M["land"]); WATER = (150, 182, 222)
        EPC = [hexrgb(x) for x in ("#B4C2D8", "#8FA3C4", "#6B82AE", "#4A62A0", "#2D45B8", "#1E3CFF")]; OFF = (200, 210, 224)
    f_big = font("display", 132, 700); f_mid = font("display", 92, 700); f_lab = font("ui", 44, 520)
    f_year = font("mono", 84, 600); f_src = font("mono", 18, 400); f_leg = font("mono", 28, 500)

GLASS = None; OFF = (215, 208, 196)

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def load(cues):
    meta = json.loads((ROOT / "web/data/sprawl/sprawl.json").read_text())
    c = next(x for x in meta["cities"] if x["slug"] == cues["city"])
    ep = np.array(Image.open(ROOT / f"web/data/sprawl/{c['slug']}.png"))
    assert list(ep.shape) == c["size"] and [int((ep == k).sum()) for k in range(1, 7)] == c["new_cells"]
    # every number on a card is checked against the data file here, so a typo in the cue file can't reach the video
    k = c["km2"]; E = meta["epochs"]
    for chk in cues["checks"]:
        got = round(k[E.index(chk["epoch"])], chk.get("dp", 0)) if "epoch" in chk else round(k[E.index(chk["b"])] - k[E.index(chk["a"])], chk.get("dp", 0))
        assert got == chk["value"], (chk, got)
    # when each square appears: at a snapshot year exactly that snapshot; between snapshots, nearest-to-built-land first
    E_ = meta["epochs"]; appear = np.full(ep.shape, np.inf, np.float32); appear[ep == 1] = E_[0]
    for k in range(2, 7):
        new = ep == k
        if not new.any(): continue
        dist = distance_transform_edt(~((ep >= 1) & (ep < k)))
        order = dist[new].argsort().argsort() / max(1, new.sum() - 1)
        appear[new] = E_[k - 2] + (E_[k - 1] - E_[k - 2]) * (0.04 + 0.96 * order)
    assert all(((appear <= e) == ((ep >= 1) & (ep <= i + 1))).all() for i, e in enumerate(E_))   # every snapshot year is exact
    rel = np.array(Image.open(ROOT / f"web/data/sprawl/{c['slug']}_relief.png").convert("L")).astype(np.float32) / 255
    wat = np.array(Image.open(ROOT / f"web/data/sprawl/{c['slug']}_water.png").convert("L")) > 0
    if "mode" in cues: use_route(cues["mode"])
    land = np.array(LAND, np.float32) * (0.68 + 0.38 * rel[..., None])            # land tinted by the hillshade
    land[wat] = np.array(WATER, np.float32) * (0.92 + 0.08 * rel[wat][..., None])
    bg = Image.fromarray(np.clip(land, 0, 255).astype(np.uint8))
    return meta, c, ep, appear, bg

def city_frame(ep, appear, year, bg, size):
    """Every square that has appeared by `year`, in its snapshot's colour, over the relief."""
    n = ep.shape[0]; on = appear <= year
    rgba = np.zeros((n, n, 4), np.uint8)
    for k in range(1, 7):
        m = on & (ep == k); rgba[m, :3] = EPC[k - 1]; rgba[m, 3] = 235
    lay = Image.fromarray(rgba, "RGBA").resize((n * 3, n * 3), Image.NEAREST).resize((size, size), Image.LANCZOS)
    out = bg.resize((size, size), Image.LANCZOS).convert("RGBA"); out.alpha_composite(lay); return out.convert("RGB")

def card(d, c, a):
    y = c.get("y", 250); big = c["big"]; fb = f_big if len(big) <= 14 else f_mid
    top = y - (150 if c.get("kick") else 95); bot = y + (150 if c.get("sub") else 85)
    d.rounded_rectangle([50, top, W - 50, bot], 28, fill=(*GLASS[:3], int(GLASS[3] * a * 1.3)) if GLASS else (*PAPER, int(236 * a)))
    if c.get("kick"): d.text((W // 2, y - 98), c["kick"], font=f_lab, fill=(*ACC, int(255 * a)), anchor="mm")
    d.text((W // 2, y), big, font=fb, fill=(*INK, int(255 * a)), anchor="mm")
    if c.get("sub"): d.text((W // 2, y + 104), c["sub"], font=f_lab, fill=(*INK, int(255 * a)), anchor="mm")

def year_at(t, cues, E):
    tk = cues["tick"]                       # {"t0": start, "t1": end}: years run E[0] → E[-1] one at a time
    if t <= tk["t0"]: return E[0]
    if t >= tk["t1"]: return E[-1]
    return E[0] + (E[-1] - E[0]) * (t - tk["t0"]) / (tk["t1"] - tk["t0"])

def frame(t, cues, meta, c, ep, appear, bg):
    E = meta["epochs"]; yf = year_at(t, cues, E); yr = int(math.floor(yf + 1e-6))
    base = city_frame(ep, appear, yf, bg, 1080)
    z = 1.0; cx = cy = 540
    oz = cues.get("open_zoom")            # opening: the 1975 city fills the frame, then the camera eases back to all of it
    if oz and t < oz["t1"]: z = 1 + (oz["from"] - 1) * (1 - ease(t / oz["t1"]))
    for p in cues.get("push", []):
        if p["t0"] <= t <= p["t1"]:
            e = ease((t - p["t0"]) / p["ramp"]) if t < p["t0"] + p["ramp"] else (1 - ease((t - (p["t1"] - p["ramp"])) / p["ramp"]) if t > p["t1"] - p["ramp"] else 1)
            z = 1 + (p["zoom"] - 1) * e; cx = 540 + (p["at"][0] * 1080 - 540) * e; cy = 540 + (p["at"][1] * 1080 - 540) * e
    if z > 1.001:
        s = 1080 / z; box = (cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)
        box = (max(0, min(1080 - s, box[0])), max(0, min(1080 - s, box[1])))
        base = base.resize((1080, 1080), Image.BICUBIC, box=(box[0], box[1], box[0] + s, box[1] + s))
    img = Image.new("RGB", (W, H), PAPER); img.paste(base, (0, cues["map_y"]))
    d = ImageDraw.Draw(img, "RGBA")
    # year chip (top-right of the map) and legend under it
    d.rounded_rectangle([W - 330, cues["map_y"] + 24, W - 30, cues["map_y"] + 150], 22, fill=(*GLASS[:3], 210) if GLASS else (*PAPER, 230))
    d.text((W - 180, cues["map_y"] + 87), str(yr), font=f_year, fill=INK, anchor="mm")
    ly = cues["map_y"] + 1080 + 34; x = 70
    for i, e in enumerate(E):
        on = yf >= (E[i - 1] if i else E[0]) + (0.01 if i else 0); col = EPC[i] if on else OFF
        d.rounded_rectangle([x, ly - 14, x + 28, ly + 14], 6, fill=col); d.text((x + 38, ly), str(e), font=f_leg, fill=INK if on else MUTE, anchor="lm"); x += 160 if not GLASS else 158
    # scale bar: 10 km (the picture is 60 km across, before any push-in)
    km = 1080 / (2 * c["half_km"]) * z; d.rectangle([60, cues["map_y"] + 1080 - 46, 60 + 10 * km, cues["map_y"] + 1080 - 40], fill=INK)
    d.text((60, cues["map_y"] + 1080 - 58), "10 km", font=f_src, fill=INK, anchor="ls")
    for cd in cues["cards"]:
        if cd["t0"] <= t < cd["t1"]:
            a = min(1, (t - cd["t0"]) / 0.25 if cd["t0"] > 0 else 1, (cd["t1"] - t) / 0.25); card(d, cd, a)
    d.text((W // 2, H - 150), cues["credit"], font=f_src, fill=MUTE, anchor="mm")
    # loop: the last 0.4 s cross-fade into the opening frame
    if t > cues["duration"] - 0.4 and cues.get("loop"):
        first = frame(0.0, {**cues, "loop": False}, meta, c, ep, appear, bg); img = Image.blend(img, first, ease((t - (cues["duration"] - 0.4)) / 0.4))
    return img

def main():
    cues = json.loads(Path(sys.argv[1]).read_text()); out = sys.argv[2]
    meta, c, ep, appear, bg = load(cues)
    if "--stills" in sys.argv:
        for t in [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]: frame(t, cues, meta, c, ep, appear, bg).save(f"{out}_{t:05.1f}.png")
        return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(round(cues["duration"] * FPS))
    for i in range(n): p.stdin.write(frame(i / FPS, cues, meta, c, ep, appear, bg).tobytes())
    p.stdin.close(); p.wait(); print("wrote", out, n, "frames")

if __name__ == "__main__":
    main()
