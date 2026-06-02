import sys
import requests
from datetime import date

MAX_WHATSAPP_CHARS = 4000
TOPIC_ORDER = ["Models", "Tools", "Research", "Industry", "Other"]


def _group_by_topic(articles: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for a in articles:
        groups.setdefault(a.get("topic", "Other"), []).append(a)
    return groups


def format_whatsapp(articles: list[dict], max_articles: int = 25) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"*Daily Tech Digest — {today}*\n"]
    items = articles[:max_articles]
    grouped = _group_by_topic(items)
    topics = [t for t in TOPIC_ORDER if t in grouped] + [t for t in grouped if t not in TOPIC_ORDER]
    i = 0
    for topic in topics:
        lines.append(f"\n*— {topic} —*")
        for article in grouped[topic]:
            i += 1
            multi = " 🔥" if article.get("multi_source") else ""
            imp = article.get("importance")
            imp_tag = f" [{imp:.0f}/10]" if isinstance(imp, (int, float)) else ""
            title = article["title"]
            url = article["url"]
            source = article["source"]
            summary = (article.get("llm_summary") or article.get("summary", ""))[:280]
            line = (
                f"*{i}. {title}*{multi}{imp_tag}\n"
                f"{url}\n"
                f"_{summary}_\n"
                f"Source: {source}\n"
            )
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
    headers = {"Content-Type": "application/json", "apikey": api_key}

    message = format_whatsapp(articles)
    for chunk in _chunk(message):
        payload = {"number": recipient_number, "text": chunk, "linkPreview": True}
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"[whatsapp] Failed to send chunk: {e}", file=sys.stderr)
