#!/usr/bin/env python3
"""Render the catalog as monthly markdown digests, one file per month.

    scripts/build_links.py           # writes links/YYYY-MM.md

A digest is a plain list — one link per line with its title, category,
topics, and author — so a reader (or an app that ingests the folder) gets a
page per month rather than a thousand one-line files. Newest month first in
the index; newest link first within a month.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "links.csv"
OUT = ROOT / "links"


def line(r: dict) -> str:
    meta = [r["category"], r["topics"].replace(";", ",")]
    if r["author"]:
        meta.append(f"by {r['author']}")
    tail = " · ".join(m for m in meta if m)
    return f"- [{r['title']}]({r['url']})" + (f" — {tail}" if tail else "")


def main() -> None:
    with CATALOG.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    months: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        months[r["first_seen"][:7]].append(r)
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.md"):
        old.unlink()
    index = ["# Curated Links", "", "One page per month, newest first. Built from `catalog/links.csv`.", ""]
    for month in sorted(months, reverse=True):
        rs = sorted(months[month], key=lambda r: (r["first_seen"], r["id"]), reverse=True)
        body = [f"# Links — {month}", "", f"{len(rs)} links, newest first.", ""]
        body += [line(r) for r in rs]
        (OUT / f"{month}.md").write_text("\n".join(body) + "\n", encoding="utf-8")
        index.append(f"- [{month}]({month}.md) — {len(rs)} links")
    (OUT / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"{len(rows)} links across {len(months)} months -> links/")


if __name__ == "__main__":
    main()
