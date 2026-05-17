CREATE TABLE IF NOT EXISTS articles (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  news_outlet   TEXT NOT NULL,
  country       TEXT NOT NULL,
  title         TEXT NOT NULL,
  link          TEXT NOT NULL UNIQUE,
  rss_summary   TEXT,
  ai_summary    TEXT,
  ai_tags       TEXT,                       -- JSON array stored as string
  published_at  TEXT,                       -- ISO-8601
  fetched_at    TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_articles_pub
  ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_country_pub
  ON articles(country, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_outlet_pub
  ON articles(news_outlet, published_at DESC);

CREATE TABLE IF NOT EXISTS fetch_runs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at    TEXT DEFAULT CURRENT_TIMESTAMP,
  finished_at   TEXT,
  outlets_ok    INTEGER DEFAULT 0,
  outlets_fail  INTEGER DEFAULT 0,
  rows_added    INTEGER DEFAULT 0,
  notes         TEXT
);