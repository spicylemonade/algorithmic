# Metrics and Instrumentation Framework

## Core Metrics
- `elo`: rating estimate from arena match outcomes.
- `win_rate`: per-opponent win fraction.
- `node_expansions_per_sec`: MCTS simulation throughput.
- `training_throughput_samples_per_sec`: learner pipeline throughput.
- `wall_clock_cost_usd`: accumulated compute spend estimate.
- `memory_peak_mb`: process peak resident memory.

## Logging Schema
JSONL record per measurement interval:
- `step` (int)
- `elo` (float)
- `win_rate` (float in `[0,1]`)
- `node_expansions_per_sec` (float)
- `training_throughput_samples_per_sec` (float)
- `wall_clock_cost_usd` (float)
- `memory_peak_mb` (float)

## Collection Cadence
- Training metrics every 100 learner steps.
- Arena metrics every 5,000 self-play games.
- Profiling metrics (latency/memory) every promoted checkpoint.
