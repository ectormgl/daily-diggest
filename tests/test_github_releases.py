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
