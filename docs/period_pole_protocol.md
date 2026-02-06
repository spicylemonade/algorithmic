# Baseline Period and Pole Search Protocol (Item 007)

## Reproducible Search Plan
- Seed: `42`.
- Period bounds: `[2.0, 100.0]` hours.
- Coarse period step: `0.05` hours.
- Fine period step around best coarse candidates: `0.002` hours within `±0.1` hours.
- Pole longitude (`lambda`) coarse/fine steps: `15 deg` / `3 deg`.
- Pole latitude (`beta`) coarse/fine steps: `15 deg` / `3 deg` over `[-75, 75] deg`.
- Convergence tolerance on objective improvement: `1e-5`.

## Procedure
1. Evaluate coarse period grid with coarse pole scan.
2. Keep top-K minima (default `K=20`).
3. Build local fine neighborhoods in period and pole around each candidate.
4. Run convex optimizer from each fine seed.
5. Select global minimum with degeneracy check (mirror pole pair tracking).
