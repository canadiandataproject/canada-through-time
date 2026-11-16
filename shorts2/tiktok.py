"""TikTok cross-posting through Buffer: its own captions, its own schedule.

  BUFFER_KEY=... python3 shorts2/tiktok.py plan           # print the plan, post nothing
  BUFFER_KEY=... python3 shorts2/tiktok.py post           # schedule every planned post not yet queued

Strategy (different from YouTube on purpose):
- TikTok shows every video to fresh people, and a new account has no back catalogue there, so the 8 Shorts
  already made are all "new" on TikTok. Launch with 2 a day (12:30 PM and 7:00 PM MT) until the catalogue runs out,
  strongest map openers first; then 1 a day at 7:00 PM, the same day each new Short premieres on YouTube.
- Captions are short and open with a question to pull comments; 4 hashtags; no links (not clickable on
  a new account): "free explorer, link in bio".
- isAiGenerated = False: the visuals are drawn from data by our own code and the voice is Tyson's.
"""
import json, os, sys, urllib.request, datetime
from zoneinfo import ZoneInfo
ORG = "6afa9bec49dfc7619b94264c"
BASE = "https://canadiandataproject.github.io/canada-through-time/media/"
TAIL = "\n\nFree explorer, link in bio."
PLAN = [  # (local Edmonton time, media file, title, caption)
 ("2026-11-16T19:00", "short-08-glaciers.mp4", "How much ice have Canada's glaciers lost?",
  "How much ice have Canada's glaciers lost? 🧊 Peyto lost more in 25 years than in the 35 before. 7 of 7 long-measured glaciers: net loss." + TAIL + "\n\n#canada #glaciers #climate #dataviz"),
 ("2026-11-17T12:30", "short-12-receipt.mp4", "Ottawa's $493 billion receipt",
  "If Ottawa printed a receipt for 2025–26, it would say $493.5B. About $11,860 per person. Where did it go? 🧾" + TAIL + "\n\n#canada #budget #cdnpoli #dataviz"),
 ("2026-11-17T19:00", "short-15-temporary-residents.mp4", "Canada's temporary residents: 1.3M → 2.9M → 2.8M",
  "Temporary residents in Canada went from 1.3M to 2.9M in four years, then fell for the first time. Students dropped most. 👀" + TAIL + "\n\n#canada #immigration #cdnpoli #dataviz"),
 ("2026-11-18T12:30", "short-14-toronto.mp4", "Toronto: one city, 1,227 neighbourhoods",
  "Same city, wildly different neighbourhoods. Median household income in Toronto ranges from $36K to $286K. Where's yours? 🏙️" + TAIL + "\n\n#toronto #canada #census #dataviz"),
 ("2026-11-18T19:00", "short-16-edmonton.mp4", "Edmonton spread out: 1975 to 2020",
  "Edmonton didn't grow up, it grew out. Land under buildings nearly doubled since 1975, seen from space. 🛰️ Which city next?" + TAIL + "\n\n#edmonton #alberta #canada #dataviz"),
 ("2026-11-19T12:30", "short-13-contracts.mp4", "Who got Ottawa's biggest contracts?",
  "Ottawa has disclosed 1.12M contracts worth $420B. About 1 dollar in 7 went out with no competition. Should that be allowed?" + TAIL + "\n\n#canada #cdnpoli #government #dataviz"),
 ("2026-11-19T19:00", "short-09-stations.mp4", "How many of Canada's weather stations have warmed?",
  "Canada's long-running weather stations vs their own 1961–1990 average: 263 of 263 warmer in the 2000s. One exception since. Guess where? 🌡️" + TAIL + "\n\n#canada #climate #weather #dataviz"),
 ("2026-11-20T12:30", "short-10-unemployment.mp4", "Which province has had Canada's lowest unemployment?",
  "Which province has had Canada's lowest unemployment rate? 6 different provinces have been #1 since 1976. One led 20 of 50 years. 📊" + TAIL + "\n\n#canada #jobs #economy #dataviz"),
]

def q(query, v=None):
    r = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": query, "variables": v or {}}).encode(),
                               headers={"Authorization": "Bearer " + os.environ["BUFFER_KEY"], "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=180))

def tiktok_channel():
    ch = q('query($o:OrganizationId!){ channels(input:{organizationId:$o}){ id service name } }', {"o": ORG})["data"]["channels"]
    tt = [c for c in ch if c["service"] == "tiktok"]
    if not tt: sys.exit("TikTok is not connected in Buffer yet: Channels -> Connect -> TikTok.")
    return tt[0]["id"]

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    for when, media, title, cap in PLAN:
        assert len(cap) <= 2200 and len(title) <= 90, media
        print(when, media, len(cap), "chars")
    if mode != "post": sys.exit()
    ch = tiktok_channel(); now = datetime.datetime.now(ZoneInfo("America/Edmonton"))
    have = {e["node"]["dueAt"][:16] for e in q('query($o:OrganizationId!,$c:ChannelId!){ posts(input:{organizationId:$o, filter:{status:[scheduled], channelIds:[$c]}}, first:50){ edges{ node{ dueAt } } } }', {"o": ORG, "c": ch})["data"]["posts"]["edges"]}
    M = "mutation($i: CreatePostInput!){ createPost(input:$i){ __typename ... on PostActionSuccess { post { id dueAt status } } ... on MutationError { message } } }"
    for when, media, title, cap in PLAN:
        due = datetime.datetime.fromisoformat(when).replace(tzinfo=ZoneInfo("America/Edmonton"))
        if due <= now + datetime.timedelta(minutes=10): print("skip (past)", when, media); continue
        utc = due.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")
        if utc in have: print("skip (queued)", when, media); continue
        r = q(M, {"i": dict(channelId=ch, text=cap, schedulingType="automatic", mode="customScheduled", dueAt=due.isoformat(),
                             metadata={"tiktok": {"title": title, "isAiGenerated": False}},
                             assets=[{"video": {"url": BASE + media, "metadata": {"thumbnailOffset": 0}}}])})
        print(when, media, json.dumps(r)[:200])
