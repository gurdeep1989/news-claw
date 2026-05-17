import logging
import os
import sys
from datetime import datetime, timezone

import feedparser
from dateutil import parser as dtparser
from dotenv import load_dotenv

from fetcher.db import connect, insert_article, link_exists, fetch_run
from fetcher.feeds import FEEDS
from fetcher.llm import summarize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("fetcher")

def parse_date(entry) -> str | None:
    for key in ("published", "updated"):
        val = entry.get(key)
        if val:
            try:
                return dtparser.parse(val).astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    return None

def fetch_one_feed(conn, feed_meta, max_items: int) -> tuple[int, str | None]:
    """Returns (rows_added, error_or_None)."""
    parsed = feedparser.parse(feed_meta["url"])
    if parsed.bozo and not parsed.entries:
        return 0, f"parse error: {parsed.bozo_exception}"

    added = 0
    for entry in parsed.entries[:max_items]:
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            continue
        if link_exists(conn, link):
            continue

        rss_summary = entry.get("summary") or entry.get("description") or ""
        ai = summarize(title, rss_summary)

        art = {
            "news_outlet": feed_meta["news_outlet"],
            "country": feed_meta["country"],
            "title": title.strip(),
            "link": link,
            "rss_summary": rss_summary[:2000],
            "ai_summary": ai.get("summary") or None,
            "ai_tags": ai.get("tags") or [],
            "published_at": parse_date(entry),
        }
        if insert_article(conn, art):
            added += 1
    return added, None

def main():
    load_dotenv(os.path.expanduser("~/.config/news-claw/.env"))
    db_path = os.environ["NEWS_DB_PATH"]
    max_items = int(os.environ.get("MAX_ITEMS_PER_FEED", "20"))

    conn = connect(db_path)
    with fetch_run(conn) as stats:
        for feed in FEEDS:
            log.info("Fetching %s", feed["news_outlet"])
            try:
                added, err = fetch_one_feed(conn, feed, max_items)
                if err:
                    stats["outlets_fail"] += 1
                    log.warning("%s failed: %s", feed["news_outlet"], err)
                else:
                    stats["outlets_ok"] += 1
                    stats["rows_added"] += added
                    log.info("%s: +%d rows", feed["news_outlet"], added)
                conn.commit()
            except Exception as e:
                stats["outlets_fail"] += 1
                log.exception("%s crashed: %s", feed["news_outlet"], e)
        log.info("Done. ok=%d fail=%d added=%d",
                 stats["outlets_ok"], stats["outlets_fail"], stats["rows_added"])

if __name__ == "__main__":
    sys.exit(main())