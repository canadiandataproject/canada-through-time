"""World-city Shorts: any city on Earth as a floating 3D diorama of people (GHSL, 1975 -> 2020), with a deadpan local
script. Data: tools/world_city.py -> web/data/world/<slug>.json. Script text: shorts2/city_scripts.py.

  python3 shorts2/city3d.py --make <slug> <out-cues.json>          # cues from the data + script (numbers asserted)
  python3 shorts2/city3d.py <cues.json> <out.mp4> [--stills t1,...] [--scale 1]
  python3 shorts2/mix.py zoom <cues.json> <video.mp4> <out.mp4> --scratch

Beats (≈33 s): hook (camera already diving) -> 1975 -> years tick to 2020 while the columns rise, 1975 left behind as
wireframe -> dive to the busiest square kilometre (pulsing ring) -> Canadian comparison -> local joke -> pull out,
"which city next?" (the last frame matches the first, so it loops). Captions carry the narration so jokes land muted.
The capture page is web/shorts-city3d/index.html?city=…&mode=… served from web/ on :8765.
"""
import asyncio, io, json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import MODE as STYLE, font
from city_scripts import SCRIPTS

ROOT = Path(__file__).resolve().parents[1]
FR = [0, None]
W, H, FPS = 1080, 1920, 30
CP = json.loads((ROOT / "web/data/cities/ct_profile.json").read_text())
CA_CITIES = sorted((v["v"][CP["fields"].index("pop")], v["name"]) for v in CP["areas"].values() if v["level"] == "Census metropolitan area")


def world(slug): return json.loads((ROOT / "web/data/world" / f"{slug}.json").read_text())


def fmt_m(v): return f"{v / 1e6:.1f} million" if v >= 1e6 else f"{v:,.0f}"


def ca_match(n):
    """Biggest Canadian metro (2021 Census) with fewer people than n, or None."""
    xs = [c for c in CA_CITIES if c[0] < n]; return xs[-1] if xs else None


def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def make(slug, out):
    S = SCRIPTS[slug]; key = slug; slug = S.get("base", slug)
    d = world(slug); f = d["facts"]; R = d["radius_m"]
    tot = {int(k): v for k, v in f["total"].items()}; dk = f["densest_km2"]["2020"]; at = f["densest_at"]["2020"]; at75 = f["densest_at"]["1975"]
    ctx = dict(city=d["name"], p1975=fmt_m(tot[1975]), p2020=fmt_m(tot[2020]), growth=f"×{f['growth']:.1f}", dk=f"{dk:,}", dk75=f"{f['densest_km2']['1975']:,}",
               where=S.get("where") or f["densest_name"]["2020"], where75=S.get("where75") or f["densest_name"]["1975"], km=int(R / 1000))
    cm = ca_match(dk); ctx["ca"] = cm[1].split(" - ")[0].split(" / ")[0] if cm else ""; ctx["ca_pop"] = f"{cm[0]:,.0f}" if cm else ""
    if S.get("vs"):                                               # another city's busiest km², from the same data
        o = world(S["vs"]); ctx["vs"] = o["name"]; ctx["vs_dk"] = f"{o['facts']['densest_km2']['2020']:,}"
        ctx["vs_x"] = f"{dk / o['facts']['densest_km2']['2020']:.1f}"; ctx["vs_where"] = o["facts"]["densest_name"]["2020"]
    for k, v in S.get("extra", {}).items(): ctx[k] = v(d) if callable(v) else v
    for chk in S.get("asserts", []): assert chk(d, ctx), chk.__doc__ or "script assert failed"
    seg = S["beats"]; tl = []; t = 0.0
    for b in seg: tl.append(dict(b, t0=round(t, 2), t1=round(t + b["dur"], 2))); t += b["dur"]
    dur = round(t, 2); T = {b["key"]: b for b in tl}
    fill = lambda s: s.format(**ctx) if isinstance(s, str) else s
    cards = [dict(t0=b["t0"], t1=b["t1"], **{k: fill(v) for k, v in b["card"].items()}) for b in tl if b.get("card")]
    caps = [dict(t0=round(b["t0"] + 0.1 + b.get("say_at", 0) * b["dur"], 2), t1=b["t1"] - 0.05, text=fill(b["say"])) for b in tl if b.get("say")]
    # camera (metres, degrees). Wide = whole disc; near = the busiest square km.
    wide = dict(target=[0, 0, 2500], zoom=-6.0, pitch=48, orbit=-15)
    top = dict(target=[0, 0, 0], zoom=-6.75, pitch=88, orbit=-60)
    hz = 2 * R * 0.20 * 0.45                                     # half the tallest column: keeps the whole spike in frame
    near = dict(target=[at[0], at[1], hz], zoom=-5.25, pitch=52, orbit=35)
    cam = [dict(t=0, **top), dict(t=T["then"]["t0"] + 0.6, **dict(wide, zoom=-6.15, orbit=-35)),
           dict(t=T["grow"]["t1"] - 0.4, **dict(wide, orbit=15, zoom=-6.0, pitch=42)),
           dict(t=T["dense"]["t0"] + 2.0, **near), dict(t=T["dense"]["t1"], **dict(near, orbit=55, zoom=-5.1)),
           dict(t=T["compare"]["t1"], **dict(near, target=[(at[0] + at75[0]) / 2, (at[1] + at75[1]) / 2, hz], zoom=-5.6, pitch=52, orbit=75)),
           dict(t=T["joke"]["t1"], **dict(wide, orbit=60, zoom=-6.1, pitch=46)), dict(t=dur, **dict(top, orbit=0))]
    year = [dict(t=0, y=1975), dict(t=T["grow"]["t0"] + 0.3, y=1975), dict(t=T["grow"]["t1"] - 0.6, y=2020), dict(t=dur, y=2020)]
    grow = [dict(t=0, g=0.0), dict(t=T["then"]["t0"] + 2.2, g=1.0), dict(t=T["end"]["t0"] + 1.5, g=1.0), dict(t=dur, g=0.0)]  # rises, then sinks to frame 1
    wire = [dict(t=0, w=0), dict(t=T["grow"]["t0"] + 0.8, w=0), dict(t=T["grow"]["t0"] + 2.0, w=0.85), dict(t=T["joke"]["t1"], w=0.85), dict(t=T["end"]["t0"] + 1.0, w=0)]
    if S.get("open") == "payoff":                                 # frame 1 = the answer, lit; then rewind to 1975; end back on it (loops)
        h = T["hook"]; lit = dict(near, zoom=-5.35, orbit=20)
        cam = [dict(t=0, **lit), dict(t=h["t1"] - 0.5, **dict(lit, orbit=30, zoom=-5.25)), dict(t=T["then"]["t0"] + 1.2, **dict(wide, zoom=-6.15, orbit=-35))] + \
              [k for k in cam if k["t"] > T["then"]["t0"] + 1.2 and k["t"] < T["end"]["t0"]] + [dict(t=T["end"]["t0"] + 0.4, **dict(wide, orbit=40, zoom=-6.1, pitch=46)), dict(t=dur, **lit)]
        year = [dict(t=0, y=2020), dict(t=h["t1"] - 0.3, y=2020), dict(t=T["then"]["t0"] + 0.5, y=1975), dict(t=T["grow"]["t0"] + 0.3, y=1975),
                dict(t=T["grow"]["t1"] - 0.6, y=2020), dict(t=dur, y=2020)]
        grow = [dict(t=0, g=1.0), dict(t=dur, g=1.0)]
        wire = [dict(t=0, w=0), dict(t=T["grow"]["t0"] + 0.8, w=0), dict(t=T["grow"]["t0"] + 2.0, w=0.85), dict(t=T["joke"]["t1"], w=0.85), dict(t=T["end"]["t0"] + 1.0, w=0)]
        rings0 = [dict(t0=-1, t1=h["t1"] - 0.2, at=at), dict(t0=T["end"]["t1"] - 1.2, t1=dur + 1, at=at)]
    else: rings0 = []
    rings = rings0 + [dict(t0=T["dense"]["t0"] + 1.2, t1=T["compare"]["t1"], at=at), dict(t0=T["joke"]["t0"], t1=T["joke"]["t1"] - 0.3, at=at75)] if S.get("ring75", True) else \
            [dict(t0=T["dense"]["t0"] + 1.2, t1=T["compare"]["t1"], at=at)]
    # place labels for the wide shots: biggest named places, spread out, inside the disc
    labs = []
    for p in d["places"]:
        if p["name"] in S.get("skip_places", []) or p["name"] == d["name"] or math.hypot(p["x"], p["y"]) > R * 0.8: continue
        if all(math.hypot(p["x"] - q["x"], p["y"] - q["y"]) > R * 0.28 for q in labs): labs.append(p)
        if len(labs) >= S.get("n_labels", 5): break
    labels = [dict(name=S.get("rename", {}).get(p["name"], p["name"]), x=p["x"], y=p["y"]) for p in labs]
    cues = dict(slug=slug, key=key, city=d["name"], mode=S.get("mode", "dark"), duration=dur, camera=cam, year=year, grow=grow, wire=wire, rings=rings,
                cards=cards, captions=caps, labels=labels, label_window=[T["then"]["t0"] + 1.0, T["grow"]["t1"] - 0.3],
                counter=dict(t0=T["then"]["t0"], t1=T["grow"]["t1"]), totals={str(k): v for k, v in tot.items()},
                densest=dict(at=at, name=ctx["where"], km2=dk), ctx={k: v for k, v in ctx.items()},
                source=f"GHSL GHS-POP R2023A · EU JRC · {ctx['km']} km radius · GeoNames, OSM",
                voice=f"/home/claude/audio/world/{slug}.wav", script=[c["text"] for c in caps])
    Path(out).write_text(json.dumps(cues, indent=1, ensure_ascii=False)); print("wrote", out, dur, "s")
    for c in caps: print(f"  {c['t0']:5.1f}  {c['text']}")
    return cues


def interp(keys, t, field):
    if t <= keys[0]["t"]: return keys[0][field]
    for a, b in zip(keys, keys[1:]):
        if a["t"] <= t <= b["t"]:
            e = ease((t - a["t"]) / (b["t"] - a["t"])); va, vb = a[field], b[field]
            return [x + (y - x) * e for x, y in zip(va, vb)] if isinstance(va, list) else va + (vb - va) * e
    return keys[-1][field]


def lin(keys, t, field):     # linear (the year ticks at a steady rate)
    if t <= keys[0]["t"]: return keys[0][field]
    for a, b in zip(keys, keys[1:]):
        if a["t"] <= t <= b["t"]: return a[field] + (b[field] - a[field]) * (t - a["t"]) / (b["t"] - a["t"])
    return keys[-1][field]


def state(t, cues):
    c = cues["camera"]
    st = dict(target=interp(c, t, "target"), zoom=interp(c, t, "zoom"), pitch=interp(c, t, "pitch"), orbit=interp(c, t, "orbit"),
              year=lin(cues["year"], t, "y"), grow=interp(cues["grow"], t, "g"), wire=interp(cues["wire"], t, "w"), t=t)
    st["orbit"] += t * 1.2                                        # a constant slow drift so the frame never sits still
    for r in cues["rings"]:
        if r["t0"] <= t < r["t1"]: st["ring"] = r["at"]; st["ringR"] = 900; st["hot"] = r["at"]; st["hotA"] = min(1, (t - r["t0"]) / 0.6, (r["t1"] - t) / 0.4)
    return st


def pop_at(tot, yr):
    ks = sorted(int(k) for k in tot)
    if yr <= ks[0]: return tot[str(ks[0])]
    for a, b in zip(ks, ks[1:]):
        if yr <= b: return tot[str(a)] + (tot[str(b)] - tot[str(a)]) * (yr - a) / (b - a)
    return tot[str(ks[-1])]


def glow(img, mode):
    """Soft bloom on the brightest columns and a light vignette: the cinematic part."""
    from PIL import ImageChops, ImageEnhance
    if mode == "dark":
        hi = img.point(lambda v: max(0, v - 170) * 3).filter(ImageFilter.GaussianBlur(18))
        img = ImageChops.screen(img, ImageEnhance.Brightness(hi).enhance(0.55))
    vg = Image.new("L", (W // 8, H // 8), 0); dv = ImageDraw.Draw(vg)
    for k in range(40): dv.ellipse([-W // 16 + k, -H // 32 + k, W // 8 + W // 16 - k, H // 8 + H // 32 - k], fill=int(k / 40 * 255))
    vg = vg.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(40))
    dark = Image.new("RGB", (W, H), (2, 6, 20) if mode == "dark" else (150, 165, 185))
    return Image.composite(img, Image.blend(img, dark, 0.35), vg)


def overlay(img, t, cues, st, lab_px):
    img = glow(img, cues["mode"])
    S = STYLE[cues["mode"]]; d = ImageDraw.Draw(img, "RGBA")
    hexc = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
    fade = lambda t0, t1, k=0.22: max(0, min(1, (t - t0) / k if t0 > 0 else 1, (t1 - t) / k))
    # place labels: dot on the ground, stem, name
    lw = cues["label_window"]; la = fade(lw[0], lw[1], 0.5)
    if la > 0:
        lf = font("ui", 34, 600)
        for (sx, sy, *_), L in zip(lab_px, cues["labels"]):
            sx, sy = sx * 2, sy * 2
            if not (60 < sx < W - 60 and 650 < sy < H - 560): continue
            d.line([sx, sy, sx, sy - 70], fill=hexc(S["ink"], int(200 * la)), width=2); d.ellipse([sx - 6, sy - 6, sx + 6, sy + 6], fill=hexc(S["accent"], int(255 * la)))
            tw = d.textlength(L["name"], font=lf)
            d.rounded_rectangle([sx - tw / 2 - 16, sy - 122, sx + tw / 2 + 16, sy - 70], 14, fill=(*S["glass"][:3], int(S["glass"][3] * la)))
            d.text((sx, sy - 96), L["name"], font=lf, fill=hexc(S["ink"], int(255 * la)), anchor="mm")
    # cards (top)
    big, mid, kick, sub = font("display", 150), font("display", 100), font("ui", 52, 600), font("ui", 48, 500)
    for c in cues["cards"]:
        if not (c["t0"] <= t < c["t1"]): continue
        a = fade(c["t0"], c["t1"]); y = 330; bigt = c.get("big", "")
        if c.get("counter"):                                      # live year + people counter
            yr = st["year"]; bigt = f"{yr:.0f}"; c = dict(c, sub=f"{pop_at(cues['totals'], yr) / 1e6:.1f} million people")
        f = big if len(bigt) <= 8 else mid
        bw = max(d.textlength(bigt, font=f), d.textlength(c.get("sub", ""), font=sub), d.textlength(c.get("kick", ""), font=kick)) + 110
        top, bot = y - (165 if c.get("kick") else 105), y + (150 if c.get("sub") else 90)
        d.rounded_rectangle([W / 2 - bw / 2, top, W / 2 + bw / 2, bot], 40, fill=(*S["glass"][:3], int(min(255, S["glass"][3] * 1.15) * a)),
                            outline=(*S["glass_line"][:3], int(S["glass_line"][3] * a)), width=2)
        if c.get("kick"): d.text((W / 2, y - 108), c["kick"], font=kick, fill=hexc(S["accent"], int(255 * a)), anchor="mm")
        d.text((W / 2, y), bigt, font=f, fill=hexc(S["ink"], int(255 * a)), anchor="mm")
        if c.get("sub"): d.text((W / 2, y + 104), c["sub"], font=sub, fill=hexc(S["ink2"], int(255 * a)), anchor="mm")
    # captions (the narration, deadpan) above the source line; wrap to two lines
    cf = font("ui", 50, 600)
    for c in cues["captions"]:
        if not (c["t0"] <= t < c["t1"]): continue
        a = fade(c["t0"], c["t1"], 0.15); words, lines, cur = c["text"].split(), [], ""
        for w_ in words:
            if d.textlength((cur + " " + w_).strip(), font=cf) > W - 200: lines.append(cur); cur = w_
            else: cur = (cur + " " + w_).strip()
        lines.append(cur); y0 = H - 640 - 66 * (len(lines) - 1)
        for i, ln in enumerate(lines):
            tw = d.textlength(ln, font=cf); yy = y0 + i * 66
            d.rounded_rectangle([W / 2 - tw / 2 - 22, yy - 34, W / 2 + tw / 2 + 22, yy + 34], 16, fill=(*hexc(S["ink"])[:3], int(205 * a)))
            d.text((W / 2, yy), ln, font=cf, fill=((11, 26, 61) if cues["mode"] == "dark" else (255, 255, 255)) + (int(255 * a),), anchor="mm")
    # proof stamp on frame 1, source line always
    if t < 3.0:
        a = min(1, (3.0 - t) / 0.25); pf = font("mono", 30, 600); ptxt = "DATA · EU JRC GLOBAL HUMAN SETTLEMENT LAYER"; pw = d.textlength(ptxt, font=pf) + 56
        d.rounded_rectangle([W / 2 - pw / 2, 560, W / 2 + pw / 2, 622], 14, fill=(*S["glass"][:3], int(S["glass"][3] * a * 1.15)), outline=hexc(S["accent"], int(255 * a)), width=3)
        d.text((W / 2, 591), ptxt, font=pf, fill=hexc(S["ink"], int(255 * a)), anchor="mm")
    src = font("mono", 21, 400); txt = cues["source"]; tw = d.textlength(txt, font=src) + 40
    d.rounded_rectangle([W / 2 - tw / 2, H - 520, W / 2 + tw / 2, H - 474], 23, fill=S["glass"]); d.text((W / 2, H - 497), txt, font=src, fill=hexc(S["ink2"]), anchor="mm")
    return img


async def serve_web(pg):
    """Serve web/ to the page straight from disk (no separate http.server process to keep alive)."""
    import mimetypes
    from urllib.parse import urlparse, unquote
    async def handle(route):
        p = (ROOT / "web" / unquote(urlparse(route.request.url).path).lstrip("/")).resolve()
        if p.is_dir(): p = p / "index.html"
        if not p.is_file() or ROOT / "web" not in p.parents: return await route.fulfill(status=404, body="")
        await route.fulfill(status=200, body=p.read_bytes(), content_type=mimetypes.guess_type(str(p))[0] or "application/octet-stream")
    await pg.route("http://localhost:8765/**", handle)


async def run(cues, out, stills=None, scale=1.0):
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = await b.new_page(viewport={"width": 540, "height": 960}, device_scale_factor=2 * scale)
        await serve_web(pg)
        await pg.goto(f"http://localhost:8765/shorts-city3d/index.html?city={cues['slug']}&mode={cues['mode']}"); await pg.evaluate("window.INIT")
        times = stills or [i / FPS for i in range(int(round(cues["duration"] * FPS)))][FR[0]:FR[1]]
        proc = None
        if not stills:
            proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        pts = [[L["x"], L["y"], 0] for L in cues["labels"]]
        for i, t in enumerate(times):
            st = state(t, cues); await pg.evaluate("s => window.setFrame(s)", st)
            lab_px = await pg.evaluate("p => window.project(p)", pts)
            img = Image.open(io.BytesIO(await pg.screenshot(type="png"))).convert("RGB")
            if img.size != (W, H): img = img.resize((W, H), Image.LANCZOS)
            img = overlay(img, t, cues, st, lab_px)
            if stills: img.save(f"{out}_{t:05.1f}.png")
            else: proc.stdin.write(img.tobytes())
            if i % 150 == 0: print(f"  frame {i}/{len(times)}", flush=True)
        if proc: proc.stdin.close(); proc.wait(); print("wrote", out, len(times))
        await b.close()


if __name__ == "__main__":
    if sys.argv[1] == "--make": make(sys.argv[2], sys.argv[3]); sys.exit()
    cues = json.loads(Path(sys.argv[1]).read_text())
    st = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")] if "--stills" in sys.argv else None
    sc = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.0
    if "--frames" in sys.argv: FR = [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(":")]   # render a slice (segments are joined with ffmpeg concat)
    asyncio.run(run(cues, sys.argv[2], st, sc))
