"""
OpenClaw Configuration Manager
Safely loads environment variables with defaults and type checking.
"""
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration with safe defaults."""

    # Discord
    DISCORD_TOKEN: str = os.environ.get("DISCORD_TOKEN", "")
    DISCORD_GUILD_ID: Optional[int] = None
    if guild_id := os.environ.get("DISCORD_GUILD_ID"):
        try:
            DISCORD_GUILD_ID = int(guild_id)
        except ValueError:
            logger.warning("Invalid DISCORD_GUILD_ID, using None")

    # Slack
    SLACK_BOT_TOKEN: str = os.environ.get("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN: str = os.environ.get("SLACK_APP_TOKEN", "")
    SLACK_CHANNEL: str = os.environ.get("SLACK_CHANNEL", "ops")

    # LLM
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4-turbo")

    # GitHub
    GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.environ.get("GITHUB_REPO", "")

    # Database
    MEMORY_DB: str = os.environ.get("MEMORY_DB", "openclaw_memory.db")
    MEMORY_PATH: str = os.environ.get("MEMORY_PATH", "./memory")

    # Paths
    SCREENSHOT_DIR: str = os.environ.get("SCREENSHOT_DIR", "/tmp/openclaw_screenshots")
    LOGS_DIR: str = os.environ.get("LOGS_DIR", "./logs")

    # Browser
    BROWSER_HEADLESS: bool = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"

    # Debug
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> dict[str, list[str]]:
        """Validate required configuration. Returns dict of missing/invalid keys."""
        errors: dict[str, list[str]] = {}

        # Discord
        if not cls.DISCORD_TOKEN:
            if "discord" not in errors:
                errors["discord"] = []
            errors["discord"].append("DISCORD_TOKEN not set")

        # Slack
        if not cls.SLACK_BOT_TOKEN:
            if "slack" not in errors:
                errors["slack"] = []
            errors["slack"].append("SLACK_BOT_TOKEN not set")
        if not cls.SLACK_APP_TOKEN:
            if "slack" not in errors:
                errors["slack"] = []
            errors["slack"].append("SLACK_APP_TOKEN not set")

        # LLM
        if not cls.GROQ_API_KEY and not cls.OPENAI_API_KEY:
            if "llm" not in errors:
                errors["llm"] = []
            errors["llm"].append("Neither GROQ_API_KEY nor OPENAI_API_KEY set")

        return errors

    @classmethod
    def log_config(cls) -> None:
        """Log non-sensitive configuration."""
        logger.info("=== OpenClaw Configuration ===")
        logger.info(f"Discord Token: {'✓' if cls.DISCORD_TOKEN else '✗'}")
        logger.info(f"Slack Bot Token: {'✓' if cls.SLACK_BOT_TOKEN else '✗'}")
        logger.info(f"Slack App Token: {'✓' if cls.SLACK_APP_TOKEN else '✗'}")
        logger.info(f"Groq API Key: {'✓' if cls.GROQ_API_KEY else '✗'}")
        logger.info(f"OpenAI API Key: {'✓' if cls.OPENAI_API_KEY else '✗'}")
        logger.info(f"GitHub Token: {'✓' if cls.GITHUB_TOKEN else '✗'}")
        logger.info(f"LLM Model: {cls.GROQ_MODEL if cls.GROQ_API_KEY else cls.OPENAI_MODEL}")
        logger.info(f"Slack Channel: {cls.SLACK_CHANNEL}")
        logger.info(f"Debug Mode: {cls.DEBUG}")
        logger.info(f"Log Level: {cls.LOG_LEVEL}")
        logger.info("=" * 40)
