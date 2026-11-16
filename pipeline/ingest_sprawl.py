"""Cities spreading out: built-up land around 12 metros, 1975-2020 (JRC Global Human Settlement Layer, GHS-BUILT-S R2023A, 100 m).

  web/data/sprawl/sprawl.json        per city: centre, radius, built-up surface (km2) in each epoch
  web/data/sprawl/<slug>.png         one 100 m pixel per GHSL cell: 0 = not built up by 2020, k = first epoch (1..6) in which the
                                     cell's built-up surface reached 20% of its area (2,000 of 10,000 m2)

GHS-BUILT-S is the area covered by buildings in each 100 m cell, estimated from Landsat and Sentinel-2 imagery and modelled
between observation years. Epochs: 1975, 1985, 1990, 2000, 2010, 2020. Each city is redrawn on a local equal-area grid (Lambert azimuthal) centred on it, averaging GHSL's Mollweide cells, so
shapes and areas are true.
The 20% threshold is ours (stated on screen); the km2 totals use every cell's full built-up value, with no threshold.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.merge import merge
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject, transform_bounds

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402

EPOCHS = [1975, 1985, 1990, 2000, 2010, 2020]
THRESH = 2000
OUT = ROOT / "web/data/sprawl"
# name, slug, lon, lat, half-width in km (to hold today's built-up area)
CITIES = [("Toronto", "toronto", -79.38, 43.70, 55), ("Montréal", "montreal", -73.62, 45.52, 45), ("Vancouver", "vancouver", -122.95, 49.22, 42),
          ("Calgary", "calgary", -114.07, 51.04, 28), ("Edmonton", "edmonton", -113.49, 53.54, 30), ("Ottawa-Gatineau", "ottawa", -75.70, 45.40, 32),
          ("Winnipeg", "winnipeg", -97.14, 49.88, 24), ("Québec", "quebec", -71.25, 46.81, 26), ("Halifax", "halifax", -63.60, 44.68, 24),
          ("Saskatoon", "saskatoon", -106.65, 52.13, 18), ("Regina", "regina", -104.62, 50.45, 16), ("Kelowna", "kelowna", -119.45, 49.90, 20)]


def tiles():
    reg = load_registry()["sources"]["jrc_ghsl_built_s"]
    man = verify_raw(reg["raw_file"], reg["sha256"])
    files = json.loads(man.read_text())["files"]
    by_e = {e: [] for e in EPOCHS}
    for name, meta in files.items():
        p = man.parent / name
        assert p.exists(), f"missing {name}: download it from {meta['url']}"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == meta["sha256"], name
        by_e[int(name.split("_")[3][1:])].append(f"/vsizip/{p}/{name[:-4]}.tif")
    return by_e


def main():
    by_e = tiles()
    OUT.mkdir(parents=True, exist_ok=True)
    meta = []
    for name, slug, lon, lat, km in CITIES:
        h = km * 1000; n = int(2 * h / 100)
        # a square on a local equal-area grid centred on the city (true shapes and areas), filled from GHSL's Mollweide cells
        dst_crs = f"+proj=laea +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m +no_defs"
        dst_tf = from_origin(-h, h, 100, 100)
        mb = transform_bounds(dst_crs, "ESRI:54009", -h, -h, h, h, densify_pts=41)
        pad = 3000; bounds = (mb[0] - pad, mb[1] - pad, mb[2] + pad, mb[3] + pad)
        first = None; km2 = []
        for k, e in enumerate(EPOCHS, start=1):
            srcs = [rasterio.open(f) for f in by_e[e]]
            arr, tf = merge(srcs, bounds=bounds, res=100, nodata=65535)
            crs = srcs[0].crs
            for s_ in srcs: s_.close()
            src = arr[0].astype(np.float32); src[arr[0] == 65535] = np.nan
            assert np.isfinite(src).mean() > 0.97, (name, e)          # the window must sit inside the downloaded tiles
            a = np.full((n, n), np.nan, dtype=np.float32)
            reproject(src, a, src_transform=tf, src_crs=crs, src_nodata=np.nan, dst_transform=dst_tf, dst_crs=dst_crs, dst_nodata=np.nan, resampling=Resampling.average)
            assert np.isfinite(a).mean() > 0.99, (name, e)
            km2.append(round(float(np.nansum(a)) / 1e6, 2))     # m2 of buildings per 100 m cell, summed (both grids are equal-area)
            if first is None: first = np.zeros(a.shape, dtype=np.uint8)
            first[(first == 0) & (np.nan_to_num(a) >= THRESH)] = k
        Image.fromarray(first, mode="L").save(OUT / f"{slug}.png", optimize=True)
        cells = [int((first == k).sum()) for k in range(1, len(EPOCHS) + 1)]
        meta.append(dict(name=name, slug=slug, lon=lon, lat=lat, half_km=km, size=list(first.shape), km2=km2, new_cells=cells))
        print(f"{name}: built-up {km2[0]} -> {km2[-1]} km2; cells over 20%: {cells}")
    (OUT / "sprawl.json").write_text(json.dumps(dict(source_id="jrc_ghsl_built_s", epochs=EPOCHS, threshold_m2=THRESH, cell_m=100, cities=meta,
        notes=["Built-up surface is the ground covered by buildings, estimated by the European Commission's Joint Research Centre from Landsat and Sentinel-2 satellite images (GHS-BUILT-S R2023A). Years between satellite observations are modelled by the JRC.",
               "On the picture, a 100 m square counts as built up once buildings cover 20% of it; its colour is the first year that happened. The square kilometre totals add up every square's full building area, with no threshold.",
               "The view is a square around the city centre (half-width shown), not the census metropolitan area."]), separators=(",", ":")))


if __name__ == "__main__":
    main()
