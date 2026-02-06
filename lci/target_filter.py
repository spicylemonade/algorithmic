"""Target selection filter for unknown NEA/large MBA candidates."""

from __future__ import annotations


def is_priority_candidate(obj: dict) -> bool:
    p1 = obj.get("is_neo", False) or obj.get("diameter_km", 0.0) > 100.0
    p2 = obj.get("lcdb_u", 0) >= 2
    p3 = not obj.get("in_damit", False)
    dense_ok = obj.get("dense_lightcurves", 0) > 20
    sparse_ok = obj.get("sparse_points", 0) > 100 and obj.get("apparitions", 0) > 3
    p4 = dense_ok or sparse_ok
    return p1 and p2 and p3 and p4


def filter_candidates(catalog: list[dict]) -> list[dict]:
    return [obj for obj in catalog if is_priority_candidate(obj)]
