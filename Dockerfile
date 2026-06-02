# Base image for OpenClaw
FROM python:3.10-slim

# Install system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy sources
COPY . /app

# Install python deps
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    if [ -f requirements_v2.txt ]; then pip install --no-cache-dir -r requirements_v2.txt; fi

ENV PYTHONUNBUFFERED=1

# Default command is bash; docker-compose will override with the specific gateway command
CMD ["/bin/bash"]
