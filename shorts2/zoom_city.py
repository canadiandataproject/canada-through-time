"""City zoom Shorts in the Whiteout / Blue hour look: one camera move from Canada into a city's census tracts, then the
lowest and highest neighbourhood for three measures. The format of #14 Toronto (best "stayed to watch" so far), for any CMA.

  python3 shorts2/zoom_city.py <cues.json> <out.mp4> [--stills t1,...]
  python3 shorts2/zoom_city.py --make <cma-code> <mode dark|light> <m1,m2,m3> <out-cues.json>   # write cues from the data

Numbers: 2021 Census Profile (98-401-X2021007) via web/data/cities/ct_profile.json; extremes among tracts with 500+ people.
The capture page is web/shorts-zoom/index.html?cma=…&mode=… served from web/ on :8765.
"""
import asyncio, io, json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import MODE as STYLE, font

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS = 1080, 1920, 30
RANGE = None
P = json.loads((ROOT / "web/data/cities/ct_profile.json").read_text()); F, A = P["fields"], P["areas"]
NAMES = {k: v[0] for k, v in json.loads((ROOT / "web/data/cities/cma_index.json").read_text())["cities"].items()}
MEAS = {  # kicker, how to show a value
    "hhinc": ("Median household income", lambda v: f"${v:,.0f}"),
    "imm": ("Born outside Canada", lambda v: f"{v:.0f}%"),
    "age": ("Median age", lambda v: f"{v:.0f}"),
    "rent": ("Households that rent", lambda v: f"{v:.0f}%"),
    "own": ("Households that own", lambda v: f"{v:.0f}%"),
}


def tracts(cma):
    return {k: v for k, v in A.items() if v["level"] != "Census metropolitan area" and v["cma"] == cma}


def ext(cma, f):
    xs = sorted((v["v"][F.index(f)], k) for k, v in tracts(cma).items() if v["v"][F.index(f)] is not None and (v["v"][F.index("pop")] or 0) >= 500)
    return xs[0], xs[-1]


def make(cma, mode, ms, out):
    T = tracts(cma); name = NAMES[cma[-3:]].split(" - ")[0]; pop = A[cma]["v"][F.index("pop")]
    can = sum(v["v"][F.index("pop")] or 0 for v in A.values() if v["level"] == "Census metropolitan area")
    # opener (2026-11-17): the city and a question on frame 1, camera already moving, source stamp up front (no "Canada" card)
    cards = [dict(t0=0, t1=4.8, kick="How different can one city get?", big=name, sub=f"{pop / 1e6:.2f} million people" if pop >= 1e6 else f"{pop:,.0f} people"),
             dict(t0=4.8, t1=7.9, big=f"{len(T):,}", sub="neighbourhoods (census tracts)")]
    cam = [dict(t=0, at="city", zoom="fit:city", dz=-1.8), dict(t=3.4, at="city", zoom="fit:city"),
           dict(t=4.8, at="city", zoom="fit:city", dz=0.1), dict(t=6.6, at="city", zoom="fit:city", dz=0.3)]
    hl, measures, t = [], [dict(t=0, k=ms[0])], 8.6
    spans = [(2.8, 2.5), (1.9, 2.2), (1.4, 4.4)]
    for i, m in enumerate(ms):
        (lo, klo), (hi, khi) = ext(cma, m); kick, fmt = MEAS[m]; a, b = spans[i]
        if i: measures.append(dict(t=t - 0.6, k=m))
        cam += [dict(t=t, at=f"{m}_lo", zoom=f"fit:{m}_lo"), dict(t=t + a * 0.7, at=f"{m}_lo", zoom=f"fit:{m}_lo", dz=0.15),
                dict(t=t + a, at=f"{m}_hi", zoom=f"fit:{m}_hi"), dict(t=t + a + b * 0.75, at=f"{m}_hi", zoom=f"fit:{m}_hi", dz=0.15)]
        hl += [dict(id=f"{m}_lo", t0=t, t1=t + a), dict(id=f"{m}_hi", t0=t + a, t1=t + a + b)]
        cards += [dict(t0=t + 0.2, t1=t + a, kick=f"{kick}: lowest", big=fmt(lo)), dict(t0=t + a, t1=t + a + b, kick=f"{kick}: highest", big=fmt(hi))]
        t += a + b + 0.5
    cam += [dict(t=t + 2.0, at="city", zoom="fit:city", dz=0.1), dict(t=t + 5.0, at="city", zoom="fit:city")]
    cards.append(dict(t0=t, t1=t + 5.0, big="Same city.", sub="50 cities, free map: link below"))
    cues = dict(cma=cma, mode=mode, city=name, duration=round(t + 5.0, 2), measures=measures, highlights=hl, cards=cards, camera=cam,
                facts={m: [ext(cma, m)[0][0], ext(cma, m)[1][0]] for m in ms}, tracts=len(T), pop=pop)
    Path(out).write_text(json.dumps(cues, indent=1, ensure_ascii=False)); print("wrote", out, cues["duration"], "s", cues["facts"])


def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def interp(keys, t, field):
    if t <= keys[0]["t"]: return keys[0][field]
    for a, b in zip(keys, keys[1:]):
        if a["t"] <= t <= b["t"]:
            e = ease((t - a["t"]) / (b["t"] - a["t"])); va, vb = a[field], b[field]
            return [x + (y - x) * e for x, y in zip(va, vb)] if isinstance(va, list) else va + (vb - va) * e
    return keys[-1][field]


def state(t, cues, geo):
    tgt = lambda k: geo[k["at"]] if isinstance(k.get("at"), str) else k["at"]
    zf = lambda k: geo["zoom_" + k["zoom"][4:]] + k.get("dz", 0) if isinstance(k["zoom"], str) else k["zoom"]
    keys = [dict(t=k["t"], target=tgt(k), zoom=zf(k)) for k in cues["camera"]]
    z = interp(keys, t, "zoom"); tg = interp(keys, t, "target")
    for a, b in zip(keys, keys[1:]):            # zoom segments keep the destination point steady on screen
        if a["t"] <= t <= b["t"] and abs(b["zoom"] - a["zoom"]) > 0.5:
            e = ease((t - a["t"]) / (b["t"] - a["t"]))
            if b["zoom"] > a["zoom"]: tg = [bt + (at - bt) * 2 ** (a["zoom"] - z) * (1 - e) for at, bt in zip(a["target"], b["target"])]
            else: tg = [at + (bt - at) * 2 ** (b["zoom"] - z) * e for at, bt in zip(a["target"], b["target"])]
    st = dict(target=tg, zoom=z, tractAlpha=min(1, max(0, (z - (geo["zoom_city"] - 4.6)) / 1.6)))
    ms = cues["measures"]; cur = [m for m in ms if m["t"] <= t] or ms[:1]; m = cur[-1]; i = ms.index(m); nx = ms[i + 1] if i + 1 < len(ms) else None
    st["a"], st["b"] = m["k"], (nx["k"] if nx else None)
    st["mix"] = ease((t - (nx["t"] - 0.8)) / 0.8) if nx and t > nx["t"] - 0.8 else 0
    st["hl"] = [h["id"] for h in cues["highlights"] if h["t0"] <= t < h["t1"]]
    return st


def overlay(img, t, cues):
    S = STYLE[cues["mode"]]; d = ImageDraw.Draw(img, "RGBA")
    hexc = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
    big, mid, kick, sub, src = font("display", 150), font("display", 104), font("ui", 54, 600), font("ui", 50, 500), font("mono", 24, 400)
    for c in cues["cards"]:
        if not (c["t0"] <= t < c["t1"]): continue
        a = min(1, (t - c["t0"]) / 0.2 if c["t0"] > 0 else 1, (c["t1"] - t) / 0.2)
        y = 300; f = big if len(c["big"]) <= 8 else mid
        bw = max(d.textlength(c["big"], font=f), d.textlength(c.get("sub", ""), font=sub), d.textlength(c.get("kick", ""), font=kick)) + 110
        top, bot = y - (165 if c.get("kick") else 105), y + (150 if c.get("sub") else 90)
        gl = S["glass"]; d.rounded_rectangle([W / 2 - bw / 2, top, W / 2 + bw / 2, bot], 40, fill=(*gl[:3], int(gl[3] * a * 1.15)))
        d.rounded_rectangle([W / 2 - bw / 2, top, W / 2 + bw / 2, bot], 40, outline=(*S["glass_line"][:3], int(S["glass_line"][3] * a)), width=2)
        if c.get("kick"): d.text((W / 2, y - 108), c["kick"], font=kick, fill=hexc(S["accent"], int(255 * a)), anchor="mm")
        d.text((W / 2, y), c["big"], font=f, fill=hexc(S["ink"], int(255 * a)), anchor="mm")
        if c.get("sub"): d.text((W / 2, y + 104), c["sub"], font=sub, fill=hexc(S["ink2"], int(255 * a)), anchor="mm")
    if t < 3.6 and cues.get("proof", True):   # proof stamp: readable source on frame 1
        a = min(1, (3.6 - t) / 0.25); pf = font("mono", 34, 600); ptxt = "DATA · STATISTICS CANADA · 2021 CENSUS"; pw = d.textlength(ptxt, font=pf) + 56
        d.rounded_rectangle([W / 2 - pw / 2, 500, W / 2 + pw / 2, 566], 14, fill=(*S["glass"][:3], int(S["glass"][3] * a * 1.15)), outline=hexc(S["accent"], int(255 * a)), width=3)
        d.text((W / 2, 533), ptxt, font=pf, fill=hexc(S["ink"], int(255 * a)), anchor="mm")
    txt = "2021 Census · Statistics Canada · The Canadian Data Project"
    tw = d.textlength(txt, font=src) + 48
    d.rounded_rectangle([W / 2 - tw / 2, H - 520, W / 2 + tw / 2, H - 470], 25, fill=S["glass"])
    d.text((W / 2, H - 495), txt, font=src, fill=hexc(S["ink2"]), anchor="mm")
    return img


async def run(cues, out, stills=None):
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = await b.new_page(viewport={"width": 540, "height": 960}, device_scale_factor=2)
        await pg.goto(f"http://localhost:8765/shorts-zoom/index.html?cma={cues['cma']}&mode={cues['mode']}"); await pg.evaluate("window.INIT")
        box = await pg.evaluate("window.cityBox()")
        geo = {"city": [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2], "zoom_city": math.log2(540 * 0.9 / max(box[2] - box[0], (box[3] - box[1]) * 540 / 960 * 1.6))}
        for m in {x["k"] for x in cues["measures"]}:
            for side, (v, k) in zip(("lo", "hi"), ext(cues["cma"], m)):
                bb = await pg.evaluate(f"window.tractBox('{k}')")
                geo[f"{m}_{side}"] = [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2]
                geo[f"zoom_{m}_{side}"] = max(geo["zoom_city"] + 0.8, min(geo["zoom_city"] + 5.2, math.log2(540 * 0.42 / max(bb[2] - bb[0], (bb[3] - bb[1]) * 540 / 960))))
        lut = {f"{m}_{s}": ext(cues["cma"], m)[i][1] for m in {x["k"] for x in cues["measures"]} for i, s in enumerate(("lo", "hi"))}
        for h in cues["highlights"]: h["id"] = lut.get(h["id"], h["id"])
        times = stills or [i / FPS for i in range(int(round(cues["duration"] * FPS)))]
        if RANGE: times = [x for x in times if RANGE[0] <= x < RANGE[1]]   # re-render a stretch, to splice into an earlier render
        proc = None
        if not stills:
            proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for t in times:
            await pg.evaluate("s => window.setFrame(s)", state(t, cues, geo))
            img = overlay(Image.open(io.BytesIO(await pg.screenshot(type="png"))).convert("RGB"), t, cues)
            if stills: img.save(f"{out}_{t:05.1f}.png")
            else: proc.stdin.write(img.tobytes())
        if proc: proc.stdin.close(); proc.wait(); print("wrote", out, len(times))
        await b.close()


if __name__ == "__main__":
    if sys.argv[1] == "--make":
        make(sys.argv[2], sys.argv[3], sys.argv[4].split(","), sys.argv[5]); sys.exit()
    cues = json.loads(Path(sys.argv[1]).read_text())
    st = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")] if "--stills" in sys.argv else None
    RANGE = [float(x) for x in sys.argv[sys.argv.index("--range") + 1].split(",")] if "--range" in sys.argv else None
    asyncio.run(run(cues, sys.argv[2], st))
