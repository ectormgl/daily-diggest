import feedparser
from datetime import datetime, timezone
from dateutil import parser as dateparser


def fetch_feed(url: str, name: str, priority: bool) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.get("entries", []):
            title = entry.get("title", "").strip()
            if not title:
                continue
            published_raw = entry.get("published") or entry.get("updated") or ""
            try:
                published_dt = dateparser.parse(published_raw)
            except Exception:
                published_dt = None
            articles.append({
                "title": title,
                "url": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500],
                "source": name,
                "source_type": "rss",
                "priority": priority,
                "published_at": published_dt,
                "engagement": 0,
            })
        return articles
    except Exception:
        return []


def fetch_all_feeds(sources: list[dict]) -> list[dict]:
    all_articles = []
    for source in sources:
        articles = fetch_feed(source["url"], source["name"], source.get("priority", False))
        all_articles.extend(articles)
    return all_articles
