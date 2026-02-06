#!/usr/bin/env python3
import json
from pathlib import Path

SEED = 42


def conf(o):
    dense_score = min(1.0, o["dense_curves"] / 35.0)
    sparse_score = min(1.0, o["sparse_points"] / 220.0)
    app_score = min(1.0, o["apparitions"] / 6.0)
    u_score = min(1.0, o["lcdb_u"] / 3.0)
    size_bonus = 0.15 if o["diameter_km"] > 100 else 0.0
    neo_bonus = 0.1 if o["is_neo"] else 0.0
    c = 0.35 * max(dense_score, sparse_score) + 0.25 * app_score + 0.25 * u_score + size_bonus + neo_bonus
    return max(0.0, min(1.0, c))


def main():
    selected = json.loads(Path("results/item_020_selected_candidates.json").read_text())
    ranked = []
    for o in selected:
        c = conf(o)
        rationale = []
        if o["is_neo"]:
            rationale.append("NEO")
        if o["diameter_km"] > 100:
            rationale.append(">100km")
        if o["dense_curves"] >= 20:
            rationale.append("dense>=20")
        if o["sparse_points"] >= 100 and o["apparitions"] > 3:
            rationale.append("sparse>=100 over >3 apparitions")
        ranked.append({
            **o,
            "confidence": round(c, 4),
            "ranking_rationale": ", ".join(rationale),
        })

    ranked.sort(key=lambda x: (x["confidence"], x["dense_curves"], x["sparse_points"], x["diameter_km"]), reverse=True)
    top50 = ranked[:50]
    for i, r in enumerate(top50, 1):
        r["rank"] = i

    Path("results/item_021_top50_candidates.json").write_text(json.dumps({"item_id":"item_021","seed":SEED,"count":len(top50),"candidates":top50}, indent=2))


if __name__ == "__main__":
    main()
