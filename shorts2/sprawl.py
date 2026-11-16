"""Short #16 — a city spreading out, 1975–2020, drawn from the explorer's own city picture (web/data/sprawl/<slug>.png) and
totals (web/data/sprawl/sprawl.json), with the cards and timings from a cue file.

  python3 shorts2/sprawl.py <cues.json> <out.mp4> [--stills t1,t2,...]

Data: European Commission JRC, GHS-BUILT-S R2023A (100 m), reprojected by pipeline/ingest_sprawl.py. Each 100 m square appears at
the first satellite snapshot (1975, 1985, 1990, 2000, 2010, 2020) in which buildings covered 20% of it. Nothing is interpolated
between snapshots; the opening camera pull-back is the only motion that isn't data.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]; FONTS = Path("/home/claude/fonts")
W, H, FPS = 1080, 1920, 30
PAPER = (251, 248, 241); LAND = (240, 234, 222); INK = (29, 35, 38); ACC = (194, 64, 42); MUTE = (92, 96, 98)
EPC = [(52, 48, 42), (104, 92, 76), (146, 128, 98), (196, 164, 104), (222, 132, 78), ACC]   # oldest dark → newest the accent (as in the explorer)
f_big = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 128)
f_mid = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 84)
f_lab = ImageFont.truetype(str(FONTS / "oswald-latin-400-normal.ttf"), 44)
f_year = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 96)
f_src = ImageFont.truetype(str(FONTS / "share-tech-mono-latin-400-normal.ttf"), 25)
f_leg = ImageFont.truetype(str(FONTS / "oswald-latin-400-normal.ttf"), 32)

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
    return meta, c, ep

def city_frame(ep, shown, glow, size):
    """shown: highest epoch index fully drawn; glow: (epoch index, 0..1) currently appearing."""
    n = ep.shape[0]; rgb = np.zeros((n, n, 3), np.float32); rgb[:] = LAND
    for k in range(1, 7):
        m = ep == k
        if k <= shown: rgb[m] = EPC[k - 1]
        elif glow and k == glow[0]:
            a = glow[1]; col = np.array(EPC[k - 1]) * a + np.array(LAND) * (1 - a)
            rgb[m] = col
    im = Image.fromarray(rgb.astype(np.uint8)).resize((n * 3, n * 3), Image.NEAREST).resize((size, size), Image.LANCZOS)
    return im

def card(d, c, a):
    y = c.get("y", 250); big = c["big"]; fb = f_big if len(big) <= 14 else f_mid
    top = y - (150 if c.get("kick") else 95); bot = y + (150 if c.get("sub") else 85)
    d.rounded_rectangle([50, top, W - 50, bot], 28, fill=(*PAPER, int(236 * a)))
    if c.get("kick"): d.text((W // 2, y - 98), c["kick"], font=f_lab, fill=(*ACC, int(255 * a)), anchor="mm")
    d.text((W // 2, y), big, font=fb, fill=(*INK, int(255 * a)), anchor="mm")
    if c.get("sub"): d.text((W // 2, y + 104), c["sub"], font=f_lab, fill=(*INK, int(255 * a)), anchor="mm")

def frame(t, cues, meta, c, ep):
    E = meta["epochs"]; times = cues["epochs"]
    shown = 0; glow = None
    for i, te in enumerate(times):
        if t >= te + cues["fade"]: shown = i + 1
        elif t >= te: glow = (i + 1, ease((t - te) / cues["fade"])); break
    base = city_frame(ep, shown, glow, 1080)
    # camera: push-in toward the newest growth, then back out
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
    yr = E[max(0, shown - 1)] if not glow else E[glow[0] - 1]
    d.rounded_rectangle([W - 330, cues["map_y"] + 24, W - 30, cues["map_y"] + 150], 22, fill=(*PAPER, 230))
    d.text((W - 180, cues["map_y"] + 87), str(yr), font=f_year, fill=INK, anchor="mm")
    ly = cues["map_y"] + 1080 + 34; x = 70
    for i, e in enumerate(E):
        on = i < max(shown, glow[0] if glow else 0); col = EPC[i] if on else (215, 208, 196)
        d.rounded_rectangle([x, ly - 14, x + 28, ly + 14], 6, fill=col); d.text((x + 38, ly), str(e), font=f_leg, fill=INK if on else MUTE, anchor="lm"); x += 160
    # scale bar: 10 km (the picture is 60 km across, before any push-in)
    km = 1080 / (2 * c["half_km"]) * z; d.rectangle([60, cues["map_y"] + 1080 - 46, 60 + 10 * km, cues["map_y"] + 1080 - 40], fill=INK)
    d.text((60, cues["map_y"] + 1080 - 58), "10 km", font=f_src, fill=INK, anchor="ls")
    for cd in cues["cards"]:
        if cd["t0"] <= t < cd["t1"]:
            a = min(1, (t - cd["t0"]) / 0.25 if cd["t0"] > 0 else 1, (cd["t1"] - t) / 0.25); card(d, cd, a)
    d.text((W // 2, H - 150), cues["credit"], font=f_src, fill=MUTE, anchor="mm")
    # loop: the last 0.4 s cross-fade into the opening frame
    if t > cues["duration"] - 0.4 and cues.get("loop"):
        first = frame(0.0, {**cues, "loop": False}, meta, c, ep); img = Image.blend(img, first, ease((t - (cues["duration"] - 0.4)) / 0.4))
    return img

def main():
    cues = json.loads(Path(sys.argv[1]).read_text()); out = sys.argv[2]
    meta, c, ep = load(cues)
    if "--stills" in sys.argv:
        for t in [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]: frame(t, cues, meta, c, ep).save(f"{out}_{t:05.1f}.png")
        return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(round(cues["duration"] * FPS))
    for i in range(n): p.stdin.write(frame(i / FPS, cues, meta, c, ep).tobytes())
    p.stdin.close(); p.wait(); print("wrote", out, n, "frames")

if __name__ == "__main__":
    main()
