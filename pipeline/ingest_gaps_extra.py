"""Gaps worth fixing: hours of work (rent, gasoline, new homes, groceries), productivity and pay (provinces and peer
countries), and people next to the city-spreading maps.

  web/data/gaps/hours.json
    For each place and year, how many hours at the median hourly wage it takes to pay for the same thing, relative to a base
    year:  h(y, base) = (price index y / price index base) / (median wage y / median wage base).
    The file stores the raw indexes and wages; the explorer divides, so any base year from 1997 on can be chosen.
      CPI 18-10-0005-01 (annual average, 2002 = 100): Food, Gasoline.
      New housing price index 18-10-0205-01 (Dec 2016 = 100), "Total (house and land)": calendar-year mean of the 12 months,
      complete years only.
      Median hourly wage 14-10-0064-01 (all employees, all industries, 15+, current dollars), 1997 on.
  web/data/gaps/productivity.json
    prov: business-sector labour productivity (chained 2017 $ per hour) and compensation per hour (current $), 36-10-0480-01.
    peers: GDP per person employed and GDP per person, constant 2021 PPP $ (World Bank WDI), Canada vs 10 countries + OECD.
  web/data/sprawl/people.json
    July 1 population of the census metropolitan area each sprawl city sits in (17-10-0148-01, 2021 boundaries, 2001 on),
    so the built-up growth can be read next to population growth. The CMA and the satellite square are different areas.
Published values only; a missing year is left out, never filled.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_registry, verify_raw  # noqa: E402

AB = {"Canada": "CAN", "Newfoundland and Labrador": "NL", "Prince Edward Island": "PE", "Nova Scotia": "NS", "New Brunswick": "NB", "Quebec": "QC",
      "Ontario": "ON", "Manitoba": "MB", "Saskatchewan": "SK", "Alberta": "AB", "British Columbia": "BC", "Yukon": "YT",
      "Northwest Territories": "NT", "Nunavut": "NU"}
REG = load_registry()["sources"]


def rows(key):
    r = REG[key]
    z = zipfile.ZipFile(verify_raw(r["raw_file"], r["sha256"]))
    yield from csv.DictReader(io.TextIOWrapper(z.open([n for n in z.namelist() if "MetaData" not in n][0]), encoding="utf-8-sig"))


def num(r):
    return None if r["VALUE"] in ("", None) or r.get("STATUS") in ("..", "x", "F", "...") else float(r["VALUE"])


CPI_ITEMS = {"Food": "food", "Gasoline": "gas"}


def hours():
    idx = defaultdict(lambda: defaultdict(dict))   # geo -> item -> year -> index
    for r in rows("statcan_18100005"):
        k = CPI_ITEMS.get(r["Products and product groups"])
        if k and r["UOM"] == "2002=100" and r["GEO"] in AB and num(r) is not None:
            idx[AB[r["GEO"]]][k][int(r["REF_DATE"])] = num(r)
    months = defaultdict(lambda: defaultdict(list))
    for r in rows("statcan_18100205"):
        if r["New housing price indexes"] == "Total (house and land)" and r["GEO"] in AB and num(r) is not None:
            months[AB[r["GEO"]]][int(r["REF_DATE"][:4])].append(num(r))
    for g, ys in months.items():
        for y, v in ys.items():
            if len(v) == 12:
                idx[g]["home"][y] = round(sum(v) / 12, 2)
    wage = defaultdict(dict)
    for r in rows("statcan_14100064"):
        if (r["Wages"] == "Median hourly wage rate" and r["Type of work"] == "Both full- and part-time employees" and r["Gender"] == "Total - Gender"
                and r["Age group"] == "15 years and over" and r["North American Industry Classification System (NAICS)"] == "Total employees, all industries"
                and r["GEO"] in AB and num(r) is not None):
            wage[AB[r["GEO"]]][int(r["REF_DATE"])] = num(r)
    data = {}
    for g in wage:
        d = {"wage": {str(y): v for y, v in sorted(wage[g].items())}}
        for k, s in idx[g].items():
            d[k] = {str(y): v for y, v in sorted(s.items()) if y >= 1997}
        data[g] = d
    rent = {}
    for c in json.loads((ROOT / "web/data/housing/cities.json").read_text())["cities"]:
        w = wage.get(c["prov"], {})
        r = {y: [v, round(v / w[int(y)], 1)] for y, v in c.get("rent2br", {}).items() if int(y) in w}
        if r:
            rent[c["name"]] = {"prov": c["prov"], "y": r}
    return dict(sources=["statcan_18100005", "statcan_18100205", "statcan_14100064", "statcan_34100133"], items=["food", "gas", "home"],
                rent=rent,
                base_from=1997, data=data,
                notes=["Hours of work: how many hours at the median hourly wage it takes to pay for the same thing, compared with the year you choose (1997 or later). Above 1.00, prices outran wages; below 1.00, wages outran prices.",
                       "Price indexes follow the same goods over time, so each place is compared with its own past, not with other places.",
                       "Rent: one month of the average two-bedroom rent in purpose-built rental buildings (CMHC October survey, existing tenants included), divided by the province's median hourly wage. Groceries and gasoline: Consumer Price Index. New homes: New Housing Price Index (new single-family houses, house and land; resale homes and condos are not included). Wages: median hourly wage of all employees."])


def productivity():
    prov = defaultdict(lambda: defaultdict(dict))
    for r in rows("statcan_36100480"):
        if r["Industry"] != "Business sector industries" or r["GEO"] not in AB or num(r) is None:
            continue
        k = {"Labour productivity": "lp", "Total compensation per hour worked": "comp"}.get(r["Labour productivity and related measures"])
        if k:
            prov[AB[r["GEO"]]][k][r["REF_DATE"][:4]] = num(r)
    peers = {}
    for key, ind in (("perworker", "SL.GDP.PCAP.EM.KD"), ("perperson", "NY.GDP.PCAP.PP.KD")):
        r = REG["worldbank_gdp_per_worker" if key == "perworker" else "worldbank_gdp_per_person_ppp"]
        d = json.loads(verify_raw(r["raw_file"], r["sha256"]).read_text())[1]
        for x in d:
            if x["value"] is not None:
                peers.setdefault(x["countryiso3code"], {"name": x["country"]["value"]}).setdefault(key, {})[x["date"]] = round(x["value"])
    return dict(sources=["statcan_36100480", "worldbank_gdp_per_worker", "worldbank_gdp_per_person_ppp"],
                prov={g: {k: dict(sorted(v.items())) for k, v in s.items()} for g, s in prov.items()}, peers=peers,
                notes=["Provinces: business-sector output per hour worked, in chained 2017 dollars (so years compare without inflation), and what businesses paid per hour worked (wages, salaries and benefits, current dollars). Statistics Canada, table 36-10-0480-01, 1997–2024.",
                       "Countries: GDP per person employed and GDP per person, both in constant 2021 dollars at purchasing power parity (what money buys locally). World Bank, World Development Indicators. Per worker, not per hour."])


SPRAWL_CMA = {"toronto": "Toronto", "montreal": "Montréal", "vancouver": "Vancouver", "calgary": "Calgary", "edmonton": "Edmonton", "ottawa": "Ottawa - Gatineau",
              "winnipeg": "Winnipeg", "quebec": "Québec", "halifax": "Halifax", "saskatoon": "Saskatoon", "regina": "Regina", "kelowna": "Kelowna"}


def people():
    m = json.loads((ROOT / "web/data/demography/metro.json").read_text())
    out = {}
    for slug, cma in SPRAWL_CMA.items():
        p = m["cmas"][cma]["pop"]
        out[slug] = {"cma": cma, "pop": {y: p[y] for y in ("2001", "2010", "2020") if y in p} | {"latest": [max(p), p[max(p)]]}}
    return dict(source="statcan_17100148", boundaries="2021", cities=out,
                note="People: July 1 population of the census metropolitan area (2021 boundaries), which is not the same area as the satellite square. Population by these boundaries starts in 2001, so the comparison is 2000/2001 to 2020.")


def calc():
    """Inputs for the "what would it take" calculators: people aged 12+ (the survey population for the family-doctor question)
    and, for each province, the measured city with the most people (its rent stands for the province in the report card)."""
    pop12 = defaultdict(dict)
    young = {f"{a} year" if a == 1 else f"{a} years" for a in range(12)}
    tot = defaultdict(dict); kid = defaultdict(lambda: defaultdict(float)); seen = defaultdict(lambda: defaultdict(int))
    for r in rows("statcan_17100005"):
        if r["Gender"] != "Total - gender" or r["GEO"] not in AB or num(r) is None or not 2015 <= int(r["REF_DATE"]) <= 2025:
            continue
        g, y = AB[r["GEO"]], r["REF_DATE"]
        if r["Age group"] == "All ages":
            tot[g][y] = num(r)
        elif r["Age group"] in young:
            kid[g][y] += num(r); seen[g][y] += 1
    for g in tot:
        for y in tot[g]:
            if seen[g][y] == 12:
                pop12[g][y] = int(tot[g][y] - kid[g][y])
    m = json.loads((ROOT / "web/data/demography/metro.json").read_text())["cmas"]
    norm = lambda n: n.replace(" ", "").replace("-", "").lower()
    mp = {norm(k): v["pop"][max(v["pop"])] for k, v in m.items()}
    main_city = {}
    for c in json.loads((ROOT / "web/data/housing/cities.json").read_text())["cities"]:
        p = mp.get(norm(c["name"]))
        if p and c.get("rent2br") and (c["prov"] not in main_city or p > main_city[c["prov"]][1]):
            main_city[c["prov"]] = [c["name"], p]
    return dict(sources=["statcan_17100005", "statcan_17100148"], pop12=dict(pop12), main_city={k: v[0] for k, v in main_city.items()})


def main():
    out = ROOT / "web/data/gaps"
    (out / "hours.json").write_text(json.dumps(hours(), separators=(",", ":"), ensure_ascii=False))
    (out / "productivity.json").write_text(json.dumps(productivity(), separators=(",", ":"), ensure_ascii=False))
    (out / "calc.json").write_text(json.dumps(calc(), separators=(",", ":"), ensure_ascii=False))
    (ROOT / "web/data/sprawl/people.json").write_text(json.dumps(people(), separators=(",", ":"), ensure_ascii=False))
    h = json.loads((out / "hours.json").read_text())
    print("hours:", {g: {k: (min(v), max(v)) for k, v in d.items()} for g, d in list(h["data"].items())[:2]})
    p = json.loads((out / "productivity.json").read_text())
    print("productivity provs:", sorted(p["prov"]), "peers:", sorted(p["peers"]))


if __name__ == "__main__":
    main()
