# Light Curve Inversion Pipeline — Module Architecture

## Overview

This document defines the modular architecture of the custom Light Curve Inversion (LCI) pipeline. The system is designed to reconstruct 3D asteroid shape models and spin states from photometric observations (both dense time-series lightcurves and sparse survey data). The pipeline synthesizes methods from convex inversion (Kaasalainen & Torppa 2001), genetic/evolutionary optimization (Bartczak & Dudzinski 2018, SAGE), sparse photometric inversion (Durech et al. 2009/2010), and multi-data fusion (Viikinkoski et al. 2015, ADAM).

---

## Module 1: Forward Model / Scattering Engine (`forward_model.py`)

**Responsibility:** Compute the disk-integrated brightness of a faceted 3D shape model at a given epoch, accounting for the illumination and viewing geometry and surface scattering properties.

**Key capabilities:**
- Load a triangulated mesh (`.obj` format) representing the asteroid shape
- Compute visible and illuminated facet areas from Sun and observer direction vectors
- Apply combined Lambert + Lommel-Seeliger scattering law to each facet
- Sum facet contributions to produce a single disk-integrated brightness value
- Generate full synthetic lightcurves over a sequence of Julian Date epochs

**Inputs:**
- Triangulated mesh (vertices, faces)
- Spin state: pole direction (ecliptic lambda, beta), sidereal rotation period (hours), reference epoch (JD)
- Observer/Sun positions at each epoch (or orbital elements + epoch list)
- Scattering parameters (Lambert weight `c_L`, Lommel-Seeliger weight)

**Outputs:**
- Array of synthetic brightness values at requested epochs
- Per-facet visibility/illumination flags (for debugging)

**Dependencies:** Module 8 (Viewing Geometry Calculator)

---

## Module 2: Convex Inversion Solver (`convex_solver.py`)

**Responsibility:** Determine the best-fit convex shape, pole direction, and sidereal period by minimizing chi-squared residuals between observed and modeled lightcurves, following the Kaasalainen-Torppa method.

**Key capabilities:**
- Parameterize convex shapes via spherical harmonics (Gaussian surface area density) or direct facet-area representation
- Levenberg-Marquardt gradient-based optimization of shape parameters at fixed pole+period
- Period search via chi-squared scanning over a user-specified range with configurable step
- Pole direction grid search over (lambda, beta) hemisphere
- Regularization (smoothness penalty, non-negativity constraint on facet areas)

**Inputs:**
- Observed lightcurve data (JD, magnitude, uncertainty)
- Period search range (P_min, P_max, step)
- Pole grid resolution
- Spherical harmonics order or number of facets
- Regularization weights

**Outputs:**
- Best-fit convex shape (as mesh vertices/faces)
- Best-fit pole direction (lambda, beta) in ecliptic coordinates
- Best-fit sidereal period (hours)
- Chi-squared residual and convergence history
- Period scan chi-squared landscape

**Dependencies:** Module 1 (Forward Model), Module 7 (Period Search)

---

## Module 3: Evolutionary/Genetic Solver (`genetic_solver.py`)

**Responsibility:** Optimize non-convex asteroid shape models using a population-based evolutionary algorithm (inspired by SAGE, Bartczak & Dudzinski 2018). Capable of recovering concavities, bifurcated shapes, and large-scale surface features missed by convex inversion.

**Key capabilities:**
- Represent individuals as non-convex triangulated meshes (vertex positions as genome)
- Mutation operators: vertex displacement with topology preservation, Laplacian smoothing
- Crossover: weighted vertex interpolation between parent meshes
- Tournament selection with elitism
- Fitness function: chi-squared of lightcurve fit (from forward model)
- Configurable population size (>= 50), generation count, mutation rate

**Inputs:**
- Observed lightcurve data
- Initial seed mesh (from convex solver or random icosphere)
- Fixed pole and period (from convex solver or supplied)
- GA hyperparameters (pop_size, n_generations, mutation_rate, crossover_rate)

**Outputs:**
- Best-fit non-convex mesh (vertices, faces)
- Fitness/chi-squared convergence history per generation
- Population diversity metrics

**Dependencies:** Module 1 (Forward Model)

---

## Module 4: Sparse Data Handler (`sparse_handler.py`)

**Responsibility:** Parse, calibrate, and integrate sparse photometric data (from Gaia DR3, ZTF, Pan-STARRS, CSS, and other surveys) into the inversion objective function. Also supports standalone sparse-only inversion.

**Key capabilities:**
- Parse Gaia DR3 SSO CSV, ZTF forced-photometry, Pan-STARRS DR2, and generic CSV formats
- Calibrate apparent magnitudes to reduced magnitude using H-G or H-G1-G2 phase curve model (Muinonen et al. 2010)
- Compute proper weighting for sparse data in combined chi-squared (following Durech et al. 2009)
- Standalone sparse-only mode: period search (Lomb-Scargle / phase dispersion minimization), pole search via brightness residual minimization, crude ellipsoid shape estimation

**Inputs:**
- Sparse photometry files (JD, magnitude, filter, uncertainty)
- Asteroid orbital elements (for phase angle computation)
- Phase curve parameters (H, G or H, G1, G2)

**Outputs:**
- Calibrated sparse brightness array with viewing geometry metadata
- Weighted chi-squared contribution from sparse data
- (Sparse-only mode) Best-fit pole, period, and ellipsoid axis ratios

**Dependencies:** Module 8 (Viewing Geometry Calculator)

---

## Module 5: Mesh Comparator (`mesh_comparator.py`)

**Responsibility:** Quantitatively compare two 3D shape models (a recovered model vs. ground truth) using standard mesh comparison metrics.

**Key capabilities:**
- Load two `.obj` meshes and normalize to common scale/orientation (align by principal axes)
- Sample surface point clouds (>= 10000 points per mesh) via barycentric random sampling
- Compute one-sided and symmetric Hausdorff distance
- Compute Volumetric Intersection over Union (IoU) via voxelization at user-specified resolution
- Compute Chamfer distance as supplementary metric

**Inputs:**
- Two mesh file paths (`.obj`)
- Sampling density (number of surface points)
- Voxel resolution for IoU

**Outputs:**
- Hausdorff distance (one-sided A->B, B->A, symmetric)
- Volumetric IoU
- Chamfer distance
- Normalized Hausdorff (as fraction of bounding-box diagonal)

**Dependencies:** None (standalone utility)

---

## Module 6: Data Ingestion Layer (`data_ingestion.py`)

**Responsibility:** Download, parse, and standardize photometric data from external databases (ALCDEF, DAMIT, PDS, MPC) and ground truth shape models.

**Key capabilities:**
- ALCDEF: download and parse ALCDEF-format files for a given asteroid, extracting JD, magnitude, filter, metadata
- DAMIT: download shape model `.obj` files and spin parameters for a given DAMIT asteroid ID
- PDS Small Bodies Node: retrieve calibrated sparse photometry
- MPC: fetch orbital elements for viewing geometry computation
- LCDB: parse lightcurve database summary for quality codes, periods, diameters

**Inputs:**
- Asteroid designation (number, name, or packed designation)
- Target database(s) to query

**Outputs:**
- Standardized `LightcurveData` objects (JD, mag, mag_err, filter, observer_geo, sun_geo)
- Standardized `ShapeModel` objects (vertices, faces, spin parameters)
- `OrbitalElements` objects (a, e, i, node, peri, M, epoch)

**Dependencies:** None (standalone, uses HTTP requests)

---

## Module 7: Period Search (`period_search.py`)

**Responsibility:** Determine the sidereal rotation period of an asteroid from photometric data using multiple complementary methods.

**Key capabilities:**
- Lomb-Scargle periodogram for initial period detection
- Phase Dispersion Minimization (PDM) for refinement
- Chi-squared landscape scanning (dense grid search over period range) integrated with forward model
- Multi-resolution search: coarse scan followed by fine refinement around best candidates
- Handle aliasing and distinguish sidereal vs. synodic period

**Inputs:**
- Lightcurve data (JD, magnitude)
- Search range (P_min, P_max)
- Step size / frequency resolution

**Outputs:**
- Best period estimate with uncertainty
- Periodogram / chi-squared landscape array
- Top-N period candidates with scores

**Dependencies:** Module 1 (Forward Model) for chi-squared scanning mode

---

## Module 8: Viewing Geometry Calculator (`geometry.py`)

**Responsibility:** Compute the Sun-asteroid-observer geometry (phase angle, aspect angle, solar elongation, light-time correction) at any epoch from orbital elements or ephemeris data.

**Key capabilities:**
- Keplerian orbit propagation (two-body) from osculating elements
- Compute heliocentric and geocentric asteroid positions
- Compute Sun and observer direction vectors in asteroid body frame (using pole + rotation)
- Phase angle, aspect angle, solar elongation at each epoch
- Light-time correction

**Inputs:**
- Orbital elements (a, e, i, Omega, omega, M0, epoch)
- Observer location (geocenter or topocentric coordinates)
- Pole direction (lambda, beta), period, epoch for body-frame transformation
- List of JD epochs

**Outputs:**
- Arrays of phase angle, aspect angle, solar elongation at each epoch
- Sun direction unit vectors in body frame
- Observer direction unit vectors in body frame
- Heliocentric/geocentric distance

**Dependencies:** None (standalone utility; may use `astropy` for coordinate transforms)

---

## Module 9: Hybrid Pipeline Orchestrator (`pipeline.py`)

**Responsibility:** Orchestrate the end-to-end inversion workflow: data ingestion, period search, convex inversion, non-convex refinement, uncertainty quantification, and output generation.

**Key capabilities:**
- Configure and chain all modules into a single pipeline run
- Decision logic: run convex inversion first, evaluate residuals, switch to evolutionary refinement if threshold exceeded
- Bootstrap uncertainty estimation (resample data, re-run inversion)
- Export results: `.obj` meshes, spin vector JSON, convergence logs
- Logging and progress tracking

**Inputs:**
- Asteroid designation
- Data source configuration (which databases to query)
- Pipeline parameters (period range, pole grid, GA hyperparams, convergence thresholds)

**Outputs:**
- Final shape model (`.obj`)
- Spin vector file (`.json`: lambda, beta, period, epoch, uncertainties)
- Convergence log
- Validation metrics (if ground truth provided)

**Dependencies:** All modules (1-8)

---

## Module 10: Target Selection Engine (`target_selector.py`)

**Responsibility:** Query external databases and apply Boolean selection criteria to identify high-priority asteroid targets for new shape modeling.

**Key capabilities:**
- Query MPC for NEO flag and orbital class
- Query LCDB for lightcurve quality code (U), period, diameter
- Query DAMIT for existing shape models
- Query ALCDEF for count of available dense lightcurves
- Apply selection logic: (NEO OR D > 100km) AND (U >= 2) AND (NOT in DAMIT) AND (sufficient data)
- Rank candidates by priority score

**Inputs:**
- Selection criteria thresholds
- Database access configuration

**Outputs:**
- `candidates_top50.csv`: ranked list with designation, name, NEO flag, diameter, quality code, data counts, priority score

**Dependencies:** Module 6 (Data Ingestion Layer) for database access

---

## Module 11: Uncertainty Quantification (`uncertainty.py`)

**Responsibility:** Estimate uncertainties on all derived parameters (pole direction, period, shape) using bootstrap resampling and chi-squared landscape analysis.

**Key capabilities:**
- Bootstrap resampling of photometric data points (>= 100 iterations)
- Re-run inversion for each bootstrap sample (pole + period + shape)
- Compute 1-sigma confidence regions for pole direction in (lambda, beta)
- Compute period uncertainty from chi-squared landscape parabolic fit
- Per-vertex shape variance map across bootstrap runs

**Inputs:**
- Photometric data with uncertainties
- Best-fit model parameters (as starting point for bootstrap runs)
- Number of bootstrap iterations

**Outputs:**
- Pole uncertainty ellipse (sigma_lambda, sigma_beta, correlation)
- Period uncertainty (sigma_P in hours)
- Vertex position variance array (N_vertices,)

**Dependencies:** Module 2 (Convex Solver) or Module 3 (Genetic Solver), Module 1 (Forward Model)

---

## Module 12: C++ Acceleration Extension (`cpp_ext/`)

**Responsibility:** Provide optimized C++ implementations of computationally intensive inner loops to achieve >= 10x speedup over pure Python.

**Key capabilities:**
- Forward brightness integral: vectorized facet visibility/illumination check and brightness summation over all facets for all epochs
- Chi-squared gradient computation: analytical Jacobian of brightness w.r.t. shape parameters
- Exposed to Python via `pybind11` or `ctypes`

**Inputs/Outputs:** Same interface as corresponding Python functions (drop-in replacement)

**Dependencies:** None (compiled extension, called by Module 1 and Module 2)

---

## Inter-Module Dependency Graph

```
                    ┌─────────────────┐
                    │  Pipeline (M9)  │
                    └──────┬──────────┘
           ┌───────────────┼────────────────┐
           ▼               ▼                ▼
    ┌──────────┐   ┌──────────────┐  ┌─────────────┐
    │Data Ing. │   │Target Select.│  │ Uncertainty │
    │  (M6)    │   │   (M10)      │  │   (M11)     │
    └────┬─────┘   └──────────────┘  └──────┬──────┘
         │                                   │
         ▼                                   ▼
    ┌──────────┐                     ┌──────────────┐
    │ Sparse   │                     │Convex Solver │
    │Handler(4)│                     │    (M2)      │
    └────┬─────┘                     └──────┬───────┘
         │                                  │
         ▼                                  ▼
    ┌──────────┐                     ┌──────────────┐
    │ Geometry │                     │Genetic Solver│
    │  (M8)    │                     │    (M3)      │
    └──────────┘                     └──────┬───────┘
                                            │
                                            ▼
                                     ┌──────────────┐
                                     │Forward Model │
                                     │    (M1)      │
                                     └──────┬───────┘
                                            │
                                            ▼
                                     ┌──────────────┐
                                     │  C++ Ext.    │
                                     │   (M12)      │
                                     └──────────────┘

    Standalone utilities:
    ┌──────────────┐   ┌──────────────┐
    │Period Search │   │Mesh Compare  │
    │    (M7)      │   │    (M5)      │
    └──────────────┘   └──────────────┘
```

---

## Data Flow Summary

1. **Ingestion**: M6 fetches photometric data and ground-truth shapes from ALCDEF, DAMIT, PDS, MPC
2. **Preprocessing**: M4 calibrates sparse data; M8 computes viewing geometry for all epochs
3. **Period Search**: M7 identifies candidate rotation periods
4. **Convex Inversion**: M2 performs pole grid search + shape optimization at each candidate period
5. **Non-Convex Refinement**: M3 takes the convex solution as seed and evolves non-convex features
6. **Uncertainty**: M11 runs bootstrap resampling over M2/M3
7. **Validation**: M5 compares recovered shapes against ground truth
8. **Target Selection**: M10 queries databases to identify new targets
9. **Orchestration**: M9 chains all steps and manages I/O

---

## File Layout

```
repo/
├── architecture.md          # This document
├── sources.bib              # BibTeX bibliography
├── forward_model.py         # Module 1
├── convex_solver.py         # Module 2
├── genetic_solver.py        # Module 3
├── sparse_handler.py        # Module 4
├── mesh_comparator.py       # Module 5
├── data_ingestion.py        # Module 6
├── period_search.py         # Module 7
├── geometry.py              # Module 8
├── pipeline.py              # Module 9
├── target_selector.py       # Module 10
├── uncertainty.py           # Module 11
├── cpp_ext/                 # Module 12 (C++ acceleration)
│   ├── brightness.cpp
│   └── CMakeLists.txt
├── tests/                   # Unit and integration tests
├── results/                 # Experimental output
│   ├── ground_truth/
│   ├── observations/
│   ├── blind_tests/
│   └── models/
├── figures/                 # Publication-quality figures
├── requirements.txt
└── run_validation.sh
```
