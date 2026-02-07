# Validation Report: Custom LCI vs Baselines

## Scope
This report compares the custom pipeline against implemented baseline references using generated benchmark runs and sparse stress tests.

## Per-object Comparison (5-object matched baseline set)
| Metric delta (Custom - Reference) | Mean |
|---|---:|
| Period error pct | 0.9291 |
| Pole error deg | 4.6857 |
| Hausdorff distance | -0.2556 |

Interpretation: negative delta is better for all three metrics.

## Aggregate Benchmark Metrics (20 blind objects)
| Metric | Value |
|---|---:|
| Mean initial normalized deviation pct | 5.224 |
| Mean initial volumetric IoU | 0.043 |
| Recursive retuning triggers | 12 |

## Statistical Significance (15-run hybrid analysis)
{
  "mse": {
    "mean_convex": 0.002518209076747896,
    "mean_evo": 5.686009817833326e-05,
    "mean_hybrid": 0.0025203194695532795,
    "p_convex_gt_hybrid": 0.5022486212992368,
    "p_evo_gt_hybrid": 0.9996748121577482,
    "significant_against_both": false
  },
  "hausdorff": {
    "mean_convex": 0.1971615011067858,
    "mean_evo": 0.1559640534825632,
    "mean_hybrid": 0.16286617698200528,
    "p_convex_gt_hybrid": 0.04075311530887108,
    "p_evo_gt_hybrid": 0.6102318147471166,
    "significant_against_both": false
  },
  "pole_err": {
    "mean_convex": 17.180903425581576,
    "mean_evo": 60.75183542288514,
    "mean_hybrid": 12.52409962934676,
    "p_convex_gt_hybrid": 8.25063660321089e-06,
    "p_evo_gt_hybrid": 8.496587046861811e-12,
    "significant_against_both": true
  }
}

Key result: significant improvement against both single optimizers was achieved in 1 metrics.

## Sparse Stress Test Summary
{
  "0.3": {
    "failure_rate": 0.7,
    "pole_ambiguity_count": 57,
    "mean_mse": 0.07104515594951243
  },
  "0.15": {
    "failure_rate": 1.0,
    "pole_ambiguity_count": 50,
    "mean_mse": 0.06287101101814425
  },
  "0.08": {
    "failure_rate": 0.85,
    "pole_ambiguity_count": 57,
    "mean_mse": 0.061217188596780624
  }
}

Degradation slope (MSE vs level): 0.046227

## Failure Analysis
1. Convex period recovery remains unstable in several synthetic trials (item_007 failure).
2. Sparse pole convergence is below required threshold (item_008 failure).
3. Hybrid significance target (>=3 metrics) not reached (item_012 failure).
4. Adaptive weighting target not met for pole reduction >=15% (item_013 failure).

## Explicit SOTA Claim Assessment
Claim tested: custom engine surpasses MPO LCInvert/SAGE/KOALA-like baselines.
Assessment: **Not supported** by current evidence in this run set. Several required gates failed, so superiority cannot be claimed.
