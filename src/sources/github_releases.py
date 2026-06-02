import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dateutil import parser as dateparser

GITHUB_API = "https://api.github.com"
MAX_WORKERS = 8


def fetch_repo_releases(owner: str, repo: str, token: str | None, max_releases: int = 3) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/releases?per_page={max_releases}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        articles = []
        for release in response.json():
            tag = release.get("tag_name", "")
            release_name = release.get("name") or tag
            published_raw = release.get("published_at", "")
            published_dt = None
            if published_raw:
                try:
                    published_dt = dateparser.parse(published_raw)
                except Exception:
                    pass
            engagement = release.get("reactions", {}).get("total_count", 0)
            articles.append({
                "title": f"{owner}/{repo} released {release_name}",
                "url": release.get("html_url", ""),
                "summary": (release.get("body") or "")[:500],
                "source": f"{owner}/{repo}",
                "source_type": "github_release",
                "priority": False,
                "published_at": published_dt,
                "engagement": engagement,
            })
        return articles
    except Exception as e:
        print(f"[github_releases] Failed to fetch {owner}/{repo}: {e}", file=sys.stderr)
        return []


def fetch_all_releases(repos: list[dict], token: str | None) -> list[dict]:
    all_articles = []
    total = len(repos)
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(fetch_repo_releases, r["owner"], r["repo"], token)
            for r in repos
        ]
        for future in as_completed(futures):
            all_articles.extend(future.result())
            completed += 1
            if completed % 5 == 0 or completed == total:
                print(f"[github_releases]   progress {completed}/{total} repos ({time.time()-t0:.1f}s)", flush=True)
    return all_articles
