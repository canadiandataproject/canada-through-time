"""Crime Severity Index: hash-verified raw file, values exactly as published, no gaps filled."""
import csv, io, json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "web/data/more/crime.json").read_text())


def raw():
    import sys; sys.path.insert(0, str(ROOT / "pipeline"))
    from common import load_registry, verify_raw
    r = load_registry()["sources"]["statcan_35100026"]
    z = zipfile.ZipFile(verify_raw(r["raw_file"], r["sha256"]))
    return list(csv.DictReader(io.TextIOWrapper(z.open("35100026.csv"), encoding="utf-8-sig")))


def test_base_year_is_100():
    assert abs(D["data"]["CAN"]["2006"]["csi"] - 100) < 0.01


def test_every_value_matches_the_table():
    want = {"Crime severity index": "csi", "Violent crime severity index": "vcsi", "Non-violent crime severity index": "nvcsi", "Weighted clearance rate": "wcr"}
    n = 0
    for r in raw():
        if r["GEO"] == "Canada" and r["Statistics"] in want and r["VALUE"] and not r["STATUS"]:
            assert D["data"]["CAN"][r["REF_DATE"]][want[r["Statistics"]]] == float(r["VALUE"]); n += 1
        if r["GEO"].startswith("Toronto,") and r["Statistics"] in want and r["VALUE"] and r["STATUS"] not in ("..", "x", "F"):
            assert D["cma"]["Toronto"][r["REF_DATE"]][want[r["Statistics"]]] == float(r["VALUE"]); n += 1
    assert n > 150


def test_no_zero_fill_and_nunavut_split():
    assert set(D["data"]["NT+NU"]) == {"1998"}
    assert "1998" not in D["data"].get("NU", {}) and "1998" not in D["data"]["NT"]
    for g in D["data"].values():
        for v in g.values():
            assert all(x is not None and x > 0 for x in v.values())
