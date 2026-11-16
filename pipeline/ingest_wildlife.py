"""Animals on the move: satellite-tracked ivory gulls from Seymour Island, Nunavut, 2010-2013 (Spencer, Gilchrist and Mallory; CC0).

  web/data/wildlife/ivory_gulls.json
    One position per bird per day: the median latitude and longitude of that day's best Argos fixes (location classes 3, 2, 1).
    A day that would need more than 500 km of travel from the previous kept day is dropped as a likely bad fix.
    Positions are rounded to 0.2 deg latitude / 0.5 deg longitude (about 15-25 km) because the species is endangered, then
    projected to Statistics Canada Lambert (km), the explorer's map projection.
Nothing is interpolated: a day with no good fix has no position.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402
from build_explorer_data import lcc  # noqa: E402

GOOD = {"3", "2", "1"}
MAX_KM_PER_DAY = 500


def km(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0]); dp = p2 - p1; dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def main():
    r = load_registry()["sources"]["zenodo_ivory_gull_tracks"]
    fixes = defaultdict(lambda: defaultdict(list))
    with verify_raw(r["raw_file"], r["sha256"]).open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["Location.class"] not in GOOD or not row["Latitude"] or not row["Longitude"]:
                continue
            d = dt.datetime.strptime(row["Location.date"].split()[0], "%d/%m/%Y").date()
            fixes[row["PTT"]][d].append((float(row["Latitude"]), float(row["Longitude"])))
    start = min(min(days) for days in fixes.values())
    birds, dropped = [], 0
    for i, (ptt, days) in enumerate(sorted(fixes.items())):
        kept, prev = [], None
        for d in sorted(days):
            lat = statistics.median(p[0] for p in days[d]); lon = statistics.median(p[1] for p in days[d])
            if prev and km(prev[1], (lat, lon)) > MAX_KM_PER_DAY * (d - prev[0]).days:
                dropped += 1; continue
            prev = (d, (lat, lon))
            rl, ro = round(lat / 0.2) * 0.2, round(lon / 0.5) * 0.5
            x, y = lcc(ro, rl)
            kept.append([(d - start).days, x, y, round(rl, 1)])
        birds.append({"id": chr(65 + i), "first": kept[0][0], "last": kept[-1][0], "n": len(kept), "days": kept})
    colony = lcc(-101.3, 76.8)
    out = dict(source="zenodo_ivory_gull_tracks", species="Ivory gull (Pagophila eburnea)", start=start.isoformat(),
               end=(start + dt.timedelta(days=max(b["last"] for b in birds))).isoformat(), colony=list(colony), birds=birds,
               notes=["Twelve ivory gulls fitted with satellite transmitters on Seymour Island, Nunavut, in 2010. One dot per bird per day, at the middle of that day's best satellite fixes; days without a good fix are left empty.",
                      "Positions are rounded to about 15–25 km because the ivory gull is endangered in Canada.",
                      "Transmitters stopped at different times, so fewer birds are on the map in later years. Twelve birds from one colony show routes, not a count of the population."])
    p = ROOT / "web/data/wildlife/ivory_gulls.json"; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, separators=(",", ":")))
    print(p.relative_to(ROOT), len(birds), "birds,", sum(b["n"] for b in birds), "bird-days,", dropped, "days dropped;", out["start"], "to", out["end"])


if __name__ == "__main__":
    main()
