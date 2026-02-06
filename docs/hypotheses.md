# Testable Hypotheses for 5D AlphaGo-Style Research

1. **PUCT prior quality hypothesis**
   - Independent variable: policy prior source (`uniform` vs `learned`).
   - Dependent variable: Elo against fixed baseline at equal simulations.
   - Expected direction: learned priors increase Elo.
   - Success threshold: `+120` Elo or more at 95% CI lower bound > `+60`.

2. **Temporal-context encoding hypothesis**
   - Independent variable: history depth in encoder (`1`, `2`, `4`, `8` snapshots).
   - Dependent variable: validation policy top-1 accuracy and match Elo.
   - Expected direction: depth up to `4` improves performance then saturates.
   - Success threshold: depth `4` beats depth `1` by >= `3.0` points top-1 and >= `+70` Elo.

3. **Symmetry-aware cache hypothesis**
   - Independent variable: transposition cache (`off` vs `on` with symmetry canonicalization).
   - Dependent variable: nodes/sec and search strength at fixed wall-clock.
   - Expected direction: cache increases throughput and strength.
   - Success threshold: >= `25%` nodes/sec gain and >= `+40` Elo.

4. **Gumbel policy improvement hypothesis**
   - Independent variable: target policy generation (`standard visit-count` vs `Gumbel`).
   - Dependent variable: policy entropy calibration and self-play Elo progression rate.
   - Expected direction: Gumbel yields faster early Elo growth.
   - Success threshold: >= `15%` higher Elo gain per 100k games over first 1M games.

5. **Curriculum branch-depth hypothesis**
   - Independent variable: max branch depth schedule (`static high` vs `curriculum`).
   - Dependent variable: training stability (collapse events) and final Elo.
   - Expected direction: curriculum reduces collapse and improves final strength.
   - Success threshold: collapse events reduced by >= `50%` and final Elo >= `+80`.

6. **Learned move-pruning hypothesis**
   - Independent variable: pruning gate (`none` vs `learned gate retaining top-k`).
   - Dependent variable: simulations per second and Elo under fixed time control.
   - Expected direction: moderate pruning improves efficiency with minimal strength loss.
   - Success threshold: >= `35%` more sims/sec with Elo drop <= `20`.

7. **Replay diversity governance hypothesis**
   - Independent variable: replay sampling (`uniform` vs `diversity-weighted`).
   - Dependent variable: exploitability proxy and held-out scenario robustness.
   - Expected direction: diversity-weighted replay improves robustness.
   - Success threshold: held-out suite Elo degradation improves by >= `60` Elo.
