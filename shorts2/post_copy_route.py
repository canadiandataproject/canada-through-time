"""Post text for Shorts #17–#19 (the first in the Whiteout / Blue hour look). Numbers come from the same files the videos
use (tools/build_route_shorts.py checks them too). Adds to shorts2/out/post_copy.json."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = ROOT / "web/data"; OUT = ROOT / "shorts2/out/post_copy.json"
SITE = "https://canadiandataproject.github.io/canada-through-time/"
P = json.loads((D / "population.json").read_text()); S = P["series"]; J = {int(d[:4]): i for i, d in enumerate(P["dates"]) if d.endswith("-07-01")}
pop = lambda g, y: S[g][J[y]]
H = json.loads((D / "gaps/hours.json").read_text()); R = {c: v["y"] for c, v in H["rent"].items()}
rh = lambda c, y: R[c][str(y)][1]
def hx(g, k, y, b=1997):
    h = H["data"][g]; return (h[k][str(y)] / h[k][str(b)]) / (h["wage"][str(y)] / h["wage"][str(b)])
ab71, ab26, k, can = pop("AB", 1971), pop("AB", 2026), pop("AB", 2026) / pop("AB", 1971), pop("CAN", 2026) / pop("CAN", 1971)
bc71, bc26 = pop("BC", 1971), pop("BC", 2026)
assert round(k, 2) == 3.06 and round(can, 2) == 1.90 and round(bc26 / bc71, 2) == 2.55
out = json.loads(OUT.read_text()) if OUT.exists() else {}
out["17"] = dict(
    title="Alberta tripled: 1.67M → 5.10M people (1971–2026)",
    desc=f"""Alberta had {ab71/1e6:.2f} million people on July 1, 1971. On July 1, 2026 (preliminary): {ab26/1e6:.2f} million.

📊 The numbers (Statistics Canada, table 17-10-0009-01, July 1 estimates)
• Alberta: ×{k:.2f} since 1971, the fastest of the 13 provinces and territories
• Passed 2 million in 1978, 3 million in 2000, 4 million in 2014, 5 million in 2025
• Canada as a whole: ×{can:.2f}; British Columbia ×{bc26/bc71:.2f}

💬 When did your family arrive?

2026 is a preliminary estimate. Column height shows the number of people; movement between years is animation.

Explore every province, every year: {SITE}#pop-2026-ab""",
    x=f"Alberta had {ab71/1e6:.2f}M people in 1971. Now: {ab26/1e6:.2f}M. ×{k:.2f}, the fastest growth of any province or territory (Canada: ×{can:.2f}).\n\nStatCan 17-10-0009-01 · July 1, 2026 is preliminary.\n{SITE}#pop-2026-ab")
v25, v97, k25, k97, low = rh("Vancouver", 2025), rh("Vancouver", 1997), rh("Kelowna", 2025), rh("Kelowna", 1997), rh("Saguenay", 2025)
assert (round(v25, 1), round(k97, 1), round(k25, 1), round(low, 1)) == (72.8, 39.8, 64.6, 32.9)
out["18"] = dict(
    title=f"Rent in hours of work: Vancouver {v25:.0f} hours a month",
    desc=f"""How many hours do you work just to pay one month of rent?

📊 The numbers (CMHC Rental Market Survey via Statistics Canada 34-10-0133-01; median hourly wage, 14-10-0064-01)
• Vancouver: {v25:.0f} hours a month in October 2025, about {v25/8:.0f} eight-hour days (1997: {v97:.0f} h)
• Kelowna: {k97:.0f} h → {k25:.0f} h since 1997, the biggest jump of 33 cities
• Saguenay: {low:.0f} h, the lowest measured
• Edmonton {rh('Edmonton', 2025):.0f} h · Calgary {rh('Calgary', 2025):.0f} h · Toronto {rh('Toronto', 2025):.0f} h · Montréal {rh('Montréal', 2025):.0f} h

💬 How many hours is yours?

Average two-bedroom rent in purpose-built rentals, existing tenants included (new leases are often higher), divided by the province's median hourly wage.

Find your city: {SITE}#renth-2025""",
    x=f"One month of 2-bedroom rent, in hours of work at the median wage (Oct 2025):\nVancouver {v25:.0f} h\nToronto {rh('Toronto', 2025):.0f} h\nCalgary {rh('Calgary', 2025):.0f} h\nEdmonton {rh('Edmonton', 2025):.0f} h\nKelowna went {k97:.0f} → {k25:.0f} h since 1997.\n\nCMHC via StatCan.\n{SITE}#renth-2025")
bc, cn, sk = hx("BC", "gas", 2025), hx("CAN", "gas", 2025), hx("SK", "gas", 2025)
assert (round(bc, 2), round(cn, 2), round(sk, 2)) == (1.39, 1.11, 0.93)
out["19"] = dict(
    title="Is gas harder to pay for than in 1997? (hours of work)",
    desc=f"""The same gasoline, measured in hours of work at the median hourly wage, against each province's own 1997.

📊 The numbers (Consumer Price Index, gasoline, 18-10-0005-01; median hourly wage, 14-10-0064-01)
• British Columbia: ×{bc:.2f}, {(bc-1)*100:.0f}% more hours of work than in 1997, the most of 10 provinces
• Canada: ×{cn:.2f}
• Saskatchewan: ×{sk:.2f}, wages outran the pump

💬 Does this match what you feel at the pump?

A price index follows the same goods over time, so each province is compared with its own past, not with the others.

Groceries and new homes in hours of work too: {SITE}#gash-2025""",
    x=f"Gas in hours of work at the median wage, 2025 vs 1997:\nB.C. ×{bc:.2f} ({(bc-1)*100:.0f}% more work for the same gas)\nCanada ×{cn:.2f}\nSask. ×{sk:.2f} (wages won)\n\nStatCan CPI + wages.\n{SITE}#gash-2025")
for n in ("17", "18", "19"): assert len(out[n]["x"]) <= 280, (n, len(out[n]["x"]))
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
print({n: len(out[n]["x"]) for n in ("17", "18", "19")})
