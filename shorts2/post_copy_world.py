"""Post copy for the world-city Shorts, built from the cues (every number comes from web/data/world via city3d.py --make).

  python3 shorts2/post_copy_world.py     # merges entries into shorts2/out/post_copy.json and prints them
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://canadiandataproject.github.io/canada-through-time/"
NUM = {"newyork": "29", "london": "30", "mumbai": "31", "sydney": "32", "edmonton": "33"}
TAGS = {"newyork": "#nyc #newyork", "london": "#london #uk", "mumbai": "#mumbai #india", "sydney": "#sydney #australia", "edmonton": "#edmonton #yeg"}
HOOK = {"newyork": "New York's most packed square kilometre isn't Times Square",
        "london": "London's most packed square kilometre isn't in Zone 1",
        "mumbai": "Mumbai's most packed square kilometre isn't Dharavi",
        "sydney": "Sydney's most packed square kilometre, 1975 vs now",
        "edmonton": "Edmonton grew faster than Mumbai since 1975"}


def copy(slug):
    c = json.loads((ROOT / f"shorts2/cues/world/{slug}.json").read_text()); x = c["ctx"]; city = c["city"]
    tor = json.loads((ROOT / "web/data/world/toronto.json").read_text())["facts"]["densest_km2"]["2020"]
    lines = [f"• Within {x['km']} km of the centre: {x['p1975']} people in 1975 → {x['p2020']} in 2020 ({x['growth']})",
             f"• Busiest square km (2020): {x['dk']} people, {x['where']}",
             f"• Busiest square km in 1975: {x['dk75']} people, {x['where75']}",
             f"• Toronto's busiest (St. James Town): {tor:,}"]
    desc = (f"Every 400 m square of {city} as a column of people, 1975 to 2020.\n\n📊 The numbers\n" + "\n".join(lines) +
            "\n\n💬 Which city should we do next?\n\nData: GHSL GHS-POP R2023A (European Commission JRC), 100 m population grid; 2020 is a modelled estimate. "
            "Places: GeoNames, OpenStreetMap. Narration: synthetic voice.\n\nFree interactive map of Canada: " + SITE)
    xt = (f"{city}, every 400 m square as a column of people (all within {x['km']} km).\n\n1975: {x['p1975']}\n2020: {x['p2020']}\n"
          f"Busiest square km: {x['dk']} people ({x['where']})\nToronto's busiest: {tor:,}\n\nSource: EU JRC GHSL\n{SITE}")
    assert len(xt) <= 280, (slug, len(xt))
    tt = dict(title=HOOK[slug][:90], caption=f"{HOOK[slug]}. Busiest square km: {x['dk']} people ({x['where']}). 1975 → 2020.\n\nWhich city next? 👇\n\n{TAGS[slug]} #dataviz #maps")
    return NUM[slug], dict(title=HOOK[slug], desc=desc, x=xt), tt


if __name__ == "__main__":
    p = ROOT / "shorts2/out/post_copy.json"; allc = json.loads(p.read_text()) if p.exists() else {}
    for s in NUM:
        n, pc, tt = copy(s); allc[n] = pc; print(f"#{n} {s}\n{pc['title']}\n---\n{pc['x']}\n---TikTok: {tt['title']}\n")
    p.write_text(json.dumps(allc, indent=1, ensure_ascii=False))
