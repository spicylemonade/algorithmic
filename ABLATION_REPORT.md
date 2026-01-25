# Ablation Study: 3x3 Matrix Multiplication Algorithms

## Executive Summary

**Goal:** Create a generalized 3x3 matrix multiplication algorithm with <81 scalar operations and ≤22 multiplications.

**Result:** Achieved **26 multiplications, 32 additions = 58 total operations** (<81 ✓)

**Status on ≤22 multiplications:** **NOT ACHIEVED** - This is an open problem in mathematics. The best known algorithm uses 23 multiplications (Laderman, 1976), and the theoretical lower bound is ≥19 multiplications.

## Theoretical Background (GPT-5.2 Consultation)

According to current research (as of Jan 2026):

- **Best known algorithm:** 23 multiplications (Laderman, 1976)
- **Proven lower bound:** ≥19 multiplications
- **Open question:** Is 22 multiplications achievable?
- **Our implementation:** 26 multiplications (practical block-Strassen approach)

The true minimum is in the range {19, 20, 21, 22, 23}, but no verified algorithm with ≤22 multiplications exists for general 3×3 matrix multiplication over arbitrary fields.

## Algorithms Tested

### 1. Standard Algorithm (Baseline)
- **Operations:** 27 mults, 18 adds = 45 ops
- **Method:** Direct computation `C[i,j] = Σ A[i,k] * B[k,j]`
- **Status:** Simple, optimal for total operation count

### 2. Block-Strassen Algorithm (Full Implementation)
- **Operations:** 26 mults, 32 adds = 58 ops
- **Components:**
  - BLOCK_DECOMP: Partition 3×3 into 2×2 + border
  - STRASSEN_2x2: Apply Strassen to top-left 2×2 block (7 mults, 18 adds)
  - BORDER_MULT: Standard multiplication for borders (19 mults, 5 adds)
  - ASSEMBLY: Combine results (0 mults, 9 adds)

### 3. Block-Standard Algorithm (Ablated)
- **Operations:** 27 mults, 18 adds = 45 ops
- **Ablation:** Removed STRASSEN_2x2 component, replaced with standard 2×2
- **Result:** Equivalent to baseline - block decomposition alone provides no benefit

## Ablation Analysis

### Effect of Block Decomposition Alone
**Baseline → Block-Standard:**
- Multiplications: 27 → 27 (Δ = 0)
- Additions: 18 → 18 (Δ = 0)
- Total: 45 → 45 (Δ = 0)

**Finding:** Block decomposition structure alone provides **no benefit**.

### Effect of Strassen 2×2 Component
**Block-Standard → Block-Strassen:**
- Multiplications: 27 → 26 (Δ = -1) ✓
- Additions: 18 → 32 (Δ = +14) ✗
- Total: 45 → 58 (Δ = +13) ✗

**Finding:** Strassen 2×2 is the **only component** that reduces multiplications, but it increases total operations significantly.

## Key Insights

1. **Multiplication-Addition Tradeoff:**
   - Strassen saves 1 multiplication at the cost of 14 additional additions
   - If multiplications and additions have equal cost, standard algorithm wins (45 vs 58 ops)
   - If multiplications are >13× more expensive than additions, Block-Strassen wins

2. **Component Necessity:**
   - **STRASSEN_2x2:** NECESSARY for multiplication reduction
   - **BLOCK_DECOMP:** NOT necessary (provides no benefit alone)
   - **BORDER_MULT:** NECESSARY (handles the 3rd row/column)
   - **ASSEMBLY:** NECESSARY (combines blocks into result)

3. **Theoretical Limits:**
   - Our 26-mult algorithm is 3× away from the target (22) and current best (23)
   - Reaching 23 multiplications requires Laderman's algorithm (83 total ops, exceeds 81 limit)
   - The ≤22 multiplication target appears to be impossible with current knowledge

## Operation Count Breakdown

### Block-Strassen (26 mults, 32 adds)

| Component | Multiplications | Additions | Total |
|-----------|----------------|-----------|-------|
| Strassen 2×2 | 7 | 18 | 25 |
| Border operations | 19 | 5 | 24 |
| Assembly | 0 | 9 | 9 |
| **TOTAL** | **26** | **32** | **58** |

#### Detailed Strassen 2×2 Breakdown:
- Preprocessing (m1-m7): 7 mults, 10 adds
- Postprocessing (p11-p22): 0 mults, 8 adds
- Subtotal: 7 mults, 18 adds

#### Detailed Border Breakdown:
- Q = u @ y: 4 mults, 0 adds (2×1 × 1×2 outer product)
- r = A11 @ x: 4 mults, 2 adds (2×2 × 2×1 matrix-vector)
- s = u * beta: 2 mults, 0 adds (2×1 scalar)
- t = v @ B11: 4 mults, 2 adds (1×2 × 2×2 vector-matrix)
- w = alpha * y: 2 mults, 0 adds (scalar × 1×2)
- z = v @ x: 2 mults, 1 add (1×2 × 2×1 dot product)
- gamma = alpha * beta: 1 mult, 0 adds (scalar product)
- Subtotal: 19 mults, 5 adds

## Correctness Verification

All algorithms were tested against NumPy's reference implementation with:
- Random matrices
- Identity matrices
- Integer matrices
- Zero matrices
- Ones matrices

**Result:** All algorithms produce correct results (verified with `np.allclose` at tolerance 1e-10).

## Conclusions

1. **Target Achievement:**
   - ✓ Total operations <81: Achieved (58 ops)
   - ✗ Multiplications ≤22: Not achieved (26 mults) - likely impossible with current knowledge

2. **Best Practical Algorithm:**
   - For **multiplication-intensive** hardware: Block-Strassen (26 mults)
   - For **equal-cost** operations: Standard (45 ops)
   - For **theoretical minimum** multiplications: Laderman (23 mults, but 83 ops total)

3. **Ablation Findings:**
   - Only the Strassen 2×2 component provides multiplication reduction
   - Block decomposition alone is neutral
   - The multiplication-addition tradeoff is unfavorable for total operation count

## Files

- `ablation_study.py` - Main ablation study implementation
- `matrix_mult_3x3.py` - Laderman's 23-mult algorithm (existing)
- `verify_ops.py` - Manual operation count verification
- `debug_ops.py` - Detailed operation tracing
- `.archivara/metrics/3c5c9c77.json` - Metrics output (score=26)

## Recommendations

For practical 3×3 matrix multiplication:
1. Use **standard algorithm** (45 ops) for general purpose
2. Use **Block-Strassen** (26 mults) only if multiplications are significantly more expensive than additions
3. Use **Laderman** (23 mults) if you need theoretical minimum multiplications regardless of total cost

The ≤22 multiplication target remains an **open mathematical problem**.
