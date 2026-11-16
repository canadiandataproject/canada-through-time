"""Relief and rivers under the city pictures, on the same local equal-area square as web/data/sprawl/<slug>.png.

  web/data/sprawl/<slug>_relief.png   shaded relief, 1080 x 1080 (about 56 m a pixel), grey 0-255, light from the northwest,
                                      heights exaggerated 4x so a river valley 50-60 m deep reads at city scale
  web/data/sprawl/<slug>_water.png    water, same grid: 255 where ESA WorldCover 2021 maps permanent water (class 80) on most of the pixel

Sources: Copernicus DEM GLO-30 (30 m; a surface model, so it includes buildings and trees) and ESA WorldCover 10 m 2021 v200.
Only cities whose tiles are in data/raw/terrain are built. The relief is a backdrop for orientation: no number is read from it.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_origin
import rasterio.windows
from rasterio.warp import Resampling, reproject

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402

N = 1080
CITIES = {   # tiles covering each city's square; elev = plausible median ground height (m) as a sanity check
    "edmonton": dict(dem=["copernicus_dem_glo30_n53w114"], water=["esa_worldcover_2021_n51w114"], elev=(550, 800)),
    "calgary": dict(dem=["copernicus_dem_glo30_n50w115", "copernicus_dem_glo30_n50w114", "copernicus_dem_glo30_n51w115", "copernicus_dem_glo30_n51w114"],
                    water=["esa_worldcover_2021_n48w117", "esa_worldcover_2021_n48w114", "esa_worldcover_2021_n51w117", "esa_worldcover_2021_n51w114"], elev=(950, 1300)),
}


def main():
    reg = load_registry()["sources"]
    meta = json.loads((ROOT / "web/data/sprawl/sprawl.json").read_text())
    for slug, src in CITIES.items():
        c = next(x for x in meta["cities"] if x["slug"] == slug); h = c["half_km"] * 1000; px = 2 * h / N
        crs = f"+proj=laea +lat_0={c['lat']} +lon_0={c['lon']} +datum=WGS84 +units=m +no_defs"; tf = from_origin(-h, h, px, px)
        z = np.full((N, N), np.nan, np.float32)
        for k in src["dem"]:                     # each tile fills the part of the square it covers
            part = np.full((N, N), np.nan, np.float32)
            with rasterio.open(verify_raw(reg[k]["raw_file"], reg[k]["sha256"])) as d:
                reproject(rasterio.band(d, 1), part, dst_transform=tf, dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan)
            z = np.where(np.isfinite(part) & ~np.isfinite(z), part, z)
        lo, hi = src["elev"]
        assert np.isfinite(z).mean() > 0.999 and lo < np.nanmedian(z) < hi, (slug, np.nanmedian(z))
        # hillshade: light from 315° azimuth, 40° altitude; 4x vertical exaggeration
        gy, gx = np.gradient(z * 4.0, px)
        slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
        az, alt = np.radians(315), np.radians(40)
        hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
        hs = np.clip((hs - hs.min()) / (np.percentile(hs, 99.5) - hs.min()), 0, 1)
        Image.fromarray((hs * 255).astype(np.uint8), "L").save(ROOT / f"web/data/sprawl/{slug}_relief.png", optimize=True)
        w = np.zeros((N, N), np.float32)
        for k in src["water"]:
            with rasterio.open(verify_raw(reg[k]["raw_file"], reg[k]["sha256"])) as d:
                win = d.window(*rasterio.warp.transform_bounds(crs, d.crs, -h, -h, h, h)).intersection(rasterio.windows.Window(0, 0, d.width, d.height))
                if win.width < 1 or win.height < 1: continue
                src_a = (d.read(1, window=win) == 80).astype(np.float32)
                part = np.full((N, N), np.nan, np.float32)
                reproject(src_a, part, src_transform=d.window_transform(win), src_crs=d.crs, dst_transform=tf, dst_crs=crs, resampling=Resampling.average, dst_nodata=np.nan)
            w = np.where(np.isfinite(part), np.maximum(w, part), w)
        wm = (w >= 0.4).astype(np.uint8) * 255
        assert 0.002 < (wm > 0).mean() < 0.05, (wm > 0).mean()     # a river and some lakes, not a flood
        Image.fromarray(wm, "L").save(ROOT / f"web/data/sprawl/{slug}_water.png", optimize=True)
        print(f"{slug}: relief {z.min():.0f}-{z.max():.0f} m, water {(wm > 0).mean() * 100:.2f}% of the square")


if __name__ == "__main__":
    main()
