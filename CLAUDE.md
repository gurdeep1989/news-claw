# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**news-claw** is a news aggregator that fetches RSS feeds from US/India/Canada outlets every 2 hours, enriches each article with a locally-run LLM summary and topic tags, persists everything to a local SQLite database, and exposes a CLI skill for querying the stored news.

It runs as a macOS LaunchAgent background service.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

The real env file lives at `~/.config/news-claw/.env` (not in the project root). Required variables:

| Variable | Purpose |
|---|---|
| `NEWS_DB_PATH` | Absolute path to the SQLite file (e.g. `~/.local/share/news-claw/news.db`) |
| `MAX_ITEMS_PER_FEED` | Optional, default `20` |

LLM summarization runs locally via **Ollama** (`llama3.2:3b`). No API key needed.

### Ollama setup (one-time)

```bash
# Install Ollama
brew install ollama

# Pull the model (~2GB download)
ollama pull llama3.2:3b

# Verify it's available
ollama list
```

### Running Ollama

Ollama must be running before the fetcher starts:

```bash
ollama serve
```

If you see `address already in use`, Ollama is already running — nothing to do. To check:

```bash
ollama ps
```

## Running

```bash
# Run the fetcher once manually
python -m fetcher.fetch

# Query the database (all args optional)
python skills/news/query.py --country US --topic politics --hours 24 --limit 10
python skills/news/query.py --outlet "NY Times"
```

## Architecture

```
fetcher/
  feeds.py    # Static list of FEEDS dicts: {news_outlet, url, country}
  fetch.py    # Entry point: iterates FEEDS, calls llm.summarize, writes via db
  db.py       # sqlite3 helpers: connect (WAL mode), insert_article, link_exists, fetch_run ctx manager
  llm.py      # Calls local Ollama (llama3.2:3b) to produce {summary, tags} per article

sql/
  001_init.sql  # Applied by db.connect — creates articles and fetch_runs tables

skills/news/
  query.py    # Read-only CLI: filters by --country/--outlet/--topic/--hours/--limit, prints JSON

deploy/
  com.you.newsbot-fetcher.plist  # LaunchAgent: runs python -m fetcher.fetch every 2 hours
  bootstrap.sh                   # One-time machine setup
```

### Data flow

1. `fetch.py:main()` loads env, calls `db.connect(db_path)` which bootstraps the schema from `sql/001_init.sql`
2. For each feed in `feeds.FEEDS`, `fetch_one_feed` parses the RSS, skips seen links (`link_exists`), calls `llm.summarize(title, rss_summary)`
3. `db.insert_article` writes the row; deduplication is enforced by a `UNIQUE` constraint on `link`
4. The `fetch_run` context manager records start/finish/stats in the `fetch_runs` table
5. `skills/news/query.py` opens the same DB read-only and returns JSON to stdout

### Database schema notes

- `ai_tags` is stored as a JSON string (e.g. `'["politics","world"]'`) — deserialize with `json.loads` when reading
- Ordering uses `COALESCE(published_at, fetched_at)` because some feeds omit publish dates
- Three indexes on `articles`: by `published_at`, by `(country, published_at)`, by `(news_outlet, published_at)`

### LaunchAgent deployment

```bash
cp deploy/com.you.newsbot-fetcher.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.you.newsbot-fetcher.plist

# Logs
tail -f data/fetcher.out.log
tail -f data/fetcher.err.log

# Stop / disable
launchctl unload ~/Library/LaunchAgents/com.you.newsbot-fetcher.plist
```