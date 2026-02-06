# Formal 5D Chess Problem Statement

## Environment Definition
- **State `s_t`**: Tuple `(timelines, side_to_move, castling_rights, en_passant, repetition_hashes, halfmove_clock, fullmove_number)` where each timeline stores an ordered set of boards indexed by `(timeline_id, time_index)`.
- **Action `a_t`**: Move tuple `(source_timeline, source_time, source_square, target_timeline, target_time, target_square, promotion_piece, special_flag)` with legality conditioned on 5D movement rules.
- **Transition `T(s_t, a_t) -> s_{t+1}`**: Applies move on source board, creates/extends timelines for temporal moves, updates clocks and rights, and resolves checks/checkmates across active timelines.
- **Reward `r_t`**: `+1` win, `-1` loss, `0` draw for terminal states; optional shaped auxiliary rewards remain disabled in baseline.
- **Terminal**: True on checkmate, stalemate, threefold repetition, 50-move rule, insufficient material, or adjudication timeout.

## Constraints
- Move must originate from a piece owned by `side_to_move` at the selected `(timeline,time,square)`.
- Destination must satisfy piece kinematics in spatial-temporal manifold.
- Resulting global position must not leave own king in check in any active present board.

## Worked Examples
1. **Legal spatial move**: White knight from `(L0,T4,g1)` to `(L0,T4,f3)` is legal because knight displacement `(−1,+2)` is valid and destination is empty.
2. **Illegal spatial move**: White bishop from `(L0,T4,c1)` to `(L0,T4,c3)` is illegal because bishop requires diagonal motion but file is unchanged.
3. **Legal temporal branch move**: White rook from `(L0,T6,a1)` to `(L+1,T5,a1)` is legal when rules permit backward-time rook transfer and branch `L+1` is created with copied prior board context.
4. **Illegal temporal move**: White pawn from `(L0,T6,e5)` to `(L0,T5,e5)` is illegal in baseline rule set because pawns cannot move backward in time.
5. **Legal capture creating checkmate**: Black queen from `(L0,T9,h4)` to `(L0,T9,e1)` captures and checkmates if no legal king escape exists across active timelines.
6. **Illegal self-check**: White king from `(L0,T10,e1)` to `(L0,T10,e2)` is illegal if black rook on `e8` gives open-file check after move.

## Optimization Objective
Find policy `pi(a|s)` and value `v(s)` maximizing expected terminal reward under self-play and search-improved policy iteration:
`max_{theta} E_{s~self-play}[ z * log v_theta(s) + pi_mcts(\cdot|s)^T log pi_theta(\cdot|s) ]`.
