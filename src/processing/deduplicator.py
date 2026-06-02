from difflib import SequenceMatcher


def title_similarity(a: str, b: str) -> float:
    a_norm = a.lower().strip()
    b_norm = b.lower().strip()
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def deduplicate(articles: list[dict], threshold: float = 0.75) -> list[dict]:
    groups: list[list[dict]] = []
    assigned = [False] * len(articles)

    for i, article in enumerate(articles):
        if assigned[i]:
            continue
        group = [article]
        assigned[i] = True
        for j in range(i + 1, len(articles)):
            if assigned[j]:
                continue
            if title_similarity(article["title"], articles[j]["title"]) >= threshold:
                group.append(articles[j])
                assigned[j] = True
        groups.append(group)

    result = []
    for group in groups:
        representative = group[0]
        source_count = len(group)
        sources = list({a["source"] for a in group})
        representative = {
            **representative,
            "multi_source": source_count > 1,
            "source_count": source_count,
            "all_sources": sources,
        }
        result.append(representative)

    return result
