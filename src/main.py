import json
import os
import sys
import time
from datetime import datetime

from src.sources.rss_fetcher import fetch_all_feeds
from src.sources.github_releases import fetch_all_releases
from src.sources.brave_search import fetch_all_searches
from src.processing.deduplicator import deduplicate
from src.processing.scorer import sort_by_score
from src.processing.semantic_dedup import semantic_dedup
from src.processing.enricher import enrich_articles, sort_by_importance, filter_by_importance
from src.delivery.discord import send_digest
from src.delivery.telegram import send_telegram_digest
from src.delivery.whatsapp import send_whatsapp_digest


def log(msg: str) -> None:
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _int_env(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        log(f"WARN: {name}={v!r} is not an int, using default {default}")
        return default


def _float_env(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return float(v)
    except ValueError:
        log(f"WARN: {name}={v!r} is not a float, using default {default}")
        return default


def load_sources(config_path: str = "config/sources.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def run_digest(config_path: str = "config/sources.json") -> list[dict]:
    t0 = time.time()
    sources = load_sources(config_path)
    log(
        f"Loaded sources: {len(sources['rss_feeds'])} RSS feeds, "
        f"{len(sources['github_repos'])} GitHub repos, "
        f"{len(sources['search_queries'])} search queries"
    )

    github_token = os.getenv("GITHUB_TOKEN")
    brave_api_key = os.getenv("BRAVE_API_KEY")
    log(f"Env: github_token={'set' if github_token else 'MISSING'}, brave_key={'set' if brave_api_key else 'MISSING'}")

    t = time.time()
    log(f"Fetching {len(sources['rss_feeds'])} RSS feeds (parallel)...")
    rss_articles = fetch_all_feeds(sources["rss_feeds"])
    log(f"RSS done in {time.time()-t:.1f}s — {len(rss_articles)} articles")

    t = time.time()
    log(f"Fetching {len(sources['github_repos'])} GitHub release feeds (parallel)...")
    gh_articles = fetch_all_releases(sources["github_repos"], token=github_token)
    log(f"GitHub releases done in {time.time()-t:.1f}s — {len(gh_articles)} articles")

    t = time.time()
    log(f"Fetching {len(sources['search_queries'])} Brave Search queries...")
    search_articles = fetch_all_searches(sources["search_queries"], api_key=brave_api_key)
    log(f"Brave Search done in {time.time()-t:.1f}s — {len(search_articles)} articles")

    all_articles = rss_articles + gh_articles + search_articles
    log(f"Total before dedup: {len(all_articles)}")

    t = time.time()
    deduplicated = deduplicate(all_articles, threshold=0.75)
    log(f"String dedup done in {time.time()-t:.1f}s — {len(deduplicated)} articles")

    ranked = sort_by_score(deduplicated)

    pool_size = _int_env("LLM_POOL_SIZE", 40)
    top_pool = ranked[:pool_size]
    log(f"Kept top {len(top_pool)} for further processing (pool size = {pool_size})")

    use_llm = bool(os.getenv("OPENROUTER_API_KEY"))
    if use_llm:
        t = time.time()
        log(f"LLM semantic dedup: sending {len(top_pool)} titles to OpenRouter...")
        top_pool = semantic_dedup(top_pool)
        log(f"Semantic dedup done in {time.time()-t:.1f}s — {len(top_pool)} articles")

        enrich_limit = _int_env("LLM_ENRICH_LIMIT", 25)
        t = time.time()
        log(f"LLM enrichment: summarizing/scoring top {min(enrich_limit, len(top_pool))}...")
        top_pool = enrich_articles(top_pool, limit=enrich_limit)
        log(f"Enrichment done in {time.time()-t:.1f}s")

        min_importance = _float_env("MIN_IMPORTANCE", 3.0)
        before = len(top_pool)
        top_pool = filter_by_importance(top_pool, min_score=min_importance)
        log(f"Filtered by importance >= {min_importance}: {before} -> {len(top_pool)}")
        top_pool = sort_by_importance(top_pool)
    else:
        log("OPENROUTER_API_KEY not set — skipping LLM enrichment.")

    final_articles = top_pool
    log(f"Final article count: {len(final_articles)}")

    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    evolution_api_url = os.getenv("EVOLUTION_API_URL")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE")
    evolution_api_key = os.getenv("EVOLUTION_API_KEY")
    whatsapp_recipient = os.getenv("WHATSAPP_RECIPIENT_NUMBER")
    log(
        "Delivery targets: "
        f"discord={'on' if discord_webhook else 'off'}, "
        f"telegram={'on' if telegram_token and telegram_chat_id else 'off'}, "
        f"whatsapp={'on' if all([evolution_api_url, evolution_instance, evolution_api_key, whatsapp_recipient]) else 'off'}"
    )

    if discord_webhook:
        t = time.time()
        try:
            send_digest(final_articles, webhook_url=discord_webhook)
            log(f"Discord delivered in {time.time()-t:.1f}s")
        except Exception as e:
            log(f"Discord delivery failed: {e}")

    if telegram_token and telegram_chat_id:
        t = time.time()
        try:
            send_telegram_digest(final_articles, bot_token=telegram_token, chat_id=telegram_chat_id)
            log(f"Telegram delivered in {time.time()-t:.1f}s")
        except Exception as e:
            log(f"Telegram delivery failed: {e}")

    if evolution_api_url and evolution_instance and evolution_api_key and whatsapp_recipient:
        t = time.time()
        try:
            send_whatsapp_digest(
                final_articles,
                api_url=evolution_api_url,
                instance=evolution_instance,
                api_key=evolution_api_key,
                recipient_number=whatsapp_recipient,
            )
            log(f"WhatsApp delivered in {time.time()-t:.1f}s")
        except Exception as e:
            log(f"WhatsApp delivery failed: {e}")

    log(f"Done. Total runtime: {time.time()-t0:.1f}s")
    return final_articles


if __name__ == "__main__":
    run_digest()
