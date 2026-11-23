"""Any city on Earth -> one spike-grid data file for the world-city Shorts (shorts2/city3d.py).

  python3 tools/world_city.py <slug> "<place name>" [--radius 30] [--cell 400] [--lat .. --lon ..]

Data (identical method for every country, so cities are comparable):
  * Population: GHSL GHS-POP R2023A, 100 m (Mollweide), epochs 1975 … 2020. European Commission JRC.
    2020 is the latest estimate; 2025/2030 in R2023A are projections and are NOT used.
  * Land/water: GHSL GHS-LAND R2022A, 100 m.
  * City centre: OpenStreetMap Nominatim (or --lat/--lon). Neighbourhood names: GeoNames (country dump).
Output: web/data/world/<slug>.json — cells on a local azimuthal-equidistant grid in metres (x east, y north) around the
centre, population per cell for each epoch, a coarse water mask, and asserted facts (totals, densest km², places).
Raw tiles are cached in /home/claude/world/ghsl (not committed).
"""
import argparse, io, json, math, subprocess, sys, urllib.parse, urllib.request, zipfile
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from pyproj import CRS, Transformer

ROOT = Path(__file__).resolve().parents[1]; CACHE = Path("/home/claude/world/ghsl"); CACHE.mkdir(parents=True, exist_ok=True)
GH = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
EPOCHS = [1975, 1990, 2005, 2020]
UA = "TheCanadianDataProject/1.0 (public-interest data videos)"
NOMI = CACHE / "nominatim.json"


def nominatim(path, **q):
    """Cached Nominatim call (curl; at most one request a second, per the usage policy)."""
    import time
    memo = json.loads(NOMI.read_text()) if NOMI.exists() else {}
    u = f"https://nominatim.openstreetmap.org/{path}?" + urllib.parse.urlencode(dict(format="json", **q))
    if u not in memo:
        time.sleep(1.2)
        memo[u] = json.loads(subprocess.run(["curl", "-sf", "--retry", "3", "--retry-delay", "3", "-A", UA, u], capture_output=True, check=True).stdout)
        NOMI.write_text(json.dumps(memo))
    return memo[u]


def get(url, dest):
    if not dest.exists():
        print("  downloading", url.rsplit("/", 1)[-1], flush=True)
        subprocess.run(["curl", "-sfL", "--retry", "3", "-o", str(dest) + ".part", url], check=True); Path(str(dest) + ".part").rename(dest)
    return dest


def tile(kind, epoch, r, c):
    if kind == "pop":
        name = f"GHS_POP_E{epoch}_GLOBE_R2023A_54009_100_V1_0_R{r}_C{c}"
        url = f"{GH}/GHS_POP_GLOBE_R2023A/GHS_POP_E{epoch}_GLOBE_R2023A_54009_100/V1-0/tiles/{name}.zip"
    else:
        name = f"GHS_LAND_E2018_GLOBE_R2022A_54009_100_V1_0_R{r}_C{c}"
        url = f"{GH}/GHS_LAND_GLOBE_R2022A/GHS_LAND_E2018_GLOBE_R2022A_54009_100/V1-0/tiles/{name}.zip"
    tif = CACHE / f"{name}.tif"
    if not tif.exists():
        z = get(url, CACHE / f"{name}.zip")
        with zipfile.ZipFile(z) as zf: tif.write_bytes(zf.read(f"{name}.tif"))
        z.unlink()
    return tif


def geocode(q):
    r = nominatim("search", q=q, limit=1, addressdetails=1)[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"], (r.get("address", {}).get("country_code") or "").upper()


def reverse(lat, lon):
    """OSM name of the neighbourhood at a point (suburb / neighbourhood / quarter), for on-screen callouts."""
    ad = nominatim("reverse", lat=round(lat, 5), lon=round(lon, 5), zoom=16).get("address", {})
    for k in ("suburb", "neighbourhood", "quarter", "city_district", "borough", "town", "village", "city"):
        if ad.get(k): return ad[k]
    return None


def places(cc, lat, lon, radius_km):
    """GeoNames neighbourhoods/towns inside the box: (name, lat, lon, feature code, population)."""
    z = get(f"https://download.geonames.org/export/dump/{cc}.zip", CACHE / f"geonames_{cc}.zip")
    out = []; dlat = radius_km / 111.0; dlon = radius_km / (111.0 * math.cos(math.radians(lat)))
    with zipfile.ZipFile(z) as zf:
        for ln in io.TextIOWrapper(zf.open(f"{cc}.txt"), encoding="utf-8"):
            p = ln.split("\t")
            if p[6] != "P" or p[7] not in ("PPL", "PPLX", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC", "PPLL"): continue
            la, lo = float(p[4]), float(p[5])
            if abs(la - lat) <= dlat and abs(lo - lon) <= dlon: out.append((p[1], la, lo, p[7], int(p[14] or 0)))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("slug"); ap.add_argument("place")
    ap.add_argument("--radius", type=float, default=30); ap.add_argument("--cell", type=float, default=400)
    ap.add_argument("--lat", type=float); ap.add_argument("--lon", type=float); ap.add_argument("--name"); ap.add_argument("--cc")
    a = ap.parse_args()
    lat, lon, disp, cc = geocode(a.place)
    if a.lat is not None: lat, lon = a.lat, a.lon
    cc = a.cc or cc; name = a.name or a.place.split(",")[0]
    print(f"{name}: {lat:.4f}, {lon:.4f} ({disp}) [{cc}]")
    R = a.radius * 1000; C = a.cell; N = int(round(2 * R / C)); FINE = 100; NF = int(round(2 * R / FINE))
    local = CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
    dst_t = from_origin(-R, R, FINE, FINE)                    # 100 m local grid, then summed into C-metre cells
    # which Mollweide tiles cover the box (1000 km tiles; R = row from the top at y = 9,000 km, C from x = -18,041 km)
    tm = Transformer.from_crs(local, "ESRI:54009", always_xy=True)
    xs, ys = tm.transform(*np.meshgrid(np.linspace(-R, R, 9), np.linspace(-R, R, 9)))
    tiles = sorted({(int((9_000_000 - y) // 1e6) + 1, int((x + 18_041_000) // 1e6) + 1) for x, y in zip(xs.ravel(), ys.ravel())})
    print("tiles", tiles)

    def warp(kind, epoch=None, resamp=Resampling.nearest):
        dst = np.zeros((NF, NF), np.float32)
        for r, c in tiles:
            with rasterio.open(tile(kind, epoch, r, c)) as s:
                src = s.read(1).astype(np.float32); nod = s.nodata
                if nod is not None: src[src == nod] = 0
                src[src < 0] = 0; part = np.zeros_like(dst)
                reproject(src, part, src_transform=s.transform, src_crs=s.crs, dst_transform=dst_t, dst_crs=local, resampling=resamp, src_nodata=None, dst_nodata=0)
                dst = np.maximum(dst, part)               # tiles don't overlap; max stitches them
        return dst

    pops = {}
    for e in EPOCHS:
        fine = warp("pop", e)                              # 100 m -> 100 m: nearest keeps each source cell's count
        pops[e] = fine
        print(f"  {e}: {fine.sum():,.0f} people within {a.radius:.0f} km", flush=True)
    land = warp("land")                                    # land fraction 0..1 (GHS-LAND stores 0..1 or 0..100)
    if land.max() > 1.5: land = land / 100.0

    k = int(round(C / FINE)); n = NF // k
    agg = lambda g: g[:n * k, :n * k].reshape(n, k, n, k).sum((1, 3))
    P = {e: agg(pops[e]) for e in EPOCHS}; L = agg(land) / (k * k)
    # densest square kilometre (sliding 10 x 10 window of 100 m cells), and where
    def densest(g):
        cs = np.pad(g, ((1, 0), (1, 0))).cumsum(0).cumsum(1); w = 10
        s = cs[w:, w:] - cs[:-w, w:] - cs[w:, :-w] + cs[:-w, :-w]; i, j = np.unravel_index(np.argmax(s), s.shape)
        return float(s[i, j]), (-R + (j + w / 2) * FINE, R - (i + w / 2) * FINE)
    d20, at20 = densest(pops[2020]); d75, at75 = densest(pops[1975])
    back = Transformer.from_crs(local, 4326, always_xy=True)
    tot = {e: float(pops[e].sum()) for e in EPOCHS}
    # places, nearest name to the densest km and labels for the map (biggest few)
    pl = places(cc, lat, lon, a.radius * 1.1) if cc else []
    fwd = Transformer.from_crs(4326, local, always_xy=True)
    P_ = []
    for nm, la, lo, fc, pp in pl:
        x, y = fwd.transform(lo, la)
        if abs(x) < R and abs(y) < R: P_.append(dict(name=nm, x=round(x), y=round(y), code=fc, pop=pp))
    near = lambda pt: min(P_, key=lambda p: (p["x"] - pt[0]) ** 2 + (p["y"] - pt[1]) ** 2) if P_ else None
    cells = []
    for i in range(n):
        for j in range(n):
            vs = [float(P[e][i, j]) for e in EPOCHS]
            if max(vs) >= 1 or L[i, j] > 0.5:
                cells.append([round(-R + (j + 0.5) * C), round(R - (i + 0.5) * C), round(float(L[i, j]), 2)] + [round(v) for v in vs])
    nm20 = near(at20)
    facts = dict(total={str(e): round(tot[e]) for e in EPOCHS}, growth=round(tot[2020] / max(1, tot[1975]), 2),
                 densest_km2={"2020": round(d20), "1975": round(d75)}, densest_at={"2020": [round(v) for v in at20], "1975": [round(v) for v in at75]},
                 densest_near=nm20["name"] if nm20 else None,
                 densest_near_dist_m=round(math.hypot(nm20["x"] - at20[0], nm20["y"] - at20[1])) if nm20 else None,
                 densest_latlon=[round(v, 5) for v in back.transform(*at20)[::-1]],
                 densest_name={"2020": reverse(*back.transform(*at20)[::-1]), "1975": reverse(*back.transform(*at75)[::-1])},
                 max_cell={str(e): round(float(P[e].max())) for e in EPOCHS})
    # checks: totals in a sane range, cells sum to the totals, epochs ordered
    for e in EPOCHS:
        s = sum(c[3 + EPOCHS.index(e)] for c in cells); assert abs(s - tot[e]) / max(1, tot[e]) < 0.01, (e, s, tot[e])
    assert all(v >= 0 for v in tot.values()) and tot[2020] > 1000
    out = dict(slug=a.slug, name=name, country=cc, lat=lat, lon=lon, radius_m=R, cell_m=C, epochs=EPOCHS,
               cell_fields=["x", "y", "land", *[f"p{e}" for e in EPOCHS]], cells=cells, places=sorted(P_, key=lambda p: -p["pop"])[:400], facts=facts,
               source="GHSL GHS-POP R2023A & GHS-LAND R2022A (European Commission JRC); places: GeoNames; centre: OpenStreetMap Nominatim")
    dst = ROOT / "web/data/world" / f"{a.slug}.json"; dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    print(json.dumps(facts, indent=1, ensure_ascii=False)); print("wrote", dst, f"{dst.stat().st_size / 1e6:.1f} MB", len(cells), "cells")


if __name__ == "__main__":
    main()
