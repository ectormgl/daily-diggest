import requests
from datetime import date

from src.delivery.text_utils import article_summary

MAX_DISCORD_CHARS = 1900
TOPIC_ORDER = ["Models", "Tools", "Research", "Industry", "Other"]


def _group_by_topic(articles: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for a in articles:
        groups.setdefault(a.get("topic", "Other"), []).append(a)
    return groups


def format_digest(articles: list[dict], max_articles: int = 25) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"**Daily Tech Digest — {today}**\n"]
    items = articles[:max_articles]
    grouped = _group_by_topic(items)
    topics = [t for t in TOPIC_ORDER if t in grouped] + [t for t in grouped if t not in TOPIC_ORDER]
    i = 0
    for topic in topics:
        lines.append(f"\n__**{topic}**__")
        for article in grouped[topic]:
            i += 1
            multi = " 🔥" if article.get("multi_source") else ""
            imp = article.get("importance")
            imp_tag = f" `{imp:.0f}/10`" if isinstance(imp, (int, float)) else ""
            summary = article_summary(article)
            line = (
                f"**{i}. [{article['title']}]({article['url']})**{multi}{imp_tag}\n"
                f"> {summary}\n"
                f"*Source: {article['source']}*\n"
            )
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
