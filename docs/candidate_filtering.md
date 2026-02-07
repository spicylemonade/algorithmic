# Candidate Filtering Pipeline

Boolean logic implemented:
- Priority 1: `neo == True` OR `diameter_km > 100`
- Priority 2: `LCDB U >= 2`
- Priority 3: `in_damit == False`
- Priority 4: `lightcurve_count > 20` OR (`sparse_points_est > 100` AND `apparitions > 3`)

Data sources used in pipeline execution:
- JPL SBDB query API (candidate pool)
- MinorPlanet.info LCDB endpoint (`generateoneasteroidinfo.php`) for U/period and observational coverage proxies
- DAMIT search endpoint for model-presence check

Output:
- `results/item_019_candidate_filtering.json` (ranked selected set + full audit)
