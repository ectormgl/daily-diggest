import sys
import requests
from datetime import date

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
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"[whatsapp] Failed to send chunk: {e}", file=sys.stderr)
