"""Gaps #2-#4: values trace to the published tables; nothing filled."""
import csv, io, json, sys, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from common import load_registry, verify_raw  # noqa: E402
D = json.loads((ROOT / "web/data/gaps/more.json").read_text())


def rows(key):
    r = load_registry()["sources"][key]; z = zipfile.ZipFile(verify_raw(r["raw_file"], r["sha256"]))
    return csv.DictReader(io.TextIOWrapper(z.open([n for n in z.namelist() if "MetaData" not in n][0]), encoding="utf-8-sig"))


def test_no_provider_is_100_minus_published():
    n = 0
    for r in rows("statcan_13100096"):
        if r["GEO"] == "Alberta" and r["Indicators"] == "Has a regular healthcare provider" and r["Age group"] == "Total, 12 years and over" and r["Sex"] == "Both sexes" and r["Characteristics"] == "Percent":
            assert D["doctor"]["AB"][r["REF_DATE"]]["v"] == round(100 - float(r["VALUE"]), 1); n += 1
    assert n == 8


def test_food_hours_base_year_and_formula():
    for g, s in D["food"].items():
        assert s["1997"]["h"] == 1.0
        for y, v in s.items():
            assert abs(v["h"] - (v["cpi"] / s["1997"]["cpi"]) / (v["wage"] / s["1997"]["wage"])) < 0.001
