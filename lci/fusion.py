"""Data fusion across heterogeneous photometric repositories."""

from __future__ import annotations


def harmonize_record(source: str, rec: dict) -> dict:
    return {
        "source": source,
        "target_id": rec.get("target_id") or rec.get("designation"),
        "jd": rec.get("jd") or rec.get("mjd"),
        "flux": rec.get("flux") or rec.get("calib_flux") or rec.get("mag"),
        "sigma": rec.get("sigma") or rec.get("err") or 0.05,
        "filter": rec.get("filter") or rec.get("band") or "V",
        "phase_angle_deg": rec.get("phase_angle_deg") or rec.get("alpha"),
        "apparition": rec.get("apparition") or rec.get("year_bin"),
        "provenance": {"source": source, "raw_id": rec.get("id")},
    }


def normalize_photometry(records: list[dict]) -> list[dict]:
    # Anchor each source by median subtraction in magnitude space.
    by_source = {}
    for r in records:
        by_source.setdefault(r["source"], []).append(r)
    for src, arr in by_source.items():
        vals = sorted(x["flux"] for x in arr if x["flux"] is not None)
        if not vals:
            continue
        med = vals[len(vals) // 2]
        for x in arr:
            x["flux_norm"] = x["flux"] - med
    return records


def reject_outliers(records: list[dict], zmax: float = 4.0) -> list[dict]:
    vals = [r.get("flux_norm", r.get("flux", 0.0)) for r in records]
    if not vals:
        return records
    mu = sum(vals) / len(vals)
    var = sum((v - mu) ** 2 for v in vals) / max(len(vals) - 1, 1)
    sigma = max(var**0.5, 1e-6)
    clean = []
    for r in records:
        v = r.get("flux_norm", r.get("flux", 0.0))
        if abs((v - mu) / sigma) <= zmax:
            clean.append(r)
    return clean
