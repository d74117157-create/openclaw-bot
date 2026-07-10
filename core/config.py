"""Configuration loaded from environment."""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DISCORD_TOKEN: Optional[str] = None
    TELEGRAM_BOT1_TOKEN: Optional[str] = None
    TELEGRAM_BOT2_TOKEN: Optional[str] = None
    TELEGRAM_BOT3_TOKEN: Optional[str] = None
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_APP_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql://user:pass@localhost/openclaw"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    ENVIRONMENT: str = "production"
    SWARM_MODE: str = "auto-reconnect"
    MAX_AGENTS: int = 12
    AGENT_HEARTBEAT_INTERVAL: int = 30
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
