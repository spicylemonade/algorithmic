# PUCT Formulation for 5D Chess

Selection score for child action `a` from node `s`:

`PUCT(s,a) = Q(s,a) + c_puct * P(s,a) * sqrt(N(s)) / (1 + N(s,a))`

Where:
- `Q(s,a)`: mean backed-up value.
- `P(s,a)`: policy prior probability (normalized over trans-dimensional action set).
- `N(s)`: parent visits.
- `N(s,a)`: child visits.

Backup rule (alternating perspective):
- increment visit count on each node in path by `1`.
- add propagated value `v` and flip sign each ply.

Parallelism:
- virtual loss can be applied by temporary visit/value adjustments per in-flight simulation.
- trans-dimensional priors are normalized once per expansion to preserve probability mass.
