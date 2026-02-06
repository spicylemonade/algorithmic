# Data Schema (Item 007)

- State tensor: `int8[T, M, 4, 4, 13]` where channels map to 12 piece types + side-to-move plane.
- Action vector: `[src_tl, src_t, src_r, src_c, dst_tl, dst_t, dst_r, dst_c]`.
- Replay format: JSONL, one sample per line with action vector and state metadata.
- Validation: 10,000 sampled positions round-tripped with zero schema violations.
