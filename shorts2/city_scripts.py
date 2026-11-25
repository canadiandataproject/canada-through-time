"""Scripts for the world-city Shorts (shorts2/city3d.py). One entry per city.

Rules (Tyson, standing): deadpan, tight, 2–3 jokes max, local references only people from there get. Every number on a
card or in a line comes from the data via {placeholders}; anything a joke implies as fact gets an assert here.
Jokes punch at places, prices, transit and weather, never at people or groups. The "say" lines are what Tyson records;
they are also burned in as captions so the jokes land with the sound off.

Placeholders: city p1975 p2020 growth dk dk75 where where75 km ca ca_pop vs vs_dk vs_x vs_where (+ per-city "extra").
Beat keys and order are fixed: hook then grow dense compare joke end.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = lambda s: json.loads((ROOT / "web/data/world" / f"{s}.json").read_text())["facts"]
END = dict(key="end", dur=4.0, say="Which city should I do next?", card=dict(kick="Comment a city", big="Yours next?", sub="Free map of Canada: link below"))


def beats(hook, then, grow, dense, compare, joke, end=END):
    return [dict(key="hook", dur=3.4, **hook), dict(key="then", dur=4.2, **then), dict(key="grow", dur=5.6, say_at=0.5, **grow),
            dict(key="dense", dur=5.4, **dense), dict(key="compare", dur=5.0, **compare), dict(key="joke", dur=4.6, **joke), end]


SCRIPTS = {
    "mumbai": dict(
        mode="dark", vs="toronto",
        asserts=[lambda d, c: W("mumbai")["densest_km2"]["2020"] > 130_613,          # "more than all of Saint John"
                 lambda d, c: d["facts"]["densest_at"]["1975"][1] < d["facts"]["densest_at"]["2020"][1],    # the crowd moved north
                 lambda d, c: max(x[6] for x in d["cells"] if (x[0] + 267) ** 2 + (x[1] + 553) ** 2 < 1500 ** 2) < 0.6 * d["facts"]["max_cell"]["2020"]],  # "not Dharavi"
        where="Jogeshwari West",
        beats=beats(
            hook=dict(say="Mumbai. Let's find the most packed square kilometre.", card=dict(kick="How packed can one square km get?", big="Mumbai")),
            then=dict(say="1975. {p1975} people. The Virar fast was already full.", card=dict(counter=True, kick="Within {km} km of the centre")),
            grow=dict(say="By 2020, {p2020}. Same trains.", card=dict(counter=True, kick="Within {km} km of the centre")),
            dense=dict(say="The busiest square kilometre? Not Dharavi. {where}.", card=dict(kick="People in one square km", big="{dk}", sub="{where} · 2020 estimate")),
            compare=dict(say="More people than all of {ca}, New Brunswick. Minus the fog. Plus vada pav.",
                         card=dict(kick="More people than all of", big="{ca}, N.B.", sub="{ca_pop} people (2021 Census)")),
            joke=dict(say="In 1975 the busiest square was down in {where75}. Then everyone took the train north.",
                      card=dict(kick="Busiest square km in 1975", big="{where75}", sub="{dk75} people")))),

    "london": dict(
        mode="dark", vs="toronto",
        asserts=[lambda d, c: d["facts"]["total"]["1990"] < d["facts"]["total"]["1975"],                  # "then it shrank"
                 lambda d, c: d["facts"]["densest_km2"]["2020"] < W("toronto")["densest_km2"]["2020"]],    # St. James Town packs in more
        where="Maida Hill, W9",
        beats=beats(
            hook=dict(say="London. Let's find its most packed square kilometre.", card=dict(kick="How packed can one square km get?", big="London")),
            then=dict(say="1975. {p1975} people. Then it shrank.", card=dict(counter=True, kick="Within {km} km of the centre")),
            grow=dict(say="Then it got expensive, and grew anyway. {p2020}.", card=dict(counter=True, kick="Within {km} km of the centre")),
            dense=dict(say="The busiest square kilometre: {where}. Not even Zone 1.", card=dict(kick="People in one square km", big="{dk}", sub="{where} · 2020 estimate")),
            compare=dict(say="Toronto's St. James Town packs in more. {vs_dk}. Mind the gap.",
                         card=dict(kick="Toronto's busiest square km", big="{vs_dk}", sub="St. James Town beats all of London")),
            joke=dict(say="In 1975 it was {where75}. Back when people could afford {where75}.",
                      card=dict(kick="Busiest square km in 1975", big="{where75}", sub="{dk75} people")))),

    "newyork": dict(
        mode="dark", vs="toronto", where="Upper East Side", n_labels=5, skip_places=["Manhattan"],
        asserts=[lambda d, c: 1.9 <= d["facts"]["densest_km2"]["2020"] / W("toronto")["densest_km2"]["2020"] <= 2.1],   # "about twice"
        beats=beats(
            hook=dict(say="New York. Let's find the most packed square kilometre.", card=dict(kick="How packed can one square km get?", big="New York")),
            then=dict(say="1975. {p1975} people. All of them in a hurry.", card=dict(counter=True, kick="Within {km} km of City Hall")),
            grow=dict(say="By 2020, {p2020}. They found room. Somehow.", card=dict(counter=True, kick="Within {km} km of City Hall")),
            dense=dict(say="The busiest square kilometre: the {where}. Nobody actually lives in Times Square.",
                       card=dict(kick="People in one square km", big="{dk}", sub="Yorkville, {where} · 2020 estimate")),
            compare=dict(say="That's about twice Toronto's St. James Town.", card=dict(kick="Toronto's busiest square km ×{vs_x}", big="{dk}", sub="vs {vs_dk} in St. James Town")),
            joke=dict(say="Where a one-bedroom is a hallway with ambition.", card=dict(kick="Busiest square km", big="Yorkville", sub="{where}, Manhattan")))),

    "edmonton": dict(
        mode="dark", vs="toronto", where="Wîhkwêntôwin", n_labels=5,
        asserts=[lambda d, c: 450_000 < d["facts"]["total"]["1975"] < 550_000,                          # "half a million"
                 lambda d, c: d["facts"]["growth"] > W("mumbai")["growth"],                               # "faster than Mumbai"
                 lambda d, c: W("toronto")["densest_km2"]["2020"] / d["facts"]["densest_km2"]["2020"] > 2],  # "more than twice"
        extra=dict(mumbai_g=lambda d: f"×{W('mumbai')['growth']:.1f}"),
        beats=beats(
            hook=dict(say="Edmonton. Two seasons: winter, and construction.", card=dict(kick="How packed can one square km get?", big="Edmonton")),
            then=dict(say="1975. Half a million people. Same potholes.", card=dict(counter=True, kick="Within {km} km of downtown")),
            grow=dict(say="Then it grew {growth}. Faster than Mumbai, somehow.", card=dict(counter=True, kick="Within {km} km of downtown")),
            dense=dict(say="The busiest square kilometre: {where}. You might still call it Oliver.",
                       card=dict(kick="People in one square km", big="{dk}", sub="{where} (Oliver) · 2020 estimate")),
            compare=dict(say="Toronto's St. James Town fits in more than twice that.", card=dict(kick="Toronto's busiest square km", big="{vs_dk}", sub="vs {dk} here")),
            joke=dict(say="Still easier to find a home here than parking on Whyte Ave on a Friday.",
                      card=dict(kick="Since 1975", big="{growth}", sub="Mumbai: {mumbai_g}")))),

    "sydney": dict(
        mode="dark", vs="toronto", where="Haymarket", where75="Bondi",
        asserts=[lambda d, c: d["facts"]["densest_km2"]["2020"] < W("toronto")["densest_km2"]["2020"],   # St. James Town packs in more
                 lambda d, c: d["facts"]["densest_name"]["1975"] == "Bondi Beach"],
        beats=beats(
            hook=dict(say="Sydney. Let's find the most packed square kilometre.", card=dict(kick="How packed can one square km get?", big="Sydney")),
            then=dict(say="1975. {p1975} people. Not one of them could afford a house here today.", card=dict(counter=True, kick="Within {km} km of the CBD")),
            grow=dict(say="By 2020, {p2020}. Mostly on the M4.", card=dict(counter=True, kick="Within {km} km of the CBD")),
            dense=dict(say="The busiest square kilometre: {where}. Right next to Central.", card=dict(kick="People in one square km", big="{dk}", sub="{where} · 2020 estimate")),
            compare=dict(say="Toronto's St. James Town still packs in more. {vs_dk}.", card=dict(kick="Toronto's busiest square km", big="{vs_dk}", sub="vs {dk} in {where}")),
            joke=dict(say="In 1975 it was Bondi. Now Bondi's mostly the brunch queue.",
                      card=dict(kick="Busiest square km in 1975", big="{where75}", sub="{dk75} people")))),
}

# Nature-documentary narration (Tyson, 2026-11-24): a hushed, awed narrator who isn't anyone in particular (no impression
# of a real person). Payoff-first open (open="payoff"): frame 1 is the busiest square km already lit, with its number,
# then the year rewinds to 1975. Hook test vs the question open: Toronto (moving from frame 1) held 64%.
PAYOFF_HOOK = lambda say, city: dict(say=say, card=dict(kick="People in ONE square km", big="{dk}", sub=city + " · 2020 estimate"))

SCRIPTS["newyork_doc"] = dict(SCRIPTS["newyork"], open="payoff", base="newyork", beats=beats(
    hook=PAYOFF_HOOK("Here, in a single square kilometre, {dk} New Yorkers have made their nest.", "New York"),
    then=dict(say="1975. {p1975}. The herd is already restless.", card=dict(counter=True, kick="Within {km} km of City Hall")),
    grow=dict(say="By 2020, {p2020}. Space is scarce. And yet, they keep coming.", card=dict(counter=True, kick="Within {km} km of City Hall")),
    dense=dict(say="Their densest nesting ground: the {where}. Times Square, curiously, is uninhabited.",
               card=dict(kick="People in one square km", big="{dk}", sub="Yorkville, {where} · 2020 estimate")),
    compare=dict(say="Twice as crowded as their northern cousins, in Toronto's St. James Town.",
                 card=dict(kick="Toronto's busiest square km ×{vs_x}", big="{dk}", sub="vs {vs_dk} in St. James Town")),
    joke=dict(say="Each one-bedroom, a hallway with ambition.", card=dict(kick="Busiest square km", big="Yorkville", sub="{where}, Manhattan")),
    end=dict(END, say="Which habitat should we observe next?")))

SCRIPTS["london_doc"] = dict(SCRIPTS["london"], open="payoff", base="london", beats=beats(
    hook=PAYOFF_HOOK("Here, in one square kilometre of west London, {dk} people have made their burrow.", "London"),
    then=dict(say="1975. {p1975}. Then, mysteriously, the colony shrank.", card=dict(counter=True, kick="Within {km} km of the centre")),
    grow=dict(say="The rents rose. The colony grew anyway. {p2020}.", card=dict(counter=True, kick="Within {km} km of the centre")),
    dense=dict(say="The densest burrow: {where}. Remarkably, not even Zone 1.", card=dict(kick="People in one square km", big="{dk}", sub="{where} · 2020 estimate")),
    compare=dict(say="And yet Toronto's St. James Town packs in more. {vs_dk}. Mind the gap.",
                 card=dict(kick="Toronto's busiest square km", big="{vs_dk}", sub="St. James Town beats all of London")),
    joke=dict(say="In 1975, the colony gathered at {where75}. Before it learned what {where75} costs.",
              card=dict(kick="Busiest square km in 1975", big="{where75}", sub="{dk75} people")),
    end=dict(END, say="Which habitat should we observe next?")))

for _k in ("newyork_doc", "london_doc"):            # the slower narrator needs room: longer hook and dense beats (~34 s total)
    _b = SCRIPTS[_k]["beats"]; _b[0]["dur"] = 4.4; _b[3]["dur"] = 6.2
