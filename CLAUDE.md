# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**news-claw** is a news aggregator that fetches RSS/news feeds, persists articles to a local SQLite database, optionally processes them with an LLM, and exposes a Claude Code skill for querying the stored news.

It is designed to run as a macOS LaunchAgent background service.

## Development Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the project in editable mode (once pyproject.toml has dependencies)
pip install -e .

# Copy and fill in environment variables
cp .env.example .env
```

## Running the Fetcher

```bash
# Run the fetcher directly
python -m fetcher.fetch
```

## Architecture

```
fetcher/        # Core Python package
  fetch.py      # Entry point — orchestrates the fetch pipeline
  feeds.py      # Feed definitions and configuration
  db.py         # SQLite connection, schema bootstrap, read/write helpers
  llm.py        # Claude API calls for enriching/summarising articles

sql/
  001_init.sql  # Schema definition applied on first run

skills/news/
  query.py      # Claude Code skill — queries the local DB for the user
  SKILL.md      # Skill manifest

deploy/
  bootstrap.sh                        # One-time machine setup script
  com.you.newsbot-fetcher.plist       # macOS LaunchAgent plist (runs fetcher on a schedule)

data/           # SQLite DB files live here (gitignored)
```

### Data Flow

1. `fetch.py` reads feed URLs from `feeds.py`
2. Fetches new articles and passes them to `llm.py` for optional enrichment
3. `db.py` applies `sql/001_init.sql` on startup and persists articles
4. The Claude Code skill in `skills/news/query.py` reads from the same DB to answer user questions

### Deployment (macOS LaunchAgent)

Load the plist to run the fetcher automatically:

```bash
cp deploy/com.you.newsbot-fetcher.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.you.newsbot-fetcher.plist
```

## Environment Variables

See `.env.example` for required variables (e.g. `ANTHROPIC_API_KEY` for LLM features, DB path).
