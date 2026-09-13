#!/usr/bin/env python3
"""Render the catalog as an Open Knowledge Format bundle: one concept file
per link under sources/, so a reader that speaks OKF (Alchemy) gets every
link as its own source — a web URL with its title, cover image, and tags —
rather than one page per month.

    scripts/build_sources.py         # writes sources/<id>-<slug>.md

Identity is stable: each link's sync_id is a UUID derived from its URL, so
regenerating the bundle never turns an existing link into a new one. The
bundle deliberately ships no index.md or log.md — a reader writes its own
listing and history beside these files, and those must never collide with
what this repo commits.
"""
import csv
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "links.csv"
OUT = ROOT / "sources"
NAMESPACE = uuid.UUID("6f0a1c3e-4b8d-4e3a-9f2b-7c5d1e0a9b42")  # curated-links
SLUG_MAX = 60


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:SLUG_MAX].rstrip("-") or "link"


def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def tags_for(row: dict) -> list[str]:
    tags = []
    for raw in [row["category"], *row["topics"].split(";")]:
        t = slug(raw)
        if t and t != "link" and t not in tags:
            tags.append(t)
    return tags


def concept(row: dict) -> str:
    tags = tags_for(row)
    summary_bits = [row["category"], row["resource_type"]]
    if row["topics"]:
        summary_bits.append(row["topics"].replace(";", ","))
    if row["author"]:
        summary_bits.append(f"by {row['author']}")
    summary = " · ".join(b for b in summary_bits if b)
    lines = [
        "---",
        "type: Source",
        f"title: {yaml_str(row['title'])}",
        f"description: {yaml_str(summary)}",
        f"resource: {yaml_str(row['url'])}",
        f"tags: [{', '.join(tags)}]",
        "generated:",
        '  by: "curated-links"',
        f"  at: {yaml_str(row['first_seen'])}",
        "alchemy:",
        '  source_type: "url"',
        f"  tags: {yaml_str(' '.join(tags))}",
        f"  sync_id: {yaml_str(str(uuid.uuid5(NAMESPACE, row['url'])))}",
        f"  origin: {yaml_str(row['url'])}",
    ]
    if row["image"]:
        lines.append(f"  image_url: {yaml_str(row['image'])}")
    if row["author"]:
        lines.append(f"  author: {yaml_str(row['author'])}")
    lines += [
        f"timestamp: {yaml_str(row['first_seen'])}",
        "---",
        "",
        f"# {row['title']}",
        "",
        f"{summary}." if summary else "",
        "",
        f"Link: <{row['url']}>",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    with CATALOG.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.md"):
        old.unlink()
    for r in rows:
        (OUT / f"{r['id'].lower()}-{slug(r['title'])}.md").write_text(concept(r), encoding="utf-8")
    print(f"{len(rows)} concept files -> sources/")


if __name__ == "__main__":
    main()
