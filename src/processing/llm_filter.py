import json
import os
import sys

import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-haiku-4.5"

RELEVANCE_PROMPT = """You are curating a daily digest for an AI/ML engineer.

Score each item from 0-10 on newsworthiness. High scores: major model releases, significant research, new products, notable open-source launches, important industry news. Low scores: minor patch releases (x.y.Z bugfixes), dev/nightly/pre-release builds, version bumps with no notable changes, generic infra notices, duplicate announcements, low-signal blog posts.

Return ONLY a JSON array of objects with "id" and "score" fields, one per item, no other text.

Items:
{items}"""


def filter_with_llm(
    articles: list[dict],
    api_key: str | None,
    candidate_pool: int = 40,
    keep_top: int = 15,
    min_score: int = 6,
) -> list[dict]:
    if not api_key or not articles:
        return articles

    candidates = articles[:candidate_pool]
    items_payload = [
        {
            "id": i,
            "title": a.get("title", "")[:200],
            "source": a.get("source", ""),
            "summary": (a.get("summary") or "")[:300],
        }
        for i, a in enumerate(candidates)
    ]
    prompt = RELEVANCE_PROMPT.format(items=json.dumps(items_payload, ensure_ascii=False))

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        scores = json.loads(text)
    except Exception as e:
        print(f"[llm_filter] Failed, returning unfiltered: {e}", file=sys.stderr)
        return articles[:keep_top] + articles[keep_top:]

    score_by_id = {s["id"]: s.get("score", 0) for s in scores if isinstance(s, dict) and "id" in s}
    scored = [
        (score_by_id.get(i, 0), i, a)
        for i, a in enumerate(candidates)
    ]
    kept = [a for score, _, a in sorted(scored, key=lambda x: (-x[0], x[1])) if score >= min_score]
    return kept[:keep_top] + articles[candidate_pool:]
