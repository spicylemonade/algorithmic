# Policy-Value Network Family for 5D Chess

## Variant A: Temporal-Residual CNN (TR-CNN-S)
- Structure: 3D convolutions over `(timeline,time,board)` followed by 8 residual blocks.
- Parameter count: ~7.2M.
- FLOPs/inference (batch=1): ~3.4 GFLOPs.
- Receptive-field rationale: captures local tactical motifs plus short temporal interactions across adjacent time slices.

## Variant B: Hybrid Conv-Transformer (HCT-M)
- Structure: spatial stem conv + timeline-time tokenization + 6-layer transformer encoder.
- Parameter count: ~18.9M.
- FLOPs/inference: ~8.1 GFLOPs.
- Receptive-field rationale: global attention across timelines resolves long-range temporal dependencies and cross-branch constraints.

## Variant C: Factorized Dual-Head EfficientNet (FDH-L)
- Structure: depthwise-separable temporal blocks + factorized policy head + scalar value head.
- Parameter count: ~12.4M.
- FLOPs/inference: ~2.6 GFLOPs.
- Receptive-field rationale: efficient broad coverage with lower compute, tuned for high MCTS query volume.
