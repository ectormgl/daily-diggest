import sys

from src.processing.llm_client import call_llm, extract_json

SYSTEM_PROMPT = (
    "You are a news editor. You will receive a numbered list of article titles. "
    "Group together items that refer to the same underlying story or announcement. "
    "Different framings, sources, or wording of the SAME event = same group. "
    "Reply with ONLY a JSON object of the form: "
    '{"groups": [[1, 5, 9], [2], [3, 7], ...]} '
    "where each inner list contains the numbers of articles that belong together. "
    "Every input number must appear in exactly one group."
)


def semantic_dedup(articles: list[dict]) -> list[dict]:
    if len(articles) < 2:
        return articles

    numbered = "\n".join(f"{i+1}. {a['title']}" for i, a in enumerate(articles))
    response = call_llm(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": numbered},
        ],
        temperature=0.0,
        max_tokens=1500,
        require_json=True,
    )
    if not response:
        return articles

    parsed = extract_json(response)
    raw_groups = _extract_groups(parsed)
    if raw_groups is None:
        print(
            f"[semantic_dedup] could not find groups in LLM response. Raw start: {response[:500]!r}",
            flush=True,
        )
        return articles
    print(f"[semantic_dedup] received {len(raw_groups)} groups from LLM", flush=True)

    n = len(articles)
    seen: set[int] = set()
    merged: list[dict] = []
    for group in raw_groups:
        if not isinstance(group, list) or not group:
            continue
        indices = []
        for x in group:
            try:
                idx = int(x) - 1
            except (TypeError, ValueError):
                continue
            if 0 <= idx < n and idx not in seen:
                indices.append(idx)
                seen.add(idx)
        if not indices:
            continue
        group_articles = [articles[i] for i in indices]
        merged.append(_merge_group(group_articles))

    for i in range(n):
        if i not in seen:
            merged.append(articles[i])

    return merged


def _extract_groups(parsed) -> list | None:
    if isinstance(parsed, list):
        if all(isinstance(g, list) for g in parsed):
            return parsed
        return None
    if isinstance(parsed, dict):
        for key in ("groups", "clusters", "duplicates", "items", "result"):
            v = parsed.get(key)
            if isinstance(v, list):
                return v
    return None


def _merge_group(group: list[dict]) -> dict:
    rep = dict(group[0])
    sources = []
    seen_sources = set()
    for a in group:
        for s in a.get("all_sources") or [a.get("source", "")]:
            if s and s not in seen_sources:
                sources.append(s)
                seen_sources.add(s)
    total_count = sum(a.get("source_count", 1) for a in group)
    rep["all_sources"] = sources
    rep["source_count"] = total_count
    rep["multi_source"] = total_count > 1
    rep["engagement"] = max(a.get("engagement", 0) for a in group)
    return rep
