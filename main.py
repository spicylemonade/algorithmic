"""CLI entrypoint for the custom LCI research pipeline."""
from __future__ import annotations

import argparse
import json

from src.lci.pipeline import run_manifest, run_pilot


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--out', default='results/main_run.json')
    args = ap.parse_args()

    result = run_pilot(seed=args.seed)
    payload = {
        'manifest': run_manifest(seed=args.seed),
        'pilot': result.__dict__,
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


if __name__ == '__main__':
    main()
