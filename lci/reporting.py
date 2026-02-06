"""Result packaging and manifest generation."""

from __future__ import annotations


def build_manifest(target: dict):
    tid = target["target_id"]
    return {
        "target_id": tid,
        "deliverables": {
            "mesh_obj": f"outputs/{tid}/shape.obj",
            "spin_vector": {
                "lambda_deg": target.get("lambda_deg"),
                "beta_deg": target.get("beta_deg"),
                "period_h": target.get("period_h"),
            },
            "uncertainty": {
                "lambda_ci_deg": target.get("lambda_ci_deg", [None, None]),
                "beta_ci_deg": target.get("beta_ci_deg", [None, None]),
                "period_ci_h": target.get("period_ci_h", [None, None]),
            },
            "provenance_manifest": {
                "photometry_sources": target.get("photometry_sources", []),
                "ground_truth_ref": target.get("ground_truth_ref"),
                "run_id": target.get("run_id"),
            },
        },
    }
