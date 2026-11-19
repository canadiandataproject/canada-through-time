"""Which city spread the most? 12 metros side by side, 1975 -> 2020, then re-sorted by how much their built-up land multiplied.

  python3 shorts2/sprawl_grid.py <cues.json> <out.mp4> [--stills t1,t2,...]

Data: web/data/sprawl/<slug>.png + sprawl.json (EU JRC GHS-BUILT-S R2023A, 100 m; see pipeline/ingest_sprawl.py). Each city is
measured inside a fixed square around its centre (half-width `half_km`), so the ratio is "land covered by buildings in 2020 vs
1975 inside that square", not city-limit figures. Each tile is drawn at its own scale (said on screen). Between snapshot years,
new squares appear outward from built land (illustrative order, as in sprawl.py); at each snapshot year the tile is exact.
Look: Blue hour (shorts2/style.py). Every number on screen is computed here and checked against the cue file's `checks`.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import MODE as STYLE, font

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS = 1080, 1920, 30
M = STYLE["dark"]
def hx(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
BG, INK, INK2, INK3, ACC, GL = hx(M["bg"]), hx(M["ink"]), hx(M["ink2"]), hx(M["ink3"]), hx(M["accent"]), M["glass"]
TILE_BG = (16, 32, 68)
EPC = [hx(x) for x in ("#86A6DA", "#93B2E0", "#A5C3E8", "#BCD6F1", "#DCEEFC", "#FFFFFF")]
COLS, TS, GAP, GX, GY = 3, 340, 10, (W - (3 * 340 + 2 * 10)) // 2, 330
f_big, f_mid, f_kick, f_sub = font("display", 120, 700), font("display", 88, 700), font("ui", 42, 520), font("ui", 38, 480)
f_name, f_x, f_rank, f_year, f_src = font("ui", 30, 600), font("mono", 34, 600), font("mono", 30, 700), font("mono", 64, 600), font("mono", 18, 400)

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def load(cues):
    meta = json.loads((ROOT / "web/data/sprawl/sprawl.json").read_text()); E = meta["epochs"]; out = []
    for c in meta["cities"]:
        ep = np.array(Image.open(ROOT / f"web/data/sprawl/{c['slug']}.png"))
        assert list(ep.shape) == c["size"] and [int((ep == k).sum()) for k in range(1, 7)] == c["new_cells"]
        appear = np.full(ep.shape, np.inf, np.float32); appear[ep == 1] = E[0]
        for k in range(2, 7):
            new = ep == k
            if not new.any(): continue
            dist = distance_transform_edt(~((ep >= 1) & (ep < k)))
            order = dist[new].argsort().argsort() / max(1, new.sum() - 1)
            appear[new] = E[k - 2] + (E[k - 1] - E[k - 2]) * (0.04 + 0.96 * order)
        # crop each tile to the city's 2020 footprint (square, with margin) so small and large cities both fill their tile
        ys, xs = np.nonzero(ep >= 1); cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
        half = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 * 1.08 + 4
        box = [int(max(0, cx - half)), int(max(0, cy - half)), int(min(ep.shape[1], cx + half)), int(min(ep.shape[0], cy + half))]
        k = c["km2"]
        out.append(dict(name=c["name"], slug=c["slug"], lon=c["lon"], ep=ep, appear=appear, box=box, k0=k[0], k1=k[-1], ratio=k[-1] / k[0], added=k[-1] - k[0], ks=k))
    by = {c["slug"]: c for c in out}
    for chk in cues["checks"]:       # every on-screen number, checked against the data
        c = by[chk["slug"]]; got = round(c[chk["what"]], chk.get("dp", 0))
        assert got == chk["value"], (chk, got)
    start = sorted(out, key=lambda c: c["lon"])                       # west to east
    ranked = sorted(out, key=lambda c: -c["ratio"])
    for i, c in enumerate(start): c["pos0"] = i
    for i, c in enumerate(ranked): c["pos1"] = i; c["rank"] = i + 1
    assert [c["slug"] for c in ranked[:2]] == cues["expect_top2"], [c["slug"] for c in ranked[:3]]
    return meta, out

def year_at(t, cues, E):
    tk = cues["tick"]
    return E[0] if t <= tk["t0"] else E[-1] if t >= tk["t1"] else E[0] + (E[-1] - E[0]) * (t - tk["t0"]) / (tk["t1"] - tk["t0"])

def tile(c, year):
    x0, y0, x1, y1 = c["box"]; ep = c["ep"][y0:y1, x0:x1]; ap = c["appear"][y0:y1, x0:x1]; n = ep.shape
    rgba = np.zeros((*n, 4), np.uint8); on = ap <= year
    for k in range(1, 7):
        m = on & (ep == k); rgba[m, :3] = EPC[k - 1]; rgba[m, 3] = 255
    lay = Image.fromarray(rgba, "RGBA").resize((n[1] * 3, n[0] * 3), Image.NEAREST).resize((TS, TS), Image.LANCZOS)
    im = Image.new("RGBA", (TS, TS), (*TILE_BG, 255)); im.alpha_composite(lay); return im

def xy(pos): return GX + (pos % COLS) * (TS + GAP), GY + (pos // COLS) * (TS + GAP)

def card(d, cd, a):
    y = cd.get("y", 170); big = cd["big"]; fb = f_big if len(big) <= 15 else f_mid
    top, bot = y - (128 if cd.get("kick") else 80), y + (118 if cd.get("sub") else 76)
    d.rounded_rectangle([40, top, W - 40, bot], 28, fill=(*GL[:3], int(min(255, GL[3] * 1.4) * a)))
    if cd.get("kick"): d.text((W // 2, y - 84), cd["kick"], font=f_kick, fill=(*ACC, int(255 * a)), anchor="mm")
    d.text((W // 2, y), big, font=fb, fill=(*INK, int(255 * a)), anchor="mm")
    if cd.get("sub"): d.text((W // 2, y + 82), cd["sub"], font=f_sub, fill=(*INK2, int(255 * a)), anchor="mm")

def frame(t, cues, meta, cities):
    E = meta["epochs"]; yf = year_at(t, cues, E)
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img, "RGBA")
    so = cues["sort"]; s = ease((t - so["t0"]) / (so["t1"] - so["t0"]))          # 0 = west-to-east, 1 = ranked
    hl = next((h for h in cues.get("highlight", []) if h["t0"] <= t < h["t1"]), None)
    oz = cues.get("open_zoom"); z = 1 + (oz["from"] - 1) * (1 - ease(t / oz["t1"])) if oz and t < oz["t1"] else 1.0
    grid = Image.new("RGBA", (W, 4 * (TS + GAP)), (0, 0, 0, 0)); gd = ImageDraw.Draw(grid, "RGBA")
    order = sorted(cities, key=lambda c: (hl is not None and c["slug"] in hl["slugs"]))          # highlighted on top
    for c in order:
        (ax, ay), (bx, by) = xy(c["pos0"]), xy(c["pos1"]); x, y = ax + (bx - ax) * s, ay + (by - ay) * s - GY
        im = tile(c, yf)
        dim = hl is not None and c["slug"] not in hl["slugs"]
        if dim: im = Image.blend(im, Image.new("RGBA", im.size, (*BG, 255)), 0.62)
        grid.alpha_composite(im, (int(x), int(y)))
        if hl is not None and not dim: gd.rounded_rectangle([x - 4, y - 4, x + TS + 3, y + TS + 3], 14, outline=(*ACC, 255), width=5)
        cur = float(np.interp(yf, E, c["ks"]))     # exact at every snapshot year; straight line only between neighbouring snapshots
        al = 110 if dim else 255
        gd.rounded_rectangle([x + 8, y + TS - 58, x + TS - 8, y + TS - 8], 12, fill=(*GL[:3], int(200 * (al / 255))))
        fn = f_name
        while gd.textlength(c["name"], font=fn) > TS - 160: fn = font("ui", fn.size - 2, 600)
        gd.text((x + 22, y + TS - 33), c["name"], font=fn, fill=(*INK, al), anchor="lm")
        gd.text((x + TS - 20, y + TS - 33), f"×{cur / c['k0']:.2f}", font=f_x, fill=(*ACC, al), anchor="rm")
        if s > 0.98:
            gd.rounded_rectangle([x + 10, y + 10, x + 70, y + 56], 12, fill=(*GL[:3], int(210 * (al / 255))))
            gd.text((x + 40, y + 33), f"{c['rank']}", font=f_rank, fill=(*INK, al), anchor="mm")
    if z > 1.001: grid = grid.resize(grid.size, Image.BICUBIC, box=(W / 2 - W / 2 / z, grid.size[1] / 2 - grid.size[1] / 2 / z, W / 2 + W / 2 / z, grid.size[1] / 2 + grid.size[1] / 2 / z))
    img.paste(grid, (0, GY), grid)
    # year (bottom) and notes
    by = GY + 4 * (TS + GAP) + 26
    d.text((W // 2, by + 34), str(int(math.floor(yf + 1e-6))), font=f_year, fill=INK, anchor="mm")
    d.text((W // 2, H - 92), cues["note"], font=f_src, fill=INK3, anchor="mm")
    d.text((W // 2, H - 62), cues["credit"], font=f_src, fill=INK3, anchor="mm")
    for cd in cues["cards"]:
        if cd["t0"] <= t < cd["t1"]:
            a = min(1, (t - cd["t0"]) / 0.25 if cd["t0"] > 0 else 1, (cd["t1"] - t) / 0.25); card(d, cd, a)
    if t > cues["duration"] - 0.4 and cues.get("loop"):
        img = Image.blend(img, frame(0.0, {**cues, "loop": False}, meta, cities), ease((t - (cues["duration"] - 0.4)) / 0.4))
    return img

def main():
    cues = json.loads(Path(sys.argv[1]).read_text()); out = sys.argv[2]
    meta, cities = load(cues)
    if "--stills" in sys.argv:
        for t in [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]: frame(t, cues, meta, cities).save(f"{out}_{t:05.1f}.png")
        return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(round(cues["duration"] * FPS))
    for i in range(n): p.stdin.write(frame(i / FPS, cues, meta, cities).tobytes())
    p.stdin.close(); p.wait(); print("wrote", out, n, "frames")

if __name__ == "__main__":
    main()
