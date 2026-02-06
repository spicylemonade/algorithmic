# AlphaGo-Style Policy-Value Network for 5D Chess

## Input and Output
- Input: encoded tensor `[timeline,time,rank,file,channel] = [4,4,8,8,14]`.
- Policy head: logits over packed action index space.
- Value head: scalar in `[-1, 1]` representing expected game outcome.

## Backbone Candidates
See `results/item_011_arch_ablation.json` for a 3-way ablation over:
- `resnet_3d_small`
- `axial_attention_hybrid`
- `token_transformer_compact`

## Selected Architecture
- Selected: `axial_attention_hybrid`
- Parameter count: `~18.6M`
- Rationale: global mixing on timeline/time dimensions with lower latency than full transformer.
- Receptive field: captures distant cross-timeline dependencies in fewer layers than local-only convs.

## Latency Target
- Inference target: `<12 ms` per position on pilot GPU-equivalent hardware.
- Chosen backbone meets target in ablation artifact.
