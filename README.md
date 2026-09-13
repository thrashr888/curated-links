# Curated Links

Links worth keeping — tools, repositories, threads, papers — one line each,
collected over months and published three ways from one catalog:

| What | Where | For |
| --- | --- | --- |
| The catalog | [`catalog/links.csv`](catalog/links.csv) | the source of truth: one row per link |
| A JSON Feed | [`feed/feed.json`](feed/feed.json) | feed readers; newest first |
| Monthly digests | [`links/`](links/) | reading, and apps that ingest a folder |

Alchemy reads the digests as a git source (`links/` on `main`) and the
feed as a feed source, so a new link here shows up there on its next sync.

## Adding links

Links arrive as exports from a Slack channel where they were first posted.
An export goes in `raw/` (ignored by git — it carries workspace permalinks
that never leave this machine), then:

```bash
scripts/import_slack_export.py raw/<export>.csv   # fold into the catalog
scripts/build_feed.py                              # feed/feed.json
scripts/build_links.py                             # links/<month>.md
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
  "content_text": "Category · Resource type · Topic; Topic · by author",
  "date_published": "2026-09-10T16:20:23Z",
  "tags": ["Category", "Topic", "Topic"],
  "authors": [{ "name": "author" }],
  "image": "https://…/og-image.jpg"
}
```
