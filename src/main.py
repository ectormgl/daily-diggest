import json
import os
import sys
from pathlib import Path

from src.sources.rss_fetcher import fetch_all_feeds
from src.sources.github_releases import fetch_all_releases
from src.sources.brave_search import fetch_all_searches
from src.processing.deduplicator import deduplicate
from src.processing.scorer import sort_by_score
from src.delivery.discord import send_digest
from src.delivery.telegram import send_telegram_digest
from src.delivery.whatsapp import send_whatsapp_digest


def load_sources(config_path: str = "config/sources.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def run_digest(config_path: str = "config/sources.json") -> list[dict]:
    sources = load_sources(config_path)

    github_token = os.getenv("GITHUB_TOKEN")
    brave_api_key = os.getenv("BRAVE_API_KEY")

    print("Fetching RSS feeds...")
    rss_articles = fetch_all_feeds(sources["rss_feeds"])
    print(f"  Got {len(rss_articles)} RSS articles")

    print("Fetching GitHub releases...")
    gh_articles = fetch_all_releases(sources["github_repos"], token=github_token)
    print(f"  Got {len(gh_articles)} GitHub release articles")

    print("Fetching Brave Search results...")
    search_articles = fetch_all_searches(sources["search_queries"], api_key=brave_api_key)
    print(f"  Got {len(search_articles)} search articles")

    all_articles = rss_articles + gh_articles + search_articles
    print(f"Total before dedup: {len(all_articles)}")

    deduplicated = deduplicate(all_articles, threshold=0.75)
    print(f"Total after dedup: {len(deduplicated)}")

    ranked = sort_by_score(deduplicated)

    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    evolution_api_url = os.getenv("EVOLUTION_API_URL")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE")
    evolution_api_key = os.getenv("EVOLUTION_API_KEY")
    whatsapp_recipient = os.getenv("WHATSAPP_RECIPIENT_NUMBER")

    print("Delivering digest...")
    try:
        send_digest(ranked, webhook_url=discord_webhook)
    except Exception as e:
        print(f"[main] Discord delivery failed: {e}", file=sys.stderr)

    try:
        send_telegram_digest(ranked, bot_token=telegram_token, chat_id=telegram_chat_id)
    except Exception as e:
        print(f"[main] Telegram delivery failed: {e}", file=sys.stderr)

    try:
        send_whatsapp_digest(
            ranked,
            api_url=evolution_api_url,
            instance=evolution_instance,
            api_key=evolution_api_key,
            recipient_number=whatsapp_recipient,
        )
    except Exception as e:
        print(f"[main] WhatsApp delivery failed: {e}", file=sys.stderr)

    print("Done.")

    return ranked


if __name__ == "__main__":
    run_digest()
