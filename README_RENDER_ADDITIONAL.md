Added environment validation and runtime safeguards:
- scripts/env_check.py validates required environment variables and prints actionable gh commands.
- requirements_v2.txt lists core runtime dependencies.
- start.sh now runs env_check.py and fails fast with clear log messages if required vars are missing.

These changes help Render logs show the real cause (missing/invalid tokens) quickly so you can rotate or re-add secrets.
