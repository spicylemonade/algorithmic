"""Target ranking for unknown NEA / MBA candidates."""

from __future__ import annotations


def candidate_score(c: dict) -> float:
    # Weighted composite score in [0, 1+] depending on novelty bonus.
    return (
        0.40 * c.get("model_confidence", 0.0)
        + 0.25 * c.get("data_coverage", 0.0)
        + 0.20 * c.get("inversion_stability", 0.0)
        + 0.15 * c.get("scientific_novelty", 0.0)
    )


def rank_candidates(candidates: list[dict]) -> list[dict]:
    enriched = []
    for c in candidates:
        row = dict(c)
        row["score"] = candidate_score(row)
        enriched.append(row)

    # Tie-breakers: higher novelty, then more sparse points, then lower designation.
    enriched.sort(
        key=lambda c: (
            c["score"],
            c.get("scientific_novelty", 0.0),
            c.get("sparse_points", 0),
            -c.get("designation_number", 10**9),
        ),
        reverse=True,
    )
    return enriched
