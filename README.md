# Curated Links

Links worth keeping — tools, repositories, threads, papers — one line each,
collected over months and published three ways from one catalog:

| What | Where | For |
| --- | --- | --- |
| The catalog | [`catalog/links.csv`](catalog/links.csv) | the source of truth: one row per link |
| A JSON Feed | [`feed/feed.json`](feed/feed.json) | feed readers; newest first |
| Resolved posts | [`catalog/resolved.json`](catalog/resolved.json) | what each post on X says and points at |

Alchemy's "Curated Links" notebook reads the feed: every item becomes a
source it captures itself — the page behind the link, with its cover image
and the item's tags — and new items land on the hourly check.

A post on X is usually a pointer, so the feed favors the destination: when
a post links out to a page, the item *is* that page (the post's URL rides
in `external_url` and its text in the body). A post that stands alone keeps
its own URL and its text.

## Adding links

Links arrive as exports from a Slack channel where they were first posted.
An export goes in `raw/` (ignored by git — it carries workspace permalinks
that never leave this machine), then:

```bash
scripts/import_slack_export.py raw/<export>.csv   # fold into the catalog
scripts/resolve_links.py                           # what new posts point at
scripts/build_feed.py                              # feed/feed.json
```

The importer keeps only what describes the link — URL, title, domain,
category, topics, author, images, first/last seen — and drops anything
that only resolves inside a workplace network. Rows are keyed by URL, so
re-importing updates metadata and keeps the first-seen date.

Commit the catalog and the built files together; CI checks that the built
files match the catalog.

## Shape of a feed item

```json
{
  "id": "L01427",
  "url": "https://example.com/post",
  "title": "…",
  "content_text": "What the post said …\n\n— @author\n\nCategory · Resource type · Topic",
  "external_url": "https://x.com/author/status/…",
  "date_published": "2026-09-10T16:20:23Z",
  "tags": ["Category", "Topic", "Topic"],
  "authors": [{ "name": "author" }],
  "image": "https://…/og-image.jpg"
}

`external_url` is present only when the item is the page a post pointed at.
```
