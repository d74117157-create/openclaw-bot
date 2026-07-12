#!/usr/bin/env python3
"""
OpenClaw YouTube Content Pipeline
Generates, creates, and uploads videos automatically.
"""
import os
import json
import random
import requests
from datetime import datetime, timedelta

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

def get_trending_topics(region="US", max_results=10):
    """Fetch trending video topics from YouTube"""
    if not GOOGLE_API_KEY:
        print("[ERROR] GOOGLE_API_KEY not set")
        return []

    url = f"{YOUTUBE_API_BASE}/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": max_results,
        "key": GOOGLE_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        topics = []
        for item in data.get("items", []):
            topic = {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "category": item["snippet"]["categoryId"],
                "tags": item["snippet"].get("tags", [])[:5],
                "view_count": item["statistics"].get("viewCount", 0)
            }
            topics.append(topic)
        return topics
    except Exception as e:
        print(f"[ERROR] Failed to fetch trending: {e}")
        return []

def generate_script(topic, niche="tech"):
    """Generate a video script from a trending topic"""
    title = topic["title"]
    hooks = [
        f"You won't believe what {topic['channel']} just revealed about {title}...",
        f"The truth about {title} that nobody is talking about.",
        f"Why {title} is about to change everything.",
        f"I analyzed {title} so you don't have to. Here's what I found."
    ]

    script = {
        "hook": random.choice(hooks),
        "title": f"{title} - Explained by AI Swarm",
        "body": f"Today we're breaking down: {title}. This topic is trending with {topic['view_count']} views. Here's what you need to know in 60 seconds.",
        "cta": "Like and subscribe if you want more AI-generated breakdowns. Comment what topic I should cover next.",
        "tags": topic["tags"] + [niche, "AI", "automation", "trending"],
        "source_topic": title
    }
    return script

def create_video_project(script, output_dir="/tmp/youtube_projects"):
    """Create a video project folder with all assets ready for rendering"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = f"{output_dir}/project_{timestamp}"
    os.makedirs(project_dir, exist_ok=True)

    # Save script
    with open(f"{project_dir}/script.json", "w") as f:
        json.dump(script, f, indent=2)

    # Create instructions for video assembly
    instructions = f"""
VIDEO PROJECT: {script['title']}
================================
HOOK (0-3 sec): {script['hook']}
BODY (3-55 sec): {script['body']}
CTA (55-60 sec): {script['cta']}

TAGS: {', '.join(script['tags'])}

NEXT STEPS:
1. Run: python3 render_video.py {project_dir}
2. Upload via: python3 upload_youtube.py {project_dir}
"""
    with open(f"{project_dir}/INSTRUCTIONS.txt", "w") as f:
        f.write(instructions)

    print(f"[OK] Video project created: {project_dir}")
    print(f"[INFO] Title: {script['title']}")
    print(f"[INFO] Tags: {script['tags']}")
    return project_dir

def run_pipeline(niche="tech", region="US"):
    """Full pipeline: trending → script → project"""
    print("=" * 50)
    print("OPENCLAW YOUTUBE PIPELINE STARTING")
    print("=" * 50)

    print("[1/3] Fetching trending topics...")
    topics = get_trending_topics(region=region)
    if not topics:
        print("[FAIL] No topics fetched. Check GOOGLE_API_KEY.")
        return None

    # Pick a topic in the niche (or random if no match)
    topic = random.choice(topics)
    print(f"[OK] Selected topic: {topic['title'][:50]}...")

    print("[2/3] Generating script...")
    script = generate_script(topic, niche=niche)

    print("[3/3] Creating video project...")
    project = create_video_project(script)

    print("=" * 50)
    print("PIPELINE COMPLETE")
    print(f"Project ready at: {project}")
    print("=" * 50)
    return project

if __name__ == "__main__":
    import sys
    niche = sys.argv[1] if len(sys.argv) > 1 else "tech"
    region = sys.argv[2] if len(sys.argv) > 2 else "US"
    run_pipeline(niche=niche, region=region)
