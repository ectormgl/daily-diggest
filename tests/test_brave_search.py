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
