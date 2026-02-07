#!/usr/bin/env python3
import json
from pathlib import Path


def run():
    data = json.loads(Path("results/item_021_candidates.json").read_text())["candidates"]

    ranked = []
    for r in data:
        data_completeness = min(1.0, (r["n_lightcurves"] / 40.0) * 0.55 + (r["n_sparse_points"] / 220.0) * 0.45)
        geometry_coverage = min(1.0, r["n_apparitions"] / 6.0)
        confidence = min(1.0, (r["lcdb_u"] / 3.0) * 0.6 + geometry_coverage * 0.4)
        pass_bonus = 0.2 if r["passes_all"] else 0.0
        score = 0.45 * data_completeness + 0.30 * geometry_coverage + 0.25 * confidence + pass_bonus

        ranked.append({
            "object_id": r["object_id"],
            "passes_all": r["passes_all"],
            "data_completeness": data_completeness,
            "geometry_coverage": geometry_coverage,
            "confidence_estimate": confidence,
            "rank_score": score,
            "provenance_links": {
                "selection_record": f"results/item_021_candidates.json#{r['object_id']}",
                "jpl_sbdb": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={r['object_id']}",
                "mpc": f"https://minorplanetcenter.net/db_search/show_object?object_id={r['object_id']}",
            },
        })

    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    top50 = ranked[:50]

    out = {
        "item_id": "item_022",
        "top_n": 50,
        "generated_count": len(top50),
        "acceptance_pass": bool(len(top50) == 50 and all(all(k in x for k in ["data_completeness", "geometry_coverage", "confidence_estimate", "provenance_links"]) for x in top50)),
        "top_candidates": top50,
    }
    Path("results/item_022_top50.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    run()
