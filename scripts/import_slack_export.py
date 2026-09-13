#!/usr/bin/env python3
"""Fold a Slack links export into the public catalog.

The export (Slack's conversations.searchLinks, via the catalog script that
produced it) carries workspace permalinks, channel ids, and Slack titles.
None of that leaves this script: the catalog keeps only what describes the
link itself. Rows are keyed by normalized URL; a re-import updates a row's
metadata and keeps its first-seen date.

    scripts/import_slack_export.py raw/slack-links-catalog-2026-09-10.csv
"""
import csv
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "links.csv"
FIELDS = [
    "id",
    "url",
    "title",
    "domain",
    "category",
    "resource_type",
    "topics",
    "author",
    "github_repository",
    "image",
    "icon",
    "first_seen",
    "last_seen",
]
# Rows that describe the export's own plumbing, and links that only resolve
# inside a workplace network — neither is a link worth sharing.
SKIP_DOMAINS = {"slack.com", "github.ibm.com", "w3.ibm.com"}


def canonical(url: str) -> str:
    """One row per page: the export lists the same repo as http:// and
    https://, and a trailing slash or a mobile host is not a different link."""
    p = urlparse(url)
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host in ("mobile.twitter.com", "twitter.com"):
        host = "x.com"
    path = p.path.rstrip("/") or "/"
    query = f"?{p.query}" if p.query and host not in ("x.com", "github.com") else ""
    return f"https://{host}{path}{query}"


def fallback_title(url: str) -> str:
    p = urlparse(url)
    path = p.path.rstrip("/")
    return f"{p.netloc}{path}" if path else p.netloc


def load_catalog() -> dict[str, dict]:
    if not CATALOG.exists():
        return {}
    with CATALOG.open(encoding="utf-8") as f:
        return {row["url"]: row for row in csv.DictReader(f)}


def save_catalog(rows: dict[str, dict]) -> None:
    ordered = sorted(rows.values(), key=lambda r: (r["first_seen"], r["url"]))
    for n, row in enumerate(ordered, 1):
        row["id"] = f"L{n:05d}"
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(ordered)


def main(path: str) -> None:
    catalog = load_catalog()
    added = updated = skipped = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            url = canonical(raw["normalized_url"].strip() or raw["url"].strip())
            domain = raw["domain"].strip().lower()
            if not url.startswith("http") or any(domain.endswith(d) for d in SKIP_DOMAINS):
                skipped += 1
                continue
            row = {
                "id": "",
                "url": url,
                "title": raw["title"].strip() or fallback_title(url),
                "domain": domain,
                "category": raw["category"].strip(),
                "resource_type": raw["resource_type"].strip(),
                "topics": raw["topics"].strip(),
                "author": raw["url_author_or_owner"].strip(),
                "github_repository": raw["github_repository"].strip(),
                "image": raw["thumbnail_url"].strip(),
                "icon": raw["icon_url"].strip(),
                "first_seen": raw["first_shared_at_utc"].strip()[:19] + "Z",
                "last_seen": raw["last_shared_at_utc"].strip()[:19] + "Z",
            }
            if url in catalog:
                old = catalog[url]
                row["first_seen"] = min(old["first_seen"], row["first_seen"])
                row["last_seen"] = max(old["last_seen"], row["last_seen"])
                if old != {**old, **row}:
                    updated += 1
                catalog[url] = {**old, **row}
            else:
                catalog[url] = row
                added += 1
    save_catalog(catalog)
    print(f"{added} added, {updated} updated, {skipped} skipped; catalog holds {len(catalog)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
