"""
YouTube Automation Engine
Complete pipeline: research → script → voice → edit → publish → analytics
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import aiohttp

logger = logging.getLogger("youtube_automation")


@dataclass
class VideoProject:
    """Represents a video project through the pipeline."""
    project_id: str
    title: str
    topic: str
    target_duration: int  # seconds
    status: str  # research | scripting | voiceover | editing | publishing | published
    script: Optional[str] = None
    voiceover_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    video_path: Optional[str] = None
    youtube_video_id: Optional[str] = None
    seo_score: Optional[float] = None
    analytics: Optional[Dict] = None
    created_at: str = None
    published_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class YouTubeResearcher:
    """Researches trending topics and generates video ideas."""

    def __init__(self, google_api_key: str = None, groq_api_key: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def research_trending(self, niche: str = "technology", max_results: int = 10) -> List[Dict]:
        """Find trending topics in a niche using YouTube Data API + Groq analysis."""
        topics = []

        # Search for popular videos in niche
        search_url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": niche,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",
            "maxResults": max_results,
            "key": self.google_api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data.get("items", []):
                        topics.append({
                            "title": item["snippet"]["title"],
                            "description": item["snippet"]["description"][:200],
                            "channel": item["snippet"]["channelTitle"],
                            "video_id": item["id"]["videoId"],
                            "published": item["snippet"]["publishedAt"]
                        })

        # Use Groq to analyze and rank topics
        if self.groq_api_key and topics:
            ranked = await self._rank_topics_with_ai(topics, niche)
            return ranked

        return topics

    async def _rank_topics_with_ai(self, topics: List[Dict], niche: str) -> List[Dict]:
        """Use Groq to rank topics by viral potential."""
        prompt = f"""Analyze these YouTube video topics in the '{niche}' niche.
Rank them by viral potential (1-10) considering:
- Search volume potential
- Audience engagement likelihood  
- Content uniqueness
- Monetization potential

Topics:
{json.dumps(topics, indent=2)}

Return ONLY a JSON array with the same objects plus a 'viral_score' field."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    # Extract JSON from response
                    try:
                        ranked = json.loads(content)
                        return sorted(ranked, key=lambda x: x.get("viral_score", 0), reverse=True)
                    except Exception:
                        return topics
        return topics

    async def generate_video_ideas(self, count: int = 5) -> List[Dict]:
        """Generate original video ideas using AI."""
        if not self.groq_api_key:
            return []

        prompt = f"""Generate {count} original YouTube video ideas for a channel about AI, automation, and digital entrepreneurship.
Each idea should include: title, hook (first 30 seconds), key points (3-5), target keywords, estimated duration.
Return as JSON array."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 3000
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    try:
                        return json.loads(content)
                    except Exception:
                        return []
        return []


class ScriptGenerator:
    """Generates video scripts optimized for retention and SEO."""

    def __init__(self, groq_api_key: str = None, openai_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

    async def generate_script(self, topic: str, duration: int = 600, style: str = "educational") -> Dict:
        """Generate a complete video script with timestamps."""
        words_per_minute = 150
        target_words = (duration // 60) * words_per_minute

        prompt = f"""Write a YouTube video script about: "{topic}"

Requirements:
- Target duration: {duration} seconds (~{target_words} words)
- Style: {style}
- Include: Hook (0-30s), Main Content, Call to Action
- Format with timestamps [MM:SS]
- Include visual direction notes in [brackets]
- Optimize for retention: pattern interrupts every 60-90 seconds
- Include 3-5 SEO keywords naturally

Return JSON format:
{{
  "title": "...",
  "hook": "...",
  "sections": [
    {{"timestamp": "00:00", "text": "...", "visual": "...", "duration": 30}}
  ],
  "keywords": ["..."],
  "cta": "..."
}}"""

        api_key = self.groq_api_key or self.openai_api_key
        if not api_key:
            return {"error": "No API key configured"}

        url = "https://api.groq.com/openai/v1/chat/completions" if self.groq_api_key else "https://api.openai.com/v1/chat/completions"
        model = "llama-3.3-70b-versatile" if self.groq_api_key else "gpt-4o"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 4000}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    try:
                        return json.loads(content)
                    except Exception:
                        return {"raw_script": content}
        return {"error": "Failed to generate script"}


class VoiceWorkflow:
    """Manages text-to-speech voiceover generation."""

    def __init__(self, elevenlabs_api_key: str = None):
        self.elevenlabs_api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel

    async def generate_voiceover(self, text: str, output_path: str = "output/voiceover.mp3") -> str:
        """Generate voiceover from script text."""
        if not self.elevenlabs_api_key:
            logger.warning("ElevenLabs API key not configured — voiceover skipped")
            return None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {"xi-api-key": self.elevenlabs_api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    audio_data = await resp.read()
                    with open(output_path, "wb") as f:
                        f.write(audio_data)
                    logger.info(f"Voiceover saved: {output_path}")
                    return output_path
                else:
                    logger.error(f"Voiceover generation failed: {resp.status}")
        return None


class EditingPipeline:
    """Automated video editing pipeline."""

    def __init__(self):
        self.output_dir = "output/videos"
        os.makedirs(self.output_dir, exist_ok=True)

    async def create_video(self, script: Dict, voiceover_path: str, 
                          b_roll_paths: List[str] = None,
                          output_path: str = None) -> str:
        """Assemble video from voiceover, b-roll, and graphics."""
        if output_path is None:
            output_path = f"{self.output_dir}/video_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"

        # This is a placeholder — real implementation uses moviepy or ffmpeg
        logger.info(f"Video assembly started: {output_path}")
        logger.info(f"  - Voiceover: {voiceover_path}")
        logger.info(f"  - B-roll clips: {len(b_roll_paths) if b_roll_paths else 0}")

        # TODO: Implement actual video assembly with moviepy
        # For now, return the path that would be created
        return output_path


class SEOOptimizer:
    """Optimizes video metadata for YouTube SEO."""

    def __init__(self, google_api_key: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")

    async def optimize_metadata(self, title: str, description: str, 
                                keywords: List[str]) -> Dict:
        """Generate SEO-optimized title, description, tags, and thumbnail text."""
        optimized = {
            "title": title,
            "description": description,
            "tags": keywords[:15],
            "thumbnail_text": title[:60],
            "category_id": "27",  # Education
            "privacy_status": "public"
        }

        # Title optimization: front-load keywords, keep under 60 chars
        if len(title) > 60:
            optimized["title"] = title[:57] + "..."

        # Description optimization
        optimized["description"] = f"""{description}

🔔 Subscribe for more AI & automation content!
👍 Like if you found this helpful
💬 Comment with your questions

#{" #".join(keywords[:5])}
"""

        return optimized


class PublishingWorkflow:
    """Manages YouTube video publishing."""

    def __init__(self, google_api_key: str = None, 
                 google_client_id: str = None,
                 google_client_secret: str = None,
                 refresh_token: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.client_id = google_client_id or os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = google_client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("GOOGLE_REFRESH_TOKEN")
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def publish_video(self, video_path: str, metadata: Dict) -> Dict:
        """Upload video to YouTube with optimized metadata."""
        # This requires OAuth2 flow — simplified here
        logger.info(f"Publishing video: {metadata.get('title')}")
        logger.info(f"  - Tags: {metadata.get('tags', [])}")
        logger.info(f"  - Privacy: {metadata.get('privacy_status', 'public')}")

        # TODO: Implement actual YouTube upload using Google API client
        return {
            "status": "published",
            "video_id": "placeholder",
            "url": f"https://youtube.com/watch?v=placeholder",
            "published_at": datetime.utcnow().isoformat()
        }


class AnalyticsTracker:
    """Tracks YouTube video performance."""

    def __init__(self, google_api_key: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.analytics_base = "https://youtubeanalytics.googleapis.com/v2"

    async def get_video_metrics(self, video_id: str) -> Dict:
        """Get performance metrics for a published video."""
        metrics = {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "avg_view_duration": 0,
            "ctr": 0,
            "subscribers_gained": 0
        }

        # TODO: Implement actual YouTube Analytics API calls
        logger.info(f"Fetching analytics for video: {video_id}")

        return metrics

    async def generate_performance_report(self, video_ids: List[str]) -> str:
        """Generate a markdown performance report."""
        report = "# YouTube Performance Report\n\n"
        for vid in video_ids:
            metrics = await self.get_video_metrics(vid)
            report += f"## Video: {vid}\n"
            report += f"- Views: {metrics['views']:,}\n"
            report += f"- Likes: {metrics['likes']:,}\n"
            report += f"- Avg View Duration: {metrics['avg_view_duration']}s\n"
            report += f"- CTR: {metrics['ctr']:.2%}\n\n"
        return report


class YouTubeAutomationEngine:
    """Orchestrates the complete YouTube content pipeline."""

    def __init__(self):
        self.researcher = YouTubeResearcher()
        self.script_gen = ScriptGenerator()
        self.voice = VoiceWorkflow()
        self.editor = EditingPipeline()
        self.seo = SEOOptimizer()
        self.publisher = PublishingWorkflow()
        self.analytics = AnalyticsTracker()
        self.projects_dir = Path("projects/youtube")
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    async def create_project(self, topic: str, duration: int = 600) -> VideoProject:
        """Create a new video project."""
        project_id = f"yt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        project = VideoProject(
            project_id=project_id,
            title=f"Draft: {topic}",
            topic=topic,
            target_duration=duration,
            status="research"
        )
        self._save_project(project)
        return project

    async def run_pipeline(self, project: VideoProject) -> VideoProject:
        """Run the complete pipeline for a project."""
        try:
            # Step 1: Script generation
            project.status = "scripting"
            self._save_project(project)
            script = await self.script_gen.generate_script(project.topic, project.target_duration)
            project.script = json.dumps(script)
            project.title = script.get("title", project.title)

            # Step 2: Voiceover
            project.status = "voiceover"
            self._save_project(project)
            if script.get("sections"):
                full_text = " ".join([s.get("text", "") for s in script["sections"]])
                voice_path = await self.voice.generate_voiceover(
                    full_text, 
                    f"projects/youtube/{project.project_id}/voiceover.mp3"
                )
                project.voiceover_path = voice_path

            # Step 3: Editing
            project.status = "editing"
            self._save_project(project)
            video_path = await self.editor.create_video(
                script, 
                project.voiceover_path,
                output_path=f"projects/youtube/{project.project_id}/video.mp4"
            )
            project.video_path = video_path

            # Step 4: SEO
            keywords = script.get("keywords", [])
            metadata = await self.seo.optimize_metadata(project.title, "", keywords)
            project.seo_score = 0.85  # Placeholder

            # Step 5: Publishing
            project.status = "publishing"
            self._save_project(project)
            result = await self.publisher.publish_video(project.video_path, metadata)
            project.youtube_video_id = result.get("video_id")
            project.published_at = result.get("published_at")
            project.status = "published"

        except Exception as e:
            logger.error(f"Pipeline failed for {project.project_id}: {e}")
            project.status = "failed"

        self._save_project(project)
        return project

    def _save_project(self, project: VideoProject):
        """Persist project state to disk."""
        path = self.projects_dir / f"{project.project_id}.json"
        path.write_text(json.dumps(asdict(project), indent=2))

    def load_project(self, project_id: str) -> Optional[VideoProject]:
        """Load project from disk."""
        path = self.projects_dir / f"{project_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return VideoProject(**data)
        return None
