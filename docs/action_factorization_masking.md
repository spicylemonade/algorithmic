# Action-Space Factorization and Legality Masking

## Factorized Representation
A move is factorized into:
- `src_timeline`
- `src_time`
- `src_square`
- `dst_timeline`
- `dst_time`
- `dst_square`
- `promotion`

This avoids allocating dense probability over impossible joint combinations and supports staged legality filtering.

## Masking Pipeline
1. Generate candidate legal move set from rule engine.
2. Convert legal moves to flat action indices.
3. Build binary mask over action logits (`1` legal, `0` illegal).
4. Apply `masked_softmax` that sets illegal logits to `-inf` equivalent and renormalizes only legal actions.
5. Assert `sum(prob_illegal) == 0.0` during validation.
