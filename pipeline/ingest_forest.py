"""Forest disturbance: area burned and harvested by year, 1985-2015 (NRCan Canada Landsat Disturbance, CanLaD 1984-2015).

  web/data/forest/disturbance.json   9 km grid (StatCan Lambert km), hectares by year and type for each cell with any disturbance,
                                     plus Canada and province totals by year (derived).

CanLaD gives, for each 30 m pixel, the year and type (1 = fire, 2 = harvest, per NRCan's legend) of the LATEST stand-replacing
disturbance from 1985 to 2015. A pixel disturbed twice counts once, in its later year, so earlier years are undercounted where
land was disturbed again; this is stated on screen. Hectares = pixel count x 0.09. Cells are assigned to the province or territory
that contains the cell centre. Nothing else is computed.

The two GeoTIFFs (870 MB) are not in git; the pipeline checks their SHA-256 against the registry.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.windows import Window
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402

CELL = 300            # pixels: 300 x 30 m = 9 km
Y0, Y1 = 1985, 2015
OUT = ROOT / "web/data/forest/disturbance.json"
MAP_KM = 18


def main():
    reg = load_registry()["sources"]
    fy = verify_raw(reg["nrcan_canlad_year"]["raw_file"], reg["nrcan_canlad_year"]["sha256"])
    ft = verify_raw(reg["nrcan_canlad_type"]["raw_file"], reg["nrcan_canlad_type"]["sha256"])
    ry, rt = rasterio.open(fy), rasterio.open(ft)
    assert ry.shape == rt.shape and ry.transform == rt.transform
    H, W = ry.shape
    ncol = (W + CELL - 1) // CELL
    nyear = Y1 - Y0 + 1
    acc = defaultdict(lambda: np.zeros((nyear, 2), dtype=np.int64))
    for r0, c0 in ((r, c) for r in range(0, H, 1024) for c in range(0, W, 16384)):   # 1024 x 16384 tiles keep memory low
        h, w = min(1024, H - r0), min(16384, W - c0)
        yr = ry.read(1, window=Window(c0, r0, w, h)); ty = rt.read(1, window=Window(c0, r0, w, h))
        ok = (yr >= Y0) & (yr <= Y1) & ((ty == 1) | (ty == 2))
        rr, cc = np.nonzero(ok)
        if not len(rr):
            continue
        cell = ((r0 + rr) // CELL) * ncol + (c0 + cc) // CELL
        key = (cell * nyear + (yr[rr, cc] - Y0)) * 2 + (ty[rr, cc] - 1)
        u, n = np.unique(key, return_counts=True)
        for k, c in zip(u.tolist(), n.tolist()):
            cid, rest = divmod(k, nyear * 2)
            yi, ti = divmod(rest, 2)
            acc[cid][yi, ti] += c
        c0 == 0 and (r0 // 1024) % 8 == 0 and print(f"rows {r0 + h}/{H}: {len(acc)} cells", flush=True)

    to3347 = Transformer.from_crs(ry.crs, "EPSG:3347", always_xy=True)
    prov = json.loads((ROOT / "web/data/provinces.geojson").read_text())
    geoms = [shape(f["geometry"]) for f in prov["features"]]
    codes = [f["properties"].get("abbr") or f["properties"].get("id") for f in prov["features"]]
    tree = STRtree(geoms)
    cells, tot = [], defaultdict(lambda: np.zeros((nyear, 2), dtype=np.int64))
    for cid, a in sorted(acc.items()):
        r, c = divmod(cid, ncol)
        x, y = ry.transform * ((c + 0.5) * CELL, (r + 0.5) * CELL)
        X, Y = to3347.transform(x, y)
        p = Point(X, Y)
        hit = [i for i in tree.query(p) if geoms[i].contains(p)]
        if not hit:   # centre falls just offshore or in a lake gap: take the nearest province
            hit = [int(tree.nearest(p))]
        g = codes[hit[0]]
        tot[g] += a; tot["CAN"] += a
        yrs = {Y0 + i: [int(a[i, 0]), int(a[i, 1])] for i in range(nyear) if a[i].any()}   # pixel counts; hectares after regridding
        cells.append([round(X / 1e3, 1), round(Y / 1e3, 1), g, [[y_, f_, h_] for y_, (f_, h_) in yrs.items()]])
    totals = {g: {"fire": [round(v) for v in (a[:, 0] * 0.09).tolist()], "harvest": [round(v) for v in (a[:, 1] * 0.09).tolist()]} for g, a in tot.items()}
    write(cells, totals)


def regrid(cells, km=MAP_KM):
    """For the map only: add the 9 km cells into a km x km grid in StatCan Lambert (totals are computed before this, from the 9 km cells)."""
    out = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for x, y, g, yrs in cells:
        k = (round(x / km) * km, round(y / km) * km)
        for yy, f, h in yrs:
            out[k][yy][0] += f; out[k][yy][1] += h
    return [[x, y, [[yy, round(f * 0.09, 1), round(h * 0.09, 1)] for yy, (f, h) in sorted(v.items())]] for (x, y), v in sorted(out.items())]


def write(cells, totals):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(sources=["nrcan_canlad_year", "nrcan_canlad_type"], years=[Y0, Y1], cell_km=MAP_KM, units="hectares",
                                   cells=regrid(cells), totals=totals,
                                   notes=["Stand-replacing disturbance mapped from Landsat at 30 m by Natural Resources Canada (CanLaD 1984-2015).",
                                          "Each pixel keeps only its latest disturbance: land burned or cut twice counts once, in the later year, so earlier years are undercounted.",
                                          "Harvest and fire are disturbances, not permanent deforestation: most harvested and burned land regrows as forest.",
                                          "Totals use 9 km cells, each placed in the province or territory containing its centre. The map adds them into 18 km squares."]),
                              separators=(",", ":")))
    print(f"{OUT.relative_to(ROOT)}: {len(cells)} 9 km cells; Canada fire {sum(totals['CAN']['fire']):,} ha, harvest {sum(totals['CAN']['harvest']):,} ha")


if __name__ == "__main__":
    main()
