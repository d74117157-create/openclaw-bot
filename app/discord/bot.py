"""OpenClaw Empire — Discord Bot (stub for production)"""
import os
import logging

logger = logging.getLogger("openclaw.discord")

class DiscordBot:
    """Discord bot wrapper — initialized on demand."""

    def __init__(self):
        self.token = os.environ.get("DISCORD_TOKEN")
        self.enabled = bool(self.token)
        if self.enabled:
            logger.info("[Discord] Bot configured")
        else:
            logger.warning("[Discord] No token set — Discord disabled")

    def is_enabled(self) -> bool:
        return self.enabled

    async def send_message(self, channel_id: str, text: str) -> bool:
        """Send message to Discord channel."""
        if not self.enabled:
            return False
        logger.info(f"[Discord] Would send to {channel_id}: {text[:50]}...")
        return True
