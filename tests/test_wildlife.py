"""Ivory gull tracks: one position per bird per day, from the best Argos fixes, rounded; nothing interpolated."""
import csv, datetime as dt, json, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from common import load_registry, verify_raw  # noqa: E402
from build_explorer_data import lcc  # noqa: E402

W = json.loads((ROOT / "web/data/wildlife/ivory_gulls.json").read_text())


def test_days_are_unique_and_sorted():
    for b in W["birds"]:
        d = [x[0] for x in b["days"]]
        assert d == sorted(set(d)) and b["n"] == len(d)


def test_a_day_matches_the_median_of_good_fixes():
    r = load_registry()["sources"]["zenodo_ivory_gull_tracks"]
    start = dt.date.fromisoformat(W["start"]); ptts = sorted({row["PTT"] for row in csv.DictReader(verify_raw(r["raw_file"], r["sha256"]).open(encoding="utf-8-sig"))})
    b = W["birds"][5]; day = b["days"][100]; date = start + dt.timedelta(days=day[0])
    fx = [(float(x["Latitude"]), float(x["Longitude"])) for x in csv.DictReader(verify_raw(r["raw_file"], r["sha256"]).open(encoding="utf-8-sig"))
          if x["PTT"] == ptts[5] and x["Location.class"] in {"1", "2", "3"} and dt.datetime.strptime(x["Location.date"].split()[0], "%d/%m/%Y").date() == date]
    lat, lon = statistics.median(p[0] for p in fx), statistics.median(p[1] for p in fx)
    assert [day[1], day[2]] == list(lcc(round(lon / 0.5) * 0.5, round(lat / 0.2) * 0.2))
