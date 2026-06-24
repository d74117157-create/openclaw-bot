# OpenClaw Bot — Render Background Worker
# Discord-only bot (no HTTP traffic)

FROM python:3.11-slim

WORKDIR /app

# Install system deps for discord.py and other packages
RUN apt-get update && apt-get install -y --no-install-recommends     gcc     libffi-dev     && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Start the bot
CMD ["bash", "start.sh"]
