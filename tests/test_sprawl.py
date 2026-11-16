"""Cities spreading: images and totals come from the same GHSL cells; built-up land never shrinks on the picture."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "web/data/sprawl/sprawl.json").read_text())


def test_images_match_metadata():
    for c in D["cities"]:
        a = np.array(Image.open(ROOT / f"web/data/sprawl/{c['slug']}.png"))
        assert list(a.shape) == c["size"] and a.shape[0] == c["half_km"] * 20
        assert a.max() <= len(D["epochs"])
        assert [int((a == k).sum()) for k in range(1, len(D["epochs"]) + 1)] == c["new_cells"]


def test_totals_positive_and_threshold_stated():
    assert D["threshold_m2"] == 2000 and D["epochs"] == [1975, 1985, 1990, 2000, 2010, 2020]
    for c in D["cities"]:
        assert all(v > 0 for v in c["km2"])
