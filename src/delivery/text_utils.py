import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_summary(text: str) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def article_summary(article: dict, max_len: int = 280) -> str:
    raw = article.get("llm_summary") or article.get("summary") or ""
    if not article.get("llm_summary"):
        raw = clean_summary(raw)
    return raw[:max_len]
