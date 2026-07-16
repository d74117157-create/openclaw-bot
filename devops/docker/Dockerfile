# OpenClaw Superswarm - Production Docker Image
FROM python:3.11-slim

# Security: Run as non-root
RUN groupadd -r openclaw && useradd -r -g openclaw openclaw

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R openclaw:openclaw /app
USER openclaw

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose FastAPI health server port
EXPOSE 8000

# Start command
CMD ["./start.sh"]
