"""Playwright browser agent for web automation."""
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("openclaw.browser")

BROWSER_HEADLESS = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"


class BrowserWorker:
    def __init__(self):
        self.log = []
        self.steps_done = 0
        self.steps_failed = 0
        self.last_url = ""
        self.success = False

    def run_web_task(self, task: str, parent_task: str = "") -> Dict[str, Any]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed")
            return {"success": False, "log": ["Playwright not installed"], "steps_done": 0, "steps_failed": 1, "last_url": ""}

        self.log.append(f"Starting browser task: {task[:80]}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=BROWSER_HEADLESS)
                context = browser.new_context()
                page = context.new_page()
                self.log.append("Browser launched")
                # Simple heuristic: if task contains a URL, navigate to it
                words = task.split()
                for w in words:
                    if w.startswith("http"):
                        page.goto(w)
                        self.last_url = w
                        self.log.append(f"Navigated to {w}")
                        self.steps_done += 1
                        break
                else:
                    self.log.append("No explicit URL found; task may need manual step parsing")
                page.screenshot(path=f"/tmp/openclaw_screenshots/{hash(task) % 10000}.png")
                self.steps_done += 1
                browser.close()
                self.success = True
                self.log.append("Browser task completed")
        except Exception as e:
            self.steps_failed += 1
            self.log.append(f"Browser error: {e}")
            logger.error(f"Browser error: {e}")
        return {
            "success": self.success,
            "log": self.log,
            "steps_done": self.steps_done,
            "steps_failed": self.steps_failed,
            "last_url": self.last_url,
        }
