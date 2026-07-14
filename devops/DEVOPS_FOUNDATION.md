# DEVOPS FOUNDATION
## OpenClaw Digital Empire v4.3
### Infrastructure & Operations

---

## 1. DOCKER STRATEGY

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data /data/backups

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /data
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "main.py"]
```

---

## 2. CI/CD PIPELINE

### GitHub Actions
```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      - run: pytest tests/ -v --tb=short
      - run: |
          pip install flake8
          flake8 . --count --select=E9,F63,F7,F82

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            https://api.render.com/v1/services/${{ secrets.RENDER_SERVICE_ID }}/deploys
```

---

## 3. TESTING PIPELINE

### Test Structure
```
tests/
├── test_empire_state.py
├── test_revenue_tracker.py
├── test_task_engine.py
├── test_security_guardian.py
└── conftest.py
```

---

## 4. MONITORING

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Bot uptime | Health check | < 95% in 24h |
| API response time | FastAPI | > 2s average |
| Error rate | Logs | > 5% in 1h |
| Revenue | Revenue tracker | < 50% of target |
| Task queue depth | Task engine | > 100 pending |

---

## 5. ERROR TRACKING

### Sentry Integration
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

---

## 6. DATABASE BACKUP PLAN

### Automated Backups (every 6 hours)
```bash
#!/bin/bash
BACKUP_DIR="/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar czf "$BACKUP_DIR/empire-$TIMESTAMP.tar.gz" /data/*.json /data/*.db
ls -t $BACKUP_DIR/empire-*.tar.gz | tail -n +21 | xargs rm -f
```

---

## 7. DEPLOYMENT CHECKLIST

- [ ] All secrets in environment variables
- [ ] No secrets in code
- [ ] JWT secret strong and persistent
- [ ] API rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] HTTPS only
- [ ] Regular dependency updates
- [ ] Secret rotation policy

---

*DevOps Version: 1.0*
*Last Updated: 2026-07-14*
