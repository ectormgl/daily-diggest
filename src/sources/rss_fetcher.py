import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
import requests
from dateutil import parser as dateparser

REQUEST_TIMEOUT = 10
MAX_WORKERS = 10
USER_AGENT = "daily-diggest/1.0 (+https://github.com/ectormgl/daily-diggest)"


def fetch_feed(url: str, name: str, priority: bool) -> list[dict]:
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8"},
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        articles = []
        for entry in feed.get("entries", []):
            title = entry.get("title", "").strip()
            if not title:
                continue
            published_raw = entry.get("published") or entry.get("updated") or ""
            published_dt = None
            if published_raw:
                try:
                    published_dt = dateparser.parse(published_raw)
                except Exception:
                    pass
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
    except Exception as e:
        print(f"[rss_fetcher] Failed to fetch {url}: {e}", file=sys.stderr)
        return []


def fetch_all_feeds(sources: list[dict]) -> list[dict]:
    all_articles = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(fetch_feed, s["url"], s["name"], s.get("priority", False))
            for s in sources
        ]
        for future in as_completed(futures):
            all_articles.extend(future.result())
    return all_articles
