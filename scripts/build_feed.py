#!/usr/bin/env python3
"""Render the catalog as a JSON Feed (https://jsonfeed.org/version/1.1).

    scripts/build_feed.py            # writes feed/feed.json

Newest first. Every item is one link: its title, the URL, when it was first
seen, its category and topics as tags, and a one-line text summary so a
reader with no page fetch still has something to index.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "links.csv"
OUT = ROOT / "feed" / "feed.json"
REPO = "thrashr888/curated-links"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/feed/feed.json"


def summary(row: dict) -> str:
    bits = [row["category"] or None, row["resource_type"] or None]
    if row["topics"]:
        bits.append(row["topics"])
    if row["author"]:
        bits.append(f"by {row['author']}")
    if row["github_repository"]:
        bits.append(f"github.com/{row['github_repository']}")
    return " · ".join(b for b in bits if b)


def main() -> None:
    with CATALOG.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: (r["first_seen"], r["id"]), reverse=True)
    items = []
    for r in rows:
        tags = [t.strip() for t in r["topics"].split(";") if t.strip()]
        if r["category"]:
            tags.insert(0, r["category"])
        item = {
            "id": r["id"],
            "url": r["url"],
            "title": r["title"],
            "content_text": summary(r),
            "date_published": r["first_seen"],
            "tags": tags,
        }
        if r["author"]:
            item["authors"] = [{"name": r["author"]}]
        if r["image"]:
            item["image"] = r["image"]
        items.append(item)
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "Curated Links",
        "home_page_url": f"https://github.com/{REPO}",
        "feed_url": RAW,
        "description": "Links worth keeping: tools, repositories, threads, and papers, one line each.",
        "language": "en",
        "items": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(feed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(items)} items -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
