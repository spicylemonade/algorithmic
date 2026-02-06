import random

from alphago5d.encoding import CanonicalEncoder
from alphago5d.state import sample_state


def test_roundtrip_100_states_seed_42() -> None:
    rng = random.Random(42)
    encoder = CanonicalEncoder()

    for _ in range(100):
        state = sample_state(rng)
        encoded = encoder.encode(state)
        decoded = encoder.decode(
            encoded,
            side_to_move=state.side_to_move,
            halfmove_clock=state.halfmove_clock,
            fullmove_number=state.fullmove_number,
        )
        assert decoded.boards == state.boards
        assert decoded.side_to_move == state.side_to_move
        assert decoded.halfmove_clock == state.halfmove_clock
        assert decoded.fullmove_number == state.fullmove_number
