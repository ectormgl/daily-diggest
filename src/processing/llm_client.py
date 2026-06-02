import json
import os
import sys
import time

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "deepseek/deepseek-chat-v3.1:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "meta-llama/llama-3.1-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
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

    for model in _models():
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if require_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
            )
        except Exception as e:
            print(f"[llm] {model} request error: {e}", file=sys.stderr)
            continue

        if response.status_code == 429:
            print(f"[llm] {model} rate-limited, trying next", file=sys.stderr)
            time.sleep(1)
            continue
        if response.status_code >= 500:
            print(f"[llm] {model} server error {response.status_code}, trying next", file=sys.stderr)
            continue
        if response.status_code != 200:
            body = response.text[:200]
            print(f"[llm] {model} status {response.status_code}: {body}", file=sys.stderr)
            continue

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if content and content.strip():
                return content
            print(f"[llm] {model} returned empty content, trying next", file=sys.stderr)
        except Exception as e:
            print(f"[llm] {model} parse error: {e}", file=sys.stderr)
            continue

    return None


def extract_json(text: str):
    text = text.strip()
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
