import os
import time

import requests

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
REQUEST_TIMEOUT = 60

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
    """LLM re-rank candidates with Claude Haiku, return the top_n most newsworthy."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not articles or len(articles) <= top_n:
        return articles[:top_n] if articles else articles

    model = os.getenv("ANTHROPIC_RERANK_MODEL", DEFAULT_MODEL)

    lines = []
    for i, a in enumerate(articles, start=1):
        title = (a.get("title") or "")[:200]
        blurb = (a.get("summary") or "")[:300]
        source = a.get("source", "")
        lines.append(f"id={i} | source={source}\n  title: {title}\n  blurb: {blurb}")
    user_msg = "\n\n".join(lines)

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT.replace("{top_n}", str(top_n)),
        "messages": [{"role": "user", "content": user_msg}],
    }

    print(f"[rerank] sending {len(articles)} candidates to {model} for top-{top_n}", flush=True)
    t0 = time.time()
    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"[rerank] request error: {e}", flush=True)
        return articles[:top_n]

    if resp.status_code != 200:
        print(f"[rerank] status {resp.status_code}: {resp.text[:200]}", flush=True)
        return articles[:top_n]

    try:
        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        usage = data.get("usage", {})
        print(
            f"[rerank] OK in {time.time()-t0:.1f}s "
            f"(input={usage.get('input_tokens', '?')} output={usage.get('output_tokens', '?')})",
            flush=True,
        )
    except Exception as e:
        print(f"[rerank] parse error: {e}", flush=True)
        return articles[:top_n]

    from src.processing.llm_client import extract_json

    parsed = extract_json(text)
    picks = None
    if isinstance(parsed, dict):
        for k in ("picks", "items", "results"):
            if isinstance(parsed.get(k), list):
                picks = parsed[k]
                break
    elif isinstance(parsed, list):
        picks = parsed

    if not picks:
        print(f"[rerank] could not parse picks; raw start: {text[:300]!r}", flush=True)
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
