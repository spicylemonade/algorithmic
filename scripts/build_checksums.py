#!/usr/bin/env python3
import hashlib
from pathlib import Path

OUT = Path("results/checksums.sha256")
paths = []
for root in [Path("results"), Path("figures"), Path("docs")]:
    for p in sorted(root.rglob("*")):
        if p.is_file() and p != OUT:
            paths.append(p)

with OUT.open("w") as f:
    for p in paths:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        f.write(f"{h}  {p.as_posix()}\n")
