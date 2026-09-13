#!/usr/bin/env python3
"""Resolve what each link actually points at.

A post on X is usually a pointer: the thing worth keeping is the page it
links to. For every x.com link this asks fxtwitter for the post's text and
its expanded links, keeps the text as the link's description, and — when
the post carries exactly one outbound link that isn't itself a social
post — records that as the link's destination. Everything is cached in
catalog/resolved.json so a rerun only asks about new links.

    scripts/resolve_links.py           # updates catalog/resolved.json
"""
import csv
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "links.csv"
CACHE = ROOT / "catalog" / "resolved.json"
SOCIAL = ("x.com", "twitter.com", "t.co", "threads.net", "bsky.app", "mastodon.social")
STATUS = re.compile(r"^https?://(?:www\.)?(?:x|twitter)\.com/([^/]+)/status/(\d+)")


def fetch_json(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "curated-links/1 (+https://github.com/thrashr888/curated-links)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def resolve_post(url: str) -> dict:
    m = STATUS.match(url)
    if not m:
        return {}
    data = fetch_json(f"https://api.fxtwitter.com/{m.group(1)}/status/{m.group(2)}")
    tweet = (data or {}).get("tweet") or {}
    if not tweet:
        return {"status": "unavailable"}
    text = (tweet.get("text") or "").strip()
    # Where the post points: the link card first (fxtwitter resolves it),
    # else a URL written into the text. Social destinations don't count —
    # a post pointing at another post is still a post.
    def outbound(u: str) -> bool:
        host = urlparse(u).netloc.lower().replace("www.", "")
        return bool(host) and not any(host == s or host.endswith("." + s) for s in SOCIAL)

    links = []
    card = tweet.get("card") or {}
    if isinstance(card, dict) and card.get("url") and outbound(card["url"]):
        links.append(card["url"])
    for u in re.findall(r"https?://[^\s)\]]+", text):
        if outbound(u) and u not in links:
            links.append(u)
    quote = tweet.get("quote") or {}
    out = {
        "status": "ok",
        "author": (tweet.get("author") or {}).get("screen_name", ""),
        "text": text,
        "links": links,
        "quote": quote.get("url", "") if isinstance(quote, dict) else "",
    }
    if links:
        out["end_url"] = links[0]
        if isinstance(card, dict) and card.get("url") == links[0]:
            out["end_title"] = (card.get("title") or "").strip()
            out["end_description"] = (card.get("description") or "").strip()
    media = tweet.get("media") or {}
    photos = media.get("photos") or [] if isinstance(media, dict) else []
    if photos:
        out["image"] = photos[0].get("url", "")
    return out


def main() -> None:
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    with CATALOG.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    todo = [r["url"] for r in rows if STATUS.match(r["url"]) and r["url"] not in cache]
    print(f"{len(todo)} posts to resolve ({len(cache)} cached)")
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for url, res in zip(todo, pool.map(resolve_post, todo)):
            cache[url] = res
            done += 1
            if done % 50 == 0:
                CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n")
                print(f"  {done}/{len(todo)}", file=sys.stderr)
            time.sleep(0.05)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n")
    ok = sum(1 for v in cache.values() if v.get("status") == "ok")
    ends = sum(1 for v in cache.values() if v.get("end_url"))
    print(f"resolved {ok} posts; {ends} carry one outbound link; {len(cache) - ok} unavailable")


if __name__ == "__main__":
    main()
