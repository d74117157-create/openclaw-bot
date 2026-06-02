#!/usr/bin/env python3
"""Simple environment validation script to fail fast with clear messages.
Do NOT include secrets in logs. This script prints which env vars are missing and
how to set them using gh secret set or the Render dashboard.
"""
import os
import sys

required = [
    'SLACK_BOT_TOKEN',
    'SLACK_APP_TOKEN',
    'SLACK_CHANNEL',
]

missing = [v for v in required if not os.environ.get(v)]

# LLM or Discord may be optional depending on your deployment; warn if none set
llm_vars = ['OLLAMA_BASE_URL', 'ANTHROPIC_API_KEY', 'GROQ_API_KEY']
llm_present = any(os.environ.get(v) for v in llm_vars)

discord_present = bool(os.environ.get('DISCORD_TOKEN'))

if missing:
    print('\nERROR: Required environment variables are missing:')
    for v in missing:
        print(f"  - {v}")
    print('\nAction: Add them as GitHub repository secrets (preferred) or Render environment variables.')
    print('\nExample commands (do NOT paste secrets into chat):')
    print('  gh secret set SLACK_BOT_TOKEN --body "<your_xoxb_token>" --repo d74117157-create/openclaw-bot')
    print('  gh secret set SLACK_APP_TOKEN --body "<your_xapp_token>" --repo d74117157-create/openclaw-bot')
    print('  gh secret set SLACK_CHANNEL --body "<channel-name-or-id>" --repo d74117157-create/openclaw-bot')
    print('\nOr set them in the Render dashboard for your service under Environment.')
    sys.exit(2)

# Warn if neither an LLM nor Discord token is present — service may be limited
if not llm_present and not discord_present:
    print('\nWARNING: No LLM keys (OLLAMA_BASE_URL/ANTHROPIC_API_KEY/GROQ_API_KEY) and no DISCORD_TOKEN found.')
    print('The bots may start but will be unable to make LLM requests or run Discord features.')

# Ensure PORT is present for Render
if not os.environ.get('PORT'):
    print('\nWARNING: PORT environment variable is not set; Render will provide PORT at runtime.')

print('\nEnvironment check passed — required vars are present.')
sys.exit(0)
