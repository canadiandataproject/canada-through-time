"""Write timelapses/short-glaciers.json (Short #8) from WGMS mass-balance figures in web/data/climate/glaciers.json.
Every story number is computed here; the asserts stop the build if the data no longer supports the wording.
Running totals are sums of published annual values; missing years add nothing and are drawn as gaps."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = {g["name"]: g for g in json.loads((ROOT / "web/data/climate/glaciers.json").read_text())["glaciers"]}
def pub(n): y0, v = G[n]["b"]; return {y0 + i: x for i, x in enumerate(v) if x is not None}
def missing(n): y0, v = G[n]["b"]; return [y0 + i for i, x in enumerate(v) if x is None]
LONG = [n for n in G if len(pub(n)) >= 40]
MTN = ["Helm", "Place", "Peyto"]; ARC = ["Melville South Ice Cap", "White", "Meighen Ice Cap", "Devon Ice Cap NW"]
assert sorted(LONG) == sorted(MTN + ARC), LONG
tot = {n: sum(pub(n).values()) for n in LONG}
first = {n: min(pub(n)) for n in LONG}
last = {n: max(pub(n)) for n in LONG}
worst = {n: min(pub(n), key=lambda y: pub(n)[y]) for n in LONG}
print({n: (first[n], last[n], round(tot[n], 2), worst[n], pub(n)[worst[n]], missing(n)) for n in LONG})
assert all(t < 0 for t in tot.values()) and all(last[n] == 2025 for n in LONG)
assert all(worst[n] == 2023 for n in MTN)
Y0, Y1 = min(first.values()), 2025
idx = lambda y: y - Y0
pk = tot["Peyto"]
arc_lo, arc_hi = max(tot[n] for n in ARC), min(tot[n] for n in ARC)
helm23 = pub("Helm")[2023]
assert round(pk, 1) == -48.5 and round(tot["Helm"], 1) == -69.8
def part(n, a, b): return sum(v for y, v in pub(n).items() if a <= y <= b)
pk_early, pk_late = part("Peyto", first["Peyto"], 2000), part("Peyto", 2001, 2025)
n_early, n_late = len([y for y in pub("Peyto") if y <= 2000]), len([y for y in pub("Peyto") if y > 2000])
assert abs(pk_late) > abs(pk_early) and n_late < n_early and (n_early, n_late) == (35, 25)

col = {"Helm": "#FF5A47", "Place": "#FF9A3D", "Peyto": "#FFD166", "Melville South Ice Cap": "#2EA8FF", "White": "#5CC8FF", "Meighen Ice Cap": "#8FD9FF", "Devon Ice Cap NW": "#C2ECFF"}
lab = {"Melville South Ice Cap": "Melville S.", "Meighen Ice Cap": "Meighen", "Devon Ice Cap NW": "Devon NW"}
m1 = lambda v: f"−{abs(v):.1f}"
cfg = dict(
    id="short-glaciers", format="9x16", voice="audio/voice/short-glaciers.wav", theme="dark", ghost=0.45, channel="The Canadian Data Project", fps=30, title="How much ice have Canada's glaciers lost?", years=[Y0, Y1], yRange=[-74, 4], gridStep=10, xTicks=[1960, 1980, 2000, 2020],
    kicker="Glacier mass balance · running total · WGMS",
    between="Between cards, the year counts up and each glacier’s line extends to its running total for that year, labelled with the published-years sum.",
    hook=dict(seconds=3.4, question="How much ice have Canada’s <em>glaciers</em> lost?"),
    yearSub="Running total, metres of water equivalent, from each glacier’s first measured year",
    glaciers=[dict(name=n, label=lab.get(n, n), color=col[n], region="mountain" if n in MTN else "arctic") for n in MTN + ARC],
    plan=[
        dict(kind="run", to=3, s=3.4, ease="linear"),
        dict(kind="run", to=idx(2000), s=4.8, ease="linear"),
        dict(kind="beat", s=2.2, kicker=f"Peyto · {first['Peyto']}–2000", big=f"{m1(pk_early)} m", line=f"lost in its first {n_early} years of measurement", focus=["Peyto"], sfx="tick", cardTop=268),
        dict(kind="run", to=idx(2022), s=0.8, ease="linear", riser=True),
        dict(kind="run", to=idx(2023), s=0.3, ease="out"),
        dict(kind="beat", s=7.9, kicker="2023 · one year", big=f"{m1(helm23)} m", line=f"<em>Helm</em>’s biggest one-year loss measured since {first['Helm']}. The biggest ever measured at <em>Place</em> and <em>Peyto</em> too", focus=MTN, sfx="hit", cardTop=268),
        dict(kind="run", to=idx(Y1), s=1.7, ease="out"),
        dict(kind="beat", s=4.1, kicker=f"Peyto · 2001–{Y1}", big=f"{m1(pk_late)} m", line=f"in the next {n_late} years: <em>more</em> than in the {n_early} before", focus=["Peyto"], sfx="hit", cardTop=268),
        dict(kind="summary", s=8.7),
        dict(kind="loop", s=0.8),
    ],
    summary=dict(kicker=f"Measured 40+ years", big=f"{sum(t < 0 for t in tot.values())} of {len(LONG)}",
                 line="Canadian glaciers measured for 40+ years have <em>lost ice</em> overall",
                 sub=f"Peyto, Alberta: {m1(pk)} m since {first['Peyto']}. 1 m of water equivalent = a 1-metre layer of water over the whole glacier. Source: World Glacier Monitoring Service."),
    note=f"Dotted lines preview the full published record. <b>Source:</b> World Glacier Monitoring Service, Fluctuations of Glaciers database (2026-02-10 release), glacier-wide annual mass balance. Running total = sum of published years; missing years (White {', '.join(map(str, missing('White')))}; Place {', '.join(map(str, missing('Place')))}; Helm {', '.join(map(str, missing('Helm')))}) are gaps, not zero. Recent years may be revised. Lines grow between years as animation.",
    sources=["wgms_fog_2026_02_10"],
    method="Each line is the running sum of a glacier's published annual glacier-wide mass balance (m w.e.) from its first measured year. Missing years add nothing and break the line. Glaciers shown: every Canadian glacier in the WGMS release with 40 or more published years. No causes are claimed.",
    figures=dict(peyto_split=dict(early=round(pk_early, 3), early_years=n_early, late=round(pk_late, 3), late_years=n_late), glaciers={n: dict(first=first[n], last=last[n], total=round(tot[n], 3), worst_year=worst[n], worst_value=pub(n)[worst[n]], missing=missing(n), published_years=len(pub(n))) for n in LONG},
                 negative=sum(t < 0 for t in tot.values()), count=len(LONG), arctic_range=[round(arc_lo, 2), round(arc_hi, 2)]),
)
dst = ROOT / "timelapses/short-glaciers.json"; dst.write_text(json.dumps(cfg, indent=1, ensure_ascii=False)); print(dst.relative_to(ROOT))
