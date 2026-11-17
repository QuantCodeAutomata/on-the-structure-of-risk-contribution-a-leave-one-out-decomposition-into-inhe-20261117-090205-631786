#!/usr/bin/env bash
# Runs the test suite and both experiments, overwriting the files in results/.
set -uo pipefail

cd "$(dirname "$0")"

echo "=== Unit tests (no network access) ==="
python -m pytest -m "not market_data" -q || exit 1

echo "=== Experiment 2: convergence simulation (synthetic data) ==="
python -m exp.exp_2 || exit 1

if [[ -n "${DATALOADER_API_KEY:-}" && -n "${MASSIVE_API_KEY:-}" ]]; then
  echo "=== Market-data tests ==="
  python -m pytest -m market_data -q || exit 1
  echo "=== Experiment 1: multi-asset ICD application ==="
  python -m exp.exp_1 || exit 1
else
  echo "DATALOADER_API_KEY / MASSIVE_API_KEY not set: skipping Experiment 1 and market-data tests."
fi

echo "Done. See results/ for tables, figures and RESULTS.md."
