# Daily Tech News Digest — GitHub Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a four-layer tech news aggregator that runs daily via GitHub Actions, scoring and deduplicating articles from RSS, GitHub Releases, Brave Search (and optionally Twitter/X), then delivering a formatted digest to Discord, Telegram, and WhatsApp via Evolution API.

**Architecture:** A Python orchestrator (`src/main.py`) calls each source fetcher in sequence, merges results into a unified article list, runs deduplication (fuzzy title similarity) and quality scoring, then dispatches the ranked digest to configured delivery channels. All secrets (API keys, webhook URLs) live in GitHub Actions Secrets and are injected as environment variables at runtime.

**Tech Stack:** Python 3.11, `feedparser` (RSS), `requests` (HTTP), `difflib` (dedup), GitHub Actions (cron + secrets), Discord Webhooks, Telegram Bot API, Evolution API (WhatsApp), Brave Search API, GitHub REST API (releases).

---

## File Structure

```
.github/
  workflows/
    daily-digest.yml          # Scheduled cron + manual trigger
config/
  sources.json                # All RSS feeds, GitHub repos, search queries
src/
  sources/
    rss_fetcher.py            # Fetch + parse RSS/Atom feeds
    github_releases.py        # Fetch latest releases from GitHub repos
    brave_search.py           # Brave Search API queries
  processing/
    deduplicator.py           # Fuzzy title deduplication
    scorer.py                 # Quality scoring algorithm
  delivery/
    discord.py                # Discord webhook delivery
    telegram.py               # Telegram Bot API delivery
    whatsapp.py               # WhatsApp delivery via Evolution API
  main.py                     # Orchestrator — wires all pieces together
tests/
  test_rss_fetcher.py
  test_deduplicator.py
  test_scorer.py
  test_github_releases.py
  test_brave_search.py
requirements.txt
```

---

## Task 1: Initialize Repo + Requirements

**Files:**
- Create: `requirements.txt`
- Create: `config/sources.json`

- [ ] **Step 1: Create `requirements.txt`**

```text
feedparser==6.0.11
requests==2.32.3
python-dateutil==2.9.0
pytest==8.3.4
```

- [ ] **Step 2: Create `config/sources.json`**

```json
{
  "rss_feeds": [
    {"url": "https://openai.com/blog/rss.xml", "name": "OpenAI Blog", "priority": true},
    {"url": "https://news.ycombinator.com/rss", "name": "Hacker News", "priority": true},
    {"url": "https://www.technologyreview.com/feed/", "name": "MIT Tech Review", "priority": true},
    {"url": "https://techcrunch.com/feed/", "name": "TechCrunch", "priority": false},
    {"url": "https://www.theverge.com/rss/index.xml", "name": "The Verge", "priority": false},
    {"url": "https://venturebeat.com/feed/", "name": "VentureBeat", "priority": false},
    {"url": "https://www.wired.com/feed/rss", "name": "Wired", "priority": false},
    {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "name": "Ars Technica", "priority": false},
    {"url": "https://www.infoq.com/feed/", "name": "InfoQ", "priority": false},
    {"url": "https://blogs.microsoft.com/feed/", "name": "Microsoft Blog", "priority": true},
    {"url": "https://blog.google/rss/", "name": "Google Blog", "priority": true},
    {"url": "https://engineering.fb.com/feed/", "name": "Meta Engineering", "priority": false},
    {"url": "https://aws.amazon.com/blogs/aws/feed/", "name": "AWS Blog", "priority": false},
    {"url": "https://cloud.google.com/blog/rss/", "name": "Google Cloud Blog", "priority": false},
    {"url": "https://azure.microsoft.com/en-us/blog/feed/", "name": "Azure Blog", "priority": false},
    {"url": "https://deepmind.google/blog/rss.xml", "name": "DeepMind Blog", "priority": true},
    {"url": "https://huggingface.co/blog/feed.xml", "name": "Hugging Face Blog", "priority": true},
    {"url": "https://lilianweng.github.io/index.xml", "name": "Lilian Weng Blog", "priority": true},
    {"url": "https://karpathy.github.io/feed.xml", "name": "Karpathy Blog", "priority": true},
    {"url": "https://sebastianraschka.com/rss_feed.xml", "name": "Sebastian Raschka", "priority": false},
    {"url": "https://newsletter.theaiedge.io/feed", "name": "AI Edge Newsletter", "priority": false},
    {"url": "https://thealgorithmicbridge.substack.com/feed", "name": "Algorithmic Bridge", "priority": false},
    {"url": "https://blog.langchain.dev/rss/", "name": "LangChain Blog", "priority": true},
    {"url": "https://www.anthropic.com/rss.xml", "name": "Anthropic Blog", "priority": true},
    {"url": "https://cohere.com/blog/rss", "name": "Cohere Blog", "priority": false},
    {"url": "https://mistral.ai/news/rss", "name": "Mistral Blog", "priority": true},
    {"url": "https://www.databricks.com/blog/feed", "name": "Databricks Blog", "priority": false},
    {"url": "https://pytorch.org/blog/feed.xml", "name": "PyTorch Blog", "priority": false},
    {"url": "https://jax.readthedocs.io/en/latest/_static/rss.xml", "name": "JAX Docs", "priority": false},
    {"url": "https://paperswithcode.com/latest.rss", "name": "Papers With Code", "priority": true},
    {"url": "https://arxiv.org/rss/cs.AI", "name": "arXiv AI", "priority": true},
    {"url": "https://arxiv.org/rss/cs.LG", "name": "arXiv ML", "priority": true},
    {"url": "https://arxiv.org/rss/cs.CL", "name": "arXiv NLP", "priority": true},
    {"url": "https://www.reddit.com/r/MachineLearning/.rss", "name": "r/MachineLearning", "priority": false},
    {"url": "https://www.reddit.com/r/LocalLLaMA/.rss", "name": "r/LocalLLaMA", "priority": false},
    {"url": "https://www.reddit.com/r/artificial/.rss", "name": "r/artificial", "priority": false},
    {"url": "https://changelog.com/news/feed", "name": "Changelog", "priority": false},
    {"url": "https://softwareengineeringdaily.com/feed/", "name": "SE Daily", "priority": false},
    {"url": "https://twimlai.com/feed/", "name": "TWIML AI Podcast", "priority": false},
    {"url": "https://lexfridman.com/feed/podcast/", "name": "Lex Fridman", "priority": false},
    {"url": "https://feeds.simplecast.com/54nAGcIl", "name": "Practical AI", "priority": false},
    {"url": "https://stability.ai/news?format=rss", "name": "Stability AI", "priority": false},
    {"url": "https://replicate.com/changelog/rss", "name": "Replicate Changelog", "priority": false},
    {"url": "https://modal.com/blog/feed", "name": "Modal Blog", "priority": false},
    {"url": "https://scale.com/blog/feed", "name": "Scale AI Blog", "priority": false},
    {"url": "https://research.google/blog/rss/", "name": "Google Research", "priority": true}
  ],
  "github_repos": [
    {"owner": "vllm-project", "repo": "vllm"},
    {"owner": "langchain-ai", "repo": "langchain"},
    {"owner": "ollama", "repo": "ollama"},
    {"owner": "mudler", "repo": "LocalAI"},
    {"owner": "langgenius", "repo": "dify"},
    {"owner": "microsoft", "repo": "autogen"},
    {"owner": "microsoft", "repo": "promptflow"},
    {"owner": "openai", "repo": "openai-python"},
    {"owner": "anthropics", "repo": "anthropic-sdk-python"},
    {"owner": "huggingface", "repo": "transformers"},
    {"owner": "ggerganov", "repo": "llama.cpp"},
    {"owner": "run-llama", "repo": "llama_index"},
    {"owner": "chroma-core", "repo": "chroma"},
    {"owner": "milvus-io", "repo": "milvus"},
    {"owner": "BerriAI", "repo": "litellm"},
    {"owner": "commaai", "repo": "openpilot"},
    {"owner": "unslothai", "repo": "unsloth"},
    {"owner": "pytorch", "repo": "pytorch"},
    {"owner": "openai", "repo": "whisper"}
  ],
  "search_queries": [
    "AI large language model release 2024",
    "open source AI tool launch",
    "machine learning research breakthrough",
    "generative AI product announcement"
  ]
}
```

- [ ] **Step 3: Init git repo**

```bash
git init
git add requirements.txt config/sources.json
git commit -m "chore: init repo with sources config and requirements"
```

---

## Task 2: RSS Fetcher

**Files:**
- Create: `src/__init__.py` (empty)
- Create: `src/sources/__init__.py` (empty)
- Create: `src/sources/rss_fetcher.py`
- Create: `tests/test_rss_fetcher.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_rss_fetcher.py
from unittest.mock import patch, MagicMock
from src.sources.rss_fetcher import fetch_feed, fetch_all_feeds

MOCK_FEED = {
    "entries": [
        {
            "title": "GPT-5 Released Today",
            "link": "https://openai.com/blog/gpt5",
            "summary": "OpenAI announces GPT-5 with improved reasoning.",
            "published": "Mon, 02 Jun 2026 09:00:00 +0000",
        }
    ]
}

def test_fetch_feed_returns_articles():
    with patch("feedparser.parse", return_value=MOCK_FEED):
        articles = fetch_feed("https://openai.com/blog/rss.xml", "OpenAI Blog", priority=True)
    assert len(articles) == 1
    assert articles[0]["title"] == "GPT-5 Released Today"
    assert articles[0]["source"] == "OpenAI Blog"
    assert articles[0]["priority"] is True
    assert articles[0]["url"] == "https://openai.com/blog/gpt5"


def test_fetch_feed_empty_on_exception():
    with patch("feedparser.parse", side_effect=Exception("timeout")):
        articles = fetch_feed("https://bad.url/feed", "Bad Source", priority=False)
    assert articles == []


def test_fetch_feed_skips_entries_without_title():
    feed = {"entries": [{"link": "https://example.com", "summary": "no title here"}]}
    with patch("feedparser.parse", return_value=feed):
        articles = fetch_feed("https://example.com/rss", "Example", priority=False)
    assert articles == []


def test_fetch_all_feeds_aggregates():
    sources = [
        {"url": "https://openai.com/rss", "name": "OpenAI", "priority": True},
        {"url": "https://hacker.news/rss", "name": "HN", "priority": False},
    ]
    with patch("src.sources.rss_fetcher.fetch_feed") as mock_fetch:
        mock_fetch.side_effect = [
            [{"title": "A", "source": "OpenAI", "priority": True}],
            [{"title": "B", "source": "HN", "priority": False}],
        ]
        result = fetch_all_feeds(sources)
    assert len(result) == 2
    assert mock_fetch.call_count == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_rss_fetcher.py -v
```
Expected: `ModuleNotFoundError` or `ImportError` — `src.sources.rss_fetcher` not found.

- [ ] **Step 3: Create `src/__init__.py` and `src/sources/__init__.py`**

Both files are empty. Create them:

```bash
mkdir -p src/sources && touch src/__init__.py src/sources/__init__.py
```

- [ ] **Step 4: Implement `src/sources/rss_fetcher.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_rss_fetcher.py -v
```
Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/__init__.py src/sources/__init__.py src/sources/rss_fetcher.py tests/test_rss_fetcher.py
git commit -m "feat: RSS feed fetcher with tests"
```

---

## Task 3: GitHub Releases Fetcher

**Files:**
- Create: `src/sources/github_releases.py`
- Create: `tests/test_github_releases.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_github_releases.py
from unittest.mock import patch, MagicMock
from src.sources.github_releases import fetch_repo_releases, fetch_all_releases

MOCK_RELEASE = {
    "tag_name": "v0.5.0",
    "name": "vLLM v0.5.0",
    "html_url": "https://github.com/vllm-project/vllm/releases/tag/v0.5.0",
    "body": "Major performance improvements to PagedAttention.",
    "published_at": "2026-06-01T10:00:00Z",
    "reactions": {"total_count": 42},
}


def test_fetch_repo_releases_returns_article():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [MOCK_RELEASE]
    with patch("requests.get", return_value=mock_response):
        articles = fetch_repo_releases("vllm-project", "vllm", token=None)
    assert len(articles) == 1
    assert articles[0]["title"] == "vllm-project/vllm released vLLM v0.5.0"
    assert articles[0]["source_type"] == "github_release"
    assert articles[0]["engagement"] == 42


def test_fetch_repo_releases_returns_empty_on_404():
    mock_response = MagicMock()
    mock_response.status_code = 404
    with patch("requests.get", return_value=mock_response):
        articles = fetch_repo_releases("bad", "repo", token=None)
    assert articles == []


def test_fetch_repo_releases_returns_empty_on_exception():
    with patch("requests.get", side_effect=Exception("network error")):
        articles = fetch_repo_releases("vllm-project", "vllm", token=None)
    assert articles == []


def test_fetch_all_releases_aggregates():
    repos = [
        {"owner": "vllm-project", "repo": "vllm"},
        {"owner": "langchain-ai", "repo": "langchain"},
    ]
    with patch("src.sources.github_releases.fetch_repo_releases") as mock_fetch:
        mock_fetch.side_effect = [
            [{"title": "vllm release", "source": "vllm-project/vllm"}],
            [{"title": "langchain release", "source": "langchain-ai/langchain"}],
        ]
        result = fetch_all_releases(repos, token=None)
    assert len(result) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_github_releases.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement `src/sources/github_releases.py`**

```python
import requests
from dateutil import parser as dateparser

GITHUB_API = "https://api.github.com"


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
            try:
                published_dt = dateparser.parse(published_raw)
            except Exception:
                published_dt = None
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
    except Exception:
        return []


def fetch_all_releases(repos: list[dict], token: str | None) -> list[dict]:
    all_articles = []
    for repo in repos:
        articles = fetch_repo_releases(repo["owner"], repo["repo"], token)
        all_articles.extend(articles)
    return all_articles
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_github_releases.py -v
```
Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/sources/github_releases.py tests/test_github_releases.py
git commit -m "feat: GitHub releases fetcher with tests"
```

---

## Task 4: Brave Search Fetcher

**Files:**
- Create: `src/sources/brave_search.py`
- Create: `tests/test_brave_search.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_brave_search.py
from unittest.mock import patch, MagicMock
from src.sources.brave_search import search_query, fetch_all_searches

MOCK_RESPONSE = {
    "web": {
        "results": [
            {
                "title": "Meta releases LLaMA 4",
                "url": "https://ai.meta.com/llama4",
                "description": "Meta announces LLaMA 4 with 70B parameters.",
                "age": "2 hours ago",
            }
        ]
    }
}


def test_search_query_returns_articles():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RESPONSE
    with patch("requests.get", return_value=mock_resp):
        articles = search_query("AI model release", api_key="fake-key")
    assert len(articles) == 1
    assert articles[0]["title"] == "Meta releases LLaMA 4"
    assert articles[0]["source_type"] == "web_search"


def test_search_query_empty_on_missing_api_key():
    articles = search_query("AI news", api_key=None)
    assert articles == []


def test_search_query_empty_on_non_200():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    with patch("requests.get", return_value=mock_resp):
        articles = search_query("AI news", api_key="bad-key")
    assert articles == []


def test_fetch_all_searches_aggregates():
    queries = ["query A", "query B"]
    with patch("src.sources.brave_search.search_query") as mock_search:
        mock_search.side_effect = [
            [{"title": "Result A"}],
            [{"title": "Result B"}],
        ]
        result = fetch_all_searches(queries, api_key="key")
    assert len(result) == 2
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_brave_search.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement `src/sources/brave_search.py`**

```python
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
    except Exception:
        return []


def fetch_all_searches(queries: list[str], api_key: str | None) -> list[dict]:
    all_articles = []
    for query in queries:
        articles = search_query(query, api_key)
        all_articles.extend(articles)
    return all_articles
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_brave_search.py -v
```
Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/sources/brave_search.py tests/test_brave_search.py
git commit -m "feat: Brave Search fetcher with tests"
```

---

## Task 5: Deduplicator

**Files:**
- Create: `src/processing/__init__.py` (empty)
- Create: `src/processing/deduplicator.py`
- Create: `tests/test_deduplicator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_deduplicator.py
from src.processing.deduplicator import deduplicate, title_similarity

def test_title_similarity_identical():
    assert title_similarity("GPT-5 Released Today", "GPT-5 Released Today") == 1.0


def test_title_similarity_different():
    score = title_similarity("Apple launches iPhone 17", "Microsoft releases Windows 12")
    assert score < 0.4


def test_title_similarity_near_duplicate():
    score = title_similarity(
        "OpenAI releases GPT-5 with improved reasoning",
        "OpenAI releases GPT-5 — improved reasoning capabilities",
    )
    assert score > 0.7


def test_deduplicate_removes_near_duplicate():
    articles = [
        {"title": "OpenAI releases GPT-5 with improved reasoning", "source": "TechCrunch", "source_type": "rss", "priority": False},
        {"title": "OpenAI releases GPT-5 — improved reasoning capabilities", "source": "The Verge", "source_type": "rss", "priority": False},
        {"title": "Apple launches M4 MacBook Pro", "source": "Wired", "source_type": "rss", "priority": False},
    ]
    result = deduplicate(articles, threshold=0.7)
    assert len(result) == 2
    titles = [a["title"] for a in result]
    assert "Apple launches M4 MacBook Pro" in titles


def test_deduplicate_keeps_multi_source_flag():
    articles = [
        {"title": "OpenAI GPT-5 announced", "source": "TechCrunch", "source_type": "rss", "priority": False},
        {"title": "OpenAI GPT-5 announced", "source": "The Verge", "source_type": "rss", "priority": False},
    ]
    result = deduplicate(articles, threshold=0.9)
    assert len(result) == 1
    assert result[0]["multi_source"] is True
    assert result[0]["source_count"] == 2


def test_deduplicate_unique_articles_unchanged():
    articles = [
        {"title": "Article A about AI", "source": "S1", "source_type": "rss", "priority": False},
        {"title": "Article B about robots", "source": "S2", "source_type": "rss", "priority": False},
        {"title": "Article C about quantum", "source": "S3", "source_type": "rss", "priority": False},
    ]
    result = deduplicate(articles, threshold=0.7)
    assert len(result) == 3
    for article in result:
        assert article["multi_source"] is False
        assert article["source_count"] == 1
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_deduplicator.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement `src/processing/deduplicator.py`**

```python
from difflib import SequenceMatcher


def title_similarity(a: str, b: str) -> float:
    a_norm = a.lower().strip()
    b_norm = b.lower().strip()
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def deduplicate(articles: list[dict], threshold: float = 0.75) -> list[dict]:
    groups: list[list[dict]] = []
    assigned = [False] * len(articles)

    for i, article in enumerate(articles):
        if assigned[i]:
            continue
        group = [article]
        assigned[i] = True
        for j in range(i + 1, len(articles)):
            if assigned[j]:
                continue
            if title_similarity(article["title"], articles[j]["title"]) >= threshold:
                group.append(articles[j])
                assigned[j] = True
        groups.append(group)

    result = []
    for group in groups:
        representative = group[0]
        source_count = len(group)
        sources = list({a["source"] for a in group})
        representative = {
            **representative,
            "multi_source": source_count > 1,
            "source_count": source_count,
            "all_sources": sources,
        }
        result.append(representative)

    return result
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_deduplicator.py -v
```
Expected: 6 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/processing/__init__.py src/processing/deduplicator.py tests/test_deduplicator.py
git commit -m "feat: fuzzy title deduplicator with tests"
```

---

## Task 6: Quality Scorer

**Files:**
- Create: `src/processing/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_scorer.py
from datetime import datetime, timezone, timedelta
from src.processing.scorer import score_article, sort_by_score

BASE_ARTICLE = {
    "title": "GPT-5 released",
    "priority": False,
    "multi_source": False,
    "source_count": 1,
    "published_at": None,
    "engagement": 0,
}


def test_priority_source_adds_3():
    article = {**BASE_ARTICLE, "priority": True}
    assert score_article(article) >= 3


def test_multi_source_adds_5():
    article = {**BASE_ARTICLE, "multi_source": True, "source_count": 3}
    assert score_article(article) >= 5


def test_recent_article_adds_2():
    recent = datetime.now(timezone.utc) - timedelta(hours=6)
    article = {**BASE_ARTICLE, "published_at": recent}
    assert score_article(article) >= 2


def test_old_article_no_recency_bonus():
    old = datetime.now(timezone.utc) - timedelta(days=3)
    article = {**BASE_ARTICLE, "published_at": old}
    assert score_article(article) == 0


def test_engagement_adds_1():
    article = {**BASE_ARTICLE, "engagement": 5}
    assert score_article(article) >= 1


def test_combined_score():
    recent = datetime.now(timezone.utc) - timedelta(hours=2)
    article = {
        "title": "Big AI news",
        "priority": True,
        "multi_source": True,
        "source_count": 2,
        "published_at": recent,
        "engagement": 10,
    }
    # priority(3) + multi_source(5) + recency(2) + engagement(1) = 11
    assert score_article(article) == 11


def test_sort_by_score_descending():
    articles = [
        {**BASE_ARTICLE, "title": "Low score"},
        {**BASE_ARTICLE, "title": "High score", "priority": True, "multi_source": True, "source_count": 2},
    ]
    sorted_articles = sort_by_score(articles)
    assert sorted_articles[0]["title"] == "High score"
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_scorer.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement `src/processing/scorer.py`**

```python
from datetime import datetime, timezone, timedelta

RECENCY_WINDOW_HOURS = 24


def score_article(article: dict) -> int:
    score = 0
    if article.get("priority"):
        score += 3
    if article.get("multi_source"):
        score += 5
    published_at = article.get("published_at")
    if published_at is not None:
        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age = now - published_at
        if age <= timedelta(hours=RECENCY_WINDOW_HOURS):
            score += 2
    if article.get("engagement", 0) > 0:
        score += 1
    return score


def sort_by_score(articles: list[dict]) -> list[dict]:
    return sorted(articles, key=score_article, reverse=True)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_scorer.py -v
```
Expected: 7 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/processing/scorer.py tests/test_scorer.py
git commit -m "feat: quality scorer with tests"
```

---

## Task 7: Discord Delivery

**Files:**
- Create: `src/delivery/__init__.py` (empty)
- Create: `src/delivery/discord.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_discord.py
from unittest.mock import patch, MagicMock
from src.delivery.discord import send_digest, format_digest

SAMPLE_ARTICLES = [
    {
        "title": "GPT-5 Released",
        "url": "https://openai.com/blog/gpt5",
        "source": "OpenAI Blog",
        "summary": "OpenAI announces GPT-5.",
        "multi_source": True,
        "source_count": 3,
    },
    {
        "title": "LLaMA 4 from Meta",
        "url": "https://ai.meta.com/llama4",
        "source": "TechCrunch",
        "summary": "Meta releases open-source model.",
        "multi_source": False,
        "source_count": 1,
    },
]


def test_format_digest_contains_titles():
    text = format_digest(SAMPLE_ARTICLES, max_articles=10)
    assert "GPT-5 Released" in text
    assert "LLaMA 4 from Meta" in text


def test_format_digest_respects_max():
    text = format_digest(SAMPLE_ARTICLES, max_articles=1)
    assert "GPT-5 Released" in text
    assert "LLaMA 4 from Meta" not in text


def test_send_digest_posts_to_webhook():
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    with patch("requests.post", return_value=mock_resp) as mock_post:
        send_digest(SAMPLE_ARTICLES, webhook_url="https://discord.com/api/webhooks/fake")
    assert mock_post.called
    payload = mock_post.call_args[1]["json"]
    assert "content" in payload


def test_send_digest_skips_if_no_webhook():
    with patch("requests.post") as mock_post:
        send_digest(SAMPLE_ARTICLES, webhook_url=None)
    assert not mock_post.called
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_discord.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement `src/delivery/discord.py`**

```python
import requests
from datetime import date

MAX_DISCORD_CHARS = 1900  # Discord limit is 2000, keep buffer


def format_digest(articles: list[dict], max_articles: int = 20) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"**Daily Tech Digest — {today}**\n"]
    for i, article in enumerate(articles[:max_articles]):
        multi = " 🔥 *(multi-source)*" if article.get("multi_source") else ""
        line = f"**{i+1}. [{article['title']}]({article['url']})**{multi}\n> {article.get('summary', '')[:200]}\n*Source: {article['source']}*\n"
        lines.append(line)
    return "\n".join(lines)


def _chunk_message(text: str, max_len: int = MAX_DISCORD_CHARS) -> list[str]:
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks


def send_digest(articles: list[dict], webhook_url: str | None) -> None:
    if not webhook_url:
        return
    message = format_digest(articles)
    for chunk in _chunk_message(message):
        response = requests.post(webhook_url, json={"content": chunk}, timeout=10)
        response.raise_for_status()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_discord.py -v
```
Expected: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/delivery/__init__.py src/delivery/discord.py tests/test_discord.py
git commit -m "feat: Discord delivery via webhook with tests"
```

---

## Task 8: Telegram Delivery

**Files:**
- Create: `src/delivery/telegram.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_telegram.py
from unittest.mock import patch, MagicMock
from src.delivery.telegram import send_telegram_digest

SAMPLE_ARTICLES = [
    {
        "title": "GPT-5 Released",
        "url": "https://openai.com/blog/gpt5",
        "source": "OpenAI Blog",
        "summary": "OpenAI announces GPT-5.",
        "multi_source": True,
        "source_count": 3,
    }
]


def test_send_telegram_posts_message():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True}
    with patch("requests.post", return_value=mock_resp) as mock_post:
        send_telegram_digest(
            SAMPLE_ARTICLES,
            bot_token="123:fake",
            chat_id="-1001234567890"
        )
    assert mock_post.called


def test_send_telegram_skips_if_no_token():
    with patch("requests.post") as mock_post:
        send_telegram_digest(SAMPLE_ARTICLES, bot_token=None, chat_id="123")
    assert not mock_post.called


def test_send_telegram_skips_if_no_chat():
    with patch("requests.post") as mock_post:
        send_telegram_digest(SAMPLE_ARTICLES, bot_token="123:fake", chat_id=None)
    assert not mock_post.called
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_telegram.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement `src/delivery/telegram.py`**

```python
import requests
from datetime import date

TELEGRAM_API = "https://api.telegram.org"
MAX_TELEGRAM_CHARS = 4000  # Telegram limit is 4096


def _format_telegram(articles: list[dict], max_articles: int = 20) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"<b>Daily Tech Digest — {today}</b>\n"]
    for i, article in enumerate(articles[:max_articles]):
        multi = " 🔥" if article.get("multi_source") else ""
        title = article["title"].replace("<", "&lt;").replace(">", "&gt;")
        url = article["url"]
        source = article["source"].replace("<", "&lt;")
        summary = article.get("summary", "")[:200].replace("<", "&lt;").replace(">", "&gt;")
        line = f'<b>{i+1}. <a href="{url}">{title}</a></b>{multi}\n<i>{summary}</i>\n<code>{source}</code>\n'
        lines.append(line)
    return "\n".join(lines)


def _chunk(text: str, max_len: int = MAX_TELEGRAM_CHARS) -> list[str]:
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks


def send_telegram_digest(articles: list[dict], bot_token: str | None, chat_id: str | None) -> None:
    if not bot_token or not chat_id:
        return
    message = _format_telegram(articles)
    api_url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    for chunk in _chunk(message):
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "HTML", "disable_web_page_preview": True}
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_telegram.py -v
```
Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/delivery/telegram.py tests/test_telegram.py
git commit -m "feat: Telegram delivery via Bot API with tests"
```

---

## Task 9: WhatsApp Delivery via Evolution API

**Files:**
- Create: `src/delivery/whatsapp.py`
- Create: `tests/test_whatsapp.py`

**Evolution API endpoint:**
```
POST https://{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}
Header: apikey: {EVOLUTION_API_KEY}
Body: { "number": "<recipient_with_country_code>", "text": "...", "linkPreview": true }
```

- [ ] **Step 1: Write failing tests**

```python
# tests/test_whatsapp.py
from unittest.mock import patch, MagicMock
from src.delivery.whatsapp import send_whatsapp_digest, format_whatsapp

SAMPLE_ARTICLES = [
    {
        "title": "GPT-5 Released",
        "url": "https://openai.com/blog/gpt5",
        "source": "OpenAI Blog",
        "summary": "OpenAI announces GPT-5 with improved reasoning.",
        "multi_source": True,
        "source_count": 3,
    },
    {
        "title": "LLaMA 4 from Meta",
        "url": "https://ai.meta.com/llama4",
        "source": "TechCrunch",
        "summary": "Meta releases open-source LLaMA 4 model.",
        "multi_source": False,
        "source_count": 1,
    },
]


def test_format_whatsapp_contains_titles():
    text = format_whatsapp(SAMPLE_ARTICLES, max_articles=10)
    assert "GPT-5 Released" in text
    assert "LLaMA 4 from Meta" in text


def test_format_whatsapp_respects_max():
    text = format_whatsapp(SAMPLE_ARTICLES, max_articles=1)
    assert "GPT-5 Released" in text
    assert "LLaMA 4 from Meta" not in text


def test_format_whatsapp_marks_multi_source():
    text = format_whatsapp(SAMPLE_ARTICLES, max_articles=10)
    assert "🔥" in text  # multi-source marker


def test_send_whatsapp_posts_to_evolution():
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    with patch("requests.post", return_value=mock_resp) as mock_post:
        send_whatsapp_digest(
            SAMPLE_ARTICLES,
            api_url="https://evolution.example.com",
            instance="myinstance",
            api_key="my-api-key",
            recipient_number="5511999999999",
        )
    assert mock_post.called
    call_args = mock_post.call_args
    assert "sendText" in call_args[0][0]
    assert call_args[1]["headers"]["apikey"] == "my-api-key"
    body = call_args[1]["json"]
    assert body["number"] == "5511999999999"
    assert "GPT-5 Released" in body["text"]


def test_send_whatsapp_skips_if_no_api_url():
    with patch("requests.post") as mock_post:
        send_whatsapp_digest(
            SAMPLE_ARTICLES,
            api_url=None,
            instance="inst",
            api_key="key",
            recipient_number="5511999999999",
        )
    assert not mock_post.called


def test_send_whatsapp_skips_if_no_recipient():
    with patch("requests.post") as mock_post:
        send_whatsapp_digest(
            SAMPLE_ARTICLES,
            api_url="https://evolution.example.com",
            instance="inst",
            api_key="key",
            recipient_number=None,
        )
    assert not mock_post.called


def test_send_whatsapp_long_digest_splits_into_chunks():
    # Create enough articles to exceed 4000 chars
    big_articles = [
        {
            "title": f"Article {i} about artificial intelligence and machine learning",
            "url": f"https://example.com/article-{i}",
            "source": "Source",
            "summary": "A" * 200,
            "multi_source": False,
            "source_count": 1,
        }
        for i in range(30)
    ]
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    with patch("requests.post", return_value=mock_resp) as mock_post:
        send_whatsapp_digest(
            big_articles,
            api_url="https://evolution.example.com",
            instance="inst",
            api_key="key",
            recipient_number="5511999999999",
        )
    # Multiple POST calls expected for chunked message
    assert mock_post.call_count >= 2
```

- [ ] **Step 2: Run failing tests**

```bash
pytest tests/test_whatsapp.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement `src/delivery/whatsapp.py`**

```python
import requests
from datetime import date

# Evolution API allows up to ~65k chars per message in WhatsApp,
# but splitting at 4000 keeps messages readable on mobile.
MAX_WHATSAPP_CHARS = 4000


def format_whatsapp(articles: list[dict], max_articles: int = 20) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"*Daily Tech Digest — {today}*\n"]
    for i, article in enumerate(articles[:max_articles]):
        multi = " 🔥 _(multi-source)_" if article.get("multi_source") else ""
        title = article["title"]
        url = article["url"]
        source = article["source"]
        summary = article.get("summary", "")[:200]
        line = f"*{i+1}. {title}*{multi}\n{url}\n_{summary}_\nSource: {source}\n"
        lines.append(line)
    return "\n".join(lines)


def _chunk(text: str, max_len: int = MAX_WHATSAPP_CHARS) -> list[str]:
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return [c for c in chunks if c.strip()]


def send_whatsapp_digest(
    articles: list[dict],
    api_url: str | None,
    instance: str | None,
    api_key: str | None,
    recipient_number: str | None,
) -> None:
    if not api_url or not instance or not api_key or not recipient_number:
        return

    endpoint = f"{api_url.rstrip('/')}/message/sendText/{instance}"
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key,
    }

    message = format_whatsapp(articles)
    for chunk in _chunk(message):
        payload = {
            "number": recipient_number,
            "text": chunk,
            "linkPreview": True,
        }
        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_whatsapp.py -v
```
Expected: 7 PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/delivery/whatsapp.py tests/test_whatsapp.py
git commit -m "feat: WhatsApp delivery via Evolution API with tests"
```

---

## Task 11: Main Orchestrator

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Implement `src/main.py`**

```python
import json
import os
from pathlib import Path

from src.sources.rss_fetcher import fetch_all_feeds
from src.sources.github_releases import fetch_all_releases
from src.sources.brave_search import fetch_all_searches
from src.processing.deduplicator import deduplicate
from src.processing.scorer import sort_by_score
from src.delivery.discord import send_digest
from src.delivery.telegram import send_telegram_digest
from src.delivery.whatsapp import send_whatsapp_digest


def load_sources(config_path: str = "config/sources.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def run_digest(config_path: str = "config/sources.json") -> list[dict]:
    sources = load_sources(config_path)

    github_token = os.getenv("GITHUB_TOKEN")
    brave_api_key = os.getenv("BRAVE_API_KEY")

    print("Fetching RSS feeds...")
    rss_articles = fetch_all_feeds(sources["rss_feeds"])
    print(f"  Got {len(rss_articles)} RSS articles")

    print("Fetching GitHub releases...")
    gh_articles = fetch_all_releases(sources["github_repos"], token=github_token)
    print(f"  Got {len(gh_articles)} GitHub release articles")

    print("Fetching Brave Search results...")
    search_articles = fetch_all_searches(sources["search_queries"], api_key=brave_api_key)
    print(f"  Got {len(search_articles)} search articles")

    all_articles = rss_articles + gh_articles + search_articles
    print(f"Total before dedup: {len(all_articles)}")

    deduplicated = deduplicate(all_articles, threshold=0.75)
    print(f"Total after dedup: {len(deduplicated)}")

    ranked = sort_by_score(deduplicated)

    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    evolution_api_url = os.getenv("EVOLUTION_API_URL")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE")
    evolution_api_key = os.getenv("EVOLUTION_API_KEY")
    whatsapp_recipient = os.getenv("WHATSAPP_RECIPIENT_NUMBER")

    print("Delivering digest...")
    send_digest(ranked, webhook_url=discord_webhook)
    send_telegram_digest(ranked, bot_token=telegram_token, chat_id=telegram_chat_id)
    send_whatsapp_digest(
        ranked,
        api_url=evolution_api_url,
        instance=evolution_instance,
        api_key=evolution_api_key,
        recipient_number=whatsapp_recipient,
    )
    print("Done.")

    return ranked


if __name__ == "__main__":
    run_digest()
```

- [ ] **Step 2: Run all tests to verify nothing broke**

```bash
pytest -v
```
Expected: All previously written tests PASS. `src/main.py` has no tests — the integration is tested via the workflow in the next task.

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: main orchestrator wiring all sources + delivery"
```

---

## Task 12: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/daily-digest.yml`

- [ ] **Step 1: Create `.github/workflows/` directory and workflow file**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/daily-digest.yml`**

```yaml
name: Daily Tech Digest

on:
  schedule:
    # Runs every day at 9:00 AM UTC (adjust to your timezone)
    - cron: "0 9 * * *"
  workflow_dispatch:
    # Allows manual trigger from GitHub UI
    inputs:
      dry_run:
        description: "Dry run (fetch only, no delivery)"
        required: false
        default: "false"
        type: choice
        options:
          - "false"
          - "true"

jobs:
  digest:
    name: Generate and Deliver Digest
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -v --tb=short

      - name: Run digest
        if: ${{ github.event.inputs.dry_run != 'true' }}
        env:
          GITHUB_TOKEN: ${{ secrets.DIGEST_GITHUB_TOKEN }}
          BRAVE_API_KEY: ${{ secrets.BRAVE_API_KEY }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          EVOLUTION_API_URL: ${{ secrets.EVOLUTION_API_URL }}
          EVOLUTION_INSTANCE: ${{ secrets.EVOLUTION_INSTANCE }}
          EVOLUTION_API_KEY: ${{ secrets.EVOLUTION_API_KEY }}
          WHATSAPP_RECIPIENT_NUMBER: ${{ secrets.WHATSAPP_RECIPIENT_NUMBER }}
        run: python -m src.main

      - name: Dry run (fetch + report only)
        if: ${{ github.event.inputs.dry_run == 'true' }}
        env:
          GITHUB_TOKEN: ${{ secrets.DIGEST_GITHUB_TOKEN }}
          BRAVE_API_KEY: ${{ secrets.BRAVE_API_KEY }}
        run: |
          python -c "
          from src.main import run_digest
          articles = run_digest.__wrapped__() if hasattr(run_digest, '__wrapped__') else None
          import json, os
          from src.main import load_sources
          from src.sources.rss_fetcher import fetch_all_feeds
          from src.sources.github_releases import fetch_all_releases
          from src.sources.brave_search import fetch_all_searches
          from src.processing.deduplicator import deduplicate
          from src.processing.scorer import sort_by_score
          sources = load_sources()
          articles = fetch_all_feeds(sources['rss_feeds']) + fetch_all_releases(sources['github_repos'], token=os.getenv('GITHUB_TOKEN')) + fetch_all_searches(sources['search_queries'], api_key=os.getenv('BRAVE_API_KEY'))
          deduped = deduplicate(articles)
          ranked = sort_by_score(deduped)
          print(f'Would deliver {len(ranked)} articles')
          for a in ranked[:10]:
              print(f'  [{a[\"title\"]}] score sources={a[\"source_count\"]}')
          "
```

> **Note on secrets:** Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret. Add:
> - `DISCORD_WEBHOOK_URL` — Discord webhook URL
> - `TELEGRAM_BOT_TOKEN` — Telegram bot token (from @BotFather)
> - `TELEGRAM_CHAT_ID` — Telegram channel/group chat ID
> - `EVOLUTION_API_URL` — Evolution API base URL (ex: `https://evolution.yourserver.com`)
> - `EVOLUTION_INSTANCE` — Evolution API instance name
> - `EVOLUTION_API_KEY` — Evolution API key (instance-level)
> - `WHATSAPP_RECIPIENT_NUMBER` — Your WhatsApp number with country code, no `+` (ex: `5511999999999`)
> - `BRAVE_API_KEY` — Brave Search API key (optional, skipped if absent)
> - `DIGEST_GITHUB_TOKEN` — GitHub PAT with `public_repo` scope (optional, increases rate limit 60→5000 req/hr)

- [ ] **Step 3: Run tests one final time**

```bash
pytest -v
```
Expected: All tests PASS.

- [ ] **Step 4: Commit and push**

```bash
git add .github/workflows/daily-digest.yml
git commit -m "feat: GitHub Actions daily digest workflow with cron + manual trigger"
```

---

## Task 13: Add `.gitignore` and `README` hint

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create `.gitignore`**

```text
__pycache__/
*.pyc
*.pyo
.env
.venv/
venv/
.pytest_cache/
*.egg-info/
dist/
build/
.coverage
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add gitignore"
```

---

## Self-Review

### Spec Coverage

| Requirement | Task |
|-------------|------|
| RSS Feeds (46 sources) | Task 1 (config/sources.json has 46 feeds), Task 2 |
| Twitter/X KOLs | ⚠️ Not implemented — Twitter API requires paid tier ($100/mo). Marked optional in the document; omitted here intentionally. |
| GitHub Releases (19 repos) | Task 1 (19 repos in config), Task 3 |
| Web Search (4 queries) | Task 1 (4 queries in config), Task 4 |
| Deduplication by title similarity | Task 5 |
| Quality scoring (priority +3, multi-source +5, recency +2, engagement +1) | Task 6 |
| Discord delivery | Task 7 |
| Telegram delivery | Task 8 |
| WhatsApp delivery via Evolution API | Task 9 |
| Schedule (daily 9am) | Task 12 |
| Manual trigger | Task 12 |
| Customizable sources | Task 1 (edit config/sources.json) |

### Twitter/X Note

Twitter API v2 free tier allows only 1 app/1M tokens read per month — insufficient for monitoring 44 accounts daily. Options:
1. **Skip it** (this plan) — 3 of 4 layers still cover the same news.
2. **Add it later** with `src/sources/twitter_fetcher.py` using `X_BEARER_TOKEN` secret when/if paid API is available.

### Placeholder Scan

None found. All steps have complete code.

### Type Consistency

- All fetchers return `list[dict]` with keys: `title`, `url`, `summary`, `source`, `source_type`, `priority`, `published_at`, `engagement` ✓
- `deduplicate()` adds `multi_source: bool`, `source_count: int`, `all_sources: list[str]` ✓
- `score_article()` reads `priority`, `multi_source`, `published_at`, `engagement` ✓
- `send_digest()` / `send_telegram_digest()` read `title`, `url`, `source`, `summary`, `multi_source` ✓

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-02-daily-digest.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
