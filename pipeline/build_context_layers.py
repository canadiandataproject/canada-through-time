"""Context layers for the explorer's Whiteout / Blue hour identity (physical geography and decoration only; no statistic).

1. Neighbour relief: the same Natural Earth "Shaded Relief Basic" 1:50m source as the Canada layer (SR_50M.tif, public
   domain), resampled to an 8 km grid in StatCan Lambert (EPSG:3347) and clipped to the map's own neighbouring-country
   outlines (USA, Greenland, Russia ...). Same flat-ground grey (205.1) and contrast stretch as pipeline/build_relief.py.
   -> web/data/relief/relief_neighbours_8km.png
2. Sea cells: a 30 km grid over the sea. Each cell stores its distance to the nearest coast in cells, so the explorer can
   draw the sea as small stepped cubes with ripples spreading from every coast. Built from the map's own outlines only.
   Codes: 0 = Canada, 1 = neighbouring land, 2+ = sea (distance + 2, capped at 62).  -> web/data/explorer/sea_cells.json
3. Lens wireframe: lines every 30 km across Canada, sampled every 12 km, lifted by the Canada relief (shade, not
   elevation: the hillshade's light/dark as a gentle bump). Drawn only inside the optional lens.
   -> web/data/explorer/lens_wire.json
Nothing here moves, resizes or recolours any mark that carries data.
"""
import base64, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer
from scipy.ndimage import distance_transform_edt
Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/raw/naturalearth/SR_50M.tif"
WEB = ROOT / "web/data"
FLAT = 205.1                                    # flat-ground grey of the source (web/data/relief/relief.json)


def rings(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        yield poly[0], poly[1:]


def raster(features, X0, Y1, cell, nx, ny):
    m = Image.new("L", (nx, ny), 0); d = ImageDraw.Draw(m)
    for f in features:
        for outer, holes in rings(f["geometry"]):
            d.polygon([((x - X0) / cell, (Y1 - y) / cell) for x, y in outer], fill=255)
            for h in holes: d.polygon([((x - X0) / cell, (Y1 - y) / cell) for x, y in h], fill=0)
    return np.asarray(m) > 0


def sample(src, X0, Y1, cell, nx, ny):
    H, W = src.shape
    gx, gy = np.meshgrid(X0 + (np.arange(nx) + .5) * cell, Y1 - (np.arange(ny) + .5) * cell)
    lon, lat = Transformer.from_crs(3347, 4326, always_xy=True).transform(gx, gy)
    px = (lon + 180) / 360 * W - .5; py = (90 - lat) / 180 * H - .5
    x0 = np.clip(np.floor(px).astype(int), 0, W - 2); y0 = np.clip(np.floor(py).astype(int), 0, H - 2)
    fx, fy = np.clip(px - x0, 0, 1), np.clip(py - y0, 0, 1)
    return src[y0, x0] * (1 - fx) * (1 - fy) + src[y0, x0 + 1] * fx * (1 - fy) + src[y0 + 1, x0] * (1 - fx) * fy + src[y0 + 1, x0 + 1] * fx * fy


def main():
    prov = json.loads((WEB / "provinces.geojson").read_text())["features"]
    ctx = json.loads((WEB / "context_countries.geojson").read_text())["features"]
    src = np.asarray(Image.open(SRC).convert("L"), dtype=np.float32)

    # 1 · neighbour relief
    cell, (X0, Y0, X1, Y1) = 8000.0, (1500e3, -900e3, 11000e3, 7500e3)
    nx, ny = int((X1 - X0) / cell), int((Y1 - Y0) / cell)
    g = sample(src, X0, Y1, cell, nx, ny); m = raster(ctx, X0, Y1, cell, nx, ny) & ~raster(prov, X0, Y1, cell, nx, ny)
    dev = (g - FLAT) / 255.0
    rgba = np.zeros((ny, nx, 4), np.uint8); rgba[..., :3] = np.where(dev[..., None] > 0, 255, 0)
    rgba[..., 3] = (np.clip(np.abs(dev) * 2.6, 0, 1) * m * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(WEB / "relief/relief_neighbours_8km.png", optimize=True)
    meta = json.loads((WEB / "relief/relief.json").read_text())
    meta["neighbours"] = {"file": "relief_neighbours_8km.png", "bounds_km": [X0 / 1e3, Y0 / 1e3, X1 / 1e3, Y1 / 1e3], "cell_km": cell / 1e3, "size": [nx, ny],
                          "note": "Same source and stretch, clipped to the neighbouring countries drawn on the map. Context only."}
    (WEB / "relief/relief.json").write_text(json.dumps(meta, indent=1))

    # 2 · sea cells
    cell, (X0, Y0, X1, Y1) = 30000.0, (-1000e3, -4000e3, 13500e3, 10000e3)
    nx, ny = int((X1 - X0) / cell), int((Y1 - Y0) / cell)
    can, other = raster(prov, X0, Y1, cell, nx, ny), raster(ctx, X0, Y1, cell, nx, ny)
    land = can | other
    dist = distance_transform_edt(~land)
    code = np.where(can, 0, np.where(other, 1, np.clip(np.round(dist) + 2, 2, 62))).astype(np.uint8)
    (WEB / "explorer/sea_cells.json").write_text(json.dumps({
        "cell_km": cell / 1e3, "x0_km": X0 / 1e3, "y1_km": Y1 / 1e3, "nx": nx, "ny": ny, "order": "rows from north (y1) to south, columns west to east",
        "codes": "0 Canada, 1 neighbouring land, 2+ sea: cells to the nearest coast + 2 (capped at 62; ripples have faded by then)",
        "data": base64.b64encode(code.tobytes()).decode()}, separators=(",", ":")))

    # 3 · lens wireframe over Canada, lifted by the Canada hillshade
    rel = np.array(Image.open(WEB / "relief/relief_canada_3km.png")).astype(float)
    shade = np.where(rel[..., 0] > 127, 1, -1) * rel[..., 3] / 255.0
    RX0, RY0, RX1, RY1 = [v * 1e3 for v in meta["bounds_km"]]; RH, RW = shade.shape
    step, spacing = 12000.0, 30000.0
    xs = np.arange(RX0, RX1, step); mx = int((RX1 - RX0) / 3000.0)
    can3 = raster(prov, RX0, RY1, 3000.0, mx, RH)
    lines = []
    for y in np.arange(RY0 + spacing / 2, RY1, spacing):
        j = int((RY1 - y) / 3000.0)
        if not 0 <= j < RH: continue
        run = []
        for x in xs:
            i = int((x - RX0) / 3000.0)
            if 0 <= i < RW and can3[j, i]:
                s = shade[max(0, j - 1):j + 2, max(0, i - 1):i + 2].mean()
                run.append([round(x / 1e3), round(y / 1e3), round(float(s) * 100)])
            elif len(run) > 1: lines.append(run); run = []
            else: run = []
        if len(run) > 1: lines.append(run)
    flat = np.array([p for ln in lines for p in ln], dtype=np.int16)
    (WEB / "explorer/lens_wire.json").write_text(json.dumps({
        "spacing_km": spacing / 1e3, "step_km": step / 1e3, "lens": [len(ln) for ln in lines],
        "xyz": base64.b64encode(flat.tobytes()).decode(), "z": "hillshade x100 (-100 dark .. +100 light); a visual bump, not elevation"}, separators=(",", ":")))
    print("neighbours", nx, ny, "| sea cells", int((code >= 2).sum()), "| wire lines", len(lines), "points", len(flat),
          "| sizes KB", *[round((WEB / p).stat().st_size / 1024) for p in ["relief/relief_neighbours_8km.png", "explorer/sea_cells.json", "explorer/lens_wire.json"]])


if __name__ == "__main__":
    main()
