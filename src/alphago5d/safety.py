from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyThresholds:
    policy_entropy_min: float = 0.4
    resign_rate_max: float = 0.75
    value_std_min: float = 0.05
    replay_uniqueness_min: float = 0.60


def detect_training_collapse(entropy: float, thresholds: SafetyThresholds) -> bool:
    return entropy < thresholds.policy_entropy_min


def detect_resign_exploit(resign_rate: float, thresholds: SafetyThresholds) -> bool:
    return resign_rate > thresholds.resign_rate_max


def detect_value_head_saturation(value_std: float, thresholds: SafetyThresholds) -> bool:
    return value_std < thresholds.value_std_min


def detect_replay_mode_collapse(unique_ratio: float, thresholds: SafetyThresholds) -> bool:
    return unique_ratio < thresholds.replay_uniqueness_min
