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
