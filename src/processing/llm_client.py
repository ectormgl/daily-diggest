import json
import os
import sys
import time

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODELS = [
    "moonshotai/kimi-k2.6:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "poolside/laguna-xs.2:free",
]

REQUEST_TIMEOUT = 60


def _models() -> list[str]:
    env = os.getenv("OPENROUTER_MODELS")
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_MODELS


def call_llm(
    messages: list[dict],
    *,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    require_json: bool = False,
    models: list[str] | None = None,
) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ectormgl/daily-diggest",
        "X-Title": "daily-diggest",
    }

    if models is None:
        models = _models()
    for i, model in enumerate(models, 1):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if require_json:
            payload["response_format"] = {"type": "json_object"}

        print(f"[llm] try {i}/{len(models)}: {model} (timeout={REQUEST_TIMEOUT}s)", flush=True)
        t0 = time.time()
        try:
            response = requests.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
            )
        except Exception as e:
            print(f"[llm] {model} request error after {time.time()-t0:.1f}s: {e}", flush=True)
            continue
        elapsed = time.time() - t0

        if response.status_code == 429:
            print(f"[llm] {model} rate-limited after {elapsed:.1f}s, trying next", flush=True)
            time.sleep(1)
            continue
        if response.status_code >= 500:
            print(f"[llm] {model} server error {response.status_code} after {elapsed:.1f}s, trying next", flush=True)
            continue
        if response.status_code != 200:
            body = response.text[:200]
            print(f"[llm] {model} status {response.status_code} after {elapsed:.1f}s: {body}", flush=True)
            continue

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if content and content.strip():
                usage = data.get("usage", {})
                print(
                    f"[llm] {model} OK in {elapsed:.1f}s "
                    f"(prompt={usage.get('prompt_tokens', '?')} completion={usage.get('completion_tokens', '?')})",
                    flush=True,
                )
                return content
            print(f"[llm] {model} returned empty content after {elapsed:.1f}s, trying next", flush=True)
        except Exception as e:
            print(f"[llm] {model} parse error after {elapsed:.1f}s: {e}", flush=True)
            continue

    print("[llm] all models failed", flush=True)
    return None


def extract_json(text: str):
    text = text.strip()
    # Strip reasoning-model thinking blocks (nemotron, deepseek-r1, qwq, etc.)
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>", start)
        if end == -1:
            break
        text = (text[:start] + text[end + len("</think>"):]).strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("[", "]"), ("{", "}")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None
