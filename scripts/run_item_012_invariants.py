#!/usr/bin/env python3
import json
import random
from pathlib import Path

from alphago5d.mcts import Node, PUCT


def run_tree(rng: random.Random) -> dict:
    puct = PUCT(c_puct=1.5)
    root = Node(prior=1.0)
    priors = {a: rng.random() for a in range(rng.randint(8, 20))}
    puct.expand(root, priors)

    prior_sum = sum(c.prior for c in root.children.values())
    monotonic = True
    backup_ok = True
    prev_visits = 0

    for _ in range(50):
        path = [root]
        cur = root
        for _ in range(3):
            if not cur.children:
                puct.expand(cur, {a: rng.random() for a in range(rng.randint(3, 8))})
            a = puct.select(cur)
            cur = cur.children[a]
            path.append(cur)
        leaf_value = rng.uniform(-1, 1)
        before = [n.visits for n in path]
        puct.backup(path, leaf_value)
        after = [n.visits for n in path]
        if any(y < x for x, y in zip(before, after)):
            monotonic = False
        if root.visits < prev_visits:
            monotonic = False
        prev_visits = root.visits

        expected_delta = 1
        if any((y - x) != expected_delta for x, y in zip(before, after)):
            backup_ok = False

    return {
        "prior_sum": prior_sum,
        "prior_norm_ok": abs(prior_sum - 1.0) < 1e-6,
        "visit_monotonic": monotonic,
        "backup_correct": backup_ok,
    }


def main() -> None:
    rng = random.Random(42)
    checks = [run_tree(rng) for _ in range(100)]
    passed = all(c["prior_norm_ok"] and c["visit_monotonic"] and c["backup_correct"] for c in checks)
    out = {
        "item_id": "item_012",
        "seed": 42,
        "trees_tested": 100,
        "passed": passed,
        "summary": {
            "prior_norm_pass": sum(1 for c in checks if c["prior_norm_ok"]),
            "visit_monotonic_pass": sum(1 for c in checks if c["visit_monotonic"]),
            "backup_pass": sum(1 for c in checks if c["backup_correct"]),
        },
    }
    Path("results/item_012_mcts_invariants.json").write_text(json.dumps(out, indent=2) + "\n")
    assert passed, out
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
