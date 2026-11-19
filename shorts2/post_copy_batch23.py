"""Post text for Shorts #23 (Calgary spreading out), #24 (which city spread most) and #25 (Ottawa–Gatineau, French by
neighbourhood). Every number is computed from the same files the videos use and asserted; adds to shorts2/out/post_copy.json."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = ROOT / "web/data"; OUT = ROOT / "shorts2/out/post_copy.json"
SITE = "https://canadiandataproject.github.io/canada-through-time/"
GHSL = "Pesaresi M., Politis P. (2023), GHS-BUILT-S R2023A, European Commission, Joint Research Centre (CC BY 4.0)"

S = json.loads((D / "sprawl/sprawl.json").read_text()); E = S["epochs"]; C = {c["slug"]: c for c in S["cities"]}
km = lambda s, y: C[s]["km2"][E.index(y)]
cal75, cal00, cal20 = km("calgary", 1975), km("calgary", 2000), km("calgary", 2020)
assert (round(cal75), round(cal20), round(cal00 - cal75), round(cal20 - cal00)) == (69, 135, 29, 36)
rank = sorted(S["cities"], key=lambda c: -c["km2"][-1] / c["km2"][0]); r = lambda c: c["km2"][-1] / c["km2"][0]
assert [c["slug"] for c in rank[:3]] == ["edmonton", "calgary", "halifax"] and round(r(rank[0]), 2) == 1.97 and round(r(rank[1]), 2) == 1.94
tor = C["toronto"]; tor_add = tor["km2"][-1] - tor["km2"][0]
assert round(tor_add) == 234 and round(r(tor), 2) == 1.59 and max(c["km2"][-1] - c["km2"][0] for c in S["cities"]) == tor_add

P = json.loads((D / "cities/ct_profile.json").read_text()); F, A = P["fields"], P["areas"]; fr, pop = F.index("fr"), F.index("pop")
OG = "2021S0503505"; T = {k: v for k, v in A.items() if v["level"] != "Census metropolitan area" and v["cma"] == OG and v["v"][fr] is not None}
qc = lambda k: 500 <= float(A[k]["name"][3:]) < 1000          # Quebec part: tracts 0500–0909 (their population = StatCan's Quebec portion)
assert sum(A[k]["v"][pop] for k in T if qc(k)) == 353293
side = lambda q: sum(A[k]["v"][fr] * A[k]["v"][pop] for k in T if qc(k) == q) / sum(A[k]["v"][pop] for k in T if qc(k) == q)
on_pct, qc_pct = side(False), side(True)
a, b = A["2021S05075050110.00"]["v"][fr], A["2021S05075050600.00"]["v"][fr]
big = [A[k]["v"][fr] for k in T if (A[k]["v"][pop] or 0) >= 500]
assert (round(on_pct, 1), round(qc_pct, 1), a, b, min(big), max(big)) == (13.5, 71.3, 9.0, 70.7, 3.1, 94.0)

out = json.loads(OUT.read_text()) if OUT.exists() else {}
out["23"] = dict(
    title="Calgary spread out: 1975 to 2020, from space",
    desc=f"""Calgary in 1975 vs 2020, from satellite pictures. Land covered by buildings went from {cal75:.0f} km² to {cal20:.0f} km², nearly double.

📊 The numbers (EU Joint Research Centre, GHS-BUILT-S; 100 m squares, inside a 56 km square around the city)
• 1975: {cal75:.0f} km² · 2000: {cal00:.0f} km² · 2020: {cal20:.0f} km²
• Added after 2000: +{cal20 - cal00:.0f} km², vs +{cal00 - cal75:.0f} km² in the 25 years before
• The southeast took the biggest share of new ground since 2000 (37%)

💬 Edmonton or Calgary: which spread more? Be nice.

This is the ground under buildings, not the city limits. The counter ticks one year at a time and the picture matches each satellite snapshot (1975, 1985, 1990, 2000, 2010, 2020) exactly; in between, new squares appear outward from built land, an illustration of the order.

Sources: {GHSL}. Relief: Copernicus DEM GLO-30 (© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the EU and ESA). Rivers and lakes: ESA WorldCover 2021 (CC BY 4.0).

See every big city spread: {SITE}#cl=sprawl/2020/ccalgary""",
    x=f"Calgary from space, 1975 → 2020: land covered by buildings went from {cal75:.0f} km² to {cal20:.0f} km², nearly double. +{cal20 - cal00:.0f} km² since 2000 vs +{cal00 - cal75:.0f} in the 25 years before.\n\nEdmonton or Calgary?\n\nEU JRC GHS-BUILT-S\n{SITE}#cl=sprawl/2020/ccalgary")
out["24"] = dict(
    title="Which Canadian city spread the most since 1975?",
    desc=f"""12 cities, 1975 to 2020, from satellite pictures: how many times over did each city's built-up land grow?

📊 The ranking (land covered by buildings, 2020 vs 1975)
""" + "\n".join(f"{i + 1}. {c['name']}: ×{r(c):.2f}" for i, c in enumerate(rank)) + f"""

• Toronto added the most ground (+{tor_add:.0f} km²) but started largest, so it grew ×{r(tor):.2f}

💬 Where did your city land? Surprised?

How it's measured: built-up land inside a fixed square around each city centre (EU JRC GHS-BUILT-S, 100 m squares), not city limits or metro areas; very large metros can spread past their square. Each tile is drawn at its own scale. The counters are exact at each satellite year (1975, 1985, 1990, 2000, 2010, 2020) and drawn in between.

Source: {GHSL}.

Watch any city spread: {SITE}#cl=sprawl/2020/cedmonton""",
    x=f"Which city spread most since 1975? Built-up land, 2020 vs 1975:\n\n1. {rank[0]['name']} ×{r(rank[0]):.2f}\n2. {rank[1]['name']} ×{r(rank[1]):.2f}\n3. {rank[2]['name']} ×{r(rank[2]):.2f}\n…\nToronto added the most ground (+{tor_add:.0f} km²), only ×{r(tor):.2f}.\n\nEU JRC GHS-BUILT-S\n{SITE}#cl=sprawl/2020/cedmonton")
out["25"] = dict(
    title="Ottawa–Gatineau: cross one bridge and the language flips",
    desc=f"""Ottawa–Gatineau is one metro area split by a river, and by a province line. Colour every neighbourhood by mother tongue.

📊 The numbers (2021 Census, Statistics Canada; mother tongue French only; neighbourhoods = census tracts)
• Ottawa side (Ontario part): about 1 in 7 ({on_pct:.0f}%)
• Gatineau side (Quebec part): about 7 in 10 ({qc_pct:.0f}%)
• Two neighbourhoods about 2 km apart across the river: {a:.0f}% and {b:.0f}%
• Across all {len(big)} neighbourhoods with 500+ people: {min(big):.0f}% to {max(big):.0f}%

💬 Ottawa side or Gatineau side? Pick one. Carefully.

Side shares are population-weighted averages of the neighbourhood shares.

Every neighbourhood in 50 cities, free: {SITE}#nb=505/fr""",
    x=f"Ottawa–Gatineau, one river apart. Mother tongue French:\n\nOttawa side: about 1 in 7 ({on_pct:.0f}%)\nGatineau side: about 7 in 10 ({qc_pct:.0f}%)\nTwo neighbourhoods ~2 km apart: {a:.0f}% vs {b:.0f}%\n\n2021 Census, Statistics Canada\n{SITE}#nb=505/fr")
for k in ("23", "24", "25"): assert len(out[k]["x"]) <= 280, (k, len(out[k]["x"]))
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False)); print("ok", {k: len(out[k]["x"]) for k in ("23", "24", "25")})
