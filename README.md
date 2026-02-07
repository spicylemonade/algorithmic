# Light Curve Inversion Pipeline

A custom asteroid light curve inversion (LCI) pipeline for reconstructing 3D shape models and spin states from disk-integrated photometric observations. The pipeline combines convex inversion, evolutionary optimization, and sparse photometry handling into a unified framework, with the goal of surpassing the accuracy of existing tools such as MPO LCInvert, SAGE, and KOALA on well-characterized validation targets.

---

## Table of Contents

- [Project Overview and Research Objectives](#project-overview-and-research-objectives)
- [Methodology and References](#methodology-and-references)
- [Installation Instructions](#installation-instructions)
- [Module Architecture](#module-architecture)
- [Usage Examples](#usage-examples)
- [Reproducing Validation Results](#reproducing-validation-results)
- [Project Structure](#project-structure)
- [License](#license)

---

## Project Overview and Research Objectives

Asteroids observed from the ground are almost always unresolved point sources. Their time-varying brightness, or light curve, encodes information about rotation period, spin axis orientation, overall shape elongation, and surface scattering properties. When observations from multiple apparitions at different viewing geometries are combined, the inverse problem becomes sufficiently constrained to recover a three-dimensional shape model.

This pipeline implements a full end-to-end workflow for that inverse problem:

1. **Data ingestion** from standard community formats (ALCDEF dense lightcurves, DAMIT shape models, and sparse survey photometry from Gaia DR3, ZTF, and Pan-STARRS).
2. **Convex inversion** following the Kaasalainen-Torppa method to recover pole direction, sidereal period, and a convex shape approximation through Levenberg-Marquardt optimization over a period/pole grid search.
3. **Non-convex refinement** via a SAGE-style genetic algorithm that evolves vertex-based mesh representations to capture concavities, bifurcated contact-binary shapes, and large-scale surface irregularities that convex models cannot represent.
4. **Hybrid pipeline** that automatically chains the convex and evolutionary stages, using the convex solution as a seed for the genetic solver when residual chi-squared exceeds a configurable threshold.
5. **Sparse photometry integration** that calibrates and folds sparse survey data into the inversion objective function, enabling shape recovery even when dense time-series lightcurves are limited.
6. **Quantitative validation** against ground truth models using Hausdorff distance, volumetric Intersection over Union (IoU), Chamfer distance, pole angular error, and period error.
7. **Uncertainty quantification** through bootstrap resampling and chi-squared landscape analysis to provide confidence intervals on recovered spin vectors and shape parameters.

The primary research objective is to demonstrate that this integrated pipeline can match or surpass the shape recovery accuracy of the three leading tools in the field: MPO LCInvert (convex-only), SAGE (genetic non-convex), and KOALA (multi-data fusion), when evaluated on a blind validation benchmark of at least five well-characterized asteroids (Eros, Itokawa, Kleopatra, Gaspra, and Betulia).

---

## Methodology and References

The mathematical and algorithmic foundations of this pipeline draw on several key publications in asteroid photometry and shape modeling:

- **Kaasalainen & Torppa (2001)**, *Icarus*, 153, 24-36 -- Introduced the convex inversion framework using Gaussian surface-area density parameterized by spherical harmonics, with Levenberg-Marquardt optimization. This paper established that convex shapes can be uniquely recovered from multi-apparition lightcurves when sufficient viewing geometry diversity is available.

- **Kaasalainen, Torppa & Muinonen (2001)**, *Icarus*, 153, 37-51 -- Extended the method to simultaneously solve for pole direction, sidereal period, and shape via hierarchical grid search. Introduced the combined Lambert + Lommel-Seeliger empirical scattering law that remains the standard for photometric inversion.

- **Bartczak & Dudzinski (2018)**, *MNRAS*, 473, 5050-5065 -- Developed the SAGE (Shaping Asteroids with Genetic Evolution) algorithm, a population-based genetic algorithm for recovering non-convex shapes from disk-integrated photometry using vertex-based mesh representations with mutation, crossover, and tournament selection operators.

- **Durech et al. (2009)**, *A&A*, 493, 291-297 -- Demonstrated that sparse photometric data from all-sky surveys (tens to hundreds of individual brightness measurements spread over years) can constrain asteroid shape models when combined with dense lightcurves.

- **Durech et al. (2010)**, *A&A*, 513, A46 -- Established the DAMIT (Database of Asteroid Models from Inversion Techniques) as the community standard repository for asteroid shape models and spin solutions, providing the ground truth data used in our validation benchmark.

- **Viikinkoski et al. (2015)** -- Multi-data fusion framework (ADAM) combining lightcurves, adaptive optics, radar, and occultation data, which inspired the hybrid architecture of this pipeline.

- **Muinonen et al. (2010)**, *Icarus*, 209, 542-555 -- Introduced the H,G1,G2 three-parameter phase curve model used in our sparse data calibration.

The forward scattering model computes disk-integrated brightness by summing contributions from all visible and illuminated triangular facets of a mesh, applying the combined Lambert + Lommel-Seeliger scattering law controlled by a single mixing parameter `c_L`. The complete mathematical formulation is documented in `formulation.md`.

---

## Installation Instructions

### Prerequisites

- **Python 3.10** or newer
- **g++** with C++11 support (for the C++ extension module)
- **Git** (to clone the repository)

### Clone and Install

```bash
git clone <repository-url>
cd repo
```

### Python Dependencies

Install the required Python packages:

```bash
pip install numpy scipy requests
```

The pipeline depends on the following packages:

| Package    | Minimum Version | Purpose                                      |
|------------|-----------------|----------------------------------------------|
| `numpy`    | 1.23+           | Array operations, linear algebra              |
| `scipy`    | 1.9+            | Optimization (L-BFGS-B), spatial KD-trees     |
| `requests` | 2.28+           | HTTP downloads from DAMIT/ALCDEF (optional)   |

No additional frameworks (TensorFlow, PyTorch, etc.) are required. The pipeline is deliberately kept lightweight with minimal dependencies.

### Compile the C++ Extension

The forward brightness integral has a C++ implementation that provides significant speedup over the pure-Python version. Compile it as follows:

```bash
cd cpp_ext
g++ -O3 -shared -fPIC -o libbrightness.so brightness.cpp
cd ..
```

This produces `cpp_ext/libbrightness.so`, which is loaded automatically via `ctypes` at runtime. If the shared library is not found, the pipeline falls back to the pure-Python implementation in `forward_model.py`.

### Verify Installation

Run the test suite to confirm everything is working:

```bash
python -m pytest tests/ -v
```

---

## Module Architecture

The pipeline is organized into 12 modules, each with a well-defined responsibility.

### Core Inversion Modules

1. **`forward_model.py`** -- Forward Scattering Model and Synthetic Lightcurve Generator. Computes disk-integrated brightness of a faceted 3D shape model using combined Lambert + Lommel-Seeliger scattering. Loads `.obj` meshes, computes per-facet visibility and illumination, and generates full synthetic lightcurves over sequences of Julian Date epochs.

2. **`convex_solver.py`** -- Convex Inversion Solver (Kaasalainen-Torppa Method). Determines the best-fit convex shape, pole direction, and sidereal period by minimizing chi-squared residuals. Implements facet-area parameterization, Levenberg-Marquardt optimization, period scanning over configurable ranges, pole direction grid search, and regularization (smoothness penalty, non-negativity constraints).

3. **`genetic_solver.py`** -- Evolutionary / Genetic Algorithm Solver for Non-Convex Shapes. A population-based optimizer inspired by SAGE where individuals are triangulated meshes with vertex-based representation. Implements mutation (Gaussian perturbation with adaptive sigma decay), BLX-alpha crossover, tournament selection, elitism, and a lightcurve chi-squared fitness function with smoothness regularization.

4. **`sparse_handler.py`** -- Sparse Photometric Data Handler. Parses, calibrates, and integrates sparse photometric data from surveys (Gaia DR3, ZTF, Pan-STARRS) into the inversion objective function. Applies the H,G1,G2 phase curve model for absolute magnitude calibration, converts magnitudes to linear flux, and supports sparse-only inversion when dense lightcurves are unavailable.

5. **`hybrid_pipeline.py`** -- Hybrid Convex-to-Nonconvex Pipeline. Combines the convex inversion solver with the evolutionary solver in a two-stage pipeline. Stage 1 runs convex inversion to recover pole, period, and convex shape. If the residual chi-squared exceeds a configurable threshold, Stage 2 seeds the evolutionary solver with the convex solution and refines toward a non-convex shape.

### Geometry and Data Handling

6. **`geometry.py`** -- Viewing Geometry Calculator. Computes Sun-asteroid-observer geometry at arbitrary epochs from Keplerian orbital elements. Provides Kepler equation solver, ecliptic-to-body-frame coordinate transformations, phase angle and aspect angle calculation, and approximate Earth/asteroid orbital positions.

7. **`data_ingestion.py`** -- Data Ingestion Layer. Downloads, parses, and standardizes photometric data from ALCDEF and DAMIT. Retrieves ground truth shape models for validation targets, generates synthetic lightcurves for testing, and exports standardized data containers.

8. **`target_selector.py`** -- Asteroid Candidate Selector. Generates a prioritized list of 50+ asteroid candidates suitable for shape modeling based on selection criteria including NEO status, diameter, LCDB quality code, DAMIT coverage, and available photometric data volume. Outputs a scored and ranked CSV file.

### Analysis and Validation

9. **`mesh_comparator.py`** -- Mesh Comparator. Quantitatively compares two 3D shape models using Hausdorff distance (normalized by bounding-box diagonal), volumetric Intersection over Union (IoU), and Chamfer distance. Uses uniform surface sampling via barycentric coordinates and KD-tree nearest-neighbor queries.

10. **`uncertainty.py`** -- Uncertainty Quantification Module. Estimates uncertainties for spin vectors and shape models via bootstrap resampling of lightcurve data and chi-squared landscape analysis. Produces per-vertex position variance maps, pole direction confidence regions, and period uncertainty intervals.

### Performance and Extensions

11. **`cpp_ext/`** -- C++ Extensions. Contains `brightness.cpp`, a high-performance C++ implementation of the forward brightness integral loaded via `ctypes`. Provides a drop-in replacement for the Python `generate_lightcurve_direct` function with identical output but significantly reduced computation time.

### Supporting Scripts

12. **Supporting pipeline scripts**:
    - **`main.py`** -- Top-level entry point for running the full pipeline.
    - **`setup_benchmark.py`** -- Assembles the ground truth validation benchmark suite for five or more asteroids (Eros, Itokawa, Kleopatra, Gaspra, Betulia), generating synthetic dense lightcurves and sparse observations from known shape models and orbital parameters.
    - **`run_blind_inversion.py`** -- Runs the full hybrid pipeline on each validation target using only synthetic observation data with no access to ground truth shapes.
    - **`compute_validation_metrics.py`** -- Computes error metrics (Hausdorff distance, IoU, Chamfer distance, pole error, period error) between blind inversion results and ground truth, outputting a summary CSV.
    - **`run_candidate_inversion.py`** -- Runs the hybrid pipeline on the top 10 candidates from the target selection output, producing recovered shape models and spin solutions.
    - **`run_sparse_stress_test.py`** -- Stress tests sparse-only inversion at decreasing data levels (200, 100, 50, 25 points) to characterize degradation behavior.

---

## Usage Examples

### Running the Full Pipeline End-to-End

The standard workflow proceeds in three stages: benchmark setup, blind inversion, and validation.

```bash
# 1. Assemble the ground truth benchmark (generates synthetic observations)
python setup_benchmark.py

# 2. Run blind inversions on all validation targets
python run_blind_inversion.py

# 3. Compute validation metrics against ground truth
python compute_validation_metrics.py
```

Results are written to the `results/` directory:
- `results/ground_truth/` -- Ground truth meshes and spin parameters
- `results/observations/` -- Synthetic dense and sparse observation files
- `results/blind_tests/` -- Recovered shapes, spin solutions, and convergence logs
- `results/validation_metrics.csv` -- Summary error metrics table

### Running on New Targets

To run inversion on real or new asteroid targets:

```python
import numpy as np
from convex_solver import LightcurveData, run_convex_inversion
from hybrid_pipeline import HybridConfig, run_hybrid_pipeline

# Prepare your lightcurve data
lc = LightcurveData(
    jd=np.array([...]),           # Julian Dates
    brightness=np.array([...]),   # relative brightness (linear flux)
    weights=np.array([...]),      # 1/sigma^2 weights
    sun_ecl=np.array([...]),      # (N, 3) Sun directions in ecliptic frame
    obs_ecl=np.array([...]),      # (N, 3) Observer directions in ecliptic frame
)

# Configure the hybrid pipeline
config = HybridConfig(
    n_periods=200,         # number of trial periods in the grid search
    n_lambda=12,           # pole longitude grid points
    n_beta=6,              # pole latitude grid points
    n_subdivisions=3,      # icosahedron subdivisions (1280 faces at n=3)
    chi2_threshold=0.05,   # threshold to trigger non-convex refinement
    ga_generations=300,    # generations for the evolutionary stage
    verbose=True,
)

# Run the full hybrid pipeline
result = run_hybrid_pipeline(
    lightcurves=[lc],
    period_range=(5.0, 15.0),  # search range in hours
    config=config,
)

# Access results
print(f"Pole: lambda={result.spin.lambda_deg:.1f}, beta={result.spin.beta_deg:.1f}")
print(f"Period: {result.spin.period_hours:.6f} hours")
print(f"Chi-squared: {result.chi_squared:.4f}")

# Save recovered shape
from forward_model import save_obj
save_obj(result.mesh, "recovered_shape.obj")
```

### Running the Candidate Selection Pipeline

To generate a prioritized list of asteroid candidates and run inversions on the top selections:

```bash
# Generate the top-50 candidate list
python target_selector.py

# Run inversions on the top 10 candidates
python run_candidate_inversion.py
```

### Running the Sparse Stress Test

To evaluate how inversion quality degrades with decreasing sparse data volume:

```bash
python run_sparse_stress_test.py
```

This outputs `results/sparse_stress_test.csv` with pole error, period error, and convergence status at data levels of 200, 100, 50, and 25 sparse photometric points.

### Running the Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific module's tests
python -m pytest tests/test_forward_model.py -v
python -m pytest tests/test_convex_solver.py -v
python -m pytest tests/test_hybrid_pipeline.py -v
```

---

## Reproducing Validation Results

The validation benchmark is designed to be fully reproducible with a fixed random seed (42). Follow these three steps in order:

### Step 1: Assemble the Benchmark

```bash
python setup_benchmark.py
```

This script:
- Retrieves or generates ground truth shape models for five validation targets (Eros, Itokawa, Kleopatra, Gaspra, Betulia)
- Generates synthetic dense lightcurves (5 per target, 60 points each) with 2% Gaussian noise using the forward model and known orbital parameters
- Generates synthetic sparse observations (200 per target) with realistic magnitude uncertainties
- Writes all data to `results/ground_truth/` and `results/observations/`
- Produces `results/benchmark_manifest.json` describing all generated files

### Step 2: Run Blind Inversions

```bash
python run_blind_inversion.py
```

This script:
- Loads the benchmark manifest and observation data for each target
- Runs the full hybrid pipeline (convex inversion + optional GA refinement) with no access to ground truth shapes
- Searches a period range of +/-10% around a literature hint value
- Exports recovered shape meshes, spin solutions, and convergence histories to `results/blind_tests/<target_name>/`

### Step 3: Compute Validation Metrics

```bash
python compute_validation_metrics.py
```

This script:
- Loads ground truth and recovered meshes for each target
- Computes normalized Hausdorff distance, volumetric IoU, Chamfer distance, pole angular error (degrees), and sidereal period error (hours)
- Writes the full results table to `results/validation_metrics.csv`
- Prints a summary table to stdout

The target accuracy thresholds for the pipeline are:
- Mean Hausdorff distance < 0.15 (normalized by bounding-box diagonal)
- Mean pole angular error < 15 degrees
- Mean period error < 0.001 hours

---

## Project Structure

```
repo/
├── README.md                      # This file
├── main.py                        # Top-level pipeline entry point
├── forward_model.py               # Forward scattering model (Module 1)
├── convex_solver.py               # Convex inversion solver (Module 2)
├── genetic_solver.py              # Genetic algorithm solver (Module 3)
├── sparse_handler.py              # Sparse data handler (Module 4)
├── mesh_comparator.py             # Mesh comparison metrics (Module 5)
├── data_ingestion.py              # Data ingestion layer (Module 6)
├── geometry.py                    # Viewing geometry calculator (Module 8)
├── hybrid_pipeline.py             # Hybrid pipeline (Module 9)
├── target_selector.py             # Candidate selector (Module 10)
├── uncertainty.py                 # Uncertainty quantification (Module 11)
├── cpp_ext/                       # C++ extensions (Module 12)
│   ├── __init__.py                # Python wrapper (ctypes)
│   ├── brightness.cpp             # C++ forward brightness integral
│   └── libbrightness.so           # Compiled shared library
├── setup_benchmark.py             # Benchmark assembly script
├── run_blind_inversion.py         # Blind inversion test runner
├── compute_validation_metrics.py  # Validation metric computation
├── run_candidate_inversion.py     # Candidate inversion pipeline
├── run_sparse_stress_test.py      # Sparse data stress test
├── tests/                         # Unit and integration tests
│   ├── test_forward_model.py
│   ├── test_convex_solver.py
│   ├── test_genetic_solver.py
│   ├── test_hybrid_pipeline.py
│   ├── test_sparse_handler.py
│   ├── test_mesh_comparator.py
│   ├── test_data_ingestion.py
│   ├── test_uncertainty.py
│   ├── test_cpp_ext.py
│   └── test_sparse_only.py
├── results/                       # Output directory
│   ├── ground_truth/              # Ground truth meshes and spin files
│   ├── observations/              # Synthetic observation data
│   ├── blind_tests/               # Blind inversion outputs
│   ├── models/                    # Candidate inversion outputs
│   ├── benchmark_manifest.json    # Benchmark metadata
│   ├── candidates_top50.csv       # Target selection output
│   └── validation_metrics.csv     # Validation error metrics
├── figures/                       # Generated plots and figures
├── architecture.md                # Detailed module architecture document
├── formulation.md                 # Mathematical formulation of the forward model
├── literature_review.md           # Comprehensive literature review
├── data_sources.md                # Data source documentation
├── sources.bib                    # BibTeX references
└── research_rubric.json           # Research evaluation rubric
```

---

## License

This project is developed for research purposes. Please cite the relevant papers listed in the [Methodology and References](#methodology-and-references) section if you use this pipeline or its results in published work.
