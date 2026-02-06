# Locked Evaluation Protocol

## Randomness and Seeds
- Global fixed seed: `42`
- Matchmaking seeds: `42 + match_id`
- Data split seeds: fixed deterministic split map committed in `results/`

## Match Formats
- Primary rating format: 2-game mini-match with color swap.
- Time controls: fast (`0.2s/move`) and medium (`1.0s/move`) search budgets.
- Opening diversity: stratified position buckets (in-distribution and held-out suites).

## Statistical Standards
- Report win rate, draw rate, Elo, and 95% confidence intervals.
- Significance test: two-sided test on score difference, alpha `0.05`.
- Minimum practical effect for promotion: lower bound of Elo improvement CI > `+30`.

## Minimum Sample Sizes
- Power analysis target: 95% confidence and 80% power for 5-point win-rate gain.
- Required games (head-to-head): see `results/item_009_power_analysis.json`.
- Benchmark gate: at least this minimum plus 10% buffer for robustness.

## Data Splits
- `train`: self-play generated positions.
- `val`: held-out checkpoints from same distribution.
- `test_id`: in-distribution fixed opening suite.
- `test_ood`: unseen timelines/openings/adversarial style suites.

## Reproducibility Rules
- Pin code revision hash per run.
- Record full config hash and hardware profile.
- No post-hoc protocol changes after this lock.
