# Data Sources and Open-Source Codebases Survey

## Code Repositories

### 1. DAMIT-convex (convexinv / conjgradinv)
- **URL:** https://github.com/mkretlow/DAMIT-convex
- **Official source:** https://astro.troja.mff.cuni.cz/projects/damit/pages/software_download
- **Language:** C (Fortran bindings)
- **License:** Not explicitly stated; academic use
- **Capabilities:** Two programs — `convexinv` (spherical harmonics shape optimization with full parameter search) and `conjgradinv` (conjugate gradient optimization of facet areas only). Implements the Kaasalainen-Torppa convex inversion method. Accepts dense lightcurve input, performs period + pole search, outputs convex shape model. The de facto standard tool used to populate the DAMIT database.
- **Relevance:** Reference implementation for our convex inversion solver (Module 2). We study its algorithm but implement from scratch in Python.

### 2. ADAM (All-Data Asteroid Modeling)
- **URL:** https://github.com/matvii/ADAM
- **Language:** MATLAB with core routines in C
- **License:** Not explicitly stated; academic use
- **Capabilities:** Multi-modal asteroid shape reconstruction from lightcurves, adaptive optics images, stellar occultation timings, radar delay-Doppler images, and interferometry. Supports non-convex shapes. Handles multiple data types via unified 2D Fourier transform projection.
- **Relevance:** Reference for multi-data fusion methodology (Module 9). We study its data fusion approach but our pipeline focuses on photometry-only inversion.

### 3. Asteroids@home / PeriodSearch
- **URL:** https://github.com/AsteroidsAtHome/PeriodSearch
- **CUDA version:** https://github.com/JStateson/CUDA12_PeriodSearch
- **Language:** C/C++ (BOINC distributed computing framework)
- **License:** GNU LGPL
- **Capabilities:** Distributed computing period search for asteroid lightcurve inversion. Scans dense period grids using sparse photometric data. CUDA-accelerated version available. Used to derive hundreds of asteroid models from survey data.
- **Relevance:** Reference for period search optimization strategy (Module 7) and C++ acceleration approach (Module 12).

### 4. MPO LCInvert
- **URL:** https://minplanobs.org/BdwPub/php/mpolcinvert.php
- **Language:** Proprietary (Windows binary)
- **License:** Commercial software by Brian D. Warner
- **Capabilities:** Implementation of the Kaasalainen lightcurve inversion method for amateur and professional use. Derives shapes and spin axes from lightcurve data. Integrates with MPO Canopus photometry software.
- **Relevance:** Commercial baseline tool we aim to surpass. Methodology documented in Warner (2007).

### 5. sbpy (Small-Body Python)
- **URL:** https://sbpy.readthedocs.io/
- **Language:** Python
- **License:** BSD 3-Clause
- **Capabilities:** Python library for small-body planetary astronomy. Includes phase curve models (H-G, H-G1-G2), photometric calibration utilities, orbit computation, and spectroscopic tools. Not an inversion tool, but provides useful utility functions.
- **Relevance:** Potential utility library for phase curve fitting and photometric calibration (Module 4).

### 6. astroquery
- **URL:** https://astroquery.readthedocs.io/
- **Language:** Python
- **License:** BSD 3-Clause
- **Capabilities:** Python package for querying astronomical databases including MPC, JPL Horizons, Gaia archive, MAST, and others. Provides programmatic access to orbital elements, ephemerides, and photometric data.
- **Relevance:** Key tool for data ingestion (Module 6) — querying MPC and JPL for orbital elements and ephemerides.

---

## Data Repositories

### 1. DAMIT (Database of Asteroid Models from Inversion Techniques)
- **URL:** https://astro.troja.mff.cuni.cz/projects/damit/
- **Access:** Web interface, direct download of `.obj` shape files and spin parameters
- **Content:** >5700 convex shape models with spin states (pole direction, period) for >3300 asteroids. Models derived via lightcurve inversion. Includes photometric data used for each inversion.
- **Data Format:** Shape models as vertex/face lists (convertible to `.obj`), spin parameters as text files (lambda, beta, period, JD0)
- **Access Method:** Browse by asteroid number/name; download individual model files. No formal API, but structured URL patterns allow scripted access.
- **Use in Pipeline:** Ground truth shapes for validation (Module 5), reference models for benchmarking.

### 2. ALCDEF (Asteroid Lightcurve Data Exchange Format)
- **URL:** https://alcdef.org/
- **Mirror:** https://minplanobs.org/mpinfo/php/alcdef.php
- **PDS Archive:** urn:nasa:pds:gbo.ast.alcdef-database::1.0
- **Access:** Web search interface at alcdef.org; bulk download from PDS
- **Content:** >2.5 million time-series photometry data points for >11,400 asteroids. Raw (uncalibrated) differential and absolute photometry.
- **Data Format:** ALCDEF standard — FITS-like keyword=value ASCII format with JD, magnitude, filter, observer metadata. One file per observing session.
- **Access Method:** Search by asteroid number/name on web interface; retrieve individual ALCDEF files. PDS bulk archive also available.
- **Use in Pipeline:** Primary source of dense lightcurves for inversion (Module 6).

### 3. NASA PDS Small Bodies Node
- **URL:** https://sbn.psi.edu/
- **Access:** Web interface, direct download, PDS4 bundles
- **Content:** Calibrated photometric, spectroscopic, radar, and shape model data for asteroids, comets, and other small bodies. Includes mission data (NEAR Shoemaker for Eros, Hayabusa for Itokawa, etc.) and ground-based survey data.
- **Data Format:** PDS3/PDS4 format (labeled data products with XML metadata)
- **Access Method:** Browse by dataset; download collections. Some datasets accessible via DOI.
- **Use in Pipeline:** Supplementary photometric data and high-fidelity spacecraft-derived shape models for validation.

### 4. Gaia DR3 Solar System Objects
- **URL:** https://gea.esac.esa.int/archive/ (table: `gaiadr3.sso_observation`)
- **Access:** ADQL queries via Gaia Archive web interface or TAP service
- **Content:** 23.3 million photometric observations of 158,152 solar system objects. G-band photometry with sub-millimagnitude precision for bright objects. Also includes osculating orbital elements and reflectance spectra.
- **Data Format:** VOTable, CSV, FITS (query results); epoch-level photometry with JD, G-mag, position
- **Access Method:** ADQL query on `gaiadr3.sso_observation` table filtered by `number_mp` (asteroid number). Example: `SELECT * FROM gaiadr3.sso_observation WHERE number_mp = 433`
- **Use in Pipeline:** High-precision sparse photometry for sparse inversion mode (Module 4).

### 5. ZTF (Zwicky Transient Facility)
- **URL:** https://www.ztf.caltech.edu/ztf-public-releases.html
- **Archive:** https://irsa.ipac.caltech.edu/Missions/ztf.html
- **Access:** IRSA archive queries, ZTF Forced Photometry Service (ZFPS)
- **Content:** Wide-field optical survey (g, r, i bands) covering entire northern sky. Public data releases on 60-day sliding window. Forced photometry lightcurves available for arbitrary sky positions.
- **Data Format:** CSV/FITS photometry catalogs; forced photometry includes JD, flux, uncertainty, filter, field metadata
- **Access Method:** ZFPS for batch forced photometry (up to 1500 positions per request); IRSA for catalog queries. Requires registration for ZFPS.
- **Use in Pipeline:** Sparse survey photometry to supplement phase angle coverage (Module 4).

### 6. Pan-STARRS (Panoramic Survey Telescope and Rapid Response System)
- **URL:** https://archive.stsci.edu/panstarrs/
- **Access:** MAST Portal, CasJobs (SQL), TAP service
- **Content:** 5-band (g, r, i, z, y) optical survey of 3/4 of sky. >2.5 billion objects with multi-epoch detection photometry (average ~50 epochs per object). PS1 DR2 is the largest astronomical data release at 1.6 PB.
- **Data Format:** Database tables queryable via SQL; results in CSV, VOTable, FITS
- **Access Method:** CasJobs SQL queries on detection photometry tables; MAST portal for searches. Programmatic access via Python with `astroquery.mast`.
- **Use in Pipeline:** Multi-epoch sparse photometry for filling phase angle gaps (Module 4).

### 7. MPC (Minor Planet Center)
- **URL:** https://www.minorplanetcenter.net/
- **Web Service:** https://minorplanetcenter.net/web_service/
- **MPCORB Database:** https://www.minorplanetcenter.net/iau/MPCORB.html
- **Access:** Web service API (JSON), MPCORB.dat bulk download, astroquery.mpc Python module
- **Content:** Orbital elements for >1.3 million minor planets. Observation records, designations, discovery information. NEO classification flags.
- **Data Format:** JSON (API), fixed-width text (MPCORB.dat)
- **Access Method:** `astroquery.mpc.MPC.query_object()` for individual objects; web service API with JSON parameter filtering; bulk MPCORB.dat download.
- **Use in Pipeline:** Orbital elements for viewing geometry computation (Module 8), NEO flag for target selection (Module 10).

### 8. LCDB (Asteroid Lightcurve Database)
- **URL:** https://minplanobs.org/mpinfo/php/lcdb.php
- **PDS Archive:** urn:nasa:pds:ast-lightcurve-database (V4.0)
- **Access:** Web search, bulk download as dBASE IV tables
- **Content:** Compiled rotation periods, lightcurve amplitudes, diameters, taxonomic classes, and quality codes (U) for >30,000 asteroids. Quality code U ranges from 0 (result unreliable) to 3 (unambiguous period).
- **Data Format:** dBASE IV tables (lc_summary, lc_details); CSV exports available
- **Access Method:** Web search by number/name; bulk download of full database files.
- **Use in Pipeline:** Quality code filtering for target selection (Module 10); known period priors for inversion.

### 9. JPL Asteroid Radar Research
- **URL:** https://echo.jpl.nasa.gov/asteroids/
- **Access:** Web interface, individual model downloads
- **Content:** Radar-derived shape models for ~100 asteroids observed by Goldstone and Arecibo radar systems. Highest-fidelity ground-based shape models available (gold standard for validation).
- **Data Format:** SHAPE format (vertex/face lists), some available as `.obj`
- **Access Method:** Browse by asteroid; download individual shape files.
- **Use in Pipeline:** Gold-standard ground truth shapes for validation benchmarking (Module 5).

---

## Summary Table

| Repository | Type | Access | Key Content | Pipeline Module |
|---|---|---|---|---|
| DAMIT | Ground Truth | Web/Download | 5700+ shape models | M5, M6 |
| ALCDEF | Dense Photometry | Web/PDS | 2.5M+ observations | M6 |
| PDS SBN | Multi-type | Web/Download | Mission data, calibrated photometry | M6 |
| Gaia DR3 SSO | Sparse Photometry | ADQL/TAP | 23M observations | M4, M6 |
| ZTF | Sparse Photometry | IRSA/ZFPS | Northern sky survey | M4, M6 |
| Pan-STARRS | Sparse Photometry | MAST/CasJobs | 2.5B objects, multi-epoch | M4, M6 |
| MPC | Orbital Elements | API/Bulk | 1.3M+ minor planets | M8, M10 |
| LCDB | Period/Quality | Web/Download | 30K+ asteroids | M10 |
| JPL Radar | Ground Truth | Web | ~100 radar shapes | M5 |

| Code Repo | Language | License | Key Capability |
|---|---|---|---|
| DAMIT-convex | C | Academic | Convex inversion (reference) |
| ADAM | MATLAB/C | Academic | Multi-data reconstruction |
| PeriodSearch | C/C++ | LGPL | Distributed period search |
| MPO LCInvert | Proprietary | Commercial | Convex inversion (baseline) |
| sbpy | Python | BSD | Phase curves, photometry utilities |
| astroquery | Python | BSD | Database query interface |
