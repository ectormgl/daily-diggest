from datetime import datetime, timezone, timedelta

RECENCY_WINDOW_HOURS = 24


def score_article(article: dict) -> int:
    score = 0
    if article.get("priority"):
        score += 3
    if article.get("multi_source"):
        score += 5
    published_at = article.get("published_at")
    if published_at is not None:
        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age = now - published_at
        if age <= timedelta(hours=RECENCY_WINDOW_HOURS):
            score += 2
    if article.get("engagement", 0) > 0:
        score += 1
    return score


def sort_by_score(articles: list[dict]) -> list[dict]:
    return sorted(articles, key=score_article, reverse=True)
