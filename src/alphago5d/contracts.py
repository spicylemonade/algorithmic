from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Move:
    src_timeline: int
    src_time: int
    src_square: int
    dst_timeline: int
    dst_time: int
    dst_square: int
    promotion: int = 0
    flags: int = 0


@dataclass(frozen=True)
class EncodedState:
    tensor_shape: tuple[int, int, int, int, int]
    data: Any
    legal_mask: Any


@dataclass(frozen=True)
class EvaluationSample:
    state_id: str
    policy_logits: list[float]
    value: float


class GameEngine(Protocol):
    def initial_state(self, seed: int = 42) -> Any:
        """Return deterministic initial state for a game instance."""

    def legal_moves(self, state: Any) -> list[Move]:
        """Return all legal moves; raise ValueError if state is invalid."""

    def apply_move(self, state: Any, move: Move) -> Any:
        """Apply move and return next state; raise RuntimeError on illegal transition."""

    def is_terminal(self, state: Any) -> bool:
        """Return terminal condition flag."""

    def terminal_value(self, state: Any) -> float:
        """Return value in [-1, 1] from current-player perspective."""


class StateEncoder(Protocol):
    def encode(self, state: Any) -> EncodedState:
        """Encode state to tensor; raise ValueError if state is incomplete."""

    def decode(self, encoded: EncodedState) -> Any:
        """Decode tensor to structured state for round-trip checks."""


class PolicyValueModel(Protocol):
    def predict(self, encoded_state: EncodedState) -> EvaluationSample:
        """Run inference; raise RuntimeError on shape mismatch or NaN outputs."""

    def train_step(self, batch: list[tuple[EncodedState, list[float], float]]) -> dict[str, float]:
        """Execute one optimization step and return scalar losses."""


class MCTSPlanner(Protocol):
    def search(self, state: Any, simulations: int, temperature: float) -> tuple[list[float], float]:
        """Return move probabilities and root value; raise TimeoutError if budget exhausted."""


class SelfPlayWorker(Protocol):
    def play_game(self, seed: int = 42) -> dict[str, Any]:
        """Generate one self-play game trajectory and training targets."""


class Evaluator(Protocol):
    def run_match(self, agent_a: Any, agent_b: Any, games: int, seed: int = 42) -> dict[str, float]:
        """Run evaluation match and return aggregate metrics."""
