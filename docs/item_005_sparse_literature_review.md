# Sparse-Photometry Inversion Review

## Source Synthesis
1. Durech et al. (2010, A&A 513 A46, DOI `10.1051/0004-6361/200912693`): DAMIT institutionalized convex inversion outputs and highlighted model quality dependence on geometric diversity and data quality.
2. Durech et al. (2009, A&A 493, DOI `10.1051/0004-6361:200810393`): combining sparse and dense photometry improves uniqueness and suppresses mirror ambiguities.
3. Cellino et al. (2009, A&A 506, DOI `10.1051/0004-6361/200912134`): genetic inversion can recover spin/shape from sparse data but is highly sensitive to cadence and photometric error.
4. Gaia DR3 documentation (ESA Cosmos, released 13 June 2022): includes solar-system epoch photometry and orbital solutions for a very large SSO set, motivating sparse-aware inversion modules.
5. Durech et al. (2016, A&A 586 A48): Lowell/Pan-STARRS-like sparse survey data alone can produce useful models but with lower certainty unless combined with higher-precision constraints.
6. Lindberg et al. (2021, arXiv:2111.12596): ZTF sparse light curves show period recovery is feasible with probabilistic methods when cadence/aliasing is handled explicitly.

## Sparse-Data Failure Modes and Mitigations
1. Temporal aliasing (diurnal/cadence aliases)
- Mitigation hypothesis: multi-resolution period grid + alias veto list + cross-survey fusion (space + ground).

2. Pole mirror ambiguity
- Mitigation hypothesis: enforce cross-apparition consistency and penalize spin solutions that violate seasonal brightness trends.

3. Phase-angle undercoverage
- Mitigation hypothesis: inject phase-function priors and prioritize ingestion from Gaia + ZTF + Pan-STARRS to widen geometry.

4. Photometric zero-point offsets across surveys
- Mitigation hypothesis: fit per-survey bias/scale nuisance parameters during inversion.

5. Outlier contamination (poor calibration, blends, trailing losses)
- Mitigation hypothesis: robust residual loss + survey quality flags + iterative sigma-clipping with uncertainty inflation.

## Implementation Implication
Sparse inversion should be treated as a probabilistic search problem with explicit ambiguity scoring, not a single deterministic fit.
