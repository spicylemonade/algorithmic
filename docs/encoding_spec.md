# State and Action Encoding Spec

State tensor schema:
- Shape: `[timeline, time, rank, file, channel] = [4, 4, 8, 8, 14]`
- Channels `0..11`: piece planes (`WP,WN,WB,WR,WQ,WK,BP,BN,BB,BR,BQ,BK`)
- Channel `12`: side-to-move marker
- Channel `13`: occupancy marker
- Storage: sparse entries `(l,t,r,c,ch)` for efficiency

Action indexing:
- Mixed-radix packed index over fields:
`(src_l, src_t, src_r, src_c, dst_l, dst_t, dst_r, dst_c, promo, branch)`
- Promotion code: `None=0,N=1,B=2,R=3,Q=4`
- Branch code: `0/1`
