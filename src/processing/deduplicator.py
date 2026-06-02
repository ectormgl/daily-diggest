from difflib import SequenceMatcher


def _normalize(title: str) -> str:
    return title.lower().strip()


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def deduplicate(articles: list[dict], threshold: float = 0.75) -> list[dict]:
    n = len(articles)
    normalized = [_normalize(a["title"]) for a in articles]

    groups: list[list[dict]] = []
    assigned = [False] * n

    for i in range(n):
        if assigned[i]:
            continue
        group = [articles[i]]
        assigned[i] = True
        ni = normalized[i]
        len_i = len(ni)
        if len_i == 0:
            groups.append(group)
            continue

        for j in range(i + 1, n):
            if assigned[j]:
                continue
            nj = normalized[j]
            len_j = len(nj)
            if len_j == 0:
                continue

            # Length-ratio upper bound on SequenceMatcher.ratio:
            # ratio <= 2*min(len_a, len_b) / (len_a + len_b). Skip if already below threshold.
            short, long_ = (len_i, len_j) if len_i < len_j else (len_j, len_i)
            if 2 * short / (short + long_) < threshold:
                continue

            sm = SequenceMatcher(None, ni, nj)
            if sm.quick_ratio() < threshold:
                continue
            if sm.ratio() >= threshold:
                group.append(articles[j])
                assigned[j] = True

        groups.append(group)

    result = []
    for group in groups:
        representative = dict(group[0])
        source_count = len(group)
        sources = list({a["source"] for a in group})
        representative["multi_source"] = source_count > 1
        representative["source_count"] = source_count
        representative["all_sources"] = sources
        result.append(representative)

    return result
