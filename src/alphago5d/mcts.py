from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Node:
    prior: float
    value_sum: float = 0.0
    visits: int = 0
    children: Dict[int, "Node"] = field(default_factory=dict)

    def q(self) -> float:
        return self.value_sum / self.visits if self.visits > 0 else 0.0


class PUCT:
    def __init__(self, c_puct: float = 1.5):
        self.c_puct = c_puct

    def normalize_priors(self, priors: Dict[int, float]) -> Dict[int, float]:
        total = sum(max(v, 0.0) for v in priors.values())
        if total <= 0:
            n = max(1, len(priors))
            return {k: 1.0 / n for k in priors}
        return {k: max(v, 0.0) / total for k, v in priors.items()}

    def expand(self, node: Node, priors: Dict[int, float]) -> None:
        p = self.normalize_priors(priors)
        for a, prior in p.items():
            node.children[a] = Node(prior=prior)

    def select(self, node: Node) -> int:
        assert node.children, "select called on leaf"
        sqrt_n = math.sqrt(max(1, node.visits))
        best_a = None
        best_score = -10**9
        for a, child in node.children.items():
            u = self.c_puct * child.prior * sqrt_n / (1 + child.visits)
            score = child.q() + u
            if score > best_score:
                best_score = score
                best_a = a
        return int(best_a)

    def backup(self, path: list[Node], leaf_value: float) -> None:
        v = leaf_value
        for node in reversed(path):
            node.visits += 1
            node.value_sum += v
            v = -v
