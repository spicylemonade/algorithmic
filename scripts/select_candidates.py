#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import argparse

import requests

SEED = 42
ROOT = Path(__file__).resolve().parents[1]


def fetch_neo_pool(limit: int = 80) -> list[dict]:
    url = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
    params = {
        "fields": "spkid,full_name,neo,diameter",
        "sb-group": "neo",
        "limit": str(limit),
    }
    data = requests.get(url, params=params, timeout=60, verify=False).json()
    out = []
    for row in data.get("data", []):
        full_name = row[1].strip()
        number_match = re.search(r"(\d+)", full_name)
        if not number_match:
            continue
        out.append(
            {
                "number": int(number_match.group(1)),
                "name": full_name,
                "neo": True,
                "diameter_km": float(row[3]) if row[3] not in (None, "") else None,
            }
        )
    return out


def large_mba_pool() -> list[dict]:
    # Known large MBAs (diameter generally >100 km).
    nums = [1, 2, 3, 4, 10, 15, 16, 24, 31, 52, 65, 87, 88, 107, 121, 130, 324, 511, 532, 704]
    return [{"number": n, "name": f"({n})", "neo": False, "diameter_km": 100.0} for n in nums]


def parse_rows(html: str) -> list[list[str]]:
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I)
    parsed = []
    for r in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S | re.I)
        clean = []
        for c in cells:
            c = re.sub(r"<[^>]+>", " ", c)
            c = unescape(c)
            c = re.sub(r"\s+", " ", c).strip()
            clean.append(c)
        if clean:
            parsed.append(clean)
    return parsed


def safe_float(x: str) -> float | None:
    try:
        return float(x)
    except Exception:
        return None


def parse_u_value(u_raw: str) -> float | None:
    m = re.search(r"(\d(?:\.\d)?)", u_raw or "")
    return float(m.group(1)) if m else None


def lcdb_metrics(number: int) -> dict:
    form = {
        "AstNumber": str(number),
        "AstName": "",
        "Longitude": "-116",
        "Latitude": "34",
        "StartDate": "2026-02-07",
        "UT": "0",
        "subOneShot": "Submit",
    }
    html = requests.post(
        "https://www.minorplanet.info/php/generateoneasteroidinfo.php",
        data=form,
        timeout=60,
        verify=False,
    ).text
    rows = parse_rows(html)

    summary_header = None
    summary_values = None
    detail_header_idx = None

    for i, r in enumerate(rows):
        if "Number" in r and "Period" in r and "U" in r and "Pole" in r:
            summary_header = r
            if i + 1 < len(rows):
                summary_values = rows[i + 1]
        if "Reference" in r and "DateObs" in r and "Period" in r and "U" in r:
            detail_header_idx = i
            break

    summary = {}
    if summary_header and summary_values:
        for k, v in zip(summary_header, summary_values):
            summary[k] = v

    lc_rows = []
    if detail_header_idx is not None:
        hdr = rows[detail_header_idx]
        j = detail_header_idx + 1
        while j < len(rows):
            r = rows[j]
            if "Reference" in r and "BibCode" in r and "DetailsRef" in r:
                break
            if len(r) >= 5:
                rec = {k: v for k, v in zip(hdr, r)}
                lc_rows.append(rec)
            j += 1

    dates = [r.get("DateObs", "") for r in lc_rows if r.get("DateObs")]
    unique_dates = sorted(set(dates))
    # Approximation: each dated row is one lightcurve entry.
    lightcurve_count = len(lc_rows)
    apparitions = len(unique_dates)
    sparse_points_est = lightcurve_count * 6

    period = safe_float(summary.get("Period", ""))
    u_value = parse_u_value(summary.get("U", ""))

    return {
        "period_hours": period,
        "u_raw": summary.get("U", ""),
        "u_value": u_value,
        "lightcurve_count": lightcurve_count,
        "apparitions": apparitions,
        "sparse_points_est": sparse_points_est,
    }


def has_damit_model(number: int) -> bool:
    html = requests.get(
        f"https://astro.troja.mff.cuni.cz/projects/damit/?q={number}",
        timeout=60,
        verify=False,
    ).text
    return "/asteroid_models/" in html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--neo-limit", type=int, default=80)
    args = parser.parse_args()

    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

    neo = fetch_neo_pool(limit=args.neo_limit)
    pool_map = {r["number"]: r for r in neo}
    for r in large_mba_pool():
        pool_map.setdefault(r["number"], r)

    selected = []
    audit = []

    for idx, (num, rec) in enumerate(sorted(pool_map.items())):
        try:
            lc = lcdb_metrics(num)
            dam = has_damit_model(num)
        except Exception as e:
            audit.append({"number": num, "name": rec["name"], "error": str(e)})
            continue

        priority1 = bool(rec["neo"] or ((rec["diameter_km"] or 0.0) > 100.0))
        priority2 = (lc["u_value"] is not None) and (lc["u_value"] >= 2.0)
        priority3 = not dam
        priority4 = (lc["lightcurve_count"] > 20) or (
            lc["sparse_points_est"] > 100 and lc["apparitions"] > 3
        )

        score = (
            (100 if priority1 else 0)
            + (80 if priority2 else 0)
            + (90 if priority3 else 0)
            + (70 if priority4 else 0)
            + min(lc["lightcurve_count"], 60)
        )

        row = {
            "number": num,
            "name": rec["name"],
            "neo": rec["neo"],
            "diameter_km": rec["diameter_km"],
            "lcdb_u": lc["u_raw"],
            "lcdb_u_value": lc["u_value"],
            "period_hours": lc["period_hours"],
            "lightcurve_count": lc["lightcurve_count"],
            "sparse_points_est": lc["sparse_points_est"],
            "apparitions": lc["apparitions"],
            "in_damit": dam,
            "priority": {
                "p1": priority1,
                "p2": priority2,
                "p3": priority3,
                "p4": priority4,
            },
            "score": score,
        }
        audit.append(row)
        if priority1 and priority2 and priority3 and priority4:
            selected.append(row)

        # Gentle pacing against public sites.
        if idx % 10 == 0:
            time.sleep(0.3)

    selected = sorted(selected, key=lambda x: (-x["score"], -x["lightcurve_count"], x["number"]))

    out = {
        "item_id": "item_019",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "input_pool_size": len(pool_map),
        "selected_count": len(selected),
        "selected": selected,
        "audit": audit,
    }

    (ROOT / "results/item_019_candidate_filtering.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
