# Self-Play Curriculum and Replay Governance

Temperature schedule:
- Early exploration: `tau=1.0` for first `200k` games.
- Mid training: `tau=0.5` until `800k` games.
- Late exploitation: `tau=0.1` afterwards.

Resignation policy:
- Enabled after warm-up (`150k` games).
- Trigger when value head predicts `< -0.92`.
- Keep 10% no-resign verification games to prevent false resign collapses.

Replay buffer governance:
- Sliding window of `500k` games.
- Weighted sampling: recent `55%`, mid `30%`, old `15%`.
- Enforce minibatch deduplication by state hash.

Operational targets:
- Game generation target: `25k games/hour`.
- Diversity metrics tracked each 5k games:
  - opening entropy >= `4.0` bits,
  - timeline-branch JSD <= `0.18`,
  - unique-state-hash ratio >= `0.72`.
