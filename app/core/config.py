"""OpenClaw Empire — Centralized Configuration"""
import os
import logging
from typing import Optional, List
from pydantic_settings import BaseSettings

logger = logging.getLogger("openclaw.config")


class Settings(BaseSettings):
    """All environment variables with validation."""

    # AI Providers
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None

    # Discord
    discord_token: Optional[str] = None
    discord_guild_id: Optional[int] = None

    # Telegram
    telegram_bot1_token: Optional[str] = None
    telegram_bot2_token: Optional[str] = None
    telegram_bot3_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None

    # Slack
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    slack_channel: str = "ops"

    # GitHub
    github_token: Optional[str] = None
    github_repo: Optional[str] = None

    # Google / YouTube
    google_api_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    youtube_channel_id: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./data/empire.db"

    # System
    health_port: int = 8080
    log_level: str = "INFO"
    environment: str = "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def validate(self) -> dict:
        """Check which integrations are configured."""
        results = {
            "ai_providers": [],
            "platforms": [],
            "integrations": [],
            "missing": []
        }

        # AI Providers
        if self.groq_api_key:
            results["ai_providers"].append("groq")
        else:
            results["missing"].append("GROQ_API_KEY")

        if self.openai_api_key:
            results["ai_providers"].append("openai")
        if self.anthropic_api_key:
            results["ai_providers"].append("anthropic")
        if self.xai_api_key:
            results["ai_providers"].append("xai")

        # Platforms
        if self.discord_token:
            results["platforms"].append("discord")
        else:
            results["missing"].append("DISCORD_TOKEN")

        if self.telegram_bot1_token:
            results["platforms"].append("telegram")
        else:
            results["missing"].append("TELEGRAM_BOT1_TOKEN")

        if self.slack_bot_token and self.slack_app_token:
            results["platforms"].append("slack")
        else:
            if not self.slack_bot_token:
                results["missing"].append("SLACK_BOT_TOKEN")
            if not self.slack_app_token:
                results["missing"].append("SLACK_APP_TOKEN")

        # Integrations
        if self.github_token:
            results["integrations"].append("github")
        if self.google_api_key:
            results["integrations"].append("google")

        return results


# Global settings instance
settings = Settings()
