"""
Mini Apps Factory
Reusable templates for profitable small applications.
"""
import os
import json
import logging
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("mini_apps")


@dataclass
class MiniAppConfig:
    app_id: str
    name: str
    template: str
    platform: str
    auth_required: bool = False
    payments_enabled: bool = False
    analytics_enabled: bool = True
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class MiniAppFactory:
    TEMPLATES = {
        "calculator": {
            "description": "Specialized calculator (ROI, compound interest, etc.)",
            "revenue_model": "ads + premium unlock"
        },
        "converter": {
            "description": "Unit/currency converter with real-time rates",
            "revenue_model": "affiliate + premium"
        },
        "tracker": {
            "description": "Habit/progress tracker with streaks",
            "revenue_model": "subscription"
        },
        "quiz": {
            "description": "Interactive quiz with leaderboard",
            "revenue_model": "ads + in-app purchases"
        },
        "generator": {
            "description": "AI content generator (names, ideas, captions)",
            "revenue_model": "credits system"
        }
    }

    def __init__(self, output_dir: str = "mini_apps/output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_app(self, config: MiniAppConfig) -> Dict:
        template = self.TEMPLATES.get(config.template)
        if not template:
            return {"error": f"Unknown template: {config.template}"}

        app_dir = os.path.join(self.output_dir, config.app_id)
        os.makedirs(app_dir, exist_ok=True)
        files_created = []

        html_path = os.path.join(app_dir, "index.html")
        with open(html_path, "w") as f:
            f.write(self._generate_html(config, template))
        files_created.append(html_path)

        js_path = os.path.join(app_dir, "app.js")
        with open(js_path, "w") as f:
            f.write(self._generate_js(config))
        files_created.append(js_path)

        css_path = os.path.join(app_dir, "styles.css")
        with open(css_path, "w") as f:
            f.write(self._generate_css(config))
        files_created.append(css_path)

        if config.platform == "telegram":
            manifest_path = os.path.join(app_dir, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(self._generate_telegram_manifest(config), f, indent=2)
            files_created.append(manifest_path)

        logger.info(f"Generated mini app: {config.name} ({config.app_id})")
        return {
            "app_id": config.app_id,
            "name": config.name,
            "template": config.template,
            "platform": config.platform,
            "files": files_created,
            "revenue_model": template["revenue_model"],
            "status": "generated"
        }

    def _generate_html(self, config: MiniAppConfig, template: Dict) -> str:
        auth_section = ""
        if config.auth_required:
            auth_section = "\n    <div id=\"auth-section\">\n        <button id=\"login-btn\" onclick=\"authenticate()\">Login with Telegram</button>\n        <div id=\"user-info\" style=\"display:none;\"></div>\n    </div>"

        payment_section = ""
        if config.payments_enabled:
            payment_section = "\n    <div id=\"premium-section\">\n        <button id=\"premium-btn\" onclick=\"upgradePremium()\">Upgrade to Premium</button>\n    </div>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>{config.name}</title>
    <link rel="stylesheet" href="styles.css">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <div class="app-container">
        <header>
            <h1>{config.name}</h1>
            <p>{template["description"]}</p>
        </header>{auth_section}
        <main id="app-content">
            <div class="loading">Loading {config.name}...</div>
        </main>{payment_section}
        <footer>
            <div id="analytics-pixel" style="display:none;"></div>
        </footer>
    </div>
    <script src="app.js"></script>
</body>
</html>"""

    def _generate_js(self, config: MiniAppConfig) -> str:
        auth_code = ""
        if config.auth_required:
            auth_code = """
function authenticate() {
    if (window.Telegram && Telegram.WebApp) {
        const user = Telegram.WebApp.initDataUnsafe.user;
        if (user) {
            document.getElementById("user-info").style.display = "block";
            document.getElementById("user-info").innerText = `Welcome, ${user.first_name}`;
            document.getElementById("login-btn").style.display = "none";
            localStorage.setItem("tg_user", JSON.stringify(user));
        }
    }
}
const savedUser = localStorage.getItem("tg_user");
if (savedUser) {
    document.getElementById("user-info").style.display = "block";
    document.getElementById("login-btn").style.display = "none";
}"""

        payment_code = ""
        if config.payments_enabled:
            payment_code = """
function upgradePremium() {
    console.log("Premium upgrade initiated");
    trackEvent("premium_click");
}"""

        analytics_code = ""
        if config.analytics_enabled:
            analytics_code = f"""
trackEvent("app_opened", {{ template: "{config.template}" }});
function trackEvent(event, data = {{}}) {{
    const payload = {{
        event: event,
        app_id: "{config.app_id}",
        timestamp: new Date().toISOString(),
        ...data
    }};
    fetch("/api/analytics", {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify(payload)
    }}).catch(e => console.log("Analytics error:", e));
}}"""

        return f"""// {config.name} - Generated by MiniAppFactory
if (window.Telegram && Telegram.WebApp) {{
    Telegram.WebApp.ready();
    Telegram.WebApp.expand();
}}
{auth_code}
{payment_code}
{analytics_code}
document.addEventListener("DOMContentLoaded", () => {{
    initApp();
}});
function initApp() {{
    console.log("App initialized:", "{config.app_id}");
}}
"""

    def _generate_css(self, config: MiniAppConfig) -> str:
        return f"""/* {config.name} */
:root {{
    --primary: #0088cc;
    --secondary: #34b7f1;
    --bg: #ffffff;
    --text: #333333;
    --radius: 12px;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}}
.app-container {{ max-width: 480px; margin: 0 auto; padding: 20px; }}
header {{ text-align: center; margin-bottom: 24px; }}
header h1 {{ font-size: 24px; color: var(--primary); margin-bottom: 8px; }}
button {{
    width: 100%; padding: 14px; border: none;
    border-radius: var(--radius); background: var(--primary);
    color: white; font-size: 16px; font-weight: 600;
    cursor: pointer; margin: 8px 0;
}}
button:hover {{ background: var(--secondary); }}
.loading {{ text-align: center; padding: 40px; color: #999; }}
"""

    def _generate_telegram_manifest(self, config: MiniAppConfig) -> Dict:
        return {
            "name": config.name,
            "short_name": config.name[:20],
            "description": f"{config.template} mini app powered by OpenClaw",
            "start_url": ".",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#0088cc"
        }


class MiniAppAnalytics:
    def __init__(self, db_path: str = "mini_apps/analytics.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def track_event(self, app_id: str, event: str, data: Dict) -> bool:
        event_data = {
            "app_id": app_id,
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Analytics: {app_id} - {event}")
        return True

    async def get_app_metrics(self, app_id: str) -> Dict:
        return {
            "app_id": app_id,
            "total_opens": 0,
            "unique_users": 0,
            "premium_conversions": 0,
            "avg_session_duration": 0,
            "top_events": []
        }
