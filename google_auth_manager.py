"""
Google OAuth Manager
Handles token refresh for YouTube Data API, YouTube Analytics API, 
Google Drive API, and any other Google APIs.
"""
import os
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")
GOOGLE_ACCESS_TOKEN = os.getenv("GOOGLE_ACCESS_TOKEN", "")

TOKEN_FILE = "/tmp/google_tokens.json"

class GoogleAuthManager:
    """Manages Google OAuth 2.0 tokens with automatic refresh."""

    TOKEN_URL = "https://oauth2.googleapis.com/token"

    SCOPES = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
        "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.refresh_token = GOOGLE_REFRESH_TOKEN
        self.access_token = GOOGLE_ACCESS_TOKEN
        self.token_expiry = None
        self._load_tokens()

    def _load_tokens(self):
        """Load cached tokens from file."""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token", self.access_token)
                    self.refresh_token = data.get("refresh_token", self.refresh_token)
                    expiry_str = data.get("token_expiry")
                    if expiry_str:
                        self.token_expiry = datetime.fromisoformat(expiry_str)
            except Exception as e:
                print(f"[GOOGLE_AUTH] Token load error: {e}")

    def _save_tokens(self):
        """Save tokens to file."""
        try:
            data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "token_expiry": self.token_expiry.isoformat() if self.token_expiry else None
            }
            with open(TOKEN_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[GOOGLE_AUTH] Token save error: {e}")

    def is_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary."""
        if not self.is_configured():
            print("[GOOGLE_AUTH] OAuth not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN")
            return None

        # Check if token needs refresh (expires in < 5 minutes or unknown)
        needs_refresh = (
            not self.access_token or
            not self.token_expiry or
            self.token_expiry < datetime.utcnow() + timedelta(minutes=5)
        )

        if needs_refresh:
            self._refresh_access_token()

        return self.access_token

    def _refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        try:
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            }

            response = requests.post(self.TOKEN_URL, data=payload, timeout=10)
            data = response.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                self._save_tokens()
                print(f"[GOOGLE_AUTH] Token refreshed. Expires in {expires_in}s")
            else:
                error = data.get("error", "unknown")
                error_desc = data.get("error_description", "")
                print(f"[GOOGLE_AUTH] Refresh failed: {error} — {error_desc}")
                if error == "invalid_grant":
                    print("[GOOGLE_AUTH] ⚠️ Refresh token expired or revoked. You need to re-authorize.")
                    print("[GOOGLE_AUTH] Go to: https://developers.google.com/oauthplayground")
                    print("[GOOGLE_AUTH] Step 1: Select YouTube APIs scopes")
                    print("[GOOGLE_AUTH] Step 2: Exchange authorization code for tokens")
                    print("[GOOGLE_AUTH] Step 3: Copy new refresh_token to Render env vars")

        except Exception as e:
            print(f"[GOOGLE_AUTH] Refresh error: {e}")

    def get_auth_header(self) -> Dict[str, str]:
        """Get Authorization header for API requests."""
        token = self.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def make_authenticated_request(self, url: str, method: str = "GET", 
                                  params: Dict = None, data: Dict = None,
                                  headers: Dict = None) -> Dict:
        """Make an authenticated request to any Google API."""
        auth_header = self.get_auth_header()
        if not auth_header:
            return {"error": "Not authenticated"}

        req_headers = headers or {}
        req_headers.update(auth_header)

        try:
            if method.upper() == "GET":
                r = requests.get(url, headers=req_headers, params=params, timeout=15)
            elif method.upper() == "POST":
                r = requests.post(url, headers=req_headers, params=params, json=data, timeout=15)
            elif method.upper() == "PUT":
                r = requests.put(url, headers=req_headers, params=params, json=data, timeout=15)
            elif method.upper() == "DELETE":
                r = requests.delete(url, headers=req_headers, params=params, timeout=15)
            else:
                return {"error": f"Unsupported method: {method}"}

            return r.json() if r.content else {"status_code": r.status_code}

        except Exception as e:
            return {"error": str(e)}

    def get_scopes(self) -> str:
        """Return space-separated scopes string."""
        return " ".join(self.SCOPES)

# Singleton instance
_google_auth_instance = None

def get_google_auth() -> GoogleAuthManager:
    global _google_auth_instance
    if _google_auth_instance is None:
        _google_auth_instance = GoogleAuthManager()
    return _google_auth_instance
