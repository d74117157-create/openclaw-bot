#!/usr/bin/env python3
"""
Twitter/X OAuth 2.0 Setup for Bot Posting
Get keys from https://developer.twitter.com/en/portal/dashboard
"""
import os

print("=== Twitter/X OAuth Setup ===")
print("""
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a new app → "OpenClaw Swarm"
3. Set permissions: Read + Write + Direct Message
4. Generate Access Token & Secret (must be for the bot account)
5. Add these to Render:

   TWITTER_API_KEY=your_consumer_key
   TWITTER_API_SECRET=your_consumer_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_token_secret
   TWITTER_BEARER_TOKEN=your_bearer_token

6. Test with: python -c "from setup.oauth_twitter import test_post; test_post()"
""")

def test_post():
    import requests
    import os

    bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
    if not bearer:
        print("❌ TWITTER_BEARER_TOKEN not set")
        return

    # Test read access
    headers = {"Authorization": f"Bearer {bearer}"}
    r = requests.get("https://api.twitter.com/2/users/me", headers=headers)
    if r.status_code == 200:
        print(f"✅ Twitter API connected: @{r.json().get('data', {}).get('username')}")
    else:
        print(f"❌ Twitter API error: {r.status_code} - {r.text}")
