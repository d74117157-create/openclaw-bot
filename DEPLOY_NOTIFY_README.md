## Deployment Notifications & Secret Rotation

### GitHub Secrets Required

Add these in **Settings → Secrets and variables → Actions → Secrets**:

| Secret | Description | How to get it |
|--------|-------------|---------------|
| `SLACK_WEBHOOK` | Slack incoming webhook URL | Slack app → Incoming Webhooks |
| `DISCORD_WEBHOOK` | Discord channel webhook URL | Channel Settings → Integrations → Webhooks |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token | @BotFather → `/newbot` or existing bot |
| `TELEGRAM_CHAT_ID` | Target chat ID (channel or group) | Send a message, then `https://api.telegram.org/bot<TOKEN>/getUpdates` |

> **Optional:** For production, move these to an **Environment** (e.g., `production`) under `Settings → Environments`.

### Rotation Checklist (every 30–90 days)

1. Generate the new credential in Slack / Discord / Telegram.
2. Update the GitHub secret with the new value. Do not change the secret name.
3. Test manually: **Actions → Deploy and Notify → Run workflow**.
4. Verify the notification arrives in all channels.
5. Revoke the old credential only after the new one is confirmed working.

### Manual Test Run

- **Actions → Deploy and Notify → Run workflow → Run workflow**
- Triggers full pipeline without pushing code — perfect for verifying new secrets.

### Notes

- The workflow does **not** change application code or deployment logic.
- Notification steps are isolated; if one service fails, the others still run.
- Secrets are never printed to logs.
- The `notify` job runs `if: always()` so you get alerts even when deploy fails.
