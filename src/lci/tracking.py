from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict


@dataclass
class RunMetadata:
    run_id: str
    timestamp_utc: str
    seed: int
    git_commit: str
    config_hash: str
    data_snapshot_hash: str
    command: str


def sha256_json(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def git_commit_hash() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        out = "unknown"
    return out


def create_run_metadata(config: Dict[str, Any], data_snapshot: Dict[str, Any], command: str, seed: int = 42) -> RunMetadata:
    cfg_hash = sha256_json(config)
    data_hash = sha256_json(data_snapshot)
    ts = datetime.now(timezone.utc).isoformat()
    run_id = hashlib.sha256(f"{ts}:{cfg_hash}:{data_hash}".encode()).hexdigest()[:16]
    return RunMetadata(
        run_id=run_id,
        timestamp_utc=ts,
        seed=seed,
        git_commit=git_commit_hash(),
        config_hash=cfg_hash,
        data_snapshot_hash=data_hash,
        command=command,
    )


def save_run_metadata(path: str, meta: RunMetadata) -> None:
    p = Path(path)
    p.write_text(json.dumps(asdict(meta), indent=2) + "\n")
