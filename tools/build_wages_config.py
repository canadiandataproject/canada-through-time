"""Write timelapses/short-wages-tfw.json: real hourly wages 1997–2025 (all employees; accommodation and food services,
where low-wage temporary foreign workers are concentrated) with dated Temporary Foreign Worker Program changes.
Wages: Statistics Canada 14-10-0064-01 (average hourly wage, both full- and part-time, 15+), deflated with the all-items
CPI 18-10-0005-01 to 2025 dollars. Every number is computed here from the registered raw files; the asserts stop the
build if the wording stops being true. Policy dates and the research finding are cited in `references`.
Framing rule: the chart shows what wages did around each change; the causal answer comes only from the cited study."""
import csv, io, json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/statcan"
def rows(zname):
    z = zipfile.ZipFile(RAW / zname); n = [x for x in z.namelist() if "Meta" not in x][0]
    return csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))
cpi = {int(r["REF_DATE"]): float(r["VALUE"]) for r in rows("18100005-eng.zip") if r["GEO"] == "Canada" and r["Products and product groups"] == "All-items" and r["VALUE"]}
IND = {"all": "Total employees, all industries", "food": "Accommodation and food services [72]"}
W = {k: {} for k in IND}
for r in rows("14100064-eng.zip"):
    if (r["GEO"] == "Canada" and r["Wages"] == "Average hourly wage rate" and r["Type of work"] == "Both full- and part-time employees"
            and r["Gender"] == "Total - Gender" and r["Age group"] == "15 years and over" and r["VALUE"]):
        for k, name in IND.items():
            if r["North American Industry Classification System (NAICS)"] == name: W[k][int(r["REF_DATE"])] = float(r["VALUE"])
Y0, Y1 = 1997, 2025
for k in W: assert sorted(W[k]) == list(range(Y0, Y1 + 1)), k        # no gaps
real = {k: {y: W[k][y] * cpi[Y1] / cpi[y] for y in W[k]} for k in W}
cagr = lambda k, a, b: ((real[k][b] / real[k][a]) ** (1 / (b - a)) - 1) * 100
g_exp, g_lim = cagr("food", 2002, 2014), cagr("food", 2014, 2019)
print({k: (round(real[k][Y0], 2), round(real[k][Y1], 2)) for k in real}, "food CAGR 2002-14", round(g_exp, 2), "2014-19", round(g_lim, 2), "2019-25", round(cagr("food", 2019, 2025), 2))
assert round(g_exp, 1) == 1.0 and round(g_lim, 1) == 1.8 and g_lim > g_exp

idx = lambda y: y - Y0
s = lambda v: f"+{v:.1f}%"
cfg = dict(
    id="short-wages-tfw", format="9x16", fps=30, theme="broadcast", channel="The Canadian Data Project", ghost=0.35,
    title="Did temporary foreign workers hold down Canadian wages?", years=[Y0, Y1],
    yRange=[12, 40], gridStart=15, gridStep=5, xTicks=[2000, 2010, 2020], prefix="$", decimals=2,
    kicker="Real hourly wages · 2025 dollars · Canada",
    hook=dict(seconds=3.2, question="Did temporary foreign workers <em>hold down wages</em>?"),
    yearSub="Average hourly wage, adjusted for inflation to 2025 dollars",
    series=[dict(name="all", label="All workers", color="#0E2A47", values={str(y): round(v, 2) for y, v in real["all"].items()}),
            dict(name="food", label="Food & hotels", color="#D62839", values={str(y): round(v, 2) for y, v in real["food"].items()})],
    events=[dict(year=2002, frac=0.5, label="2002: low-wage jobs opened", row=0), dict(year=2014, frac=0.47, label="2014: low-wage hiring capped", row=1),
            dict(year=2024, frac=0.73, label="2024: capped again", row=0)],
    between="Between cards, the year counts up and each line extends to that year's inflation-adjusted average hourly wage; dashed lines mark Temporary Foreign Worker Program changes.",
    plan=[
        dict(kind="run", to=3, s=3.2, ease="linear"),
        dict(kind="run", to=idx(2014), s=8.5, ease="linear"),
        dict(kind="beat", s=3.4, kicker="Restaurants & hotels (food services) · 2002–2014", big=f"{s(g_exp)}/yr", line="real wage growth while the program was open to low-wage jobs", focus=["Food & hotels"], sfx="tick", cardTop=268),
        dict(kind="run", to=idx(2019), s=3.0, ease="inout", riser=True),
        dict(kind="beat", s=3.6, kicker="Restaurants & hotels (food services) · 2014–2019", big=f"{s(g_lim)}/yr", line="after low-wage hiring was capped. <em>Minimum wages also rose</em>, so this alone can’t prove why", focus=["Food & hotels"], sfx="hit", cardTop=268),
        dict(kind="run", to=idx(Y1), s=3.0, ease="out"),
        dict(kind="summary", s=6.0),
        dict(kind="loop", s=0.8),
    ],
    summary=dict(kicker="What a study comparing similar jobs found", big="+3.7–4.5%",
                 line="wages for low-wage Canadians in jobs hit by the 2014 limits. <em>Real, but modest.</em>",
                 sub="Chen & Fang, Journal of Ethnic and Migration Studies (2025), LFS 2005–2019. Wages: Statistics Canada 14-10-0064-01, CPI 18-10-0005-01."),
    note="<b>Source:</b> Statistics Canada, tables 14-10-0064-01 (average hourly wage, all employees 15+) and 18-10-0005-01 (CPI, to 2025 dollars). Program dates: Government of Canada (July 2002 low-skill pilot; June 20, 2014 overhaul; Sept 26, 2024 changes). Averages change when the mix of workers changes. Lines grow between years as animation.",
    sources=["statcan_14100064", "statcan_18100005"],
    references=[
        "Chen, W.-H. & Fang, T. (2025). Restricting temporary foreign labour: evidence on wage effects from Canada's 2014 policy reform. Journal of Ethnic and Migration Studies. IZA DP 18240: https://www.iza.org/publications/dp18240",
        "IRCC Operational Bulletin 113 (2009): July 2002 Pilot Project for Occupations Requiring Lower Levels of Formal Training",
        "ESDC news release, June 20, 2014: Government of Canada overhauls the Temporary Foreign Worker Program",
        "ESDC Question Period Note EWDOL_Dec2024_017: tightening measures effective September 26, 2024",
        "Champagne, J. (2025). The Shift in Canadian Immigration Composition and its Effect on Wages. Bank of Canada Staff Discussion Paper 2025-8",
    ],
    method="Average hourly wages (current dollars) multiplied by CPI(2025)/CPI(year). Growth rates are compound annual rates between the named years. The chart is descriptive; the causal estimate is quoted from the cited difference-in-differences study, not computed here.",
    figures=dict(real_wage={k: {"1997": round(real[k][Y0], 2), "2025": round(real[k][Y1], 2)} for k in real}, food_cagr={"2002-2014": round(g_exp, 3), "2014-2019": round(g_lim, 3), "2019-2025": round(cagr("food", 2019, 2025), 3)},
                 all_cagr={"2002-2014": round(cagr("all", 2002, 2014), 3), "2014-2019": round(cagr("all", 2014, 2019), 3)}),
)
dst = ROOT / "timelapses/short-wages-tfw.json"; dst.write_text(json.dumps(cfg, indent=1, ensure_ascii=False)); print(dst.relative_to(ROOT))
