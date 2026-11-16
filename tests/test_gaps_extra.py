"""Hours of work, productivity, calculator inputs and sprawl people: every value traces to the published tables; nothing filled."""
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from common import load_registry, verify_raw  # noqa: E402

H = json.loads((ROOT / "web/data/gaps/hours.json").read_text())
P = json.loads((ROOT / "web/data/gaps/productivity.json").read_text())
C = json.loads((ROOT / "web/data/gaps/calc.json").read_text())
REG = load_registry()["sources"]


def rows(key):
    r = REG[key]; z = zipfile.ZipFile(verify_raw(r["raw_file"], r["sha256"]))
    return csv.DictReader(io.TextIOWrapper(z.open([n for n in z.namelist() if "MetaData" not in n][0]), encoding="utf-8-sig"))


def test_sources_registered():
    for d in (H, P, C):
        for s in d["sources"]:
            assert s in REG, s


def test_home_index_is_mean_of_twelve_published_months():
    m = [float(r["VALUE"]) for r in rows("statcan_18100205") if r["GEO"] == "Alberta" and r["New housing price indexes"] == "Total (house and land)" and r["REF_DATE"].startswith("2020")]
    assert len(m) == 12 and abs(H["data"]["AB"]["home"]["2020"] - round(sum(m) / 12, 2)) < 1e-9
    # incomplete current year is left out
    assert "2026" not in H["data"]["AB"]["home"]


def test_food_index_matches_existing_groceries_layer():
    g = json.loads((ROOT / "web/data/gaps/more.json").read_text())["food"]
    for geo, s in g.items():
        for y, v in s.items():
            assert H["data"][geo]["food"][y] == v["cpi"] and H["data"][geo]["wage"][y] == v["wage"]


def test_rent_hours_are_rent_over_province_wage():
    cities = {c["name"]: c for c in json.loads((ROOT / "web/data/housing/cities.json").read_text())["cities"]}
    for name, d in H["rent"].items():
        for y, (rent, hrs) in d["y"].items():
            assert rent == cities[name]["rent2br"][y]
            assert abs(hrs - round(rent / H["data"][d["prov"]]["wage"][y], 1)) < 1e-9
    assert H["rent"]["Edmonton"]["y"]["2025"] == [1598.0, 49.9]


def test_productivity_values_are_published():
    n = 0
    for r in rows("statcan_36100480"):
        if r["GEO"] == "Alberta" and r["Industry"] == "Business sector industries" and r["Labour productivity and related measures"] == "Labour productivity" and r["VALUE"]:
            assert P["prov"]["AB"]["lp"][r["REF_DATE"][:4]] == float(r["VALUE"]); n += 1
    assert n == 28   # 1997-2024


def test_peers_raw_and_rounded():
    raw = json.loads((ROOT / REG["worldbank_gdp_per_worker"]["raw_file"]).read_text())[1]
    for x in raw:
        if x["value"] is not None:
            assert P["peers"][x["countryiso3code"]]["perworker"][x["date"]] == round(x["value"])


def test_pop12_is_all_ages_minus_0_to_11():
    tot = kids = 0
    for r in rows("statcan_17100005"):
        if r["GEO"] == "Nova Scotia" and r["REF_DATE"] == "2022" and r["Gender"] == "Total - gender":
            if r["Age group"] == "All ages":
                tot = float(r["VALUE"])
            elif r["Age group"] in {"0 years", "1 year"} | {f"{a} years" for a in range(2, 12)}:
                kids += float(r["VALUE"])
    assert C["pop12"]["NS"]["2022"] == int(tot - kids)


def test_sprawl_people_cma_values():
    m = json.loads((ROOT / "web/data/demography/metro.json").read_text())["cmas"]
    p = json.loads((ROOT / "web/data/sprawl/people.json").read_text())["cities"]
    for slug, d in p.items():
        for y, v in d["pop"].items():
            if y != "latest":
                assert m[d["cma"]]["pop"][y] == v
