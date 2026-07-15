#!/bin/bash
set -e

echo "=========================================="
echo "OpenClaw Empire — Setup"
echo "=========================================="

# Install dependencies
echo "[1/4] Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env from example if not exists
if [ ! -f .env ]; then
    echo "[2/4] Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your API keys"
fi

# Create data directory
mkdir -p data

# Run validation
echo "[3/4] Running validation..."
python -m compileall . -q
python -c "from app.core.config import settings; print('Config loaded')"
python -c "from app.database.models import init_database; init_database(); print('Database initialized')"

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: python app/main.py"
echo "  3. Test: curl http://localhost:8080/health"
echo ""
echo "Or start Claude Code:"
echo "  claude"
