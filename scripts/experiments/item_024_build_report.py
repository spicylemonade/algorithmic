#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np


def jload(p):
    return json.loads(Path(p).read_text())


def main():
    i10 = jload("results/item_010_external_comparison.json")
    i12 = jload("results/item_012_hybrid_stats.json")
    i18 = jload("results/item_018_recursive_gate.json")
    i19 = jload("results/item_019_sparse_stress.json")

    deltas = i10["comparisons"]
    d_period = [d["delta_ours_minus_reference"]["period_error_pct"] for d in deltas]
    d_pole = [d["delta_ours_minus_reference"]["pole_error_deg"] for d in deltas]
    d_mesh = [d["delta_ours_minus_reference"]["hausdorff_distance"] for d in deltas]

    rec = i18["results"]
    mean_dev_init = float(np.mean([r["initial"]["deviation_pct"] for r in rec]))
    mean_iou_init = float(np.mean([r["initial"]["volumetric_iou"] for r in rec]))

    report = f"""# Validation Report: Custom LCI vs Baselines

## Scope
This report compares the custom pipeline against implemented baseline references using generated benchmark runs and sparse stress tests.

## Per-object Comparison (5-object matched baseline set)
| Metric delta (Custom - Reference) | Mean |
|---|---:|
| Period error pct | {np.mean(d_period):.4f} |
| Pole error deg | {np.mean(d_pole):.4f} |
| Hausdorff distance | {np.mean(d_mesh):.4f} |

Interpretation: negative delta is better for all three metrics.

## Aggregate Benchmark Metrics (20 blind objects)
| Metric | Value |
|---|---:|
| Mean initial normalized deviation pct | {mean_dev_init:.3f} |
| Mean initial volumetric IoU | {mean_iou_init:.3f} |
| Recursive retuning triggers | {i18['recursive_trigger_count']} |

## Statistical Significance (15-run hybrid analysis)
{json.dumps(i12['metrics'], indent=2)}

Key result: significant improvement against both single optimizers was achieved in {i12['significant_metric_count']} metrics.

## Sparse Stress Test Summary
{json.dumps(i19['summary_by_level'], indent=2)}

Degradation slope (MSE vs level): {i19['metric_degradation_slope_mse_per_level']:.6f}

## Failure Analysis
1. Convex period recovery remains unstable in several synthetic trials (item_007 failure).
2. Sparse pole convergence is below required threshold (item_008 failure).
3. Hybrid significance target (>=3 metrics) not reached (item_012 failure).
4. Adaptive weighting target not met for pole reduction >=15% (item_013 failure).

## Explicit SOTA Claim Assessment
Claim tested: custom engine surpasses MPO LCInvert/SAGE/KOALA-like baselines.
Assessment: **Not supported** by current evidence in this run set. Several required gates failed, so superiority cannot be claimed.
"""

    Path("docs/validation_report.md").write_text(report)

    out = {
        "item_id": "item_024",
        "includes_per_object_and_aggregate_tables": True,
        "includes_stat_tests": True,
        "includes_failure_analysis": True,
        "sota_claim_supported": False,
        "acceptance_pass": True,
    }
    Path("results/item_024_report_summary.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
