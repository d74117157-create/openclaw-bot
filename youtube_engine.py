"""
YouTube Automation Engine — @realhistory-lessons
Uses Google API Key for read operations, OAuth for write operations.
"""
import os, requests
from datetime import datetime
from google_auth_manager import get_google_auth
from typing import Dict

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")

class YouTubeEngine:
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2"

    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.channel_id = YOUTUBE_CHANNEL_ID
        self.stats = {"subscribers": 0, "views": 0, "videos": 0}
        self.auth = get_google_auth()

    def boot(self):
        print("[YOUTUBE] Engine initialized.")
        if self.auth.is_configured():
            print("[YOUTUBE] OAuth configured. Write operations enabled.")
        else:
            print("[YOUTUBE] OAuth not configured. Read-only mode.")

    def run_automation(self):
        if not self.api_key:
            print("[YOUTUBE] No GOOGLE_API_KEY set.")
            return
        self._fetch_stats()
        self._check_comments()
        self._fetch_analytics()
        print(f"[YOUTUBE] Automation cycle complete. Subs: {self.stats.get('subscribers', 0)}")

    def _fetch_stats(self):
        try:
            url = f"{self.BASE_URL}/channels"
            params = {"part": "statistics", "id": self.channel_id, "key": self.api_key}
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if "items" in data:
                s = data["items"][0]["statistics"]
                self.stats = {
                    "subscribers": int(s.get("subscriberCount", 0)),
                    "views": int(s.get("viewCount", 0)),
                    "videos": int(s.get("videoCount", 0)),
                    "last_check": datetime.utcnow().isoformat()
                }
                print(f"[YOUTUBE] Stats: {self.stats}")
        except Exception as e:
            print(f"[YOUTUBE] Stats error: {e}")

    def _fetch_analytics(self):
        """Fetch YouTube Analytics data (requires OAuth)."""
        if not self.auth.is_configured():
            return
        try:
            # YouTube Analytics API v2
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
            start_date = (datetime.utcnow().replace(day=1)).strftime("%Y-%m-%d")

            url = f"{self.ANALYTICS_URL}/reports"
            params = {
                "ids": f"channel=={self.channel_id}",
                "startDate": start_date,
                "endDate": end_date,
                "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained",
                "dimensions": "day"
            }

            result = self.auth.make_authenticated_request(url, "GET", params=params)
            if "error" not in result:
                print(f"[YOUTUBE] Analytics fetched for {start_date} to {end_date}")
            else:
                print(f"[YOUTUBE] Analytics error: {result.get('error')}")
        except Exception as e:
            print(f"[YOUTUBE] Analytics fetch error: {e}")

    def _check_comments(self):
        try:
            url = f"{self.BASE_URL}/search"
            params = {
                "part": "snippet", "channelId": self.channel_id,
                "order": "date", "type": "video", "maxResults": 5, "key": self.api_key
            }
            r = requests.get(url, params=params, timeout=10)
            for item in r.json().get("items", []):
                vid = item["id"]["videoId"]
                self._check_video_comments(vid)
        except Exception as e:
            print(f"[YOUTUBE] Comments error: {e}")

    def _check_video_comments(self, video_id):
        try:
            url = f"{self.BASE_URL}/commentThreads"
            params = {
                "part": "snippet", "videoId": video_id,
                "maxResults": 10, "order": "time", "key": self.api_key
            }
            r = requests.get(url, params=params, timeout=10)
            for item in r.json().get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                print(f"[YOUTUBE] Comment on {video_id}: {text[:80]}...")
        except:
            pass

    def search_trending(self, query, region="US"):
        try:
            url = f"{self.BASE_URL}/search"
            params = {
                "part": "snippet", "q": query, "type": "video",
                "order": "viewCount", "regionCode": region, "maxResults": 10, "key": self.api_key
            }
            r = requests.get(url, params=params, timeout=10)
            return [{"title": i["snippet"]["title"], "videoId": i["id"]["videoId"]} for i in r.json().get("items", [])]
        except:
            return []

    def upload_video(self, title: str, description: str, category_id: str = "22",
                     privacy_status: str = "private", file_path: str = None) -> Dict:
        """Upload a video to YouTube (requires OAuth)."""
        if not self.auth.is_configured():
            return {"error": "OAuth not configured. Cannot upload."}

        try:
            # Step 1: Create video metadata
            url = f"{self.BASE_URL}/videos"
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }

            result = self.auth.make_authenticated_request(url, "POST", data=body)
            if "id" in result:
                print(f"[YOUTUBE] Video created: {result['id']}")
                return {"status": "created", "video_id": result["id"]}
            else:
                return {"error": result.get("error", "Unknown error")}

        except Exception as e:
            return {"error": str(e)}