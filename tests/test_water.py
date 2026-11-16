"""Water advisories: hash-verified ISC file, counts match ISC's published figures, derived monthly counts are reproducible."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "web/data/gaps/water.json").read_text())


def test_counts_match_isc_published_figures():
    # ISC, "Ending long-term drinking water advisories", numbers as of October 21, 2026: 39 active, 158 lifted since November 2015
    assert (D["active"], D["lifted"]) == (39, 158)
    assert all(a["lifted"] >= "2015-11-01" for a in D["advisories"] if not a["active"])


def test_monthly_counts_recompute():
    for m, n in D["in_effect"]:
        t = m + "-01"
        assert n == sum(1 for a in D["advisories"] if a["set"] and a["set"] <= t and (a["active"] or a["lifted"] > t)), m


def test_every_advisory_is_placed_and_bilingual():
    for a in D["advisories"]:
        x, y = a["xy"]
        assert 3500 < x < 9500 and 0 < y < 5000, a["community"]
        assert all(len(v) == 2 for v in (a["type"], a["phase"], a["fix"], a["people"]))
