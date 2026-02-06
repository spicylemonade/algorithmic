"""Target ranking for unknown NEA / MBA candidates."""


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: c.get("score", 0.0), reverse=True)
