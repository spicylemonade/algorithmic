# Novelty Module For Horizon-Aware Planning (Item 015)

Implemented a timeline credit-assignment novelty mechanism in `src/fived/novelty.py`:
- Bonus for temporal actions
- Bonus for longer-range displacement
- Tactical-suite evaluation against baseline policy

Result:
- Statistically significant improvement on predefined tactical suite (`p < 0.05`).
- Full metrics in `results/item_015_novelty_module.json`.
