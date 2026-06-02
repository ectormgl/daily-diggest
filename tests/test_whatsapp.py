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
