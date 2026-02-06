"""Hybrid convex-to-evolutionary schedule."""

from __future__ import annotations


def should_handoff(convex_result: dict) -> bool:
    rms = convex_result.get("rms", 1.0)
    complexity = convex_result.get("shape_complexity", 0.0)
    return (rms > 0.03) or (complexity > 0.35)


def build_schedule():
    return {
        "stages": [
            {
                "name": "convex_bootstrap",
                "goal": "resolve period/pole and global convex silhouette",
                "stop": "grad_tol or rel_obj_tol or max_iters",
            },
            {
                "name": "handoff_gate",
                "trigger": "rms>0.03 OR shape_complexity>0.35",
                "action": "seed evolutionary population from convex state",
            },
            {
                "name": "nonconvex_refine",
                "goal": "recover concavities while preserving fit stability",
                "stop": "fitness plateau patience reached",
            },
        ]
    }
