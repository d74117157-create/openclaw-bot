"""OpenClaw Superswarm — Centralized configuration with validation."""
import os
import logging
from typing import Optional

logger = logging.getLogger("openclaw.config")


class Config:
    """All environment variables in one place."""

    # Discord
    DISCORD_TOKEN: str = os.environ.get("DISCORD_TOKEN", "")
    DISCORD_GUILD_ID: Optional[int] = None
    _guild = os.environ.get("DISCORD_GUILD_ID", "")
    if _guild:
        try:
            DISCORD_GUILD_ID = int(_guild)
        except ValueError:
            logger.warning("Invalid DISCORD_GUILD_ID")

    # Telegram (3 bots)
    TELEGRAM_BOT1_TOKEN: str = os.environ.get("TELEGRAM_BOT1_TOKEN", "")
    TELEGRAM_BOT2_TOKEN: str = os.environ.get("TELEGRAM_BOT2_TOKEN", "")
    TELEGRAM_BOT3_TOKEN: str = os.environ.get("TELEGRAM_BOT3_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.environ.get("TELEGRAM_WEBHOOK_URL", "")

    # Slack
    SLACK_BOT_TOKEN: str = os.environ.get("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN: str = os.environ.get("SLACK_APP_TOKEN", "")
    SLACK_CHANNEL: str = os.environ.get("SLACK_CHANNEL", "ops")

    # LLM
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama3-70b-8192")

    # GitHub
    GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.environ.get("GITHUB_REPO", "")

    # Infra
    MEMORY_DB: str = os.environ.get("MEMORY_DB", "openclaw_memory.db")
    BROWSER_HEADLESS: bool = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"
    SCREENSHOT_DIR: str = os.environ.get("SCREENSHOT_DIR", "/tmp/openclaw_screenshots")
    HEALTH_PORT: int = int(os.environ.get("HEALTH_PORT", "8080"))
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    RENDER_DEPLOY_HOOK: str = os.environ.get("RENDER_DEPLOY_HOOK", "")

    @classmethod
    def validate(cls) -> dict[str, list[str]]:
        errors: dict[str, list[str]] = {}
        if not cls.DISCORD_TOKEN and not cls.SLACK_BOT_TOKEN and not any(
            [cls.TELEGRAM_BOT1_TOKEN, cls.TELEGRAM_BOT2_TOKEN, cls.TELEGRAM_BOT3_TOKEN]
        ):
            errors["platform"] = ["No platform token configured (DISCORD_TOKEN, SLACK_BOT_TOKEN, or TELEGRAM_*_TOKEN)"]
        if not cls.GROQ_API_KEY:
            errors["llm"] = ["GROQ_API_KEY not set"]
        return errors

    @classmethod
    def log_status(cls) -> None:
        logger.info("=== OpenClaw Config ===")
        logger.info(f"Discord: {'OK' if cls.DISCORD_TOKEN else 'MISSING'}")
        logger.info(f"Telegram Bots: {sum(bool(t) for t in [cls.TELEGRAM_BOT1_TOKEN, cls.TELEGRAM_BOT2_TOKEN, cls.TELEGRAM_BOT3_TOKEN])}/3")
        logger.info(f"Slack: {'OK' if cls.SLACK_BOT_TOKEN else 'MISSING'}")
        logger.info(f"Groq: {'OK' if cls.GROQ_API_KEY else 'MISSING'}")
        logger.info(f"GitHub: {'OK' if cls.GITHUB_TOKEN else 'MISSING'}")
        logger.info(f"Health Port: {cls.HEALTH_PORT}")
        logger.info("=" * 30)
