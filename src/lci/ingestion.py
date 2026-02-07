from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from .types import Observation


class IngestionModule:
    """Parses photometric observations from normalized CSV inputs."""

    REQUIRED_FIELDS = ["jd", "mag", "sigma", "phase_angle_deg", "source"]

    def load_csv(self, path: str | Path) -> List[Observation]:
        p = Path(path)
        rows: List[Observation] = []
        with p.open() as f:
            reader = csv.DictReader(f)
            missing = [k for k in self.REQUIRED_FIELDS if k not in reader.fieldnames]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")
            for r in reader:
                rows.append(
                    Observation(
                        jd=float(r["jd"]),
                        mag=float(r["mag"]),
                        sigma=float(r["sigma"]),
                        phase_angle_deg=float(r["phase_angle_deg"]),
                        source=r["source"],
                    )
                )
        return rows
