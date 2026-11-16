"""Gaps worth fixing #2-#4: family-doctor access, groceries against wages (homes per new resident is derived in the explorer).

  web/data/gaps/more.json
    doctor   Share of people 12+ WITHOUT a regular health care provider = 100 - published "has a regular healthcare provider" %
             (Canadian Community Health Survey, 13-10-0096-01, 2015-2022; the 95% interval is flipped the same way).
    food     Hours of work to buy the same groceries, relative to 1997 (= 1.00):
             (CPI food, year / CPI food, 1997) / (median hourly wage, year / median hourly wage, 1997).
             CPI 18-10-0005-01 (2002 = 100, annual average); wages 14-10-0064-01 (median hourly wage, all employees, all industries,
             15 years and over, both full- and part-time, current dollars). Provinces and Canada, 1997-2025.
Published values only; a year missing from either input is left out, never filled.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402

OUT = ROOT / "web/data/gaps/more.json"
AB = {"Canada": "CAN", "Canada (excluding territories)": "CAN", "Newfoundland and Labrador": "NL", "Prince Edward Island": "PE", "Nova Scotia": "NS", "New Brunswick": "NB", "Quebec": "QC",
      "Ontario": "ON", "Manitoba": "MB", "Saskatchewan": "SK", "Alberta": "AB", "British Columbia": "BC", "Yukon": "YT", "Northwest Territories": "NT",
      "Nunavut": "NU", "Territories": "TERR"}


def rows(key):
    reg = load_registry()["sources"][key]
    z = zipfile.ZipFile(verify_raw(reg["raw_file"], reg["sha256"]))
    n = [x for x in z.namelist() if "MetaData" not in x][0]
    yield from csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))


def num(r):
    return None if r["VALUE"] in ("", None) or r.get("STATUS") in ("..", "x", "F", "...") else float(r["VALUE"])


def doctor():
    out = {}
    want = {"Percent": "v", "Low 95% confidence interval, percent": "hi", "High 95% confidence interval, percent": "lo"}   # flipped: 100 - x
    for r in rows("statcan_13100096"):
        if r["Indicators"] != "Has a regular healthcare provider" or r["Age group"] != "Total, 12 years and over" or r["Sex"] != "Both sexes":
            continue
        g = AB.get(r["GEO"]); k = want.get(r["Characteristics"]); v = num(r)
        if not g or not k or v is None:
            continue
        out.setdefault(g, {}).setdefault(r["REF_DATE"], {})[k] = round(100 - v, 1)
        if r["STATUS"] == "E":
            out[g][r["REF_DATE"]]["e"] = 1   # use with caution (StatCan "E")
    return out


def food():
    cpi, wage = {}, {}
    for r in rows("statcan_18100005"):
        if r["Products and product groups"] == "Food" and r["UOM"] == "2002=100" and r["GEO"] in AB and num(r) is not None:
            cpi.setdefault(AB[r["GEO"]], {})[int(r["REF_DATE"])] = num(r)
    for r in rows("statcan_14100064"):
        if (r["Wages"] == "Median hourly wage rate" and r["Type of work"] == "Both full- and part-time employees" and r["Gender"] == "Total - Gender"
                and r["Age group"] == "15 years and over" and r["North American Industry Classification System (NAICS)"] == "Total employees, all industries"
                and r["GEO"] in AB and num(r) is not None):
            wage.setdefault(AB[r["GEO"]], {})[int(r["REF_DATE"])] = num(r)
    out = {}
    for g in wage:
        c, w = cpi.get(g, {}), wage[g]
        if 1997 not in c or 1997 not in w:
            continue
        out[g] = {str(y): {"h": round((c[y] / c[1997]) / (w[y] / w[1997]), 3), "cpi": c[y], "wage": w[y]} for y in sorted(w) if y in c}
    return out


def main():
    d = dict(sources=["statcan_13100096", "statcan_18100005", "statcan_14100064"], doctor=doctor(), food=food(),
             notes=["Without a regular health care provider: people 12 and over who said they do not have a regular health care provider (a family doctor, nurse practitioner or other). Canadian Community Health Survey; 2015–2022 is the last span in this table. Survey estimates have a margin of error, shown as a range.",
                    "Groceries in hours of work: how many hours at the median hourly wage it takes to buy the same groceries, compared with 1997. Above 1.00 means food prices rose faster than wages. CPI food is an index of the same basket over time, not a price level, so provinces are compared with their own 1997, not with each other."])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(d, separators=(",", ":")))
    print(OUT.relative_to(ROOT), {k: len(v) for k, v in d.items() if isinstance(v, dict)})


if __name__ == "__main__":
    main()
