import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")     # safe concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def link_exists(conn: sqlite3.Connection, link: str) -> bool:
    row = conn.execute("SELECT 1 FROM articles WHERE link = ?", (link,)).fetchone()
    return row is not None

def insert_article(conn: sqlite3.Connection, art: dict) -> bool:
    """Insert one article. Returns True if inserted, False if duplicate."""
    try:
        conn.execute(
            """INSERT INTO articles
               (news_outlet, country, title, link, rss_summary,
                ai_summary, ai_tags, published_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                art["news_outlet"],
                art["country"],
                art["title"],
                art["link"],
                art.get("rss_summary"),
                art.get("ai_summary"),
                json.dumps(art.get("ai_tags") or []),
                art.get("published_at"),
            ),
        )
        return True
    except sqlite3.IntegrityError:
        return False  # UNIQUE violation on link

@contextmanager
def fetch_run(conn: sqlite3.Connection):
    cur = conn.execute("INSERT INTO fetch_runs DEFAULT VALUES")
    run_id = cur.lastrowid
    stats = {"outlets_ok": 0, "outlets_fail": 0, "rows_added": 0, "notes": ""}
    try:
        yield stats
    finally:
        conn.execute(
            """UPDATE fetch_runs
               SET finished_at = CURRENT_TIMESTAMP,
                   outlets_ok = ?, outlets_fail = ?,
                   rows_added = ?, notes = ?
               WHERE id = ?""",
            (stats["outlets_ok"], stats["outlets_fail"],
             stats["rows_added"], stats["notes"], run_id),
        )
        conn.commit()