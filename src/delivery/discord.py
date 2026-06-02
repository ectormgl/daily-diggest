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
