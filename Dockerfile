FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc curl wget gnupg \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 libx11-6 \
    libx11-xcb1 libxcb1 libxext6 \
    fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY start.sh .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium --with-deps || true

COPY . .

RUN mkdir -p memory bots logs /tmp/openclaw_screenshots

ENV PYTHONUNBUFFERED=1
ENV BROWSER_HEADLESS=true
ENV SCREENSHOT_DIR=/tmp/openclaw_screenshots
ENV PYTHONPATH=/app
ENV HEALTH_PORT=8080

CMD ["bash", "start.sh"]
