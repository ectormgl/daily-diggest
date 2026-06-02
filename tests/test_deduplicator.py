# tests/test_deduplicator.py
from src.processing.deduplicator import deduplicate, title_similarity

def test_title_similarity_identical():
    assert title_similarity("GPT-5 Released Today", "GPT-5 Released Today") == 1.0


def test_title_similarity_different():
    score = title_similarity("Apple launches iPhone 17", "Microsoft releases Windows 12")
    assert score < 0.4


def test_title_similarity_near_duplicate():
    score = title_similarity(
        "OpenAI releases GPT-5 with improved reasoning",
        "OpenAI releases GPT-5 — improved reasoning capabilities",
    )
    assert score > 0.7


def test_deduplicate_removes_near_duplicate():
    articles = [
        {"title": "OpenAI releases GPT-5 with improved reasoning", "source": "TechCrunch", "source_type": "rss", "priority": False},
        {"title": "OpenAI releases GPT-5 — improved reasoning capabilities", "source": "The Verge", "source_type": "rss", "priority": False},
        {"title": "Apple launches M4 MacBook Pro", "source": "Wired", "source_type": "rss", "priority": False},
    ]
    result = deduplicate(articles, threshold=0.7)
    assert len(result) == 2
    titles = [a["title"] for a in result]
    assert "Apple launches M4 MacBook Pro" in titles


def test_deduplicate_keeps_multi_source_flag():
    articles = [
        {"title": "OpenAI GPT-5 announced", "source": "TechCrunch", "source_type": "rss", "priority": False},
        {"title": "OpenAI GPT-5 announced", "source": "The Verge", "source_type": "rss", "priority": False},
    ]
    result = deduplicate(articles, threshold=0.9)
    assert len(result) == 1
    assert result[0]["multi_source"] is True
    assert result[0]["source_count"] == 2


def test_deduplicate_unique_articles_unchanged():
    articles = [
        {"title": "Article A about AI", "source": "S1", "source_type": "rss", "priority": False},
        {"title": "Article B about robots", "source": "S2", "source_type": "rss", "priority": False},
        {"title": "Article C about quantum", "source": "S3", "source_type": "rss", "priority": False},
    ]
    result = deduplicate(articles, threshold=0.8)
    assert len(result) == 3
    for article in result:
        assert article["multi_source"] is False
        assert article["source_count"] == 1
