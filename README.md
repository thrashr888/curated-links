# Curated Links

Links worth keeping — tools, repositories, threads, papers — one line each,
collected over months and published three ways from one catalog:

| What | Where | For |
| --- | --- | --- |
| The catalog | [`catalog/links.csv`](catalog/links.csv) | the source of truth: one row per link |
| A JSON Feed | [`feed/feed.json`](feed/feed.json) | feed readers; newest first |
| An OKF bundle | [`sources/`](sources/) | Alchemy, or any reader of the [Open Knowledge Format](https://github.com/inkeep/open-knowledge) |

Each link is one concept file under `sources/`: a web URL with its title,
cover image, and tags, and a sync identity derived from the URL so a
regeneration never turns an old link into a new one. Alchemy keeps a
checkout of this repo and binds its "Curated Links" notebook to it, so a
new link here is a new source there on the next pull. The bundle ships no
`index.md` or `log.md` on purpose: a reader writes its own beside these.

## Adding links

Links arrive as exports from a Slack channel where they were first posted.
An export goes in `raw/` (ignored by git — it carries workspace permalinks
that never leave this machine), then:

```bash
scripts/import_slack_export.py raw/<export>.csv   # fold into the catalog
scripts/build_feed.py                              # feed/feed.json
scripts/build_sources.py                           # sources/<id>-<slug>.md
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
