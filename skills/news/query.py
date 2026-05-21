"""Query the news database. Read-only. Returns JSON to stdout."""
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

def main():
    load_dotenv(os.path.expanduser("~/.config/news-claw/.env"))
    db_path = os.environ["NEWS_DB_PATH"]

    p = argparse.ArgumentParser()
    p.add_argument("--country", help="US, India, Canada")
    p.add_argument("--outlet",  help="substring match, case-insensitive")
    p.add_argument("--topic",   help="substring match against ai_tags")
    p.add_argument("--hours",   type=int, default=12)
    p.add_argument("--limit",   type=int, default=15)
    args = p.parse_args()

    since = (datetime.now(timezone.utc) - timedelta(hours=args.hours)).isoformat()

    sql = ["SELECT news_outlet, country, title, link, ai_summary, ai_tags, published_at",
           "FROM articles",
           "WHERE COALESCE(published_at, fetched_at) >= ?"]
    params = [since]
    if args.country:
        sql.append("AND country = ?"); params.append(args.country)
    if args.outlet:
        sql.append("AND LOWER(news_outlet) LIKE ?"); params.append(f"%{args.outlet.lower()}%")
    if args.topic:
        sql.append("AND LOWER(ai_tags) LIKE ?"); params.append(f"%{args.topic.lower()}%")
    sql.append("ORDER BY COALESCE(published_at, fetched_at) DESC")
    sql.append("LIMIT ?"); params.append(args.limit)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(" ".join(sql), params).fetchall()]
    for r in rows:
        try:
            r["ai_tags"] = json.loads(r.get("ai_tags") or "[]")
        except Exception:
            r["ai_tags"] = []
    json.dump({"count": len(rows), "articles": rows}, sys.stdout, ensure_ascii=False)

if __name__ == "__main__":
    main()