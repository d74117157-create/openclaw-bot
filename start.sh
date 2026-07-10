#!/bin/bash
set -e
echo "🐝 OpenClaw Superswarm starting..."
mkdir -p logs data
if [ ! -d ".venv" ]; then python -m venv .venv; fi
source .venv/bin/activate
pip install -q -r requirements.txt
exec python main.py
