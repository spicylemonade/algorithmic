from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PreprocessConfig:
    seed: int = 42
    sigma_clip: float = 3.5
    min_points_per_apparition: int = 12
    max_mag_err: float = 0.2
    zeropoint_ref: float = 0.0


def normalize_magnitude(mag: float, zeropoint: float) -> float:
    return mag - zeropoint


def reject_outliers(values: List[float], sigma: float) -> List[int]:
    if not values:
        return []
    mu = sum(values) / len(values)
    var = sum((x - mu) ** 2 for x in values) / len(values)
    std = var ** 0.5
    if std == 0.0:
        return list(range(len(values)))
    return [i for i, x in enumerate(values) if abs(x - mu) <= sigma * std]


def segment_apparitions(jds: List[float], gap_days: float = 120.0) -> List[int]:
    if not jds:
        return []
    out = [0]
    a = 0
    for i in range(1, len(jds)):
        if jds[i] - jds[i - 1] > gap_days:
            a += 1
        out.append(a)
    return out


def preprocess_records(records: List[Dict[str, float]], cfg: PreprocessConfig) -> List[Dict[str, float]]:
    mags = [r["mag"] for r in records if r.get("mag_err", 0.0) <= cfg.max_mag_err]
    keep_idx = reject_outliers(mags, cfg.sigma_clip)
    kept: List[Dict[str, float]] = []
    c = 0
    for r in records:
        if r.get("mag_err", 0.0) > cfg.max_mag_err:
            continue
        if c in keep_idx:
            rr = dict(r)
            rr["mag_norm"] = normalize_magnitude(rr["mag"], cfg.zeropoint_ref)
            kept.append(rr)
        c += 1
    app_ids = segment_apparitions([k["jd"] for k in kept])
    for k, app in zip(kept, app_ids):
        k["apparition_id"] = int(app)
    return kept
