"""Forest disturbance (CanLaD 1984-2015): map squares and totals come from the same pixels; provinces add up to Canada."""
import json
from pathlib import Path

D = json.loads((Path(__file__).resolve().parent.parent / "web/data/forest/disturbance.json").read_text())
Y0, Y1 = D["years"]


def test_provinces_add_up_to_canada():
    for k in ("fire", "harvest"):
        for i in range(Y1 - Y0 + 1):
            s = sum(t[k][i] for g, t in D["totals"].items() if g != "CAN")
            assert abs(s - D["totals"]["CAN"][k][i]) <= 14, (k, Y0 + i)   # one hectare of rounding per province at most


def test_map_squares_match_totals():
    for i, y in enumerate(range(Y0, Y1 + 1)):
        f = sum(a for c in D["cells"] for yy, a, b in c[2] if yy == y)
        h = sum(b for c in D["cells"] for yy, a, b in c[2] if yy == y)
        for got, want in ((f, D["totals"]["CAN"]["fire"][i]), (h, D["totals"]["CAN"]["harvest"][i])):
            assert abs(got - want) <= max(50, want * 0.002), y   # per-square rounding only


def test_no_zero_years_invented():
    for c in D["cells"]:
        assert all(a + b > 0 for _, a, b in c[2])
