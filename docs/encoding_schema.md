# Canonical 5D Chess Encoding Schema

- Tensor shape: `(timelines=2, time=3, channels=16, height=8, width=8)`.
- Channel semantics:
  - `0..5`: white piece planes (pawn, knight, bishop, rook, queen, king)
  - `6..11`: black piece planes
  - `12`: side-to-move broadcast plane
  - `13`: castling rights encoding plane
  - `14`: en-passant target encoding plane
  - `15`: temporal-branch metadata plane
- Normalization rules:
  - Piece occupancy planes in `{-1, 0, +1}`.
  - Metadata planes normalized to `[0, 1]`.
  - Decoder rounds clipped floats back to integer occupancy for reversible tests.
- Round-trip criterion: encode/decode over 100 sampled states must preserve board tensor and scalar metadata exactly.
