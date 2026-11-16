"""Long-term drinking water advisories on public systems on First Nations reserves (Indigenous Services Canada).

  web/data/gaps/water.json   every advisory in ISC's map file (active and lifted since November 2015), English and French text,
                             plus the number in effect at the start of each month (derived).

Values as published. Derived: the monthly count of advisories in effect, from each advisory's long-term start date
(DateLTDWASet) and, for lifted ones, the lift date. In ISC's file the lift date of a lifted advisory is the field named
DateExpected (the map labels it as the date lifted). An advisory with no long-term start date is listed but not counted
in the monthly series, and the file says so. The file only holds advisories lifted since November 2015, so no series is
built before November 2015.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402

LCC = Transformer.from_crs("EPSG:4326", "EPSG:3347", always_xy=True)
km = lambda lon, lat: [round(v / 1e3, 2) for v in LCC.transform(lon, lat)]
OUT = ROOT / "web/data/gaps/water.json"
START = "2015-11"


def load(key):
    r = load_registry()["sources"][key]
    return json.loads(verify_raw(r["raw_file"], r["sha256"]).read_text(encoding="utf-8-sig"))["data"]


def clean(s):
    return " ".join((s or "").split())


def build():
    en, fr = load("isc_ltdwa_en"), load("isc_ltdwa_fr")
    frx = {a["AdvisoryID"]: a for c in fr for k in ("LTDWACurrent", "LTDWALifted") for a in c[k]}
    adv, fixed = [], []
    for c in en:
        for k, active in (("LTDWACurrent", True), ("LTDWALifted", False)):
            for a in c[k]:
                f = frx[a["AdvisoryID"]]
                lon, lat = float(a["Longitude"]), float(a["Lattitude"])
                if lon > 0:   # data-entry slip in ISC's file (longitude missing its minus sign): place it at the community's own coordinates
                    lon, lat = float(c["Longitude"]), float(c["Latitude"]); fixed.append(f'{c["CommunityName"]} (advisory {a["AdvisoryID"]})')
                adv.append(dict(id=a["AdvisoryID"], community=c["CommunityName"], prov=c["ProvinceAcronym"], system=clean(a["WaterSystemName"]),
                                type=[clean(a["AdvisoryType"]), clean(f["AdvisoryType"])], first=a["DateSet"] or None, set=a["DateLTDWASet"] or None,
                                lifted=None if active else (a["DateExpected"] or None), active=active, phase=[a["LongPhase"], f["LongPhase"]],
                                fix=[clean(a["CorrectiveMeasure"]), clean(f["CorrectiveMeasure"])], people=[a["PopulatioEstimated"], f["PopulatioEstimated"]],
                                xy=km(lon, lat)))
    months, y, m = [], 2015, 11
    last = max([a["lifted"] for a in adv if a["lifted"]] + [a["set"] for a in adv if a["set"]])[:7]
    while f"{y:04d}-{m:02d}" <= last:
        t = f"{y:04d}-{m:02d}-01"
        months.append([t[:7], sum(1 for a in adv if a["set"] and a["set"] <= t and (a["active"] or a["lifted"] > t))])
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    nodate = [a["id"] for a in adv if not a["set"]]
    return dict(sources=["isc_ltdwa_en", "isc_ltdwa_fr"], active=sum(a["active"] for a in adv), lifted=sum(not a["active"] for a in adv),
                in_effect=months, undated=nodate, advisories=sorted(adv, key=lambda a: (not a["active"], a["set"] or "0")),
                notes=["Long-term: in place for more than 12 months. Public water systems on reserve that Indigenous Services Canada supports; private wells, "
                       "systems the federal government does not fund, and First Nations outside this program (such as in British Columbia under the First Nations "
                       "Health Authority, or self-governing nations) are not covered the same way.",
                       "Monthly counts are derived from each advisory's start and lift dates; the file only lists advisories lifted since November 2015.",
                       *([f"Placed at the community's coordinates because the advisory's own longitude in the file has no minus sign: {', '.join(fixed)}."] if fixed else []),
                       f"{len(nodate)} active advisory has no long-term start date in the file, so it is not in the monthly counts." if len(nodate) == 1 else
                       f"{len(nodate)} advisories have no long-term start date in the file and are not in the monthly counts."])


def main():
    d = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    print(f"{OUT.relative_to(ROOT)}: {d['active']} active, {d['lifted']} lifted; in effect {d['in_effect'][0]} -> {d['in_effect'][-1]}")


if __name__ == "__main__":
    main()
