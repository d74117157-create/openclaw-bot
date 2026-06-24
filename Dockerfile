# OpenClaw Bot — Discord Gateway + AI Worker
# Render Background Worker deployment

FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends     gcc     && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Start the bot (gateway + worker in one process for simple deploy)
# For scaling, split into separate services:
#   - Gateway: python main.py
#   - Worker: python worker/ai_worker.py
CMD ["python", "main.py"]
