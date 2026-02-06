# Error Taxonomy and Remediation Playbook

1. Missing/invalid timestamps
- Signal: non-monotonic or null observation epochs
- Action: drop/repair rows and reindex apparition bins

2. Cross-survey zero-point mismatch
- Signal: residual offsets by source
- Action: fit per-survey bias terms

3. Sparse aliasing in period search
- Signal: multiple near-equal period minima
- Action: multi-resolution scan + alias veto list

4. Pole mirror ambiguity
- Signal: antipodal poles with similar fit
- Action: cross-apparition consistency penalty

5. Phase-angle undercoverage
- Signal: unstable scattering coefficients
- Action: add Gaia/ZTF/Pan-STARRS supplementation and priors

6. Over-smoothed convex initialization
- Signal: high-frequency residual structure after convex stage
- Action: earlier handoff to evolutionary stage

7. GA premature convergence
- Signal: fitness plateaus early with low diversity
- Action: increase mutation schedule and tournament diversity

8. Physically implausible shape ratios
- Signal: extreme inertia/axis ratio penalties
- Action: enforce physical priors and repair operator

9. Outlier contamination
- Signal: heavy-tail residual distribution
- Action: robust loss + sigma clipping

10. Non-deterministic reruns
- Signal: metric variance > 1% at fixed seed
- Action: enforce seed propagation and deterministic sort/order

11. Metric proxy mismatch (IoU)
- Signal: box-IoU disagrees with visual mesh agreement
- Action: replace with voxelized or mesh-intersection IoU

12. Candidate ranking data gaps
- Signal: missing LCDB `U` and lightcurve-count fields
- Action: fallback to provisional ranking and explicit failure flag
