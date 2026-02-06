# Candidate Selection Boolean Filter (Item 020)

Implemented logic (exact):
`(is_neo OR diameter_km > 100) AND (lcdb_u >= 2) AND (not in_damit) AND (dense_curves >= 20 OR (sparse_points >= 100 AND apparitions > 3))`

Artifacts:
- Universe: `data/processed/candidate_universe.json`
- Audit table: `results/item_020_filter_audit_table.json`
- Selected set: `results/item_020_selected_candidates.json`
- Summary counts: `results/item_020_filter_summary.json`
