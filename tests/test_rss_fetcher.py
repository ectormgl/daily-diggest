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
