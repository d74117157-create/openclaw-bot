"""
Security Guardian Configuration
All secrets are loaded from environment variables — NEVER hardcoded.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GuardianConfig:
    """Central configuration for Security Guardian."""

    # Alert Channels (at least one required)
    slack_webhook_url: Optional[str] = field(default_factory=lambda: os.getenv("GUARDIAN_SLACK_WEBHOOK"))
    slack_bot_token: Optional[str] = field(default_factory=lambda: os.getenv("SLACK_BOT_TOKEN"))
    slack_channel: str = field(default_factory=lambda: os.getenv("GUARDIAN_SLACK_CHANNEL", "#security-alerts"))

    discord_webhook_url: Optional[str] = field(default_factory=lambda: os.getenv("GUARDIAN_DISCORD_WEBHOOK"))
    discord_channel_id: Optional[str] = field(default_factory=lambda: os.getenv("DISCORD_CHANNEL_ID"))

    telegram_bot_token: Optional[str] = field(default_factory=lambda: os.getenv("TELEGRAM_BOT1_TOKEN"))
    telegram_chat_id: Optional[str] = field(default_factory=lambda: os.getenv("GUARDIAN_TELEGRAM_CHAT_ID"))

    # GitHub
    github_token: Optional[str] = field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    github_repo: str = field(default_factory=lambda: os.getenv("GITHUB_REPO", "d74117157-create/openclaw-bot"))

    # Monitoring Intervals (seconds)
    account_check_interval: int = 300      # 5 min
    oauth_check_interval: int = 3600       # 1 hour
    secret_scan_interval: int = 3600     # 1 hour
    dependency_check_interval: int = 86400 # 24 hours
    deployment_check_interval: int = 60    # 1 min

    # Thresholds
    max_failed_logins: int = 5
    max_secret_exposure_score: int = 7
    critical_cvss_threshold: float = 7.0

    # Persistence
    state_file: str = ".guardian_state.json"
    log_file: str = "logs/guardian.log"
    report_dir: str = "security/reports"

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        if not any([self.slack_webhook_url, self.discord_webhook_url, self.telegram_bot_token]):
            issues.append("WARNING: No alert channels configured. Guardian will log locally only.")
        if not self.github_token:
            issues.append("WARNING: No GitHub token configured. Repository scanning disabled.")
        return issues
