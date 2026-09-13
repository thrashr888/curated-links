#!/usr/bin/env python3
"""Render the catalog as a JSON Feed (https://jsonfeed.org/version/1.1).

    scripts/build_feed.py            # writes feed/feed.json

Newest first. Every item is one link: its title, the URL, when it was first
seen, its category and topics as tags, and a text body. A post on X that
points at a page becomes that page (the post's URL rides in external_url and
its text in the body); a post that stands alone keeps its own URL and text.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_slack_export import canonical  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "links.csv"
RESOLVED = ROOT / "catalog" / "resolved.json"
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
    resolved = json.loads(RESOLVED.read_text()) if RESOLVED.exists() else {}
    rows.sort(key=lambda r: (r["first_seen"], r["id"]), reverse=True)
    items = []
    for r in rows:
        tags = [t.strip() for t in r["topics"].split(";") if t.strip()]
        if r["category"]:
            tags.insert(0, r["category"])
        post = resolved.get(r["url"]) or {}
        # A post that points somewhere is a pointer: the item is the page it
        # points at, and the post rides along as the reason it was kept.
        end = canonical(post["end_url"]) if post.get("end_url") else None
        item = {
            "id": r["id"],
            "url": end or r["url"],
            "title": (post.get("end_title") if end else "") or r["title"],
            "content_text": summary(r),
            "date_published": r["first_seen"],
            "tags": tags,
        }
        if post.get("text"):
            who = f"@{post['author']}" if post.get("author") else "a post on X"
            item["content_text"] = f"{post['text']}\n\n— {who}" + (
                f"\n\n{summary(r)}" if summary(r) else ""
            )
        if end:
            item["external_url"] = r["url"]
            if post.get("end_description"):
                item["summary"] = post["end_description"]
        if r["author"]:
            item["authors"] = [{"name": r["author"]}]
        elif post.get("author"):
            item["authors"] = [{"name": post["author"]}]
        image = r["image"] or post.get("image", "")
        if image:
            item["image"] = image
        items.append(item)
    # Two posts pointing at one page are one item — the newest keeps the
    # slot, and the other posts ride along as the reasons it was kept.
    by_url: dict[str, dict] = {}
    deduped = []
    for item in items:
        first = by_url.get(item["url"])
        if first is None:
            by_url[item["url"]] = item
            deduped.append(item)
        elif item.get("external_url"):
            first["content_text"] = f"{first['content_text']}\n\n— also shared: {item['external_url']}"
    items = deduped
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
