import requests
from datetime import date

from src.delivery.text_utils import article_summary

TELEGRAM_API = "https://api.telegram.org"
MAX_TELEGRAM_CHARS = 4000
TOPIC_ORDER = ["Models", "Tools", "Research", "Industry", "Other"]


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _group_by_topic(articles: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for a in articles:
        groups.setdefault(a.get("topic", "Other"), []).append(a)
    return groups


def _format_telegram(articles: list[dict], max_articles: int = 25) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"<b>Daily Tech Digest — {today}</b>\n"]
    items = articles[:max_articles]
    grouped = _group_by_topic(items)
    topics = [t for t in TOPIC_ORDER if t in grouped] + [t for t in grouped if t not in TOPIC_ORDER]
    i = 0
    for topic in topics:
        lines.append(f"\n<b>— {_esc(topic)} —</b>")
        for article in grouped[topic]:
            i += 1
            multi = " 🔥" if article.get("multi_source") else ""
            imp = article.get("importance")
            imp_tag = f" [{imp:.0f}/10]" if isinstance(imp, (int, float)) else ""
            title = _esc(article["title"])
            url = article["url"]
            source = _esc(article["source"])
            summary = _esc(article_summary(article))
            line = (
                f'<b>{i}. <a href="{url}">{title}</a></b>{multi}{imp_tag}\n'
                f"<i>{summary}</i>\n"
                f"<code>{source}</code>\n"
            )
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
