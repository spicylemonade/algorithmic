# Formal 5D Chess Problem Specification

## Objective
Design an AlphaGo-style agent that maximizes expected game outcome in 5D chess under perfect-information, turn-based, deterministic rules with trans-temporal moves.

## State
A state `s_t` is a tuple:
- `B`: set of boards indexed by `(timeline_id, time_index)`.
- `P`: piece placements on each board square.
- `A`: active player to move (`white` or `black`).
- `C`: castling rights per timeline.
- `E`: en-passant targets per timeline and time.
- `H`: halfmove clock and repetition counters.
- `L`: legality metadata including check status and branch provenance.

The canonical tensor view used by learning components is a 6D tensor:
- axes: `[timeline, time, rank, file, channel, history]`.

## Action Space
An action `a_t` is indexed by:
- source board `(l_s, t_s)` and square `(r_s, f_s)`.
- destination board `(l_d, t_d)` and square `(r_d, f_d)`.
- promotion type (optional).
- branch operation flag when move creates a new timeline.

Legal actions satisfy:
- piece movement constraints,
- causality constraints for time travel,
- king safety constraints across all affected timelines.

## Transition Function
`T(s_t, a_t) -> s_{t+1}` is deterministic:
1. Validate move legality.
2. Apply piece movement and captures on destination board-time.
3. If move enters past board-time, spawn/extend timeline branch.
4. Update check/checkmate/stalemate/repetition metadata.
5. Flip active player.

## Reward Function
Terminal sparse reward:
- `+1`: win,
- `0`: draw,
- `-1`: loss.

Optional shaping for training only:
- small material delta reward clipped to `[-0.05, 0.05]`.
- branch-efficiency penalty `-0.01` per unnecessary branch.

## Terminal Conditions
A state is terminal when any holds:
- checkmate on required present board set,
- valid resignation,
- draw by stalemate, repetition threshold, 50-move rule, or insufficient material,
- move limit reached (protocol-defined adjudication).

## Tie-Breaking and Outcome Conventions
When multiple terminal conditions trigger simultaneously:
1. Checkmate dominance: checkmate overrides draw claims.
2. Forced-draw hierarchy: stalemate > repetition > 50-move > insufficient material.
3. If unresolved by rule ordering, adjudicate by deterministic material+mobility score from current-player perspective.

## Worked Examples
1. **Standard non-branch move**
   - White knight moves within `(l=0,t=5)` from `g1` to `f3`.
   - No branch creation.
   - `A` toggles to black; clocks updated.

2. **Past-directed move creating timeline**
   - Black rook from `(l=0,t=8)` moves to `(l=0,t=6)` capturing a piece.
   - New branch `(l=+1)` spawned from `t=6` with modified board history.
   - Future boards in old timeline remain unchanged but no longer sole present frontier.

3. **Simultaneous draw/check condition resolution**
   - Move yields repetition count threshold and puts opponent in checkmate on all present boards.
   - Rule ordering returns terminal win (`+1`) due to checkmate dominance.
