#!/usr/bin/env bash
# One-liner installer for concurrency-gate
set -euo pipefail

echo "==> Installing concurrency-gate in editable mode..."
python3 -m pip install --upgrade pip
python3 -m pip install -e .

echo "==> Verifying installation of concurrency-gate..."
concurrency-gate --help >/dev/null

echo "==> Installation complete! Run 'concurrency-gate --help' to get started."
