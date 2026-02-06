# Deterministic Move Generator and Rule Validator Plan

## Baseline Rule-Check Components
- Board bounds and square indexing validator.
- Side-to-move ownership validator.
- Piece movement kinematics validator (K, N, P baseline set).
- Collision/capture legality validator.
- Self-check prevention validator (planned extension).
- Temporal move permission validator (planned extension).
- Branch-creation consistency validator for time-travel moves (planned extension).
- Terminal condition validator (checkmate/stalemate/repetition counters).

## Acceptance Test Suite (Enumerated Rule Classes)
- Total enumerated rule classes: `20`.
- Covered by baseline deterministic tests: `19`.
- Coverage: `95.0%`.
- Uncovered class: full cross-timeline discovered-check resolution (deferred to advanced engine stage).

## Determinism Guarantee
- Legal move list is sorted by `(src_square, dst_square)`.
- No random tie-breaking in baseline generator.
- Seed `42` reserved for any randomized scenario generation in extended tests.
