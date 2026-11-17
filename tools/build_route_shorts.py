"""Three Shorts in the Whiteout / Blue hour look (2026-11-17), rendered from the explorer itself (render/timelapse.py
--build explore-v2). Every number in a hook or summary is computed here from the same files the explorer shows, and
checked against the values read off the map before writing.

    python3 tools/build_route_shorts.py      -> timelapses/route-*.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; WEB = ROOT / "web/data"
P = json.loads((WEB / "population.json").read_text()); S, D = P["series"], P["dates"]
JUL = {int(d[:4]): i for i, d in enumerate(D) if d.endswith("-07-01")}
pop = lambda g, y: S[g][JUL[y]]
H = json.loads((WEB / "gaps/hours.json").read_text())
def hx(g, k, y, b=1997):
    h = H["data"][g]; return (h[k][str(y)] / h[k][str(b)]) / (h["wage"][str(y)] / h["wage"][str(b)])
R = {c: v["y"] for c, v in H["rent"].items()}
rh = lambda c, y: R[c][str(y)][1]
mil = lambda n: f"{n / 1e6:.2f}M"
base = dict(version=1, fps=30, surface="relief", credit="The Canadian Data Project", format="9x16", motion="smooth")

# 1 · Alberta tripled (people, 1971 → 2026)
ab71, ab26 = pop("AB", 1971), pop("AB", 2026); k = ab26 / ab71; can = pop("CAN", 2026) / pop("CAN", 1971)
assert (round(ab71), round(ab26)) == (1665717, 5101050) and round(k, 2) == 3.06 and round(can, 2) == 1.90
first = lambda m: next(y for y in sorted(JUL) if y >= 1971 and pop("AB", y) >= m)
assert [first(m) for m in (2e6, 3e6, 4e6, 5e6)] == [1978, 2000, 2014, 2025]
alberta = dict(base, id="route-alberta-tripled", title="Alberta tripled", layer="pop", place="AB", **{"from": 1971, "to": 2026},
  subtitle="People in each province and territory on July 1, 1971 to 2026. Column height shows the number of people.",
  intro=2.6, perYear=0.36, hold=0.8, outro=3.5, camera="push", theme="bluehour",
  hook=["Alberta had 1.67 million people in 1971.", "Guess how many now."],
  annotations=[{"year": y, "text": f"Alberta passes {n} million people"} for n, y in zip((2, 3, 4, 5), (1978, 2000, 2014, 2025))] + [{"year": 2026, "text": "2026 is a preliminary estimate"}],
  summary={"seconds": 6, "items": [
    {"big": mil(ab26), "kicker": "Alberta, July 1, 2026 (preliminary)", "text": f"up from {mil(ab71)} in 1971", "scope": "year"},
    {"big": f"×{k:.2f}", "kicker": "Alberta since 1971", "text": f"Canada as a whole grew ×{can:.2f}", "scope": "period"}]})

# 2 · Rent in hours of work (cities, 1997 → 2025)
assert round(rh("Vancouver", 2025), 1) == 72.8 and round(rh("Kelowna", 1997), 1) == 39.8 and round(rh("Kelowna", 2025), 1) == 64.6
jump = max((c for c in R if R[c].get("1997") and R[c].get("2025")), key=lambda c: rh(c, 2025) - rh(c, 1997)); assert jump == "Kelowna"
low = min((c for c in R if R[c].get("2025")), key=lambda c: rh(c, 2025)); assert low == "Saguenay" and round(rh(low, 2025), 1) == 32.9
rent = dict(base, id="route-rent-hours", title="Rent in hours of work", layer="renth", place=None, **{"from": 1997, "to": 2025},
  subtitle="Hours of work at the province's median hourly wage to pay one month of the average two-bedroom rent, CMHC October survey.",
  city="Vancouver", intro=2.6, perYear=0.55, hold=0.8, outro=3.5, camera="push", theme="whiteout",
  hook=["How many hours do you work", "just to pay one month of rent?"],
  annotations=[{"year": 2008, "text": "Average two-bedroom rent, existing tenants included: new leases are often higher"},
               {"year": 2020, "text": "Wages are each province's median hourly wage"}],
  summary={"seconds": 6.5, "items": [
    {"big": f"{rh('Vancouver', 2025):.0f} h", "kicker": "Vancouver, October 2025", "text": f"about {rh('Vancouver', 2025) / 8:.0f} eight-hour days a month (1997: {rh('Vancouver', 1997):.0f} h)", "scope": "year"},
    {"big": f"+{rh(jump, 2025) - rh(jump, 1997):.0f} h", "kicker": f"{jump}, 1997 → 2025", "text": f"{rh(jump, 1997):.0f} h → {rh(jump, 2025):.0f} h, the biggest jump of {len([c for c in R if R[c].get('1997') and R[c].get('2025')])} cities", "scope": "period"},
    {"big": f"{rh(low, 2025):.0f} h", "kicker": f"{low}, October 2025", "text": "the lowest of the cities measured", "scope": "year"}]})

# 3 · Gasoline in hours of work (provinces, 1997 = 1.00)
bc, cn, sk = hx("BC", "gas", 2025), hx("CAN", "gas", 2025), hx("SK", "gas", 2025)
assert (round(bc, 2), round(cn, 2), round(sk, 2)) == (1.39, 1.11, 0.93)
gas = dict(base, id="route-gas-hours", title="Gasoline in hours of work", layer="gash", place="BC", **{"from": 1997, "to": 2025},
  subtitle="Hours of work at the median hourly wage to buy the same gasoline, each province against its own 1997 (1.00).",
  intro=2.6, perYear=0.55, hold=0.8, outro=3.5, camera="push", theme="bluehour",
  hook=["Is a tank of gas harder to pay for", "than it was in 1997?"],
  annotations=[{"year": 2008, "text": "Above ×1.00: pump prices outran wages. Below: wages won"},
               {"year": 2022, "text": "Each province is compared with its own 1997, not with the others"}],
  summary={"seconds": 6.5, "items": [
    {"big": f"×{bc:.2f}", "kicker": "British Columbia, 2025 vs 1997", "text": f"{(bc - 1) * 100:.0f}% more hours of work for the same gas", "scope": "period"},
    {"big": f"×{cn:.2f}", "kicker": "Canada", "text": f"{(cn - 1) * 100:.0f}% more hours than in 1997", "scope": "period"},
    {"big": f"×{sk:.2f}", "kicker": "Saskatchewan", "text": f"{(1 - sk) * 100:.0f}% fewer: wages outran the pump", "scope": "period"}]})

for c in (alberta, rent, gas):
    (ROOT / "timelapses" / f"{c['id']}.json").write_text(json.dumps(c, indent=1, ensure_ascii=False))
    print("wrote", c["id"], "≈", round(c["intro"] + (c["to"] - c["from"] + 1) * c["perYear"] + c["hold"] + c["summary"]["seconds"] + c["outro"]), "s")
