# Ground-Truth Validation Set (Item 016)

Anchors curated (required trio):
- 433 Eros
  - Raw photometry: `data/raw/ground_truth/eros/lc.json` (DAMIT export)
  - Reference mesh: `data/raw/ground_truth/eros/shape_damit.obj`
- 216 Kleopatra
  - Raw photometry: `data/raw/ground_truth/kleopatra/lc.json` (DAMIT export)
  - Reference mesh: `data/raw/ground_truth/kleopatra/shape_jpl.obj`
  - Alternate reference: `data/raw/ground_truth/kleopatra/shape_damit.obj`
- 25143 Itokawa
  - Raw photometry: `data/raw/ground_truth/itokawa/pds_extract/.../data/itokawapolar.tab` (PDS)
  - Reference mesh: `data/raw/ground_truth/itokawa/shape_jpl.mod`

This satisfies paired raw-photometry + reference-mesh coverage for all three anchors.
