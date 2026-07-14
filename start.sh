#!/bin/bash
# KingLulu Empire Boot Script
# Boots the entire money machine

echo "🦅 KINGLULU EMPIRE BOOTING..."

# Ensure PORT is set for Render
export PORT="${PORT:-3000}"
export PYTHONPATH="${PYTHONPATH}:."

# Run the empire
exec python3 main.py
