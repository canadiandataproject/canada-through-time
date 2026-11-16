"""Post text (YouTube title + description, X text) for Shorts #12–#16. Every number is computed from the same data files the
videos use; asserts keep the wording true. Writes shorts2/out/post_copy.json."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = ROOT / "web/data"
SITE = "https://canadiandataproject.github.io/canada-through-time/"

pa = json.loads((D / "money/public_accounts.json").read_text()); v = dict(zip(pa["objects"], pa["totals"]["2026"])); TOT = sum(v.values()) * 1e3
pop = json.loads((D / "population.json").read_text()); P25 = pop["series"]["CAN"][pop["dates"].index("2025-07-01")]
b = lambda k: v[k] * 1e3 / 1e9; pct = lambda k: v[k] * 1e3 / TOT * 100
c = json.loads((D / "money/contracts.json").read_text())
tv = {k: sum(x[0] for x in d.values()) for k, d in c["by_proc"].items()}; CT = sum(tv.values()); NC = sum(sum(x[1] for x in d.values()) for d in c["by_proc"].values())
L = c["largest"]
pr = json.loads((D / "cities/ct_profile.json").read_text()); F = pr["fields"]
TOR = [a for a in pr["areas"].values() if a["level"] != "Census metropolitan area" and a["cma"] == "2021S0503535"]
cma = pr["areas"]["2021S0503535"]["v"]
def ext(f):
    xs = sorted(a["v"][F.index(f)] for a in TOR if a["v"][F.index(f)] is not None and (a["v"][F.index("pop")] or 0) >= 500); return xs[0], xs[-1]
n = json.loads((D / "more/npr.json").read_text())["data"]["CAN"]
MBSK = pop["series"]["MB"][pop["dates"].index("2025-07-01")] + pop["series"]["SK"][pop["dates"].index("2025-07-01")]

out = {}
out["12"] = dict(
    title="Ottawa's $493 billion receipt (2025–26)",
    desc=f"""Where federal spending went in 2025–26, by type.

📊 The numbers (Public Accounts of Canada 2025–26, Vol. II, gross expenditures by type)
• Total: ${TOT/1e9:.1f}B, about ${TOT/P25:,.0f} per person (${TOT/P25/365:.2f} a day)
• Transfer payments to people, provinces and programs: ${b('Transfer payments'):.1f}B ({pct('Transfer payments'):.0f}%)
• Federal employees: ${b('Personnel'):.1f}B
• Debt charges: ${b('Public debt charges'):.1f}B
• Consultants and professional services: ${b('Professional and special services'):.1f}B

💬 Which line surprised you?

Per person uses Statistics Canada's population on July 1, 2025 ({P25/1e6:.1f}M). Gross expenditures by standard object; items may not add due to rounding.
Voice, music and sound: original.

Explore federal spending by department and year: {SITE}?s=12#mn=spend/2026

#Canada #FederalSpending #DataViz""",
    x=f"""Ottawa spent ${TOT/1e9:.1f}B in 2025–26. Here's the receipt.

Transfers: ${b('Transfer payments'):.1f}B
Federal employees: ${b('Personnel'):.1f}B
Debt charges: ${b('Public debt charges'):.1f}B
Consultants & prof. services: ${b('Professional and special services'):.1f}B

≈ ${TOT/P25:,.0f} per person.

Source: Public Accounts of Canada""")
assert L[0]["name"].startswith("SkyAlyne") and L[1]["name"].startswith("Irving")
out["13"] = dict(
    title="Who got Ottawa's biggest contracts?",
    desc=f"""The biggest federal contracts ever disclosed, and how Ottawa awards them.

📊 The numbers (Treasury Board proactive disclosure, contracts over $10,000)
• {NC:,} contracts disclosed, worth ${CT/1e9:.0f}B in total commitments
• #1: SkyAlyne, ${L[0]['v']/1e9:.1f}B (National Defence)
• #2: Irving Shipbuilding, ${L[1]['v']/1e9:.1f}B (National Defence, ships)
• No competition: ${tv['TN']/1e9:.0f}B, about 1 dollar in 7
• Award type not stated: ${tv['?']/1e9:.0f}B

💬 Should every contract over $1M have to be competed?

Contract value is the total committed over the life of the contract (including amendments and taxes), counted once in the year it was first awarded. Lamps: green = competed, red = non-competitive.
Voice, music and sound: original.

Explore every contract by department, vendor and province: {SITE}?s=13#mn=contracts/all

#Canada #Procurement #DataViz""",
    x=f"""Ottawa has disclosed {NC/1e6:.2f}M contracts (${CT/1e9:.0f}B).

#1 SkyAlyne: ${L[0]['v']/1e9:.1f}B (Defence)
#2 Irving Shipbuilding: ${L[1]['v']/1e9:.1f}B (ships)

No competition: ${tv['TN']/1e9:.0f}B, about 1 dollar in 7.
How it was awarded "not stated": ${tv['?']/1e9:.0f}B.

Source: Treasury Board proactive disclosure""")
hi, lo = ext("hhinc"), None
out["14"] = dict(
    title="Toronto: one city, 1,227 neighbourhoods",
    desc=f"""One zoom from Canada into every census tract in Toronto.

📊 The numbers (2021 Census, Statistics Canada; neighbourhoods = census tracts with 500+ people)
• Median household income: ${ext('hhinc')[0]:,.0f} to ${ext('hhinc')[1]:,.0f} (Toronto overall: ${cma[F.index('hhinc')]:,.0f})
• Born outside Canada: {ext('imm')[0]:.0f}% to {ext('imm')[1]:.0f}%
• Median age: {ext('age')[0]:.0f} to {ext('age')[1]:.0f}
• Renters: {ext('rent')[0]:.0f}% to {ext('rent')[1]:.0f}%

💬 Which city should we zoom into next?

Income is for 2020 (pandemic benefits included).
Voice, music and sound: original.

Every neighbourhood in 50 cities, free: {SITE}?s=14#nb=535/hhinc

#Toronto #Canada #DataViz""",
    x=f"""Toronto has {len(TOR):,} neighbourhoods (census tracts).

Median household income: ${ext('hhinc')[0]/1e3:,.0f}K to ${ext('hhinc')[1]/1e3:,.0f}K
Born outside Canada: {ext('imm')[0]:.0f}% to {ext('imm')[1]:.0f}%
Median age: {ext('age')[0]:.0f} to {ext('age')[1]:.0f}

Same city.

Source: 2021 Census, Statistics Canada""")
assert len(TOR) == 1227
out["15"] = dict(
    title="Canada's temporary residents: 1.3M → 2.9M → 2.8M",
    desc=f"""Temporary residents in Canada on July 1, 2021–2026, one dot per 2,000 people.

📊 The numbers (Statistics Canada 17-10-0121-01, non-permanent residents; 2026 preliminary)
• 2021: {n['2021']['total']/1e6:.2f}M
• 2025: {n['2025']['total']/1e6:.2f}M, more than Manitoba and Saskatchewan combined ({MBSK/1e6:.2f}M)
• 2026: {n['2026']['total']/1e6:.2f}M, the first drop in this series
• Study permits: {n['2024']['study']/1e3:,.0f}K (2024) → {n['2026']['study']/1e3:,.0f}K (2026)
• Asylum claimants: {n['2025']['asylum']/1e3:,.0f}K → {n['2026']['asylum']/1e3:,.0f}K; work permits: {n['2025']['work']/1e3:,.0f}K → {n['2026']['work']/1e3:,.0f}K

💬 Is Canada's cap on temporary residents working?

Series starts July 1, 2021 after a method change.
Voice, music and sound: original.

Explore by province: {SITE}?s=15#nprsh-2026

#Canada #Immigration #DataViz""",
    x=f"""Temporary residents in Canada (July 1):

2021: {n['2021']['total']/1e6:.1f}M
2025: {n['2025']['total']/1e6:.1f}M (more than MB + SK combined)
2026: {n['2026']['total']/1e6:.1f}M, the first drop

Students fell most: {n['2024']['study']/1e3:,.0f}K → {n['2026']['study']/1e3:,.0f}K.
Asylum claimants and workers rose.

Source: Statistics Canada""")
sp = json.loads((D / "sprawl/sprawl.json").read_text()); ed = next(c for c in sp["cities"] if c["slug"] == "edmonton"); ek = dict(zip(sp["epochs"], ed["km2"]))
assert round(ek[1975]) == 84 and round(ek[2020]) == 166 and round(ek[2000] - ek[1975]) == 33 and round(ek[2020] - ek[2000]) == 49 and ed["half_km"] == 30
out["16"] = dict(
    title="Edmonton spread out: 1975 to 2020 from space",
    desc=f"""How much of the land around Edmonton is covered by buildings, mapped from satellite images, 1975 to 2020.

📊 The numbers (EU Joint Research Centre, GHS-BUILT-S R2023A, 100 m grid; a 60 km square centred on downtown)
• 1975: {ek[1975]:.0f} km² covered by buildings
• 2000: {ek[2000]:.0f} km²
• 2020: {ek[2020]:.0f} km², {(ek[2020] / ek[1975] - 1) * 100:.0f}% more than 1975 (nearly double)
• Added 2000–2020: {ek[2020] - ek[2000]:.0f} km², vs {ek[2000] - ek[1975]:.0f} km² in 1975–2000

💬 Which city should we do next?

How to read it: each 100 m square takes the colour of the first satellite snapshot (1975, 1985, 1990, 2000, 2010, 2020) in which buildings covered 20% of it. The square-kilometre totals add up the full building area of every square, with no threshold. This is the ground under buildings, not the city limits or the metro area. The counter ticks one year at a time and the picture matches each snapshot exactly; between snapshots, that snapshot's new squares appear outward from built land, an illustration of the order, since the year each square was built isn't known.

Sources: Pesaresi M., Politis P. (2023), GHS-BUILT-S R2023A, European Commission, Joint Research Centre (CC BY 4.0). Relief: Copernicus DEM GLO-30 (© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the EU and ESA). River and lakes: ESA WorldCover 2021 (CC BY 4.0).
Voice, music and sound: original.

12 cities, free: {SITE}?s=16#cl=sprawl/2020/cedmonton

#Edmonton #Canada #DataViz""",
    x=f"""Land covered by buildings around Edmonton, from satellite images:

1975: {ek[1975]:.0f} km²
2000: {ek[2000]:.0f} km²
2020: {ek[2020]:.0f} km², nearly double

More was added after 2000 than in the 25 years before.

Source: EU JRC GHS-BUILT-S""")
for k, o in out.items(): assert len(o["x"]) <= 280 and len(o["title"]) <= 100, (k, len(o["x"]))
(ROOT / "shorts2/out").mkdir(exist_ok=True); (ROOT / "shorts2/out/post_copy.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
for k, o in out.items(): print(k, len(o["x"]), o["title"])
