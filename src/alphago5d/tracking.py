from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass
class RunRecord:
    run_id: str
    timestamp_utc: str
    seed: int
    config: Dict[str, Any]
    config_hash: str
    code_revision: str
    hardware_profile: Dict[str, Any]
    metrics: Dict[str, Any]


def stable_hash(config: Dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def hardware_profile() -> Dict[str, Any]:
    return {
        "machine": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def build_record(run_id: str, seed: int, config: Dict[str, Any], metrics: Dict[str, Any]) -> RunRecord:
    return RunRecord(
        run_id=run_id,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        seed=seed,
        config=config,
        config_hash=stable_hash(config),
        code_revision=git_revision(),
        hardware_profile=hardware_profile(),
        metrics=metrics,
    )


def save_record(path: Path, record: RunRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(record), indent=2) + "\n")
