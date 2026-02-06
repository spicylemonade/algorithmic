from __future__ import annotations

from dataclasses import dataclass

from .contracts import EncodedState
from .state import GameState, Tensor5D


@dataclass(frozen=True)
class EncodingSpec:
    timelines: int = 2
    times: int = 3
    channels: int = 16
    height: int = 8
    width: int = 8


class CanonicalEncoder:
    def __init__(self, spec: EncodingSpec | None = None):
        self.spec = spec or EncodingSpec()

    def _shape(self, boards: Tensor5D) -> tuple[int, int, int, int, int]:
        return (
            len(boards),
            len(boards[0]),
            len(boards[0][0]),
            len(boards[0][0][0]),
            len(boards[0][0][0][0]),
        )

    def encode(self, state: GameState) -> EncodedState:
        expected = (
            self.spec.timelines,
            self.spec.times,
            self.spec.channels,
            self.spec.height,
            self.spec.width,
        )
        shape = self._shape(state.boards)
        if shape != expected:
            raise ValueError(f"Expected boards shape {expected}, got {shape}")

        clipped: Tensor5D = []
        for timeline in state.boards:
            tcopy = []
            for tstep in timeline:
                scopy = []
                for plane in tstep:
                    pcopy = []
                    for row in plane:
                        pcopy.append([max(-1, min(1, int(v))) for v in row])
                    scopy.append(pcopy)
                tcopy.append(scopy)
            clipped.append(tcopy)

        action_dim = self.spec.timelines * self.spec.times * 64 * self.spec.timelines * self.spec.times * 64
        legal_mask = [1.0] * action_dim
        return EncodedState(tensor_shape=shape, data=clipped, legal_mask=legal_mask)

    def decode(self, encoded: EncodedState, side_to_move: int = 0, halfmove_clock: int = 0, fullmove_number: int = 1) -> GameState:
        boards = encoded.data
        return GameState(
            boards=boards,
            side_to_move=side_to_move,
            halfmove_clock=halfmove_clock,
            fullmove_number=fullmove_number,
        )
