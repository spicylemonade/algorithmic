"""Top-level orchestration for LCI experiments."""

from lci.config import RunConfig


def run_target(target_id: str, config: RunConfig | None = None):
    config = config or RunConfig()
    return {"target_id": target_id, "seed": config.seed, "status": "not_implemented"}
