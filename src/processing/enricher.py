import sys

from src.processing.llm_client import call_llm, extract_json

TOPICS = ["Models", "Tools", "Research", "Industry", "Other"]

SYSTEM_PROMPT = (
    "You are the editor of a daily tech digest focused on AI, ML, and software. "
    "For each article you receive, produce: "
    "(1) a concise, factual 1-2 sentence summary in English (no hype, no emojis); "
    "(2) an importance score from 0 to 10 — 10 = major model release / paradigm shift, "
    "7-9 = significant new tool or research result, 4-6 = notable update, "
    "1-3 = minor or routine, 0 = noise / off-topic; "
    "(3) a topic, chosen STRICTLY from: Models, Tools, Research, Industry, Other. "
    "Reply with ONLY a JSON object of the form: "
    '{"items": [{"id": 1, "summary": "...", "importance": 8, "topic": "Models"}, ...]} '
    "Include one entry for every input id. Do not add commentary."
)


def enrich_articles(articles: list[dict], limit: int = 25) -> list[dict]:
    if not articles:
        return articles

    subset = articles[:limit]
    payload_lines = []
    for i, a in enumerate(subset, start=1):
        title = a.get("title", "")[:200]
        raw_summary = (a.get("summary") or "")[:400]
        source = a.get("source", "")
        payload_lines.append(f"id={i} | source={source}\n  title: {title}\n  blurb: {raw_summary}")
    user_msg = "\n\n".join(payload_lines)

    response = call_llm(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=3000,
        require_json=True,
    )
    if not response:
        return articles

    parsed = extract_json(response)
    items = _extract_items(parsed)
    if items is None:
        print(
            f"[enricher] could not find items array in LLM response. Raw start: {response[:500]!r}",
            flush=True,
        )
        return articles
    print(f"[enricher] received {len(items)} items from LLM", flush=True)

    by_id = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            idx = int(item.get("id")) - 1
        except (TypeError, ValueError):
            continue
        by_id[idx] = item

    enriched = []
    for i, a in enumerate(subset):
        info = by_id.get(i)
        new = dict(a)
        if info:
            summary = (info.get("summary") or "").strip()
            if summary:
                new["llm_summary"] = summary
            try:
                imp = float(info.get("importance"))
                new["importance"] = max(0.0, min(10.0, imp))
            except (TypeError, ValueError):
                pass
            topic = (info.get("topic") or "").strip()
            new["topic"] = topic if topic in TOPICS else "Other"
        else:
            new["topic"] = "Other"
        enriched.append(new)

    enriched.extend(articles[limit:])
    return enriched


def _extract_items(parsed) -> list | None:
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("items", "results", "articles", "data", "output", "enrichment"):
            v = parsed.get(key)
            if isinstance(v, list):
                return v
        # Single-item dict that looks like one article
        if any(k in parsed for k in ("id", "summary", "topic", "importance")):
            return [parsed]
    return None


def sort_by_importance(articles: list[dict]) -> list[dict]:
    return sorted(
        articles,
        key=lambda a: (a.get("importance", -1), a.get("source_count", 1)),
        reverse=True,
    )


def filter_by_importance(articles: list[dict], min_score: float = 3.0) -> list[dict]:
    kept = [a for a in articles if a.get("importance", min_score) >= min_score]
    return kept or articles
