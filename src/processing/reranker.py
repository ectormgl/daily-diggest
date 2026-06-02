import os

from src.processing.llm_client import call_llm, extract_json

DEFAULT_MODEL = "anthropic/claude-haiku-4.5"

SYSTEM_PROMPT = (
    "You are the editor of a daily AI/ML/software tech digest. "
    "From the candidate articles, pick the TRULY newsworthy ones a busy engineer "
    "would want to read today. Prioritize: major model releases, paradigm-shifting "
    "research, significant new tools/products, and consequential industry moves. "
    "Down-weight: routine updates, listicles, hype, opinion pieces, duplicates, "
    "marketing posts, and off-topic noise. "
    "Reply with ONLY a JSON object of the form: "
    '{"picks": [{"id": 3, "score": 9}, {"id": 7, "score": 8}, ...]} '
    "where score is 0-10 newsworthiness. Return EXACTLY the top {top_n} ids, "
    "ordered from most to least newsworthy. No commentary."
)


def rerank(articles: list[dict], top_n: int = 10) -> list[dict]:
    """LLM re-rank candidates via OpenRouter (Haiku) and return the top_n most newsworthy."""
    if not articles or len(articles) <= top_n:
        return articles[:top_n] if articles else articles
    if not os.getenv("OPENROUTER_API_KEY"):
        return articles[:top_n]

    model = os.getenv("RERANK_MODEL", DEFAULT_MODEL)

    lines = []
    for i, a in enumerate(articles, start=1):
        title = (a.get("title") or "")[:200]
        blurb = (a.get("summary") or "")[:300]
        source = a.get("source", "")
        lines.append(f"id={i} | source={source}\n  title: {title}\n  blurb: {blurb}")
    user_msg = "\n\n".join(lines)

    response = call_llm(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.replace("{top_n}", str(top_n))},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=1024,
        require_json=True,
        models=[model],
    )
    if not response:
        print("[rerank] LLM call failed; falling back to score order", flush=True)
        return articles[:top_n]

    parsed = extract_json(response)
    picks = None
    if isinstance(parsed, dict):
        for k in ("picks", "items", "results"):
            if isinstance(parsed.get(k), list):
                picks = parsed[k]
                break
    elif isinstance(parsed, list):
        picks = parsed

    if not picks:
        print(f"[rerank] could not parse picks; raw start: {response[:300]!r}", flush=True)
        return articles[:top_n]

    selected: list[dict] = []
    seen: set[int] = set()
    for p in picks:
        if not isinstance(p, dict):
            continue
        try:
            idx = int(p.get("id")) - 1
        except (TypeError, ValueError):
            continue
        if idx in seen or idx < 0 or idx >= len(articles):
            continue
        seen.add(idx)
        a = dict(articles[idx])
        try:
            a["rerank_score"] = float(p.get("score"))
        except (TypeError, ValueError):
            pass
        selected.append(a)
        if len(selected) >= top_n:
            break

    if not selected:
        return articles[:top_n]

    print(f"[rerank] selected {len(selected)} articles", flush=True)
    return selected
