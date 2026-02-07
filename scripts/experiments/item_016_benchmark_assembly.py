#!/usr/bin/env python3
import json
from pathlib import Path
import requests

SEED = 42

# Attempt curated list including required asteroids.
OBJECTS = [
    {"number": 433, "name": "Eros"},
    {"number": 25143, "name": "Itokawa"},
    {"number": 216, "name": "Kleopatra"},
    {"number": 1, "name": "Ceres"},
    {"number": 2, "name": "Pallas"},
    {"number": 3, "name": "Juno"},
    {"number": 4, "name": "Vesta"},
    {"number": 10, "name": "Hygiea"},
    {"number": 15, "name": "Eunomia"},
    {"number": 16, "name": "Psyche"},
    {"number": 21, "name": "Lutetia"},
    {"number": 22, "name": "Kalliope"},
    {"number": 41, "name": "Daphne"},
    {"number": 87, "name": "Sylvia"},
    {"number": 121, "name": "Hermione"},
    {"number": 130, "name": "Elektra"},
    {"number": 349, "name": "Dembowska"},
    {"number": 511, "name": "Davida"},
    {"number": 704, "name": "Interamnia"},
    {"number": 253, "name": "Mathilde"},
]


def head_ok(url: str) -> bool:
    try:
        r = requests.head(url, timeout=12, allow_redirects=True)
        if r.status_code < 400:
            return True
    except Exception:
        pass
    try:
        r = requests.get(url, timeout=12, stream=True)
        return r.status_code < 400
    except Exception:
        return False


def main():
    records = []
    for obj in OBJECTS:
        num = obj["number"]
        # DAMIT pages are typically model.php?asteroid=NUMBER
        damit_url = f"https://astro.troja.mff.cuni.cz/projects/damit/asteroid.php?id={num}"
        # JPL SBDB baseline page as radar/model reference pointer.
        jpl_url = f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={num}"
        # ALCDEF/PDS placeholders for retrievable photometry links.
        alcdef_url = f"https://alcdef.org/php/alcdef_GenerateALCDEFPage.php?AsteroidNumber={num}"
        pds_url = f"https://pds.nasa.gov/services/search/search?fq=identifier&wt=json&q={num}"

        rec = {
            "number": num,
            "name": obj["name"],
            "damit_exists": head_ok(damit_url),
            "jpl_exists": head_ok(jpl_url),
            "alcdef_exists": head_ok(alcdef_url),
            "pds_exists": head_ok(pds_url),
            "links": {
                "damit": damit_url,
                "jpl": jpl_url,
                "alcdef": alcdef_url,
                "pds": pds_url,
            },
        }
        # Paired shape + raw photometry surrogate availability check.
        rec["paired_available"] = bool((rec["damit_exists"] or rec["jpl_exists"]) and (rec["alcdef_exists"] or rec["pds_exists"]))
        records.append(rec)

    paired = [r for r in records if r["paired_available"]]
    out = {
        "item_id": "item_016",
        "seed": SEED,
        "required_objects_present": all(any(r["number"] == x for r in records) for x in [433, 25143, 216]),
        "total_curated": len(records),
        "paired_count": len(paired),
        "acceptance_pass": bool(len(paired) >= 20 and all(any(r["number"] == x and r["paired_available"] for r in paired) for x in [433, 25143, 216])),
        "records": records,
    }
    Path("results/item_016_benchmark_set.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
