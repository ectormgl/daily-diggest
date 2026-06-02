# tests/test_scorer.py
from datetime import datetime, timezone, timedelta
from src.processing.scorer import score_article, sort_by_score

BASE_ARTICLE = {
    "title": "GPT-5 released",
    "priority": False,
    "multi_source": False,
    "source_count": 1,
    "published_at": None,
    "engagement": 0,
}


def test_priority_source_adds_3():
    article = {**BASE_ARTICLE, "priority": True}
    assert score_article(article) >= 3


def test_multi_source_adds_5():
    article = {**BASE_ARTICLE, "multi_source": True, "source_count": 3}
    assert score_article(article) >= 5


def test_recent_article_adds_2():
    recent = datetime.now(timezone.utc) - timedelta(hours=6)
    article = {**BASE_ARTICLE, "published_at": recent}
    assert score_article(article) >= 2


def test_old_article_no_recency_bonus():
    old = datetime.now(timezone.utc) - timedelta(days=3)
    article = {**BASE_ARTICLE, "published_at": old}
    assert score_article(article) == 0


def test_engagement_adds_1():
    article = {**BASE_ARTICLE, "engagement": 5}
    assert score_article(article) >= 1


def test_combined_score():
    recent = datetime.now(timezone.utc) - timedelta(hours=2)
    article = {
        "title": "Big AI news",
        "priority": True,
        "multi_source": True,
        "source_count": 2,
        "published_at": recent,
        "engagement": 10,
    }
    # priority(3) + multi_source(5) + recency(2) + engagement(1) = 11
    assert score_article(article) == 11


def test_sort_by_score_descending():
    articles = [
        {**BASE_ARTICLE, "title": "Low score"},
        {**BASE_ARTICLE, "title": "High score", "priority": True, "multi_source": True, "source_count": 2},
    ]
    sorted_articles = sort_by_score(articles)
    assert sorted_articles[0]["title"] == "High score"
