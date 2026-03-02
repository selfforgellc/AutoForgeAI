#!/usr/bin/env bash
set -euo pipefail

# AutoForge backend - one-command dev run
# Creates a local venv, installs deps, and runs uvicorn.

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
