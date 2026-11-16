"""Post copy for the wages / temporary foreign worker Short; numbers pasted from the generated configuration."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / "timelapses/short-wages-tfw.json").read_text()); F = C["figures"]
fc, rw, tf = F["food_cagr"], F["real_wage"], F["tfwp_dec31"]; lo = F["tfwp_low_post"]
p = lambda v: f"+{v:.1f}%"
txt = f"""# Short: wages and the Temporary Foreign Worker Program

**Title:** Did temporary foreign workers hold down Canadian wages? What the data and research say

**Description:**
Real (inflation-adjusted) hourly wages, 1997–2025, with Temporary Foreign Worker Program changes marked.

📊 The numbers (Statistics Canada, 2025 dollars)
• Restaurants & hotels (food services): {p(fc['2002-2014'])}/yr real wage growth 2002–2014, while the program was open to lower-skill jobs
• {p(fc['2014-2019'])}/yr 2014–2019, after low-wage hiring was capped (minimum wages also rose then)
• {p(fc['2019-2025'])}/yr 2019–2025
• Temporary Foreign Worker Program permit holders on Dec. 31 (IRCC): {tf['2002']:,} in 2002 → {tf['2014']:,} in 2014 → {lo[1]:,} in {lo[0]} → {tf['2024']:,} in 2024 (preliminary; most since at least 2000)
• All workers: ${rw['all']['1997']:.2f} → ${rw['all']['2025']:.2f}/hr since 1997; food services ${rw['food']['1997']:.2f} → ${rw['food']['2025']:.2f}

🔬 What research found
A peer-reviewed study (Chen & Fang, 2025) compared low-wage jobs that relied on temporary foreign workers with similar jobs the 2014 limits didn't touch. After the limits, Canadians in the affected jobs earned 3.7–4.5% more, roughly 70–80¢ an hour on a typical restaurant or hotel wage. So the effect is real, but modest. A chart alone can't show cause: wages also move with minimum wages, the economy, and which workers are counted.

💬 Should Canada keep, tighten or end the low-wage stream? Tell us why.

Sources: Statistics Canada tables 14-10-0064-01 and 18-10-0005-01; IRCC open data, TFWP work permit holders on December 31 (preliminary). Chen, W.-H. & Fang, T. (2025), Journal of Ethnic and Migration Studies (IZA DP 18240). Program dates: Government of Canada (July 2002 low-skill pilot; June 20, 2014 overhaul; Sept 26, 2024 changes). Lines grow between years as animation.
Music and sound: original.

Explore wages and jobs by province: https://canadiandataproject.github.io/canada-through-time/

#Canada #Wages #TFW #DataViz

**Tags:** temporary foreign workers, TFW program, Canada wages, real wages, low wage jobs, Statistics Canada, immigration policy, Canadian economy

## X
Did temporary foreign workers hold down Canadian wages?

Real wages in restaurants & hotels:
2002–2014 (open to lower-skill jobs): {p(fc['2002-2014'])}/yr
2014–2019 (after the cap): {p(fc['2014-2019'])}/yr

A study comparing similar jobs: the 2014 limits raised affected wages 3.7–4.5%. Real, but modest.
"""
(ROOT / "exports/short-wages").mkdir(parents=True, exist_ok=True)
(ROOT / "exports/short-wages/post_copy.md").write_text(txt); print(txt)
