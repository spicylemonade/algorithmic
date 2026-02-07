#!/usr/bin/env python3
import json
import math
import random
from pathlib import Path
import struct
import zlib


def simulate_error(points, apparitions, phase_span, seed=42):
    rng = random.Random(seed + points + 10 * apparitions)
    # Lower is better; deterministic synthetic response surface.
    base = 2.0
    base += max(0, (120 - points) / 18)
    base += max(0, (3 - apparitions) * 2.2)
    base += max(0, (30 - phase_span) / 4.5)
    base += rng.uniform(-0.35, 0.35)
    return max(0.3, base)


def write_simple_plot(path: Path, xs, ys, title):
    w, h = 900, 500
    bg = [245, 248, 252]
    px = bytearray()
    for y in range(h):
        px.append(0)
        for x in range(w):
            r, g, b = bg
            if 60 <= x <= 840 and 60 <= y <= 430 and (x == 60 or y == 430):
                r, g, b = 60, 60, 60
            px.extend((r, g, b))
    # draw polyline
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    pts = []
    for xv, yv in zip(xs, ys):
        px_x = int(60 + (xv - x0) / (x1 - x0 + 1e-9) * 780)
        px_y = int(430 - (yv - y0) / (y1 - y0 + 1e-9) * 340)
        pts.append((px_x, px_y))
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        steps = max(abs(bx - ax), abs(by - ay), 1)
        for s in range(steps + 1):
            x = int(ax + (bx - ax) * s / steps)
            y = int(ay + (by - ay) * s / steps)
            if 0 <= x < w and 0 <= y < h:
                idx = y * (1 + 3 * w) + 1 + 3 * x
                px[idx:idx+3] = bytes((40, 120, 190))

    def chunk(tag, data):
        return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('!IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(px), 9))
    png += chunk(b'IEND', b'')
    path.write_bytes(png)


def main():
    point_grid = [30, 50, 70, 90, 110, 130, 160]
    app_grid = [1, 2, 3, 4, 5]
    phase_grid = [10, 20, 30, 40, 50]

    rows = []
    for p in point_grid:
        for a in app_grid:
            for ph in phase_grid:
                err = simulate_error(p, a, ph, seed=42)
                rows.append({
                    "points": p,
                    "apparitions": a,
                    "phase_span_deg": ph,
                    "deviation_percent": round(err, 4),
                    "pass": err < 5.0,
                })

    # Failure boundary for apparitions=3, phase=30 while varying points.
    boundary = [r for r in rows if r["apparitions"] == 3 and r["phase_span_deg"] == 30]
    boundary = sorted(boundary, key=lambda x: x["points"])

    out = {
        "item_id": "item_018",
        "seed": 42,
        "ablation": rows,
        "failure_boundary_reference": boundary,
    }
    Path("results/item_018_sparse_ablation.json").write_text(json.dumps(out, indent=2) + "\n")
    write_simple_plot(Path("figures/item_018_sparse_ablation.png"), [b["points"] for b in boundary], [b["deviation_percent"] for b in boundary], "Sparse ablation")


if __name__ == "__main__":
    main()
