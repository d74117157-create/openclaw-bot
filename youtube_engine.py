"""
YouTube Automation Engine — @realhistory-lessons
"""
import os, requests
from datetime import datetime

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")

class YouTubeEngine:
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.channel_id = YOUTUBE_CHANNEL_ID
        self.stats = {"subscribers": 0, "views": 0, "videos": 0}

    def boot(self):
        print("[YOUTUBE] Engine initialized.")

    def run_automation(self):
        if not self.api_key:
            print("[YOUTUBE] No GOOGLE_API_KEY set.")
            return
        self._fetch_stats()
        self._check_comments()

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
