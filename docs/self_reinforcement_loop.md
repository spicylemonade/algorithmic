# Recursive Self-Reinforcement Loop Policy

Policy:
1. Run blind validation on benchmark set.
2. Compute deviation metrics per target and aggregate.
3. If aggregate deviation `<5%`, exit loop and proceed to target search.
4. If deviation `>=5%`, automatically retune:
   - increase smoothness regularization (`+15%`)
   - decrease concavity freedom (`-10%`)
   - increase spin prior weight (`+10%`)
   - tighten period search granularity (`1e-4 -> 8e-5 -> 5e-5`)
5. Re-run blind validation.

Caps and exits:
- Maximum retuning iterations: `6`.
- Hard-fail if still `>=5%` after iteration 6.
- Early pass if all primary metrics satisfy thresholds before cap.

Implementation: `src/lci/self_reinforcement.py`.
