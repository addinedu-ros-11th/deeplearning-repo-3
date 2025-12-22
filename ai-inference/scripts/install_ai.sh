#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/ai-inference"
cd "${APP_DIR}"

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

echo "Installed. Optional: pip install -r requirements-gpu.txt"
