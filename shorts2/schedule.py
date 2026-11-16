"""Schedule a Short to YouTube and X through Buffer.  BUFFER_KEY env var required (never stored).

  BUFFER_KEY=... python3 shorts2/schedule.py <num> <media-file-name> <YYYY-MM-DDTHH:MM local Edmonton>
"""
import json, os, sys, urllib.request, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[1]
K = os.environ["BUFFER_KEY"]; YT = "6afa9c26ece6dfde5fdf8b01"; XC = "6afa9c4eece6dfde5fdf8e92"
BASE = "https://canadiandataproject.github.io/canada-through-time/media/"
num, media, when = sys.argv[1:4]
copy = json.loads((ROOT / "shorts2/out/post_copy.json").read_text())[num]
due = datetime.datetime.fromisoformat(when).replace(tzinfo=ZoneInfo("America/Edmonton")).isoformat()
M = "mutation($i: CreatePostInput!){ createPost(input:$i){ __typename ... on PostActionSuccess { post { id dueAt status channelService } } ... on MutationError { message } } }"
def q(i):
    r = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": M, "variables": {"i": i}}).encode(), headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=180))
video = {"video": {"url": BASE + media, "metadata": {"thumbnailOffset": 0, "title": copy["title"]}}}
common = dict(schedulingType="automatic", mode="customScheduled", dueAt=due, assets=[video])
yt = q(dict(channelId=YT, text=copy["desc"], metadata={"youtube": {"title": copy["title"], "categoryId": "27", "privacy": "public", "madeForKids": False, "notifySubscribers": True, "embeddable": True}}, **common))
print("youtube", json.dumps(yt)[:300])
x = q(dict(channelId=XC, text=copy["x"], **common))
print("x", json.dumps(x)[:300])
