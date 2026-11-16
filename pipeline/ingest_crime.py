"""Police-reported crime: Crime Severity Index (overall, violent, non-violent) and weighted clearance rate.

  web/data/more/crime.json   Canada, provinces, territories and policing-based CMAs, 1998- (35-10-0026-01)

All values as published; '..'/'x'/'F' and blank become None (no value), never zero. Nothing is filled or extended.
1998 Northwest Territories includes Nunavut (table note 15), so it is stored under 'NT+NU'.
CMA names are the table's names before the comma; the policing-based CMA boundaries do not always match census CMAs (note 52).
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402

KEY = "statcan_35100026"
OUT = ROOT / "web/data/more/crime.json"
PROV = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB", "47": "SK", "48": "AB", "59": "BC",
        "60": "YT", "61": "NT", "62": "NU"}
STATS = {"Crime severity index": "csi", "Violent crime severity index": "vcsi", "Non-violent crime severity index": "nvcsi",
         "Weighted clearance rate": "wcr"}
# table spelling -> the explorer's city names (web/data/housing/cities.json)
CMA_NAME = {"St.Catharines-Niagara": "St. Catharines-Niagara"}
SKIP = {"Ottawa-Gatineau, Quebec part [24505]", "Ottawa-Gatineau, Ontario part [35505]"}   # the combined CMA is kept


def build() -> dict:
    reg = load_registry()["sources"][KEY]
    p = verify_raw(reg["raw_file"], reg["sha256"])
    z = zipfile.ZipFile(p)
    prov, cma, status = defaultdict(lambda: defaultdict(dict)), defaultdict(lambda: defaultdict(dict)), {}
    for r in csv.DictReader(io.TextIOWrapper(z.open("35100026.csv"), encoding="utf-8-sig")):
        k = STATS.get(r["Statistics"])
        if not k or r["GEO"] in SKIP:
            continue
        y = int(r["REF_DATE"])
        v = None if r["VALUE"] in ("", None) or r["STATUS"] in ("..", "x", "F", "...") else float(r["VALUE"])
        if v is None:
            continue
        g = r["GEO"]
        if g == "Canada":
            prov["CAN"][y][k] = v
            continue
        code = re.search(r"\[([\d/]+)\]$", g).group(1)
        if code in PROV:
            ab = "NT+NU" if code == "61" and y < 1999 else PROV[code]
            prov[ab][y][k] = v
        else:
            name = g.split(",")[0].strip()
            cma[CMA_NAME.get(name, name)][y][k] = v
        if r["STATUS"]:
            status[f"{g}|{y}|{k}"] = r["STATUS"]
    years = sorted({y for d in prov.values() for y in d})
    return dict(source_id=KEY, units={"csi": "index, Canada 2006 = 100", "vcsi": "index, Canada 2006 = 100", "nvcsi": "index, Canada 2006 = 100", "wcr": "weighted %"},
                years=[years[0], years[-1]], data=json.loads(json.dumps(prov)), cma=json.loads(json.dumps(cma)),
                notes=["Police-reported crime only: crimes not reported to police are not counted.",
                       "The Crime Severity Index weights each offence by the average sentence it receives; Canada in 2006 = 100. It is not a measure of overall safety (table note 55).",
                       "Weighted clearance rate: share of incidents solved by police (charge laid or cleared otherwise), weighted the same way.",
                       "Reporting changes move some series: 2018 'founded' definition update; British Columbia 2019 classification standards (notes 44-45); see the table notes for city-specific breaks.",
                       "CMAs are policing-based and do not always match census CMA boundaries (note 52). 1998 Northwest Territories includes Nunavut.",
                       "2025 values may undercount national-security incidents (RCMP, May-December 2025, note 60)."])


def main():
    d = build()
    OUT.write_text(json.dumps(d, separators=(",", ":")))
    print(f"{OUT.relative_to(ROOT)}: {len(d['data'])} provinces/territories/Canada, {len(d['cma'])} CMAs, {d['years'][0]}-{d['years'][1]}")


if __name__ == "__main__":
    main()
