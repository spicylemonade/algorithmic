# Training Curriculum and Stabilization

## Staged Curriculum
1. **Stage A (bootstrap)**
   - Simulations: 64
   - Temperature: high (`1.0`) first 10 plies
   - Goal: legal move reliability and basic tactical motifs
2. **Stage B (intermediate)**
   - Simulations: 200
   - Temperature schedule: `1.0 -> 0.5` by ply 30
   - Goal: stable value calibration and stronger search-policy coupling
3. **Stage C (advanced)**
   - Simulations: 800
   - Temperature: near-greedy (`0.1`) after opening
   - Goal: Elo maximization and endgame precision

## Stabilization Mechanisms
- Conservative resignation threshold schedule from `-0.98` to `-0.90`.
- 5% no-resign probe games to debias false resignations.
- Gradient clipping at norm `1.0`.
- EMA target network for value smoothing.

## Hyperparameter Ranges
- Learning rate: `1e-4` to `3e-3`
- Weight decay: `1e-6` to `1e-3`
- Value loss coefficient: `0.5` to `2.0`
- Policy loss coefficient: `0.8` to `1.2`

## Promotion Criteria
- Promote stage when all are met over rolling 10k games:
  - Elo gain >= 60 vs previous stage champion
  - Illegal move rate <= 1e-6
  - Win rate >= 55% in gate arena
