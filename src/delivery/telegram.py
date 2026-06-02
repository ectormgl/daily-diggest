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
