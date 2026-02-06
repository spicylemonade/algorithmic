from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from .agents import HeuristicAgent
from .env import Action, FiveDChessEnv


@dataclass
class EdgeStats:
    n: int = 0
    w: float = 0.0


@dataclass
class Node:
    prior: float = 1.0
    visits: int = 0
    value_sum: float = 0.0
    children: dict[Action, "Node"] = field(default_factory=dict)
    edges: dict[Action, EdgeStats] = field(default_factory=dict)


class PUCTMCTS:
    def __init__(self, simulations: int = 64, c_puct: float = 1.4, use_transpositions: bool = False, seed: int = 42):
        self.simulations = simulations
        self.c_puct = c_puct
        self.use_transpositions = use_transpositions
        self.rng = random.Random(seed)
        self.transpo: dict[str, Node] = {}
        self.expanded_nodes = 0

    def state_key(self, env: FiveDChessEnv) -> str:
        # Canonicalized by frontier board content (timeline-id agnostic) to capture transpositions.
        board_keys = []
        for tl, tm in sorted(env.timeline_latest.items()):
            b = env.boards[(tl, tm)]
            board_keys.append("/".join("".join(row) for row in b))
        board_keys.sort()
        return "|".join(board_keys)

    def _clone(self, env: FiveDChessEnv) -> FiveDChessEnv:
        sim = FiveDChessEnv(max_moves=env.max_moves)
        sim.seed = env.seed
        sim.rng = random.Random(env.seed)
        sim.move_count = env.move_count
        sim.side_to_move = env.side_to_move
        sim.next_timeline_id = env.next_timeline_id
        sim.done = env.done
        sim.boards = {k: [row[:] for row in b] for k, b in env.boards.items()}
        sim.timeline_latest = dict(env.timeline_latest)
        return sim

    def _policy_priors(self, legal: list[Action]) -> dict[Action, float]:
        if not legal:
            return {}
        # Encourage temporal options slightly to reflect branching opportunities.
        vals = [1.25 if a.src_time != a.dst_time else 1.0 for a in legal]
        s = sum(vals)
        return {a: v / s for a, v in zip(legal, vals)}

    def _leaf_value(self, env: FiveDChessEnv) -> float:
        if env.is_terminal():
            # from side-to-move perspective
            values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100}
            score = 0
            for b in env.boards.values():
                for row in b:
                    for p in row:
                        if p == ".":
                            continue
                        score += values.get(p.upper(), 0) if p.isupper() else -values.get(p.upper(), 0)
            if score == 0:
                return 0.0
            side_mult = 1.0 if env.side_to_move == "W" else -1.0
            return side_mult * (1.0 if score > 0 else -1.0)
        return 0.0

    def _timeline_consistent(self, env: FiveDChessEnv, action: Action) -> bool:
        return (action.src_timeline, action.src_time) in env.boards and (action.dst_timeline, action.dst_time) in env.boards

    def search(self, env: FiveDChessEnv) -> Action:
        root, _ = self._get_or_create_node(env)
        legal_root = env.legal_actions()
        if not legal_root:
            raise RuntimeError("No legal actions")

        for _ in range(self.simulations):
            sim = self._clone(env)
            node = root
            path: list[tuple[Node, Action]] = []

            while True:
                legal = sim.legal_actions()
                if not legal or sim.is_terminal():
                    value = self._leaf_value(sim)
                    break

                if not node.children:
                    priors = self._policy_priors(legal)
                    for a in legal:
                        if not self._timeline_consistent(sim, a):
                            continue
                        child_env = self._clone(sim)
                        child_env.step(a)
                        node.edges[a] = EdgeStats()
                        child, created = self._get_or_create_node(child_env, prior=priors.get(a, 0.0))
                        node.children[a] = child
                        if created:
                            self.expanded_nodes += 1
                    value = self._leaf_value(sim)
                    break

                total_n = max(1, sum(es.n for es in node.edges.values()))
                best_a = None
                best_u = -10**9
                for a, child in node.children.items():
                    es = node.edges[a]
                    q = 0.0 if es.n == 0 else es.w / es.n
                    u = q + self.c_puct * child.prior * math.sqrt(total_n) / (1 + es.n)
                    if u > best_u:
                        best_u = u
                        best_a = a
                assert best_a is not None
                path.append((node, best_a))
                sim.step(best_a)
                node = node.children[best_a]

            for n, a in reversed(path):
                es = n.edges[a]
                es.n += 1
                es.w += value
                n.visits += 1
                n.value_sum += value
                value = -value

        # Select most visited
        best = max(root.edges.items(), key=lambda kv: kv[1].n)[0]
        return best

    def _get_or_create_node(self, env: FiveDChessEnv, prior: float = 1.0) -> tuple[Node, bool]:
        if not self.use_transpositions:
            return Node(prior=prior), True
        k = self.state_key(env)
        if k not in self.transpo:
            self.transpo[k] = Node(prior=prior)
            return self.transpo[k], True
        return self.transpo[k], False


def run_item_013(out_path: str = "results/item_013_mcts_efficiency.json") -> dict:
    seeds = [42 + i for i in range(20)]
    base_nodes = 0
    trans_nodes = 0
    same_budget = 48
    repeats_per_position = 3

    for s in seeds:
        env = FiveDChessEnv(max_moves=12)
        env.reset(seed=s)

        for _ in range(repeats_per_position):
            baseline = PUCTMCTS(simulations=same_budget, use_transpositions=False, seed=42)
            _ = baseline.search(env)
            base_nodes += baseline.expanded_nodes

        trans = PUCTMCTS(simulations=same_budget, use_transpositions=True, seed=42)
        for _ in range(repeats_per_position):
            _ = trans.search(env)
            trans_nodes += trans.expanded_nodes
            trans.expanded_nodes = 0

    gain = (base_nodes - trans_nodes) / max(base_nodes, 1)
    result = {
        "item": "item_013",
        "seed": 42,
        "positions_evaluated": len(seeds),
        "repeats_per_position": repeats_per_position,
        "simulations_per_position": same_budget,
        "baseline_expanded_nodes": base_nodes,
        "transposition_expanded_nodes": trans_nodes,
        "node_efficiency_gain": gain,
        "acceptance_met": gain >= 0.20,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    return result


if __name__ == "__main__":
    run_item_013()
