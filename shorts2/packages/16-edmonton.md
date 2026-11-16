# Short #16 — Edmonton spread out: 1975 to 2020 from space

Status: **review cut rendered, waiting on Tyson's voice take**. Not uploaded, not scheduled.
Files: `shorts2/sprawl.py` (engine), `shorts2/cues/sprawl.json` (timings, cards, checks, script), `shorts2/out/post_copy.json` key `"16"`,
`web/explore-v2/from-short.js` entry 16. Review cut: `exports/shorts/short-16-edmonton.SCRATCH.mp4` (music bed only, not in git).

## Why this Short
- Map-first, one idea, motion from frame 1. In Studio on 2026-11-16 the two map openers kept the most viewers (Who moved where
  57.2% stayed, Ottawa money 50.2%); the dense ranking-list opener kept 33.6% and glaciers 32% after 2 hours. Nine Shorts is a small
  sample, so this is a direction, not a rule.
- New look for the channel (satellite growth rings), from a feature that went live today.

## Data (verified)
- Source: Pesaresi M., Politis P. (2023): GHS-BUILT-S R2023A, built-up surface grid, 100 m. European Commission, Joint Research Centre. CC BY 4.0.
  Registry id `jrc_ghsl_built_s`; 42 tiles hash-checked against `data/raw/ghsl/manifest.json`.
- Area: a 60 km × 60 km square centred on downtown Edmonton (53.54 N, 113.49 W), on a local equal-area grid.
- Land covered by buildings: 1975 **84.4 km²**, 1985 93.6, 1990 98.4, 2000 **117.4**, 2010 143.5, 2020 **166.1** (×1.97, +97%).
  Added 1975–2000: 33.0 km²; 2000–2020: 48.7 km².
- Independent check from the raw tiles (native cells whose centres fall inside the square, no resampling): 84.2 and 165.8 km²
  (within 0.3%).
- The engine and `post_copy.py` both assert 84, 166, +33 and +49 against the data file, so a wrong card can't render.
- Honest limits (in the description): ground under buildings, not city limits or the metro area; years between satellite snapshots
  are modelled by the JRC; nothing is drawn between snapshots; the opening camera pull-back is the only motion that isn't data.

## Revision 2 (Tyson's notes, 2026-11-16 10:32)
- Growth now plays as the years tick: the counter runs 1975 → 2020 one year at a time (4.6–19.6 s). At each snapshot year the picture
  is exactly that snapshot; between snapshots, that snapshot's new squares appear outward from built land (order illustrative, said
  in the description). The engine asserts every snapshot year matches the data.
- Relief map with the river valley: shaded relief from Copernicus DEM GLO-30 (4× vertical exaggeration) and the North Saskatchewan
  and lakes from ESA WorldCover 2021, built by `pipeline/ingest_terrain.py` into `web/data/sprawl/edmonton_relief.png` and `_water.png`.
- Audio "breathing" removed: no swells or whooshes; the bed is in a new steady mode (`tools/make_bed_calm.py … steady`: each note one
  continuous tone, equal-power chord changes, slow levelling). Measured level swing 1.5 dB (old bed 12.9 dB); final scratch mix 1.8 dB.
  Ducking under the voice is slower (0.9 s) so it won't pump.
- Zooms kept. 2026: the satellite series is observed only to 2020 (2025/2030 are JRC projections); option to add Edmonton building
  permits 2021–2026 as a labelled final chapter if wanted.
- New duration 33.0 s; timings below are revision 1 except: growth 4.6–19.6, push-in and +49 card 20.0–25.0, reveal 25.4–28.8,
  call to action 29.0–32.6. Narration cues: 0.2, 4.8, 11.0, 20.1, 25.5, 29.1 (same six lines).

## Timing, picture and words (revision 1, 32.0 s, 1080×1920, 30 fps, loops)
| Time | Picture | On-screen text | Narration (Tyson, deadpan) |
|---|---|---|---|
| 0.0–4.6 | Edmonton 1975 fills the frame (dark squares), camera eases back from 1.35× to the full 60 km square; year chip **1975** | **EDMONTON · 1975 TO 2020 / HOW FAR DID IT SPREAD?** | 0.2 "This is Edmonton in 1975. Every dark speck is land covered by buildings." |
| 4.8–16.6 | Snapshots appear one by one, each fading in over 0.7 s with a soft low swell: 1985 at 5.0, 1990 at 7.0, 2000 at 9.5, 2010 at 12.0, 2020 at 14.5; legend chips light up | **LAND COVERED BY BUILDINGS / WATCH IT GROW OUT / each colour = first year built up** | 5.0 "Then the satellites kept watching." · 9.6 "Edmonton didn't really grow up. It grew out." |
| 17.0–22.2 | Push-in (1.9×) to the densest 2010–2020 growth, south Edmonton; scale bar rescales | **SINCE 2000 / +49 km² / vs +33 km² in the 25 years before** | 17.1 "And it sped up: more was built after 2000 than in the twenty-five years before." |
| 22.5–27.0 | Back out to the whole square, 2020 | **LAND COVERED BY BUILDINGS / 84 TO 166 km² / nearly double since 1975** | 22.6 "Eighty-four square kilometres of buildings in 1975. A hundred and sixty-six in 2020. Nearly double." |
| 27.2–31.6 | 2020 city | **12 CITIES · FREE EXPLORER / WHAT ABOUT YOURS? / link in the description** | 27.3 "Every big city's in the free explorer. Link's below. Yes, even Saskatoon." |
| 31.6–32.0 | Cross-fade into frame 1 (loop) | — | — |

Always on screen: year chip, colour legend (1975–2020), 10 km scale bar, credit line
"Buildings: EU JRC GHS-BUILT-S R2023A (CC BY 4.0) · The Canadian Data Project".
Two jokes (grew up / grew out; Saskatoon). Every spoken number matches a card.

## Recording (Tyson)
1. Read the six lines above on your phone, a short pause between them. Check the numbers: **eighty-four**, **a hundred and sixty-six**,
   **two thousand**, **twenty-five**.
2. Send the file. It gets the usual treatment (trim pauses > 0.7 s, 1.04× speed, clarity EQ, pitch 0.96 with formants kept), is
   re-timed so each line lands on its card, and saved as `short-16-edmonton.wav`; captions (.srt) come from the spoken words.
3. Final mix: `python3 shorts2/sprawl.py shorts2/cues/sprawl.json /tmp/s16.mp4 && python3 shorts2/mix.py sprawl shorts2/cues/sprawl.json /tmp/s16.mp4 exports/shorts/short-16-edmonton.mp4`

## Post text (generated by `python3 shorts2/post_copy.py`, key "16")
- YouTube title: **Edmonton spread out: 1975 to 2020 from space**
- X (206 characters): built-up 1975 84 km², 2000 117 km², 2020 166 km², "More was added after 2000 than in the 25 years before.", source line.
- Description: numbers, how to read it, limits, full JRC citation, "Voice, music and sound: original.", explorer link, #Edmonton #Canada #DataViz.

## Explorer link (call to action)
https://canadiandataproject.github.io/canada-through-time/?s=16#cl=sprawl/2020/cedmonton
- Opens Climate and land → Cities spreading → Edmonton, 2020. `?s=16` shows the "From the Short" banner with "Next: Now try Calgary".
- **Live site today: the view opens but the Edmonton picture is blank** (the published build asked for the picture at the wrong path).
  Fixed on the branch (`climate.js`), checked on a local copy of the built site; it goes live with the next deploy:
  `python3 tools/build_site.py && bash tools/deploy_site.sh`. The banner entry for #16 also goes live then.

## Queue fit
- Format rules (v3): motion from frame 1 ✓, question hook ✓, one big number at a time ✓, reveal at 22.5 s of 32 (70%) ✓,
  32 s with narration ✓, quiet sound cues ✓, loops ✓.
- Suggested slot: **Wed Nov 18, 1:30 PM MT** (after #13 contracts at 9:00 AM; not the same topic back to back; #14 Toronto is the day before).
- Per the queue rule, once #15 posts (Nov 17, 6 PM) only #13 is left, so #16 is the first of the next three.
- To schedule after review (not done): upload `short-16-edmonton.mp4` to the gh-pages branch under `media/`, then
  `BUFFER_KEY=… python3 shorts2/schedule.py 16 short-16-edmonton.mp4 2026-11-18T13:30` (X), and schedule YouTube in Studio as for #8–#10.

## What to measure (log in the Shorts scorecard at 2 h, 24 h, 72 h)
- Stayed to watch (target ≥ 60%; map openers so far 50–57%), average % watched, views, subscribers gained, explorer visits with `?s=16`.
- Compare against #14 (Toronto, also a city map) to see whether satellite growth beats census choropleth.
