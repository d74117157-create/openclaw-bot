"""
Google OAuth 2.0 Server — Auto-Auth + Token Exchange + Render Callback
Handles the full OAuth flow for your OpenClaw Empire.
No command line needed. Just visit the URL, authorize, tokens auto-save.
"""
import os
import json
import base64
import requests
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# ─── CONFIG ──────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://openclaw-bot.onrender.com/google/callback")

# All Google scopes for your empire
GOOGLE_SCOPES = [
    # YouTube
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtubepartner",
    "https://www.googleapis.com/auth/youtubepartner-channel-audit",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
    # Drive
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/drive.appdata",
    "https://www.googleapis.com/auth/drive.photos.readonly",
    "https://www.googleapis.com/auth/drive.scripts",
    "https://www.googleapis.com/auth/drive.activity",
    "https://www.googleapis.com/auth/drive.activity.readonly",
    "https://www.googleapis.com/auth/drive.labels",
    "https://www.googleapis.com/auth/drive.labels.readonly",
    # Gmail
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.insert",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.metadata",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
    # Calendar
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.events.owned",
    "https://www.googleapis.com/auth/calendar.events.owned.readonly",
    "https://www.googleapis.com/auth/calendar.events.public.readonly",
    "https://www.googleapis.com/auth/calendar.events.freebusy",
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/calendar.settings.readonly",
    "https://www.googleapis.com/auth/calendar.calendarlist",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "https://www.googleapis.com/auth/calendar.calendars",
    "https://www.googleapis.com/auth/calendar.calendars.readonly",
    "https://www.googleapis.com/auth/calendar.acls",
    "https://www.googleapis.com/auth/calendar.acls.readonly",
    "https://www.googleapis.com/auth/calendar.app.created",
    # Docs/Sheets/Slides
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/presentations.readonly",
    # Analytics
    "https://www.googleapis.com/auth/analytics",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.manage.users",
    "https://www.googleapis.com/auth/analytics.manage.users.readonly",
    "https://www.googleapis.com/auth/analytics.provision",
    "https://www.googleapis.com/auth/analytics.user.deletion",
    "https://www.googleapis.com/auth/marketingplatformadmin.analytics.read",
    "https://www.googleapis.com/auth/marketingplatformadmin.analytics.update",
    # Ads
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/adsense",
    "https://www.googleapis.com/auth/adsense.readonly",
    "https://www.googleapis.com/auth/admob.readonly",
    "https://www.googleapis.com/auth/admob.report",
    "https://www.googleapis.com/auth/display-video",
    "https://www.googleapis.com/auth/display-video-mediaplanning",
    "https://www.googleapis.com/auth/doubleclickbidmanager",
    "https://www.googleapis.com/auth/doubleclicksearch",
    "https://www.googleapis.com/auth/dfareporting",
    "https://www.googleapis.com/auth/dfatrafficking",
    "https://www.googleapis.com/auth/authorized-buyers-marketplace",
    "https://www.googleapis.com/auth/realtime-bidding",
    "https://www.googleapis.com/auth/adexchange.buyer",
    # Cloud
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloud-platform.read-only",
    "https://www.googleapis.com/auth/devstorage.full_control",
    "https://www.googleapis.com/auth/devstorage.read_only",
    "https://www.googleapis.com/auth/devstorage.read_write",
    "https://www.googleapis.com/auth/compute",
    "https://www.googleapis.com/auth/compute.readonly",
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/bigquery.insertdata",
    "https://www.googleapis.com/auth/cloud-vision",
    "https://www.googleapis.com/auth/cloud-translation",
    "https://www.googleapis.com/auth/cloud-language",
    "https://www.googleapis.com/auth/cloudkms",
    "https://www.googleapis.com/auth/cloudruntimeconfig",
    "https://www.googleapis.com/auth/appengine.admin",
    "https://www.googleapis.com/auth/firebase",
    "https://www.googleapis.com/auth/firebase.readonly",
    "https://www.googleapis.com/auth/firebase.messaging",
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/sqlservice.admin",
    "https://www.googleapis.com/auth/spanner.admin",
    "https://www.googleapis.com/auth/spanner.data",
    "https://www.googleapis.com/auth/cloud-billing",
    "https://www.googleapis.com/auth/cloud-billing.readonly",
    "https://www.googleapis.com/auth/cloud-healthcare",
    "https://www.googleapis.com/auth/service.management",
    "https://www.googleapis.com/auth/service.management.readonly",
    "https://www.googleapis.com/auth/servicecontrol",
    # Search / Webmasters
    "https://www.googleapis.com/auth/webmasters",
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/indexing",
    # Photos
    "https://www.googleapis.com/auth/photoslibrary",
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata",
    "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata",
    "https://www.googleapis.com/auth/photoslibrary.sharing",
    # Tasks / Keep / Contacts
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/keep",
    "https://www.googleapis.com/auth/keep.readonly",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/contacts.other.readonly",
    # User Info
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/user.addresses.read",
    "https://www.googleapis.com/auth/user.birthday.read",
    "https://www.googleapis.com/auth/user.emails.read",
    "https://www.googleapis.com/auth/user.gender.read",
    "https://www.googleapis.com/auth/user.organization.read",
    "https://www.googleapis.com/auth/user.phonenumbers.read",
    # Forms / Blogger / Books
    "https://www.googleapis.com/auth/forms",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.body.readonly",
    "https://www.googleapis.com/auth/forms.currentonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/blogger",
    "https://www.googleapis.com/auth/blogger.readonly",
    "https://www.googleapis.com/auth/books",
    # Meet / Chat / Classroom
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/meetings.space.readonly",
    "https://www.googleapis.com/auth/meetings.space.settings",
    "https://www.googleapis.com/auth/chat.spaces",
    "https://www.googleapis.com/auth/chat.spaces.readonly",
    "https://www.googleapis.com/auth/chat.messages",
    "https://www.googleapis.com/auth/chat.messages.readonly",
    "https://www.googleapis.com/auth/chat.memberships",
    "https://www.googleapis.com/auth/chat.memberships.readonly",
    "https://www.googleapis.com/auth/classroom.courses",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.rosters",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    # Play / Android
    "https://www.googleapis.com/auth/androidpublisher",
    "https://www.googleapis.com/auth/androidmanagement",
    "https://www.googleapis.com/auth/androidenterprise",
    "https://www.googleapis.com/auth/playdeveloperreporting",
    # Street View
    "https://www.googleapis.com/auth/streetviewpublish",
    # Data Portability (YouTube)
    "https://www.googleapis.com/auth/dataportability.youtube.channel",
    "https://www.googleapis.com/auth/dataportability.youtube.comments",
    "https://www.googleapis.com/auth/dataportability.youtube.clips",
    "https://www.googleapis.com/auth/dataportability.youtube.live_chat",
    "https://www.googleapis.com/auth/dataportability.youtube.music",
    "https://www.googleapis.com/auth/dataportability.youtube.playable",
    "https://www.googleapis.com/auth/dataportability.youtube.posts",
    "https://www.googleapis.com/auth/dataportability.youtube.private_playlists",
    "https://www.googleapis.com/auth/dataportability.youtube.private_videos",
    "https://www.googleapis.com/auth/dataportability.youtube.public_playlists",
    "https://www.googleapis.com/auth/dataportability.youtube.public_videos",
    "https://www.googleapis.com/auth/dataportability.youtube.shopping",
    "https://www.googleapis.com/auth/dataportability.youtube.subscriptions",
    "https://www.googleapis.com/auth/dataportability.youtube.unlisted_playlists",
    "https://www.googleapis.com/auth/dataportability.youtube.unlisted_videos",
]

TOKEN_FILE = "/tmp/google_tokens.json"

# ─── STATE ───────────────────────────────────────────────────────
_oauth_states = {}  # state -> {created_at, pkce_verifier}

# ─── HELPERS ─────────────────────────────────────────────────────
def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge."""
    verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode("utf-8").rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode("utf-8").rstrip("=")
    return verifier, challenge

def _save_tokens(access_token: str, refresh_token: str, expires_in: int):
    """Save tokens to local file AND Render env (if available)."""
    expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expiry": expiry.isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    # Save to file
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[OAUTH] Tokens saved to {TOKEN_FILE}")
    except Exception as e:
        print(f"[OAUTH] File save error: {e}")

    # Also update in-memory for immediate use
    os.environ["GOOGLE_ACCESS_TOKEN"] = access_token
    os.environ["GOOGLE_REFRESH_TOKEN"] = refresh_token

    return data

def get_auth_url() -> str:
    """Generate the Google OAuth authorization URL."""
    if not GOOGLE_CLIENT_ID:
        return "[ERROR] GOOGLE_CLIENT_ID not set"

    verifier, challenge = _generate_pkce()
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "created_at": datetime.utcnow().isoformat(),
        "verifier": verifier,
    }

    scopes = " ".join(GOOGLE_SCOPES)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return url

def exchange_code(code: str, state: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens."""
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        return {"error": "Invalid or expired state parameter"}

    verifier = state_data.get("verifier", "")

    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": verifier,
    }

    try:
        r = requests.post("https://oauth2.googleapis.com/token", data=payload, timeout=15)
        data = r.json()

        if "access_token" in data:
            access_token = data["access_token"]
            refresh_token = data.get("refresh_token", "")
            expires_in = data.get("expires_in", 3600)

            saved = _save_tokens(access_token, refresh_token, expires_in)
            return {
                "status": "success",
                "access_token": access_token[:20] + "...",
                "refresh_token": refresh_token[:20] + "..." if refresh_token else "N/A",
                "expires_in": expires_in,
                "saved_to": TOKEN_FILE,
                "message": "Tokens saved. GOOGLE_ACCESS_TOKEN and GOOGLE_REFRESH_TOKEN updated in environment.",
            }
        else:
            return {
                "error": data.get("error", "unknown"),
                "error_description": data.get("error_description", ""),
            }
    except Exception as e:
        return {"error": str(e)}

def refresh_access_token(refresh_token: str = None) -> Dict[str, Any]:
    """Refresh the access token using the refresh token."""
    rt = refresh_token or os.getenv("GOOGLE_REFRESH_TOKEN", "")
    if not rt:
        return {"error": "No refresh token available"}

    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": rt,
        "grant_type": "refresh_token",
    }

    try:
        r = requests.post("https://oauth2.googleapis.com/token", data=payload, timeout=15)
        data = r.json()

        if "access_token" in data:
            access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            saved = _save_tokens(access_token, rt, expires_in)
            return {
                "status": "success",
                "access_token": access_token[:20] + "...",
                "expires_in": expires_in,
                "message": "Access token refreshed.",
            }
        else:
            return {
                "error": data.get("error", "unknown"),
                "error_description": data.get("error_description", ""),
            }
    except Exception as e:
        return {"error": str(e)}

def get_valid_access_token() -> Optional[str]:
    """Get a valid access token, refreshing if needed."""
    # Check file first
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
            expiry = datetime.fromisoformat(data.get("token_expiry", "2000-01-01"))
            if datetime.utcnow() < expiry - timedelta(minutes=5):
                return data.get("access_token")
            # Token expired or about to expire
            rt = data.get("refresh_token", "")
            if rt:
                result = refresh_access_token(rt)
                if result.get("status") == "success":
                    return os.getenv("GOOGLE_ACCESS_TOKEN")
        except Exception as e:
            print(f"[OAUTH] Token read error: {e}")

    # Fallback to env
    return os.getenv("GOOGLE_ACCESS_TOKEN", None)

def get_auth_header() -> Dict[str, str]:
    """Get Authorization header for Google API requests."""
    token = get_valid_access_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def make_authenticated_request(url: str, method: str = "GET",
                                params: Dict = None, data: Dict = None,
                                headers: Dict = None) -> Dict:
    """Make an authenticated request to any Google API."""
    auth_header = get_auth_header()
    if not auth_header:
        return {"error": "No valid access token"}

    req_headers = headers or {}
    req_headers.update(auth_header)
    req_headers.setdefault("Content-Type", "application/json")

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

# ─── FASTAPI ROUTES (for Render integration) ───────────────────
# These will be mounted in the main FastAPI app

def register_oauth_routes(app):
    """Register OAuth routes on the FastAPI app."""
    from fastapi import Request
    from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse

    @app.get("/google/auth")
    def google_auth():
        """Start OAuth flow — redirects user to Google consent screen."""
        url = get_auth_url()
        if url.startswith("[ERROR]"):
            return JSONResponse({"error": url}, status_code=500)
        return RedirectResponse(url=url)

    @app.get("/google/callback")
    def google_callback(code: str = None, state: str = None, error: str = None):
        """Handle OAuth callback from Google."""
        if error:
            return JSONResponse({"error": error}, status_code=400)
        if not code or not state:
            return JSONResponse({"error": "Missing code or state"}, status_code=400)

        result = exchange_code(code, state)

        if result.get("status") == "success":
            html = f"""
            <html>
            <head><title>OAuth Success</title></head>
            <body style="font-family:monospace; background:#0a0a0a; color:#00ff88; padding:40px;">
            <h1>✅ GOOGLE OAUTH CONNECTED</h1>
            <p>Your empire now has full Google API access.</p>
            <pre>{json.dumps(result, indent=2)}</pre>
            <p><b>Next:</b> Tokens are saved. The bot will auto-refresh.</p>
            <p><a href="/empire/status" style="color:#00ff88;">Check Empire Status →</a></p>
            </body></html>
            """
            return HTMLResponse(content=html)
        else:
            return JSONResponse(result, status_code=400)

    @app.get("/google/status")
    def google_status():
        """Check Google OAuth status."""
        token = get_valid_access_token()
        return {
            "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
            "has_access_token": bool(token),
            "scopes_count": len(GOOGLE_SCOPES),
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "auth_url": "/google/auth" if GOOGLE_CLIENT_ID else None,
        }

    @app.post("/google/refresh")
    def google_refresh():
        """Manually trigger token refresh."""
        result = refresh_access_token()
        return result

    @app.get("/google/scopes")
    def google_scopes():
        """List all configured scopes."""
        return {"count": len(GOOGLE_SCOPES), "scopes": GOOGLE_SCOPES}

    print("[OAUTH] Google OAuth routes registered: /google/auth, /google/callback, /google/status, /google/refresh, /google/scopes")

# ─── BACKWARD COMPATIBILITY ──────────────────────────────────────
# Keep the old GoogleAuthManager interface working
class GoogleAuthManager:
    """Backward-compatible wrapper around the new OAuth server."""

    SCOPES = GOOGLE_SCOPES
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN", "")
        self.access_token = os.getenv("GOOGLE_ACCESS_TOKEN", "")
        self.token_expiry = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_access_token(self) -> Optional[str]:
        return get_valid_access_token()

    def get_auth_header(self) -> Dict[str, str]:
        return get_auth_header()

    def make_authenticated_request(self, url: str, method: str = "GET",
                                  params: Dict = None, data: Dict = None,
                                  headers: Dict = None) -> Dict:
        return make_authenticated_request(url, method, params, data, headers)

    def get_scopes(self) -> str:
        return " ".join(self.SCOPES)

# Singleton
_google_auth_instance = None

def get_google_auth() -> GoogleAuthManager:
    global _google_auth_instance
    if _google_auth_instance is None:
        _google_auth_instance = GoogleAuthManager()
    return _google_auth_instance

if __name__ == "__main__":
    print("Google OAuth Server")
    print(f"Scopes: {len(GOOGLE_SCOPES)}")
    print(f"Redirect URI: {GOOGLE_REDIRECT_URI}")
    print(f"Auth URL: {get_auth_url()}")
