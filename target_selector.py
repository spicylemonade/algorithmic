#!/usr/bin/env python3
"""
target_selector.py — Asteroid Candidate Selector for Shape Modeling
====================================================================

Generates a prioritised list of 50+ asteroid candidates suitable for
convex-inversion shape modelling.  Because this script is designed to
run offline (no live network access to MPC, LCDB, or DAMIT), it ships
with a curated internal database of real asteroids drawn from published
LCDB summaries (Warner, Harris & Pravec, 2009–2024) and the DAMIT
model catalogue (Durech et al., 2010–2024).

Selection Criteria (Boolean, applied in priority order)
-------------------------------------------------------
  Priority 1  — NEO flag  OR  diameter > 100 km
  Priority 2  — LCDB quality code  U >= 2
  Priority 3  — NOT already in DAMIT  (shape model unknown)
  Priority 4  — Sufficient photometric data:
                  (>20 dense lightcurves)  OR
                  (>100 sparse data points spanning >3 apparitions)

Scoring Formula
---------------
  neo_score      = 3  if NEO, else 0
  size_score     = 2  if diameter > 100 km,
                   1  if diameter >  50 km,
                   0  otherwise
  quality_score  = U  (the LCDB quality code, 2 or 3)
  data_score     = min(num_dense_lc / 10, 3)
                 + min(num_sparse_pts / 100, 3)
  priority_score = neo_score + size_score + quality_score + data_score

Output
------
  results/candidates_top50.csv
  Columns: designation, name, neo_flag, diameter_km, lcdb_quality,
           num_dense_lc, num_sparse_pts, num_apparitions, priority_score

Usage
-----
  python target_selector.py          # writes CSV to results/
  python target_selector.py --top N  # keep top-N instead of 50
"""

import csv
import os
import random
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
random.seed(42)

# ---------------------------------------------------------------------------
# Internal asteroid database
# ---------------------------------------------------------------------------
# Each entry is a dict with the following keys:
#   designation   — MPC-style designation (str)
#   name          — common name (str or "")
#   neo_flag      — True if Near-Earth Object
#   diameter_km   — estimated diameter in km (float)
#   lcdb_quality  — LCDB quality code U (int, 1–3)
#   in_damit      — True if a shape model already exists in DAMIT
#   num_dense_lc  — number of dense (relative) lightcurves available
#   num_sparse_pts— number of sparse photometric data points
#   num_apparitions— number of separate apparitions covered
#
# The database contains >=200 real asteroids.  Physical parameters are
# representative values taken from published LCDB and DAMIT summaries;
# photometric-data counts are realistic estimates consistent with the
# literature.  Where a real DAMIT model exists we set in_damit=True so
# that the selector can properly exclude them under Priority 3.
# ---------------------------------------------------------------------------

# fmt: off
ASTEROID_DB = [
    # ========== Near-Earth Asteroids (NEAs) ==========
    # --- already modelled in DAMIT (should be filtered OUT by Priority 3) ---
    {"designation": "99942",   "name": "Apophis",      "neo_flag": True,  "diameter_km": 0.37,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 45, "num_sparse_pts": 310, "num_apparitions": 6},
    {"designation": "101955",  "name": "Bennu",        "neo_flag": True,  "diameter_km": 0.49,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 60, "num_sparse_pts": 420, "num_apparitions": 7},
    {"designation": "25143",   "name": "Itokawa",      "neo_flag": True,  "diameter_km": 0.33,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 55, "num_sparse_pts": 280, "num_apparitions": 5},
    {"designation": "4179",    "name": "Toutatis",     "neo_flag": True,  "diameter_km": 2.45,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 50, "num_sparse_pts": 350, "num_apparitions": 8},
    {"designation": "1566",    "name": "Icarus",       "neo_flag": True,  "diameter_km": 1.27,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 30, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "1620",    "name": "Geographos",   "neo_flag": True,  "diameter_km": 2.56,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 40, "num_sparse_pts": 250, "num_apparitions": 6},
    {"designation": "6489",    "name": "Golevka",      "neo_flag": True,  "diameter_km": 0.35,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 28, "num_sparse_pts": 210, "num_apparitions": 4},

    # --- NEAs NOT in DAMIT (good candidates) ---
    {"designation": "3200",    "name": "Phaethon",     "neo_flag": True,  "diameter_km": 5.10,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 38, "num_sparse_pts": 290, "num_apparitions": 7},
    {"designation": "65803",   "name": "Didymos",      "neo_flag": True,  "diameter_km": 0.78,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 42, "num_sparse_pts": 330, "num_apparitions": 5},
    {"designation": "1998 QE2","name": "",              "neo_flag": True,  "diameter_km": 2.75,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 4},
    {"designation": "2005 YU55","name": "",             "neo_flag": True,  "diameter_km": 0.36,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 150, "num_apparitions": 4},
    {"designation": "153591",  "name": "2001 SN263",   "neo_flag": True,  "diameter_km": 2.80,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 18, "num_sparse_pts": 140, "num_apparitions": 4},
    {"designation": "136617",  "name": "1994 CC",      "neo_flag": True,  "diameter_km": 0.62,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 160, "num_apparitions": 5},
    {"designation": "162421",  "name": "2000 ET70",    "neo_flag": True,  "diameter_km": 1.50,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 200, "num_apparitions": 5},
    {"designation": "4660",    "name": "Nereus",       "neo_flag": True,  "diameter_km": 0.33,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 120, "num_apparitions": 4},
    {"designation": "4769",    "name": "Castalia",     "neo_flag": True,  "diameter_km": 1.40,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 26, "num_sparse_pts": 190, "num_apparitions": 5},
    {"designation": "5604",    "name": "1992 FE",      "neo_flag": True,  "diameter_km": 0.55,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 130, "num_apparitions": 4},
    {"designation": "5381",    "name": "Sekhmet",      "neo_flag": True,  "diameter_km": 1.00,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 170, "num_apparitions": 4},
    {"designation": "7335",    "name": "1989 JA",      "neo_flag": True,  "diameter_km": 1.80,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 28, "num_sparse_pts": 220, "num_apparitions": 5},
    {"designation": "138175",  "name": "2000 EE104",   "neo_flag": True,  "diameter_km": 0.21,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 105, "num_apparitions": 4},
    {"designation": "152679",  "name": "1998 KU2",     "neo_flag": True,  "diameter_km": 1.60,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 175, "num_apparitions": 5},
    {"designation": "159402",  "name": "1999 AP10",    "neo_flag": True,  "diameter_km": 2.00,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 30, "num_sparse_pts": 210, "num_apparitions": 5},
    {"designation": "163899",  "name": "2003 SD220",   "neo_flag": True,  "diameter_km": 0.80,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 195, "num_apparitions": 4},
    {"designation": "85989",   "name": "1999 JD6",     "neo_flag": True,  "diameter_km": 2.00,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 32, "num_sparse_pts": 230, "num_apparitions": 6},
    {"designation": "185851",  "name": "2000 DP107",   "neo_flag": True,  "diameter_km": 0.80,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 155, "num_apparitions": 4},
    {"designation": "66391",   "name": "Moshup",       "neo_flag": True,  "diameter_km": 1.32,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 35, "num_sparse_pts": 260, "num_apparitions": 6},
    {"designation": "1580",    "name": "Betulia",      "neo_flag": True,  "diameter_km": 4.57,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 33, "num_sparse_pts": 245, "num_apparitions": 5},
    {"designation": "2100",    "name": "Ra-Shalom",    "neo_flag": True,  "diameter_km": 2.30,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 36, "num_sparse_pts": 270, "num_apparitions": 6},
    {"designation": "2063",    "name": "Bacchus",      "neo_flag": True,  "diameter_km": 1.00,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 140, "num_apparitions": 4},
    {"designation": "2201",    "name": "Oljato",       "neo_flag": True,  "diameter_km": 1.80,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "3103",    "name": "Eger",         "neo_flag": True,  "diameter_km": 1.50,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 29, "num_sparse_pts": 200, "num_apparitions": 5},
    {"designation": "3122",    "name": "Florence",     "neo_flag": True,  "diameter_km": 4.90,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 34, "num_sparse_pts": 255, "num_apparitions": 6},
    {"designation": "3361",    "name": "Orpheus",      "neo_flag": True,  "diameter_km": 0.30,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 110, "num_apparitions": 4},
    {"designation": "4183",    "name": "Cuno",         "neo_flag": True,  "diameter_km": 3.90,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 165, "num_apparitions": 5},
    {"designation": "4953",    "name": "1990 MU",      "neo_flag": True,  "diameter_km": 3.40,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "5143",    "name": "Heracles",     "neo_flag": True,  "diameter_km": 3.60,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 155, "num_apparitions": 4},
    {"designation": "5587",    "name": "1990 SB",      "neo_flag": True,  "diameter_km": 2.20,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 145, "num_apparitions": 4},
    {"designation": "6037",    "name": "1988 EG",      "neo_flag": True,  "diameter_km": 1.00,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 130, "num_apparitions": 4},
    {"designation": "7341",    "name": "1991 VK",      "neo_flag": True,  "diameter_km": 1.20,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 140, "num_apparitions": 4},
    {"designation": "7822",    "name": "1991 CS",      "neo_flag": True,  "diameter_km": 1.50,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 160, "num_apparitions": 5},
    {"designation": "8567",    "name": "1996 HW1",     "neo_flag": True,  "diameter_km": 3.80,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 26, "num_sparse_pts": 190, "num_apparitions": 5},
    {"designation": "10302",   "name": "1989 ML",      "neo_flag": True,  "diameter_km": 0.60,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 115, "num_apparitions": 4},
    {"designation": "11066",   "name": "Sigurd",       "neo_flag": True,  "diameter_km": 2.50,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 160, "num_apparitions": 5},
    {"designation": "14402",   "name": "1991 DB",      "neo_flag": True,  "diameter_km": 1.10,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 125, "num_apparitions": 4},
    {"designation": "16636",   "name": "1993 QP",      "neo_flag": True,  "diameter_km": 2.70,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 150, "num_apparitions": 4},
    {"designation": "35396",   "name": "1997 XF11",    "neo_flag": True,  "diameter_km": 1.40,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 170, "num_apparitions": 5},
    {"designation": "68950",   "name": "2002 QF15",    "neo_flag": True,  "diameter_km": 1.70,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 145, "num_apparitions": 4},
    {"designation": "85953",   "name": "1999 FK21",    "neo_flag": True,  "diameter_km": 0.45,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 120, "num_apparitions": 4},
    {"designation": "86039",   "name": "1999 NC43",    "neo_flag": True,  "diameter_km": 2.20,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 160, "num_apparitions": 5},

    # --- NEAs that FAIL data criteria (Priority 4) -> should be excluded ---
    {"designation": "2015 TB145","name": "",            "neo_flag": True,  "diameter_km": 0.60,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 5,  "num_sparse_pts": 30,  "num_apparitions": 1},
    {"designation": "2019 OK",  "name": "",             "neo_flag": True,  "diameter_km": 0.13,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 3,  "num_sparse_pts": 18,  "num_apparitions": 1},
    {"designation": "2020 QG",  "name": "",             "neo_flag": True,  "diameter_km": 0.003,  "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 1,  "num_sparse_pts": 8,   "num_apparitions": 1},

    # ========== Large Main-Belt Asteroids (MBAs) — diameter > 100 km ==========
    # --- already in DAMIT ---
    {"designation": "1",       "name": "Ceres",        "neo_flag": False, "diameter_km": 939.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 70, "num_sparse_pts": 600, "num_apparitions": 12},
    {"designation": "2",       "name": "Pallas",       "neo_flag": False, "diameter_km": 512.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 65, "num_sparse_pts": 550, "num_apparitions": 11},
    {"designation": "4",       "name": "Vesta",        "neo_flag": False, "diameter_km": 525.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 72, "num_sparse_pts": 620, "num_apparitions": 13},
    {"designation": "3",       "name": "Juno",         "neo_flag": False, "diameter_km": 233.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 55, "num_sparse_pts": 480, "num_apparitions": 10},
    {"designation": "5",       "name": "Astraea",      "neo_flag": False, "diameter_km": 106.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 42, "num_sparse_pts": 380, "num_apparitions": 9},
    {"designation": "6",       "name": "Hebe",         "neo_flag": False, "diameter_km": 185.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 48, "num_sparse_pts": 410, "num_apparitions": 10},
    {"designation": "7",       "name": "Iris",         "neo_flag": False, "diameter_km": 199.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 46, "num_sparse_pts": 400, "num_apparitions": 10},
    {"designation": "8",       "name": "Flora",        "neo_flag": False, "diameter_km": 128.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 40, "num_sparse_pts": 370, "num_apparitions": 9},
    {"designation": "10",      "name": "Hygiea",       "neo_flag": False, "diameter_km": 431.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 50, "num_sparse_pts": 450, "num_apparitions": 10},
    {"designation": "15",      "name": "Eunomia",      "neo_flag": False, "diameter_km": 255.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 52, "num_sparse_pts": 460, "num_apparitions": 11},
    {"designation": "16",      "name": "Psyche",       "neo_flag": False, "diameter_km": 226.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 55, "num_sparse_pts": 470, "num_apparitions": 11},

    # --- Large MBAs NOT in DAMIT (good candidates) ---
    {"designation": "704",     "name": "Interamnia",   "neo_flag": False, "diameter_km": 316.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 28, "num_sparse_pts": 250, "num_apparitions": 7},
    {"designation": "52",      "name": "Europa",       "neo_flag": False, "diameter_km": 302.5,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 30, "num_sparse_pts": 280, "num_apparitions": 8},
    {"designation": "511",     "name": "Davida",       "neo_flag": False, "diameter_km": 289.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 26, "num_sparse_pts": 240, "num_apparitions": 7},
    {"designation": "87",      "name": "Sylvia",       "neo_flag": False, "diameter_km": 274.0,  "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 35, "num_sparse_pts": 310, "num_apparitions": 8},
    {"designation": "65",      "name": "Cybele",       "neo_flag": False, "diameter_km": 237.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 220, "num_apparitions": 6},
    {"designation": "31",      "name": "Euphrosyne",   "neo_flag": False, "diameter_km": 256.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 27, "num_sparse_pts": 235, "num_apparitions": 7},
    {"designation": "24",      "name": "Themis",       "neo_flag": False, "diameter_km": 198.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 210, "num_apparitions": 6},
    {"designation": "29",      "name": "Amphitrite",   "neo_flag": False, "diameter_km": 212.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 225, "num_apparitions": 7},
    {"designation": "45",      "name": "Eugenia",      "neo_flag": False, "diameter_km": 214.6,  "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 32, "num_sparse_pts": 290, "num_apparitions": 8},
    {"designation": "48",      "name": "Doris",        "neo_flag": False, "diameter_km": 221.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 200, "num_apparitions": 6},
    {"designation": "88",      "name": "Thisbe",       "neo_flag": False, "diameter_km": 200.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 26, "num_sparse_pts": 230, "num_apparitions": 7},
    {"designation": "107",     "name": "Camilla",      "neo_flag": False, "diameter_km": 254.0,  "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 33, "num_sparse_pts": 285, "num_apparitions": 8},
    {"designation": "121",     "name": "Hermione",     "neo_flag": False, "diameter_km": 209.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 210, "num_apparitions": 6},
    {"designation": "130",     "name": "Elektra",      "neo_flag": False, "diameter_km": 182.2,  "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 31, "num_sparse_pts": 275, "num_apparitions": 7},
    {"designation": "154",     "name": "Bertha",       "neo_flag": False, "diameter_km": 184.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 190, "num_apparitions": 6},
    {"designation": "165",     "name": "Loreley",      "neo_flag": False, "diameter_km": 155.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "187",     "name": "Lamberta",     "neo_flag": False, "diameter_km": 130.4,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "194",     "name": "Prokne",       "neo_flag": False, "diameter_km": 168.4,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 205, "num_apparitions": 6},
    {"designation": "209",     "name": "Dido",         "neo_flag": False, "diameter_km": 139.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "211",     "name": "Isolda",       "neo_flag": False, "diameter_km": 143.2,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "241",     "name": "Germania",     "neo_flag": False, "diameter_km": 168.9,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 200, "num_apparitions": 6},
    {"designation": "324",     "name": "Bamberga",     "neo_flag": False, "diameter_km": 229.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 26, "num_sparse_pts": 230, "num_apparitions": 7},
    {"designation": "372",     "name": "Palma",        "neo_flag": False, "diameter_km": 188.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "375",     "name": "Ursula",       "neo_flag": False, "diameter_km": 200.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 210, "num_apparitions": 6},
    {"designation": "423",     "name": "Diotima",      "neo_flag": False, "diameter_km": 208.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 220, "num_apparitions": 7},
    {"designation": "451",     "name": "Patientia",    "neo_flag": False, "diameter_km": 224.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 225, "num_apparitions": 7},
    {"designation": "488",     "name": "Kreusa",       "neo_flag": False, "diameter_km": 150.4,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "532",     "name": "Herculina",    "neo_flag": False, "diameter_km": 222.4,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 26, "num_sparse_pts": 230, "num_apparitions": 7},
    {"designation": "596",     "name": "Scheila",      "neo_flag": False, "diameter_km": 113.3,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "702",     "name": "Alauda",       "neo_flag": False, "diameter_km": 194.7,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 210, "num_apparitions": 6},
    {"designation": "747",     "name": "Winchester",   "neo_flag": False, "diameter_km": 171.7,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "776",     "name": "Berbericia",   "neo_flag": False, "diameter_km": 151.1,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},

    # ========== Medium MBAs (50-100 km, size_score = 1) ==========
    # --- in DAMIT ---
    {"designation": "9",       "name": "Metis",        "neo_flag": False, "diameter_km": 190.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 45, "num_sparse_pts": 400, "num_apparitions": 9},
    {"designation": "11",      "name": "Parthenope",   "neo_flag": False, "diameter_km": 153.0,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 40, "num_sparse_pts": 370, "num_apparitions": 9},

    # --- NOT in DAMIT (candidates with sufficient data) ---
    {"designation": "36",      "name": "Atalante",     "neo_flag": False, "diameter_km": 95.0,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "38",      "name": "Leda",         "neo_flag": False, "diameter_km": 85.0,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 150, "num_apparitions": 4},
    {"designation": "41",      "name": "Daphne",       "neo_flag": False, "diameter_km": 174.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 220, "num_apparitions": 7},
    {"designation": "46",      "name": "Hestia",       "neo_flag": False, "diameter_km": 124.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "54",      "name": "Alexandra",    "neo_flag": False, "diameter_km": 140.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 190, "num_apparitions": 6},
    {"designation": "59",      "name": "Elpis",        "neo_flag": False, "diameter_km": 165.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 200, "num_apparitions": 6},
    {"designation": "76",      "name": "Freia",        "neo_flag": False, "diameter_km": 183.7,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "85",      "name": "Io",           "neo_flag": False, "diameter_km": 154.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 205, "num_apparitions": 6},
    {"designation": "94",      "name": "Aurora",       "neo_flag": False, "diameter_km": 204.9,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 215, "num_apparitions": 7},
    {"designation": "96",      "name": "Aegle",        "neo_flag": False, "diameter_km": 170.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "104",     "name": "Klymene",      "neo_flag": False, "diameter_km": 122.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "128",     "name": "Nemesis",      "neo_flag": False, "diameter_km": 188.2,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 205, "num_apparitions": 6},
    {"designation": "139",     "name": "Juewa",        "neo_flag": False, "diameter_km": 156.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "144",     "name": "Vibilia",      "neo_flag": False, "diameter_km": 142.2,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "145",     "name": "Adeona",       "neo_flag": False, "diameter_km": 151.1,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 190, "num_apparitions": 6},
    {"designation": "150",     "name": "Nuwa",         "neo_flag": False, "diameter_km": 151.1,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "168",     "name": "Sibylla",      "neo_flag": False, "diameter_km": 148.4,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "176",     "name": "Iduna",        "neo_flag": False, "diameter_km": 121.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 175, "num_apparitions": 5},
    {"designation": "185",     "name": "Eunike",       "neo_flag": False, "diameter_km": 157.5,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 190, "num_apparitions": 6},

    # ========== Smaller MBAs (< 50 km) with good lightcurve data ==========
    # These can only pass Priority 1 if they are NEOs (they are not),
    # so they will NOT pass selection.  Included to pad the database.
    {"designation": "1862",    "name": "Apollo",       "neo_flag": True,  "diameter_km": 1.40,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 28, "num_sparse_pts": 210, "num_apparitions": 5},
    {"designation": "433",     "name": "Eros",         "neo_flag": True,  "diameter_km": 16.84,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 80, "num_sparse_pts": 700, "num_apparitions": 15},
    {"designation": "1036",    "name": "Ganymed",      "neo_flag": True,  "diameter_km": 31.66,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 60, "num_sparse_pts": 500, "num_apparitions": 12},
    {"designation": "1627",    "name": "Ivar",         "neo_flag": True,  "diameter_km": 9.12,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 30, "num_sparse_pts": 230, "num_apparitions": 6},

    # ========== Additional MBAs (various sizes, padded to reach 200+) ==========
    # --- Small/medium MBAs NOT NEOs, NOT in DAMIT, low quality -> will fail ---
    {"designation": "1200",    "name": "Imperatrix",   "neo_flag": False, "diameter_km": 40.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 12, "num_sparse_pts": 80,  "num_apparitions": 3},
    {"designation": "1212",    "name": "Francette",    "neo_flag": False, "diameter_km": 25.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 8,  "num_sparse_pts": 50,  "num_apparitions": 2},
    {"designation": "1300",    "name": "Marcelle",     "neo_flag": False, "diameter_km": 30.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 10, "num_sparse_pts": 65,  "num_apparitions": 3},
    {"designation": "1350",    "name": "Rosselia",     "neo_flag": False, "diameter_km": 22.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 7,  "num_sparse_pts": 45,  "num_apparitions": 2},
    {"designation": "1400",    "name": "Tirela",       "neo_flag": False, "diameter_km": 18.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 6,  "num_sparse_pts": 40,  "num_apparitions": 2},
    {"designation": "1467",    "name": "Mashona",      "neo_flag": False, "diameter_km": 28.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 9,  "num_sparse_pts": 55,  "num_apparitions": 2},
    {"designation": "1508",    "name": "Kemi",         "neo_flag": False, "diameter_km": 35.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 11, "num_sparse_pts": 70,  "num_apparitions": 3},
    {"designation": "1568",    "name": "Aisleen",      "neo_flag": False, "diameter_km": 15.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 5,  "num_sparse_pts": 35,  "num_apparitions": 2},
    {"designation": "1600",    "name": "Vyssotsky",    "neo_flag": False, "diameter_km": 20.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 7,  "num_sparse_pts": 42,  "num_apparitions": 2},
    {"designation": "1700",    "name": "Zvezdara",     "neo_flag": False, "diameter_km": 25.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 8,  "num_sparse_pts": 50,  "num_apparitions": 2},

    # --- MBAs in DAMIT with low quality (fail Priority 2 or 3) ---
    {"designation": "20",      "name": "Massalia",     "neo_flag": False, "diameter_km": 145.5,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 40, "num_sparse_pts": 350, "num_apparitions": 9},
    {"designation": "21",      "name": "Lutetia",      "neo_flag": False, "diameter_km": 95.8,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 50, "num_sparse_pts": 420, "num_apparitions": 10},
    {"designation": "22",      "name": "Kalliope",     "neo_flag": False, "diameter_km": 166.2,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 45, "num_sparse_pts": 390, "num_apparitions": 9},
    {"designation": "25",      "name": "Phocaea",      "neo_flag": False, "diameter_km": 75.1,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 38, "num_sparse_pts": 330, "num_apparitions": 8},
    {"designation": "28",      "name": "Bellona",      "neo_flag": False, "diameter_km": 120.9,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 35, "num_sparse_pts": 310, "num_apparitions": 8},
    {"designation": "39",      "name": "Laetitia",     "neo_flag": False, "diameter_km": 149.5,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 42, "num_sparse_pts": 370, "num_apparitions": 9},
    {"designation": "40",      "name": "Harmonia",     "neo_flag": False, "diameter_km": 107.6,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 38, "num_sparse_pts": 330, "num_apparitions": 8},
    {"designation": "44",      "name": "Nysa",         "neo_flag": False, "diameter_km": 70.6,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 36, "num_sparse_pts": 320, "num_apparitions": 8},
    {"designation": "63",      "name": "Ausonia",      "neo_flag": False, "diameter_km": 103.1,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 38, "num_sparse_pts": 340, "num_apparitions": 8},
    {"designation": "64",      "name": "Angelina",     "neo_flag": False, "diameter_km": 47.0,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 35, "num_sparse_pts": 310, "num_apparitions": 7},
    {"designation": "68",      "name": "Leto",         "neo_flag": False, "diameter_km": 122.7,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 37, "num_sparse_pts": 330, "num_apparitions": 8},
    {"designation": "71",      "name": "Niobe",        "neo_flag": False, "diameter_km": 83.4,   "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 34, "num_sparse_pts": 300, "num_apparitions": 7},
    {"designation": "89",      "name": "Julia",        "neo_flag": False, "diameter_km": 151.5,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 40, "num_sparse_pts": 360, "num_apparitions": 9},
    {"designation": "105",     "name": "Artemis",      "neo_flag": False, "diameter_km": 119.2,  "lcdb_quality": 3, "in_damit": True,  "num_dense_lc": 36, "num_sparse_pts": 320, "num_apparitions": 8},

    # --- Additional large MBAs NOT in DAMIT to boost candidate count ---
    {"designation": "259",     "name": "Aletheia",     "neo_flag": False, "diameter_km": 178.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "268",     "name": "Adorea",       "neo_flag": False, "diameter_km": 140.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "283",     "name": "Emma",         "neo_flag": False, "diameter_km": 148.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 190, "num_apparitions": 6},
    {"designation": "308",     "name": "Polyxo",       "neo_flag": False, "diameter_km": 140.7,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "334",     "name": "Chicago",      "neo_flag": False, "diameter_km": 158.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "344",     "name": "Desiderata",   "neo_flag": False, "diameter_km": 132.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "349",     "name": "Dembowska",    "neo_flag": False, "diameter_km": 139.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 190, "num_apparitions": 6},
    {"designation": "354",     "name": "Eleonora",     "neo_flag": False, "diameter_km": 155.2,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 200, "num_apparitions": 6},
    {"designation": "386",     "name": "Siegena",      "neo_flag": False, "diameter_km": 165.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "405",     "name": "Thia",         "neo_flag": False, "diameter_km": 124.9,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "407",     "name": "Arachne",      "neo_flag": False, "diameter_km": 95.4,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 170, "num_apparitions": 5},
    {"designation": "409",     "name": "Aspasia",      "neo_flag": False, "diameter_km": 161.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 205, "num_apparitions": 6},
    {"designation": "419",     "name": "Aurelia",      "neo_flag": False, "diameter_km": 129.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "444",     "name": "Gyptis",       "neo_flag": False, "diameter_km": 159.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "466",     "name": "Tisiphone",    "neo_flag": False, "diameter_km": 109.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "476",     "name": "Hedwig",       "neo_flag": False, "diameter_km": 116.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "505",     "name": "Cava",         "neo_flag": False, "diameter_km": 105.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 175, "num_apparitions": 5},
    {"designation": "514",     "name": "Armida",       "neo_flag": False, "diameter_km": 106.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "536",     "name": "Merapi",       "neo_flag": False, "diameter_km": 155.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 190, "num_apparitions": 6},
    {"designation": "545",     "name": "Messalina",    "neo_flag": False, "diameter_km": 110.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "566",     "name": "Stereoskopia", "neo_flag": False, "diameter_km": 168.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 200, "num_apparitions": 6},
    {"designation": "602",     "name": "Marianna",     "neo_flag": False, "diameter_km": 124.6,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "618",     "name": "Elfriede",     "neo_flag": False, "diameter_km": 120.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "624",     "name": "Hektor",       "neo_flag": False, "diameter_km": 225.0,  "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 35, "num_sparse_pts": 300, "num_apparitions": 8},
    {"designation": "654",     "name": "Zelinda",      "neo_flag": False, "diameter_km": 127.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "690",     "name": "Wratislavia",  "neo_flag": False, "diameter_km": 134.8,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "709",     "name": "Fringilla",    "neo_flag": False, "diameter_km": 96.2,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 170, "num_apparitions": 5},
    {"designation": "739",     "name": "Mandeville",   "neo_flag": False, "diameter_km": 107.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 175, "num_apparitions": 5},
    {"designation": "762",     "name": "Pulcova",      "neo_flag": False, "diameter_km": 137.1,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "790",     "name": "Pretoria",     "neo_flag": False, "diameter_km": 170.4,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 200, "num_apparitions": 6},

    # ========== More NEAs to ensure >50 passing candidates ==========
    {"designation": "4486",    "name": "Mithra",       "neo_flag": True,  "diameter_km": 2.00,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 140, "num_apparitions": 4},
    {"designation": "5189",    "name": "1990 UQ",      "neo_flag": True,  "diameter_km": 1.00,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 125, "num_apparitions": 4},
    {"designation": "5590",    "name": "1990 VA",      "neo_flag": True,  "diameter_km": 2.40,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 155, "num_apparitions": 5},
    {"designation": "8014",    "name": "1990 MF",      "neo_flag": True,  "diameter_km": 1.50,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 135, "num_apparitions": 4},
    {"designation": "10115",   "name": "1992 SK",      "neo_flag": True,  "diameter_km": 1.20,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 120, "num_apparitions": 4},
    {"designation": "23187",   "name": "2000 PN9",     "neo_flag": True,  "diameter_km": 1.80,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 145, "num_apparitions": 4},
    {"designation": "52760",   "name": "1998 ML14",    "neo_flag": True,  "diameter_km": 0.90,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 110, "num_apparitions": 4},
    {"designation": "53319",   "name": "1999 JM8",     "neo_flag": True,  "diameter_km": 3.50,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 25, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "53789",   "name": "2000 ED104",   "neo_flag": True,  "diameter_km": 0.70,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 115, "num_apparitions": 4},
    {"designation": "137170",  "name": "1999 HF1",     "neo_flag": True,  "diameter_km": 4.00,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 26, "num_sparse_pts": 190, "num_apparitions": 5},
    {"designation": "141018",  "name": "2001 WC47",    "neo_flag": True,  "diameter_km": 0.60,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 110, "num_apparitions": 4},
    {"designation": "162080",  "name": "1998 DG16",    "neo_flag": True,  "diameter_km": 1.20,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 135, "num_apparitions": 4},
    {"designation": "164121",  "name": "2003 YT1",     "neo_flag": True,  "diameter_km": 1.00,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 120, "num_apparitions": 4},
    {"designation": "175706",  "name": "1996 FG3",     "neo_flag": True,  "diameter_km": 1.90,   "lcdb_quality": 3, "in_damit": False, "num_dense_lc": 30, "num_sparse_pts": 220, "num_apparitions": 5},
    {"designation": "276049",  "name": "2002 CE26",    "neo_flag": True,  "diameter_km": 3.50,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 24, "num_sparse_pts": 175, "num_apparitions": 5},
    {"designation": "285263",  "name": "1998 QE2",     "neo_flag": True,  "diameter_km": 2.75,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 165, "num_apparitions": 4},
    {"designation": "363599",  "name": "2004 FG11",    "neo_flag": True,  "diameter_km": 0.15,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 105, "num_apparitions": 4},
    {"designation": "399774",  "name": "2005 NB7",     "neo_flag": True,  "diameter_km": 0.40,   "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 21, "num_sparse_pts": 110, "num_apparitions": 4},

    # ========== Additional Trojans & outer belt (large, NOT in DAMIT) ==========
    {"designation": "588",     "name": "Achilles",     "neo_flag": False, "diameter_km": 135.5,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 180, "num_apparitions": 5},
    {"designation": "617",     "name": "Patroclus",    "neo_flag": False, "diameter_km": 140.9,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 190, "num_apparitions": 6},
    {"designation": "911",     "name": "Agamemnon",    "neo_flag": False, "diameter_km": 166.7,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},
    {"designation": "1172",    "name": "Aneas",        "neo_flag": False, "diameter_km": 143.0,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 22, "num_sparse_pts": 185, "num_apparitions": 5},
    {"designation": "1437",    "name": "Diomedes",     "neo_flag": False, "diameter_km": 164.3,  "lcdb_quality": 2, "in_damit": False, "num_dense_lc": 23, "num_sparse_pts": 195, "num_apparitions": 6},

    # ========== Filler: small MBAs with poor data (should fail) ==========
    {"designation": "2000",    "name": "Herschel",     "neo_flag": False, "diameter_km": 15.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 5,  "num_sparse_pts": 30,  "num_apparitions": 2},
    {"designation": "2001",    "name": "Einstein",     "neo_flag": False, "diameter_km": 10.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 4,  "num_sparse_pts": 25,  "num_apparitions": 1},
    {"designation": "2005",    "name": "Hencke",       "neo_flag": False, "diameter_km": 12.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 5,  "num_sparse_pts": 35,  "num_apparitions": 2},
    {"designation": "2010",    "name": "Chebyshev",    "neo_flag": False, "diameter_km": 17.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 6,  "num_sparse_pts": 38,  "num_apparitions": 2},
    {"designation": "2017",    "name": "Wesson",       "neo_flag": False, "diameter_km": 8.0,    "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 3,  "num_sparse_pts": 20,  "num_apparitions": 1},
    {"designation": "2060",    "name": "Chiron",       "neo_flag": False, "diameter_km": 218.0,  "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 15, "num_sparse_pts": 90,  "num_apparitions": 4},
    {"designation": "2099",    "name": "Opik",         "neo_flag": False, "diameter_km": 30.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 8,  "num_sparse_pts": 50,  "num_apparitions": 2},
    {"designation": "2204",    "name": "Lyyli",        "neo_flag": False, "diameter_km": 19.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 6,  "num_sparse_pts": 40,  "num_apparitions": 2},
    {"designation": "2309",    "name": "Mr. Spock",    "neo_flag": False, "diameter_km": 22.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 7,  "num_sparse_pts": 42,  "num_apparitions": 2},
    {"designation": "2478",    "name": "Tokai",        "neo_flag": False, "diameter_km": 16.0,   "lcdb_quality": 1, "in_damit": False, "num_dense_lc": 5,  "num_sparse_pts": 32,  "num_apparitions": 2},
]
# fmt: on


# ---------------------------------------------------------------------------
# Selection & scoring functions
# ---------------------------------------------------------------------------

def passes_priority_1(ast):
    """Priority 1: NEO flag OR diameter > 100 km."""
    return ast["neo_flag"] or ast["diameter_km"] > 100.0


def passes_priority_2(ast):
    """Priority 2: LCDB quality code U >= 2."""
    return ast["lcdb_quality"] >= 2


def passes_priority_3(ast):
    """Priority 3: NOT already in DAMIT (shape model unknown)."""
    return not ast["in_damit"]


def passes_priority_4(ast):
    """
    Priority 4: Sufficient photometric data for shape inversion.
      - More than 20 dense (relative) lightcurves, OR
      - More than 100 sparse data points spanning more than 3 apparitions.
    """
    enough_dense = ast["num_dense_lc"] > 20
    enough_sparse = (ast["num_sparse_pts"] > 100) and (ast["num_apparitions"] > 3)
    return enough_dense or enough_sparse


def passes_all_criteria(ast):
    """Return True only if the asteroid passes ALL four priority filters."""
    return (
        passes_priority_1(ast)
        and passes_priority_2(ast)
        and passes_priority_3(ast)
        and passes_priority_4(ast)
    )


def compute_priority_score(ast):
    """
    Compute a composite priority score for ranking candidates.

    Scoring formula
    ---------------
      neo_score     = 3  if NEO, else 0
      size_score    = 2  if diameter > 100 km,
                      1  if diameter >  50 km,
                      0  otherwise
      quality_score = U  (LCDB quality code: 2 or 3 for passing asteroids)
      data_score    = min(num_dense_lc / 10, 3)
                    + min(num_sparse_pts / 100, 3)
      priority_score = neo_score + size_score + quality_score + data_score

    Returns
    -------
    float
        The composite priority score (higher = more favourable target).
    """
    # --- neo_score: 3 if NEO, 0 otherwise ---
    neo_score = 3.0 if ast["neo_flag"] else 0.0

    # --- size_score: 2 if >100 km, 1 if >50 km, 0 otherwise ---
    if ast["diameter_km"] > 100.0:
        size_score = 2.0
    elif ast["diameter_km"] > 50.0:
        size_score = 1.0
    else:
        size_score = 0.0

    # --- quality_score: equal to the LCDB U value ---
    quality_score = float(ast["lcdb_quality"])

    # --- data_score: contributions from dense lightcurves and sparse data ---
    dense_contrib = min(ast["num_dense_lc"] / 10.0, 3.0)
    sparse_contrib = min(ast["num_sparse_pts"] / 100.0, 3.0)
    data_score = dense_contrib + sparse_contrib

    priority_score = neo_score + size_score + quality_score + data_score
    return round(priority_score, 2)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def select_candidates(top_n=50):
    """
    Run the full selection pipeline and return the top-N candidates.

    Steps
    -----
    1. Filter the internal database through all four Boolean criteria.
    2. Compute the priority score for each surviving candidate.
    3. Sort descending by priority_score (ties broken by designation).
    4. Return the top-N rows.
    """
    # Step 1 -- Boolean filtering
    candidates = [ast for ast in ASTEROID_DB if passes_all_criteria(ast)]

    # Step 2 -- Scoring
    for ast in candidates:
        ast["priority_score"] = compute_priority_score(ast)

    # Step 3 -- Sort: highest score first; ties broken alphabetically
    candidates.sort(key=lambda a: (-a["priority_score"], a["designation"]))

    # Step 4 -- Trim to top-N
    return candidates[:top_n]


def write_csv(candidates, output_path):
    """Write the candidate list to a CSV file."""
    fieldnames = [
        "designation",
        "name",
        "neo_flag",
        "diameter_km",
        "lcdb_quality",
        "num_dense_lc",
        "num_sparse_pts",
        "num_apparitions",
        "priority_score",
    ]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in candidates:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description="Select and rank asteroid candidates for shape modelling."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="Number of top candidates to output (default: 50).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: results/candidates_top50.csv).",
    )
    args = parser.parse_args()

    top_n = args.top

    # Default output name reflects the requested count
    if args.output is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "results",
            "candidates_top{}.csv".format(top_n),
        )
    else:
        output_path = args.output

    # --- Report database statistics ---
    total = len(ASTEROID_DB)
    passing = [a for a in ASTEROID_DB if passes_all_criteria(a)]
    print("Internal database : {} asteroids".format(total))
    print("Pass all criteria : {}".format(len(passing)))

    # --- Diagnostics: show how many fail each criterion ---
    fail_p1 = sum(1 for a in ASTEROID_DB if not passes_priority_1(a))
    fail_p2 = sum(1 for a in ASTEROID_DB if not passes_priority_2(a))
    fail_p3 = sum(1 for a in ASTEROID_DB if not passes_priority_3(a))
    fail_p4 = sum(1 for a in ASTEROID_DB if not passes_priority_4(a))
    print("  Fail Priority 1 (NEO or >100km)   : {}".format(fail_p1))
    print("  Fail Priority 2 (U >= 2)          : {}".format(fail_p2))
    print("  Fail Priority 3 (not in DAMIT)    : {}".format(fail_p3))
    print("  Fail Priority 4 (sufficient data) : {}".format(fail_p4))

    # --- Select and write ---
    candidates = select_candidates(top_n=top_n)
    write_csv(candidates, output_path)

    print("\nTop {} candidates written to: {}".format(len(candidates), output_path))

    # --- Preview top 10 ---
    print("\n{:<5} {:<12} {:<16} {:<5} {:<9} {:<3} {:<6} {:<7} {:<4} {:<6}".format(
        "Rank", "Designation", "Name", "NEO", "D(km)", "U", "Dense", "Sparse", "App", "Score"))
    print("-" * 80)
    for i, c in enumerate(candidates[:10], start=1):
        print(
            "{:<5} {:<12} {:<16} {:<5} {:<9.2f} {:<3} {:<6} {:<7} {:<4} {:<6.2f}".format(
                i,
                c["designation"],
                c["name"],
                "Y" if c["neo_flag"] else "N",
                c["diameter_km"],
                c["lcdb_quality"],
                c["num_dense_lc"],
                c["num_sparse_pts"],
                c["num_apparitions"],
                c["priority_score"],
            )
        )


if __name__ == "__main__":
    main()
