"""
OpenClaw Master Brain Configuration
One config. All platforms. All LLMs.
FIXED: Added TELEGRAM_BOT3_TOKEN validation, type annotation, Redis fallback, MEMORY_DB path.
"""
import os
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class Config:
    """Master brain configuration — all tokens, all platforms."""

    # ─── TELEGRAM (3 bots) ─────────────────────────────────────────────
    TELEGRAM_BOT1_TOKEN: str = os.environ.get("TELEGRAM_BOT1_TOKEN", "")
    TELEGRAM_BOT2_TOKEN: str = os.environ.get("TELEGRAM_BOT2_TOKEN", "")
    TELEGRAM_BOT3_TOKEN: str = os.environ.get("TELEGRAM_BOT3_TOKEN", "")
    TELEGRAM_ALLOWED_USERS: List[int] = []
    if users := os.environ.get("TELEGRAM_ALLOWED_USERS", ""):
        try:
            TELEGRAM_ALLOWED_USERS = [int(u.strip()) for u in users.split(",") if u.strip()]
        except ValueError:
            logger.warning("Invalid TELEGRAM_ALLOWED_USERS format")

    # ─── DISCORD ─────────────────────────────────────────────────────────
    DISCORD_TOKEN: str = os.environ.get("DISCORD_TOKEN", "")
    DISCORD_GUILD_ID: Optional[int] = None
    if gid := os.environ.get("DISCORD_GUILD_ID"):
        try:
            DISCORD_GUILD_ID = int(gid)
        except ValueError:
            logger.warning("Invalid DISCORD_GUILD_ID")

    # ─── SLACK ───────────────────────────────────────────────────────────
    SLACK_BOT_TOKEN: str = os.environ.get("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN: str = os.environ.get("SLACK_APP_TOKEN", "")
    SLACK_CHANNEL: str = os.environ.get("SLACK_CHANNEL", "openclaw-ops")

    # ─── LLM PROVIDERS ───────────────────────────────────────────────────
    # OpenAI (primary)
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o")

    # Groq (fast inference)
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama3-70b-8192")

    # Primary LLM selection
    PRIMARY_LLM: str = os.environ.get("PRIMARY_LLM", "openai")  # "openai" or "groq"

    # ─── GITHUB ──────────────────────────────────────────────────────────
    GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.environ.get("GITHUB_REPO", "d74117157-create/openclaw-bot")

    # ─── MEMORY ──────────────────────────────────────────────────────────
    MEMORY_DB: str = os.environ.get("MEMORY_DB", "/app/data/openclaw_memory.db")
    REDIS_URL: str = os.environ.get("REDIS_URL", "")

    # ─── WEB API ─────────────────────────────────────────────────────────
    WEB_PORT: int = int(os.environ.get("WEB_PORT", "8080"))
    OPENCLAW_API_KEY: str = os.environ.get("OPENCLAW_API_KEY", "")

    # ─── SECURITY ────────────────────────────────────────────────────────
    OWNER_ID: str = os.environ.get("OWNER_ID", "")
    MASTER_BRAIN_MODE: bool = os.environ.get("MASTER_BRAIN_MODE", "true").lower() == "true"

    # ─── SYSTEM ────────────────────────────────────────────────────────
    PYTHONUNBUFFERED: str = os.environ.get("PYTHONUNBUFFERED", "1")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    @classmethod
    def get_llm_config(cls) -> dict:
        """Return active LLM config."""
        if cls.PRIMARY_LLM == "openai" and cls.OPENAI_API_KEY:
            return {
                "provider": "openai",
                "api_key": cls.OPENAI_API_KEY,
                "model": cls.OPENAI_MODEL,
                "base_url": "https://api.openai.com/v1",
            }
        elif cls.GROQ_API_KEY:
            return {
                "provider": "groq",
                "api_key": cls.GROQ_API_KEY,
                "model": cls.GROQ_MODEL,
                "base_url": "https://api.groq.com/openai/v1",
            }
        else:
            raise ValueError("No LLM API key configured. Set OPENAI_API_KEY or GROQ_API_KEY.")

    @classmethod
    def log_config(cls) -> None:
        """Log non-sensitive configuration."""
        logger.info("=" * 50)
        logger.info("🧠 OPENCLAW MASTER BRAIN CONFIG")
        logger.info("=" * 50)
        logger.info(f"Telegram Bot 1: {'✅' if cls.TELEGRAM_BOT1_TOKEN else '❌'}")
        logger.info(f"Telegram Bot 2: {'✅' if cls.TELEGRAM_BOT2_TOKEN else '❌'}")
        logger.info(f"Telegram Bot 3: {'✅' if cls.TELEGRAM_BOT3_TOKEN else '❌'}")
        logger.info(f"Discord: {'✅' if cls.DISCORD_TOKEN else '❌'}")
        logger.info(f"Slack: {'✅' if cls.SLACK_BOT_TOKEN else '❌'}")
        logger.info(f"OpenAI: {'✅' if cls.OPENAI_API_KEY else '❌'} ({cls.OPENAI_MODEL})")
        logger.info(f"Groq: {'✅' if cls.GROQ_API_KEY else '❌'} ({cls.GROQ_MODEL})")
        logger.info(f"GitHub: {'✅' if cls.GITHUB_TOKEN else '❌'}")
        logger.info(f"Primary LLM: {cls.PRIMARY_LLM}")
        logger.info(f"Master Brain Mode: {'✅ ON' if cls.MASTER_BRAIN_MODE else '❌ OFF'}")
        logger.info("=" * 50)

    @classmethod
    def validate(cls) -> dict:
        """Validate required configuration."""
        errors = {}
        # FIXED: Check all 3 Telegram tokens + Discord + Slack
        if not any([
            cls.TELEGRAM_BOT1_TOKEN,
            cls.TELEGRAM_BOT2_TOKEN,
            cls.TELEGRAM_BOT3_TOKEN,
            cls.DISCORD_TOKEN,
            cls.SLACK_BOT_TOKEN
        ]):
            errors["platforms"] = "At least one platform token required (Discord, Telegram, or Slack)"
        if not cls.OPENAI_API_KEY and not cls.GROQ_API_KEY:
            errors["llm"] = "At least one LLM API key required (OPENAI_API_KEY or GROQ_API_KEY)"
        return errors
