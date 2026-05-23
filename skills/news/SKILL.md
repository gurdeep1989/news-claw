---
name: news
description: |
  Query the user's personal news database. Use this whenever the user asks
  for "news", "headlines", "what's happening", "a digest", or mentions
  countries/outlets/topics. Returns JSON of articles with title, link,
  AI summary, tags, outlet, country, and published time.
---

# News skill

## When to use
Any user request for news, headlines, briefings, or digests.

## How to call
Run this command and parse stdout JSON:

```bash
/Users/YOURNAME/code/news-claw/.venv/bin/python \
  /Users/YOURNAME/code/news-claw/skills/news/query.py \
  [--country US|India|Canada] \
  [--outlet <name substring>] \
  [--topic <tag substring>] \
  [--hours N] \
  [--limit N]
```

Defaults: `--hours 12 --limit 15`.

## How to respond to the user
1. Call the skill with appropriate filters parsed from the user's request.
2. Write a **digest** in this fixed format:
   - **Overview** — 3 sentences summarizing the main themes across articles.
   - **Headlines** — 5 bullet points, each: `**Outlet** — Title ([link](url))`.
3. If the user asked about a specific country/outlet/topic, narrow filters first.
4. If zero articles returned, say so plainly and suggest widening the time window.