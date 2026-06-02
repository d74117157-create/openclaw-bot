# Render deployment and environment setup for OpenClaw

This document explains how to configure a Render Web Service to run the OpenClaw Slack and Discord bots.

1) Create a Render Web Service
- Connect your GitHub repository to Render and create a new Web Service.
- Select the `main` branch.
- Build command: leave empty or set to `pip install -r requirements_v2.txt` if you provide a requirements file.
- Start command: `gunicorn -w 1 -b 0.0.0.0:$PORT gateway.health_server:app` (optional) or use the Procfile which runs the health server.

2) Environment variables (set these in Render > Environment)
- SLACK_BOT_TOKEN (secret)
- SLACK_APP_TOKEN (secret)
- SLACK_CHANNEL
- DISCORD_TOKEN (if running Discord bot)
- OLLAMA_BASE_URL / OLLAMA_MODEL or ANTHROPIC_API_KEY / GROQ_API_KEY
- MEMORY_DB (path to sqlite inside the container if used)

3) GitHub Actions
- This repo contains a GitHub Actions workflow `.github/workflows/deploy-to-render.yml` which triggers a Render deploy on push to `main` or manual dispatch. The workflow requires two GitHub repository secrets:
  - RENDER_API_KEY (Render API key)
  - RENDER_SERVICE_ID (Render service ID)

4) Security note
- Never commit tokens or API keys to the repository. Use Render environment variables or GitHub repository secrets.
- If you previously pasted tokens in public channels, rotate them immediately.

5) Health checks
- The repo includes `gateway/health_server.py` which listens on $PORT and returns a JSON payload at `/health`.
- Render will use the health endpoint to determine service health.
