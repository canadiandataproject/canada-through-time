"""Schedule Shorts in Buffer from a file in the repo, so nobody has to paste the Buffer key again.

The key lives only in the repository's encrypted Actions secret BUFFER_KEY. The GitHub workflow
.github/workflows/schedule-shorts.yml runs this whenever shorts2/queue.json changes (or on demand), schedules every
entry whose status is "pending" on YouTube, X and TikTok, and writes the Buffer post ids and status back to the file.

To schedule a new Short: host the video on gh-pages media/, add its post copy to shorts2/out/post_copy.json, add an
entry here with status "pending", commit and push. Check the result in the workflow log or in the file.

    python3 shorts2/buffer_queue.py check     # validate the queue, post nothing (no key needed)
    BUFFER_KEY=... python3 shorts2/buffer_queue.py post
"""
import datetime, json, os, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
QUEUE, COPY = ROOT / "shorts2/queue.json", ROOT / "shorts2/out/post_copy.json"
ORG = "6afa9bec49dfc7619b94264c"
CH = {"youtube": "6afa9c26ece6dfde5fdf8b01", "x": "6afa9c4eece6dfde5fdf8e92", "tiktok": "6afb4e3cece6dfde5fe8bdfc"}
BASE = "https://canadiandataproject.github.io/canada-through-time/media/"
TZ = ZoneInfo("America/Edmonton")
M = "mutation($i: CreatePostInput!){ createPost(input:$i){ __typename ... on PostActionSuccess { post { id dueAt status } } ... on MutationError { message } } }"


def q(query, v):
    r = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": query, "variables": v}).encode(),
                               headers={"Authorization": "Bearer " + os.environ["BUFFER_KEY"], "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=180))


def media_ok(name):
    try:
        return urllib.request.urlopen(urllib.request.Request(BASE + name, method="HEAD"), timeout=60).status == 200
    except Exception:
        return False


def inputs(e, copy, site):
    due = datetime.datetime.fromisoformat(e["when"][site]).replace(tzinfo=TZ).isoformat()
    base = dict(channelId=CH[site], schedulingType="automatic", mode="customScheduled", dueAt=due)
    vid = lambda meta: [{"video": {"url": BASE + e["media"], "metadata": meta}}]
    if site == "youtube":
        return dict(base, text=copy["desc"], assets=vid({"thumbnailOffset": 0, "title": copy["title"]}),
                    metadata={"youtube": {"title": copy["title"], "categoryId": "27", "privacy": "public", "madeForKids": False, "notifySubscribers": True, "embeddable": True}})
    if site == "x":
        return dict(base, text=copy["x"], assets=vid({"thumbnailOffset": 0}))
    return dict(base, text=e["tiktok"]["caption"], assets=vid({"thumbnailOffset": 0}),
                metadata={"tiktok": {"title": e["tiktok"]["title"], "isAiGenerated": False}})


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    qd, copy = json.loads(QUEUE.read_text()), json.loads(COPY.read_text())
    now, problems = datetime.datetime.now(TZ), []
    for e in qd["shorts"]:
        c = copy.get(e["num"])
        if not c: problems.append(f'#{e["num"]}: no post copy'); continue
        if len(c["x"]) > 280: problems.append(f'#{e["num"]}: X text {len(c["x"])} > 280')
        if "tiktok" in e["when"] and (len(e["tiktok"]["caption"]) > 2200 or len(e["tiktok"]["title"]) > 90): problems.append(f'#{e["num"]}: TikTok text too long')
        for site, w in e["when"].items():
            if e.get("status", {}).get(site, "pending") == "pending" and datetime.datetime.fromisoformat(w).replace(tzinfo=TZ) <= now + datetime.timedelta(minutes=10):
                problems.append(f'#{e["num"]} {site}: {w} is in the past')
        days = {}
    for e in qd["shorts"]:   # never two of our new Shorts on YouTube the same day
        d = e["when"]["youtube"][:10]
        if d in days: problems.append(f'#{e["num"]} and #{days[d]} both on YouTube {d}')
        days[d] = e["num"]
    print("\n".join(problems) or "queue ok")
    if mode != "post":
        sys.exit(1 if problems else 0)
    changed = False
    for e in qd["shorts"]:   # Buffer's free plan holds 10 queued posts per channel: retry those once slots free up
        for site, err in list(e.get("errors", {}).items()):
            if "limit reached" in err and e.get("status", {}).get(site) == "error":
                e["status"][site] = "pending"; del e["errors"][site]; changed = True
        if not e.get("errors"): e.pop("errors", None)
    for e in qd["shorts"]:
        st = e.setdefault("status", {})
        if not any(st.get(s, "pending") == "pending" for s in e["when"]): continue
        if not media_ok(e["media"]): print(f'#{e["num"]}: {BASE + e["media"]} not reachable, skipped'); continue
        for site in e["when"]:
            if st.get(site, "pending") != "pending": continue
            if any(p.startswith(f'#{e["num"]} {site}:') or p.startswith(f'#{e["num"]}:') for p in problems): print(f'#{e["num"]} {site}: skipped (see above)'); continue
            r = q(M, {"i": inputs(e, copy[e["num"]], site)})
            res = (r.get("data") or {}).get("createPost") or {}
            if res.get("__typename") == "PostActionSuccess":
                st[site] = "scheduled"; e.setdefault("buffer_ids", {})[site] = res["post"]["id"]; changed = True
                print(f'#{e["num"]} {site}: scheduled {res["post"]["dueAt"]}')
            else:
                st[site] = "error"; e.setdefault("errors", {})[site] = (res.get("message") or json.dumps(r))[:300]; changed = True
                print(f'#{e["num"]} {site}: ERROR {e["errors"][site]}')
    if changed:
        QUEUE.write_text(json.dumps(qd, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
