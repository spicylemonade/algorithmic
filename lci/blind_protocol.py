"""Blinded execution protocol for validation runs."""

from __future__ import annotations

from datetime import datetime, timezone


def start_blind_run(target_id: str, seed: int = 42):
    return {
        "target_id": target_id,
        "seed": seed,
        "ground_truth_visible": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "events": [],
    }


def log_event(run_log: dict, message: str):
    run_log["events"].append({"ts": datetime.now(timezone.utc).isoformat(), "message": message})


def finalize_blind_run(run_log: dict, metrics: dict):
    run_log["completed_at"] = datetime.now(timezone.utc).isoformat()
    run_log["metrics"] = metrics
    run_log["ground_truth_unsealed_after_opt"] = True
    return run_log
