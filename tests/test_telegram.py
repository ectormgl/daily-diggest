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
