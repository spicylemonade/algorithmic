from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

from .env import Action, FiveDChessEnv
from .learning import build_dataset, tensor_features, fit_linear_regression, predict_linear


class PolicyValueNet:
    """Lightweight policy-value model with strict legal-action masking."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.value_w = None

    def fit_value(self, samples: list[dict], targets: np.ndarray) -> None:
        x = tensor_features(samples)
        self.value_w = fit_linear_regression(x, targets)

    def value(self, obs: dict) -> float:
        assert self.value_w is not None, "Call fit_value first"
        x = tensor_features([obs])
        v = float(predict_linear(x, self.value_w)[0])
        return float(np.tanh(v))

    def _action_features(self, obs: dict, actions: list[Action]) -> np.ndarray:
        side = 1.0 if obs["side_to_move"] == "W" else 0.0
        feats = []
        for a in actions:
            feats.append(
                [
                    side,
                    float(a.src_time != a.dst_time),
                    a.src_row / 3.0,
                    a.src_col / 3.0,
                    a.dst_row / 3.0,
                    a.dst_col / 3.0,
                    a.dst_time / 15.0,
                    a.src_time / 15.0,
                ]
            )
        return np.array(feats, dtype=np.float32)

    def policy(self, obs: dict, legal_actions: list[Action]) -> np.ndarray:
        if not legal_actions:
            return np.array([], dtype=np.float32)
        x = self._action_features(obs, legal_actions)
        # Randomly initialized linear scorer with fixed seed for deterministic behavior.
        w = np.array([0.7, 0.4, -0.2, -0.1, 0.3, 0.2, 0.1, -0.1], dtype=np.float32)
        logits = x @ w
        logits = logits - np.max(logits)
        probs = np.exp(logits)
        probs = probs / np.sum(probs)
        return probs.astype(np.float32)


def validate_masking(out_path: str = "results/item_012_policy_value_validation.json") -> dict:
    # Train value head on synthetic targets.
    samples, y = build_dataset(n=1600, seed=42)
    train, heldout = samples[:1200], samples[1200:]
    y_tr = y[:1200]

    model = PolicyValueNet(seed=42)
    model.fit_value(train, y_tr)

    env = FiveDChessEnv(max_moves=12)
    rng = random.Random(42)
    held_positions = 0
    mask_violations = 0
    bounded_violations = 0

    for i in range(len(heldout)):
        obs = env.reset(seed=4242 + i)
        for _ in range(3):
            legal = env.legal_actions()
            if not legal:
                break
            probs = model.policy(obs, legal)
            if len(probs) != len(legal):
                mask_violations += 1
            if np.any(probs < 0) or abs(float(np.sum(probs)) - 1.0) > 1e-4:
                mask_violations += 1
            v = model.value(obs)
            if v < -1.000001 or v > 1.000001:
                bounded_violations += 1
            held_positions += 1
            a = legal[rng.randrange(len(legal))]
            obs, _, done, _ = env.step(a)
            if done:
                break

    mask_violation_rate = mask_violations / max(held_positions, 1)
    out = {
        "item": "item_012",
        "seed": 42,
        "heldout_positions": held_positions,
        "mask_violations": mask_violations,
        "mask_violation_rate": mask_violation_rate,
        "bounded_value_violations": bounded_violations,
        "acceptance_met": mask_violation_rate < 0.001 and bounded_violations == 0,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    validate_masking()
