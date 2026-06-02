import sys
import requests

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def search_query(query: str, api_key: str | None, max_results: int = 10) -> list[dict]:
    if not api_key:
        return []
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": max_results, "freshness": "pd"}  # pd = past day
    try:
        response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return []
        results = response.json().get("web", {}).get("results", [])
        articles = []
        for item in results:
            title = item.get("title", "").strip()
            if not title:
                continue
            articles.append({
                "title": title,
                "url": item.get("url", ""),
                "summary": item.get("description", "")[:500],
                "source": f"Brave Search: {query}",
                "source_type": "web_search",
                "priority": False,
                "published_at": None,
                "engagement": 0,
            })
        return articles
    except Exception as e:
        print(f"[brave_search] Query '{query}' failed: {e}", file=sys.stderr)
        return []


def fetch_all_searches(queries: list[str], api_key: str | None) -> list[dict]:
    all_articles = []
    for query in queries:
        articles = search_query(query, api_key)
        all_articles.extend(articles)
    return all_articles
