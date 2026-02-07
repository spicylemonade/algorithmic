#!/usr/bin/env bash
# run_validation.sh
# Executes the full validation suite for the Light Curve Inversion pipeline.
#
# Usage:
#   chmod +x run_validation.sh
#   ./run_validation.sh
#
# Prerequisites:
#   pip install -r requirements.txt
#   cd cpp_ext && g++ -O3 -shared -fPIC -o libbrightness.so brightness.cpp && cd ..
#
set -e

PYTHON="${PYTHON:-python3}"

echo "============================================================"
echo "LCI Pipeline — Full Validation Suite"
echo "============================================================"

# Step 1: Run unit tests
echo ""
echo "[Step 1/6] Running unit tests..."
$PYTHON -m pytest tests/ -v --tb=short

# Step 2: Assemble benchmark suite
echo ""
echo "[Step 2/6] Assembling benchmark suite (5 targets)..."
$PYTHON setup_benchmark.py

# Step 3: Run blind inversion on all validation targets
echo ""
echo "[Step 3/6] Running blind inversion tests..."
$PYTHON run_blind_inversion.py

# Step 4: Compute validation metrics
echo ""
echo "[Step 4/6] Computing validation metrics..."
$PYTHON compute_validation_metrics.py

# Step 5: Generate candidate list
echo ""
echo "[Step 5/6] Generating top-50 candidate list..."
$PYTHON target_selector.py

# Step 6: Run sparse stress tests
echo ""
echo "[Step 6/6] Running sparse stress tests..."
$PYTHON run_sparse_stress_test.py

echo ""
echo "============================================================"
echo "Validation suite complete."
echo "Results:"
echo "  - Validation metrics: results/validation_metrics.csv"
echo "  - Candidate list:     results/candidates_top50.csv"
echo "  - Sparse stress test: results/sparse_stress_test.csv"
echo "  - Blind test outputs: results/blind_tests/"
echo "============================================================"
