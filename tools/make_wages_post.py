"""Post copy for the wages / temporary foreign worker Short; numbers pasted from the generated configuration."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / "timelapses/short-wages-tfw.json").read_text()); F = C["figures"]
fc, rw = F["food_cagr"], F["real_wage"]
p = lambda v: f"+{v:.1f}%"
txt = f"""# Short: wages and the Temporary Foreign Worker Program

**Title:** Did temporary foreign workers hold down Canadian wages? What the data and research say

**Description:**
Real (inflation-adjusted) hourly wages, 1997–2025, with Temporary Foreign Worker Program changes marked.

📊 The numbers (Statistics Canada, 2025 dollars)
• Restaurants & hotels (food services): {p(fc['2002-2014'])}/yr real wage growth 2002–2014, while the program was open to low-wage jobs
• {p(fc['2014-2019'])}/yr 2014–2019, after low-wage hiring was capped (minimum wages also rose then)
• {p(fc['2019-2025'])}/yr 2019–2025
• All workers: ${rw['all']['1997']:.2f} → ${rw['all']['2025']:.2f}/hr since 1997; food services ${rw['food']['1997']:.2f} → ${rw['food']['2025']:.2f}

🔬 What research found
A peer-reviewed study comparing similar low-skill jobs (Chen & Fang, 2025) found the 2014 limits raised wages 3.7–4.5% for low-wage Canadians in the affected jobs. The effect is real, but modest. A chart alone can't show cause: wages also move with minimum wages, the economy, and which workers are counted.

💬 Should Canada keep, tighten or end the low-wage stream? Tell us why.

Sources: Statistics Canada tables 14-10-0064-01 and 18-10-0005-01. Chen, W.-H. & Fang, T. (2025), Journal of Ethnic and Migration Studies (IZA DP 18240). Program dates: Government of Canada (July 2002 low-skill pilot; June 20, 2014 overhaul; Sept 26, 2024 changes). Lines grow between years as animation.
Music and sound: original.

Explore wages and jobs by province: https://tjreeve-ship-it.github.io/canada-through-time/

#Canada #Wages #TFW #DataViz

**Tags:** temporary foreign workers, TFW program, Canada wages, real wages, low wage jobs, Statistics Canada, immigration policy, Canadian economy

## X
Did temporary foreign workers hold down Canadian wages?

Real wages in restaurants & hotels:
2002–2014 (open to low-wage jobs): {p(fc['2002-2014'])}/yr
2014–2019 (after the cap): {p(fc['2014-2019'])}/yr

A study comparing similar jobs: the 2014 limits raised affected wages 3.7–4.5%. Real, but modest.
"""
(ROOT / "exports/short-wages").mkdir(parents=True, exist_ok=True)
(ROOT / "exports/short-wages/post_copy.md").write_text(txt); print(txt)
