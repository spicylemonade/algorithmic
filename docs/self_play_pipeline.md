# Self-Play Data Generation Pipeline

## Worker Topology
- `N` asynchronous self-play workers (baseline `N=4`) each running search-guided gameplay.
- Central learner consumes trajectories from replay buffer snapshots.
- Promotion server swaps active model only after arena gate.

## Replay Buffer Policy
- Capacity: 10k trajectories (baseline prototype), ring-buffer eviction oldest-first.
- Sampling mix: 80% recent (fresh) + 20% uniform historical.

## Target Generation
- Policy target: normalized MCTS visit counts at each move.
- Value target: final game outcome `z in {-1,0,1}` assigned to each visited state.

## Freshness Constraints
- Fresh sample window: last 50 games must contribute at least 40% of minibatch.
- Staleness cap: trajectories older than 5 model versions down-weighted.

## Throughput Target
- Minimum target throughput: `>= 12,000 games/hour` aggregated across workers.
