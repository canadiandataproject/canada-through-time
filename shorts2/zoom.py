"""Short #14 — one continuous camera move from Canada into Toronto's 1,227 census tracts, captured from the explorer's own
data and palette (web/shorts-zoom/index.html, served from web/ on :8765), with overlays drawn here.

  python3 shorts2/zoom.py <cues.json> <out.mp4> [--stills t1,...]

Numbers: 2021 Census Profile (98-401-X2021007) via web/data/cities/ct_profile.json; extremes are among tracts with 500+ people.
"""
import asyncio, io, json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]; FONTS = Path("/home/claude/fonts")
W, H, FPS = 1080, 1920, 30
p = json.loads((ROOT / "web/data/cities/ct_profile.json").read_text()); F = p["fields"]; A = p["areas"]
TOR = {k: v for k, v in A.items() if v["level"] != "Census metropolitan area" and v["cma"] == "2021S0503535"}
def ext(f):
    xs = sorted((v["v"][F.index(f)], k) for k, v in TOR.items() if v["v"][F.index(f)] is not None and (v["v"][F.index("pop")] or 0) >= 500)
    return xs[0], xs[-1]
EX = {f: ext(f) for f in ("hhinc", "imm", "age")}
assert len(TOR) == 1227 and EX["hhinc"][0][0] == 36400 and EX["hhinc"][1][0] == 286000 and round(EX["imm"][0][0]) == 10 and round(EX["imm"][1][0]) == 78
assert round(EX["age"][0][0]) == 28 and round(EX["age"][1][0]) == 63

f_big = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 150)
f_mid = ImageFont.truetype(str(FONTS / "oswald-latin-700-normal.ttf"), 70)
f_lab = ImageFont.truetype(str(FONTS / "oswald-latin-400-normal.ttf"), 44)
f_src = ImageFont.truetype(str(FONTS / "share-tech-mono-latin-400-normal.ttf"), 24)
INK = (29, 35, 38); ACC = (194, 64, 42)

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def interp(keys, t, field):
    if t <= keys[0]["t"]: return keys[0][field]
    for a, b in zip(keys, keys[1:]):
        if a["t"] <= t <= b["t"]:
            e = ease((t - a["t"]) / (b["t"] - a["t"]))
            va, vb = a[field], b[field]
            if isinstance(va, list): return [x + (y - x) * e for x, y in zip(va, vb)]
            return va + (vb - va) * e
    return keys[-1][field]

def state(t, cues, geo):
    cam = cues["camera"]
    tgt = lambda k: geo[k["at"]] if isinstance(k.get("at"), str) else k["at"]
    zf = lambda k: geo["zoom_" + k["zoom"][4:]] + k.get("dz", 0) if isinstance(k["zoom"], str) else k["zoom"]
    keys = [dict(t=k["t"], target=tgt(k), zoom=zf(k)) for k in cam]
    z = interp(keys, t, "zoom"); tgt_ = interp(keys, t, "target")
    for a, b in zip(keys, keys[1:]):            # zoom segments keep the destination point steady on screen (no drifting off)
        if a["t"] <= t <= b["t"] and abs(b["zoom"] - a["zoom"]) > 0.5:
            e = ease((t - a["t"]) / (b["t"] - a["t"]))
            if b["zoom"] > a["zoom"]: tgt_ = [bt + (at - bt) * 2 ** (a["zoom"] - z) * (1 - e) for at, bt in zip(a["target"], b["target"])]
            else: tgt_ = [at + (bt - at) * 2 ** (b["zoom"] - z) * e for at, bt in zip(a["target"], b["target"])]
    st = dict(target=tgt_, zoom=z)
    st["tractAlpha"] = min(1, max(0, (st["zoom"] + 12.6) / 1.6))
    ms = cues["measures"]; cur = [m for m in ms if m["t"] <= t] or ms[:1]; m = cur[-1]; i = ms.index(m)
    nxt = ms[i + 1] if i + 1 < len(ms) else None
    st["a"] = m["k"]; st["b"] = nxt["k"] if nxt else None
    st["mix"] = ease((t - (nxt["t"] - 0.8)) / 0.8) if nxt and t > nxt["t"] - 0.8 else 0
    st["hl"] = [h["id"] for h in cues.get("highlights", []) if h["t0"] <= t < h["t1"]]
    return st

def overlay(img, t, cues):
    d = ImageDraw.Draw(img, "RGBA")
    for c in cues.get("cards", []):
        if c["t0"] <= t < c["t1"]:
            a = min(1, (t - c["t0"]) / 0.2 if c["t0"] > 0 else 1, (c["t1"] - t) / 0.2)
            y = c.get("y", 250)
            top = y - (150 if c.get("kick") else 95); bot = y + (150 if c.get("sub") else 85)
            d.rounded_rectangle([60, top, W - 60, bot], 26, fill=(251, 248, 241, int(228 * a)))
            if c.get("kick"): d.text((W // 2, y - 95), c["kick"], font=f_lab, fill=(*ACC, int(255 * a)), anchor="mm")
            d.text((W // 2, y), c["big"], font=f_big if len(c["big"]) < 9 else f_mid, fill=(*INK, int(255 * a)), anchor="mm", stroke_width=8, stroke_fill=(251, 248, 241, int(235 * a)))
            if c.get("sub"): d.text((W // 2, y + 105), c["sub"], font=f_lab, fill=(*INK, int(255 * a)), anchor="mm", stroke_width=5, stroke_fill=(251, 248, 241, int(220 * a)))
    d.rounded_rectangle([40, H - 520, W - 40, H - 448], 12, fill=(251, 248, 241, 215))
    d.text((W // 2, H - 484), "2021 Census · Statistics Canada · The Canadian Data Project explorer", font=f_src, fill=(70, 76, 80, 255), anchor="mm")
    return img

async def run(cues, out, stills=None):
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = await b.new_page(viewport={"width": 540, "height": 960}, device_scale_factor=2)
        await pg.goto("http://localhost:8765/shorts-zoom/index.html"); info = await pg.evaluate("window.INIT")
        box = await pg.evaluate("window.cityBox()")
        geo = {"city": [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]}
        for f, (lo, hi) in EX.items():
            for side, (v, k) in (("lo", lo), ("hi", hi)):
                bb = await pg.evaluate(f"window.tractBox('{k}')")
                geo[f"{f}_{side}"] = [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2]
                geo[f"zoom_{f}_{side}"] = max(-7.2, min(-2.8, math.log2(540 * 0.42 / max(bb[2] - bb[0], (bb[3] - bb[1]) * 540 / 960))))
        for h in cues.get("highlights", []):
            if not h["id"].startswith("2021"): f, side = h["id"].rsplit("_", 1); h["id"] = EX[f][0 if side == "lo" else 1][1]
        times = stills or [i / FPS for i in range(int(round(cues["duration"] * FPS)))]
        proc = None
        if not stills:
            proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for t in times:
            await pg.evaluate("s => window.setFrame(s)", state(t, cues, geo))
            img = Image.open(io.BytesIO(await pg.screenshot(type="png"))).convert("RGB")
            img = overlay(img, t, cues)
            if stills: img.save(f"{out}_{t:05.1f}.png")
            else: proc.stdin.write(img.tobytes())
        if proc: proc.stdin.close(); proc.wait(); print("wrote", out, len(times))
        await b.close()

if __name__ == "__main__":
    cues = json.loads(Path(sys.argv[1]).read_text())
    st = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")] if "--stills" in sys.argv else None
    asyncio.run(run(cues, sys.argv[2], st))
