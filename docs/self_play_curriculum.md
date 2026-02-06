# Self-Play Curriculum & League Training (Item 014)

Implemented staged self-play curriculum with four difficulty stages and league windows in `src/fived/self_play.py`.

Outcome summary:
- Fresh self-play positions: 40,000
- Reanalyzed positions: 1,000,000
- Total training positions: 1,040,000
- Catastrophic collapse over 3 windows: not detected

See `results/item_014_self_play_curriculum.json` for full details.
