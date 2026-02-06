# 5D Chess Research Specification

## Formal Game Definition
- State `s_t`: tuple `(U_t, p_t, h_t)` where `U_t` is a multiverse set of timeline boards indexed by `(tau, lambda)`, `p_t` is side-to-move, and `h_t` is move history including branch-generation events.
- Board atom: each board node `B[timeline_id][time_index]` contains piece placement, castling rights, en-passant rights, and check flags.
- Action `a_t`: `(src_timeline, src_time, src_square, dst_timeline, dst_time, dst_square, promotion)` permitting spatial moves and temporal moves that create or target other timeline/time nodes.
- Transition `T(s_t, a_t) -> s_{t+1}`: applies legal move, resolves captures/check status, potentially creates new timeline branch if move targets a past board not on active frontier, then advances active turn frontier.
- Legality `L(s_t)`: action is legal if source piece belongs to `p_t`, movement is piece-valid in space-time topology, no causal paradox constraints are violated, and resulting king safety constraints hold for all active present boards.
- Terminal predicate `Z(s_t)`: true if side-to-move has no legal actions in all active present boards and is checkmated; may also terminate by repetition/stalemate/50-move-type rule generalized over multiverse histories.
- Scoring `R(s_T)`: win `+1`, draw `0`, loss `-1` from white perspective; optional shaping tracks material and timeline-control but final optimization target is terminal outcome.

## Complexity Drivers Unique to 5D/Timeline Chess
1. Action-space explosion from destination timeline/time coordinates in addition to squares.
2. Variable branching due to timeline creation events.
3. Non-uniform game graph depth because branches evolve asynchronously.
4. Causal consistency constraints across timeline ancestors.
5. Multiple simultaneous "present" boards requiring joint tactical evaluation.
6. Transpositions across different branch histories with equivalent board tensors.
7. Delayed reward assignment when a temporal move affects future tactical outcomes many plies later.
8. Legality checking requires cross-board king-safety propagation.
9. Representation challenge: sparse but high-dimensional multiverse occupancy tensors.
10. Symmetry handling is weaker than classical chess because time direction breaks equivalences.
11. Search budget allocation must decide among timelines, not only moves.
12. End condition detection spans composite frontier states rather than one board.

## Computational Implications
- Planning requires hybrid local tactics + global timeline management.
- Value targets have higher variance than standard chess due to delayed temporal effects.
- Efficient systems need transposition-aware MCTS and compressed multiverse encodings.
