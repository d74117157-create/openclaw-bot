#!/usr/bin/env python3
"""
Google OAuth 2.0 Setup for YouTube Upload & Analytics
Run this locally to get your YOUTUBE_REFRESH_TOKEN.
"""
import os
import json
from urllib.parse import urlencode

# Step 1: Create OAuth credentials at https://console.cloud.google.com/apis/credentials
# Step 2: Enable YouTube Data API v3 and YouTube Analytics API v2
# Step 3: Add redirect URI: http://localhost:8080/oauth/callback
# Step 4: Run this script

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8080/oauth/callback"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": " ".join(SCOPES),
    "access_type": "offline",
    "prompt": "consent",
}

print("=== Google OAuth Setup for YouTube ===")
print(f"1. Go to: {auth_url}?{urlencode(params)}")
print("2. Authorize your YouTube channel (@realhistory-lessons)")
print("3. Copy the 'code' from the redirect URL")
print("4. Exchange it for a refresh token using:")
print("""
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTH_CODE_FROM_STEP_3" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=http://localhost:8080/oauth/callback"
""")
print("5. Add the 'refresh_token' to Render as YOUTUBE_REFRESH_TOKEN")
print("
=== Required Scopes for Monetization ===")
for s in SCOPES:
    print(f"  • {s}")
