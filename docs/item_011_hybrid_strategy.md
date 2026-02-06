# Hybrid Convex + Evolutionary Strategy

Implemented handoff logic in `src/lci/hybrid.py`:
- Stage 1: convex optimization until objective plateau.
- Handoff condition: plateau in recent objective window (`eps=1e-4`, window=12), optionally reinforced by structured residual indicator (`|autocorr| > 0.25`).
- Stage 2: initialize genetic non-convex refinement from convex state and anneal convexity penalty.

This satisfies the required two-stage schedule and explicit handoff conditions based on objective plateau and residual structure.
