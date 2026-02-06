from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Tuple

import numpy as np

from .env import FiveDChessEnv
from .schema import StateSchema


def material_value(obs: dict) -> float:
    values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100}
    score = 0
    for board in obs["boards"].values():
        for row in board:
            for p in row:
                if p == ".":
                    continue
                v = values.get(p.upper(), 0)
                score += v if p.isupper() else -v
    return float(np.tanh(score / 20.0))


def build_dataset(n: int = 3000, seed: int = 42) -> Tuple[list[dict], np.ndarray]:
    rng = random.Random(seed)
    env = FiveDChessEnv(max_moves=18)
    samples = []
    y = []
    while len(samples) < n:
        obs = env.reset(seed=seed + len(samples))
        for _ in range(8):
            samples.append(obs)
            y.append(material_value(obs))
            if len(samples) >= n:
                break
            acts = env.legal_actions()
            if not acts:
                break
            a = acts[rng.randrange(len(acts))]
            obs, _, done, _ = env.step(a)
            if done:
                break
    return samples, np.array(y, dtype=np.float32)


def tensor_features(samples: list[dict]) -> np.ndarray:
    schema = StateSchema(max_timelines=8, max_time=16)
    xs = []
    for obs in samples:
        st = schema.encode(obs)
        xs.append(st.tensor.astype(np.float32).reshape(-1))
    return np.stack(xs, axis=0)


def graph_features(samples: list[dict]) -> np.ndarray:
    feats = []
    for obs in samples:
        tl_count = len(obs["timeline_latest"])
        latest_times = list(obs["timeline_latest"].values())
        max_time = max(latest_times) if latest_times else 0
        mean_time = float(np.mean(latest_times)) if latest_times else 0.0
        piece_counts = {k: 0 for k in ["P", "R", "N", "B", "Q", "K", "p", "r", "n", "b", "q", "k"]}
        for b in obs["boards"].values():
            for row in b:
                for p in row:
                    if p in piece_counts:
                        piece_counts[p] += 1
        white = sum(piece_counts[p] for p in ["P", "R", "N", "B", "Q", "K"])
        black = sum(piece_counts[p] for p in ["p", "r", "n", "b", "q", "k"])
        f = [
            tl_count,
            max_time,
            mean_time,
            len(obs["boards"]),
            1.0 if obs["side_to_move"] == "W" else 0.0,
            white,
            black,
            white - black,
        ] + [piece_counts[p] for p in ["P", "R", "K", "p", "r", "k"]]
        feats.append(np.array(f, dtype=np.float32))
    return np.stack(feats, axis=0)


def fit_linear_regression(x: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    x_aug = np.concatenate([x, np.ones((x.shape[0], 1), dtype=np.float32)], axis=1)
    eye = np.eye(x_aug.shape[1], dtype=np.float32)
    w = np.linalg.solve(x_aug.T @ x_aug + ridge * eye, x_aug.T @ y)
    return w


def predict_linear(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    x_aug = np.concatenate([x, np.ones((x.shape[0], 1), dtype=np.float32)], axis=1)
    return x_aug @ w


def mse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean((a - b) ** 2))


def run_item_011(out_path: str = "results/item_011_encoder_comparison.json") -> dict:
    samples, y = build_dataset(n=3200, seed=42)
    n_train = 2600
    tr_samples, va_samples = samples[:n_train], samples[n_train:]
    y_tr, y_va = y[:n_train], y[n_train:]

    x_t_tr, x_t_va = tensor_features(tr_samples), tensor_features(va_samples)
    x_g_tr, x_g_va = graph_features(tr_samples), graph_features(va_samples)

    w_t = fit_linear_regression(x_t_tr, y_tr)
    w_g = fit_linear_regression(x_g_tr, y_tr)

    p_t = predict_linear(x_t_va, w_t)
    p_g = predict_linear(x_g_va, w_g)

    result = {
        "item": "item_011",
        "seed": 42,
        "dataset_size": len(samples),
        "train_size": n_train,
        "val_size": len(samples) - n_train,
        "encoders": {
            "tensor_stack": {"val_value_mse": mse(y_va, p_t)},
            "graph_features": {"val_value_mse": mse(y_va, p_g)},
        },
        "better_encoder": "tensor_stack" if mse(y_va, p_t) <= mse(y_va, p_g) else "graph_features",
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    return result


if __name__ == "__main__":
    run_item_011()
