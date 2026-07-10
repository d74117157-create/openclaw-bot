"""Configuration with validation."""

import os
from typing import Optional


class Config:
    """OpenClaw configuration."""

    def __init__(self) -> None:
        self.discord_token = os.environ.get("DISCORD_TOKEN")
        self.brain_channel = os.environ.get("BRAIN_CHANNEL", "brain")
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.groq_model = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.slack_app_token = os.environ.get("SLACK_APP_TOKEN")
        self.slack_channel = os.environ.get("SLACK_CHANNEL", "ops")
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_repo = os.environ.get("GITHUB_REPO")
        self.memory_db = os.environ.get("MEMORY_DB", "openclaw_memory.db")
        self.browser_headless = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"
        self.screenshot_dir = os.environ.get("SCREENSHOT_DIR", "/tmp/openclaw_screenshots")
        self.health_port = int(os.environ.get("HEALTH_PORT", "8080"))

    def validate(self) -> list[str]:
        """Return list of missing required configs."""
        missing = []
        if not self.discord_token and not self.slack_bot_token:
            missing.append("No platform token configured (DISCORD_TOKEN or SLACK_BOT_TOKEN)")
        if not self.groq_api_key:
            missing.append("GROQ_API_KEY")
        return missing
