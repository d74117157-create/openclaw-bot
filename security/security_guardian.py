"""
SECURITY GUARDIAN AGENT
OpenClaw Superswarm — Defensive Security Subsystem
Monitors, detects, alerts, and responds to security threats.
"""

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("openclaw.security")

# ─── CONFIGURATION ───────────────────────────────────────────────

SECURITY_STATE_PATH = os.getenv("SECURITY_STATE_PATH", "/data/security-state.json")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")
TELEGRAM_ALERT_BOT = os.getenv("TELEGRAM_ALERT_BOT")
ALERT_CHANNEL_ID = os.getenv("ALERT_CHANNEL_ID")

BLOCKED_PATTERNS = [
    r"(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
    r"(api[_-]?key|token|secret)\s*=\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
    r"ghp_[a-zA-Z0-9]{36}",
    r"xox[baprs]-[a-zA-Z0-9\-]+",
    r"sk-[a-zA-Z0-9]{48}",
]

# ─── SECURITY STATE ────────────────────────────────────────────

class SecurityState:
    def __init__(self):
        self.data = self._load()
        if not self.data:
            self.data = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "alerts": [],
                "incidents": [],
                "scans": [],
                "oauth_audit": [],
                "repo_secrets_scan": [],
                "blocked_attempts": [],
                "suspicious_ips": [],
                "api_usage": {},
            }
            self._save()

    def _load(self):
        if os.path.exists(SECURITY_STATE_PATH):
            try:
                with open(SECURITY_STATE_PATH, "r") as f:
                    return json.load(f)
            except:
                return None
        return None

    def _save(self):
        os.makedirs(os.path.dirname(SECURITY_STATE_PATH), exist_ok=True)
        with open(SECURITY_STATE_PATH, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def add_alert(self, severity: str, category: str, message: str, details: dict = None):
        alert = {
            "id": hashlib.sha256(f"{datetime.utcnow().isoformat()}{message}".encode()).hexdigest()[:12],
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "category": category,
            "message": message,
            "details": details or {},
            "acknowledged": False,
        }
        self.data["alerts"].append(alert)
        self.data["alerts"] = self.data["alerts"][-1000:]
        self._save()
        logger.warning(f"[SECURITY ALERT] {severity}: {message}")
        return alert

    def get_unacknowledged_alerts(self) -> List[Dict]:
        return [a for a in self.data["alerts"] if not a["acknowledged"]]

# ─── SECURITY GUARDIAN ───────────────────────────────────────────

class SecurityGuardian:
    def __init__(self):
        self.state = SecurityState()
        self.alert_handlers = []
        self._register_default_handlers()

    def _register_default_handlers(self):
        self.alert_handlers.append(self._alert_console)
        if ALERT_WEBHOOK_URL:
            self.alert_handlers.append(self._alert_webhook)
        if TELEGRAM_ALERT_BOT and ALERT_CHANNEL_ID:
            self.alert_handlers.append(self._alert_telegram)

    def _alert_console(self, alert: dict):
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        print(f"{emoji.get(alert['severity'], '⚪')} [{alert['severity'].upper()}] {alert['category']}")
        print(f"   {alert['message']}")
        print(f"   ID: {alert['id']} | Time: {alert['timestamp']}")

    def _alert_webhook(self, alert: dict):
        import requests
        try:
            payload = {
                "text": f"🚨 Security Alert: {alert['severity'].upper()}\n"
                        f"Category: {alert['category']}\n"
                        f"Message: {alert['message']}\n"
                        f"ID: {alert['id']} | Time: {alert['timestamp']}"
            }
            requests.post(ALERT_WEBHOOK_URL, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Webhook alert failed: {e}")

    def _alert_telegram(self, alert: dict):
        import requests
        try:
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            text = (f"{emoji.get(alert['severity'], '⚪')} *Security Alert: {alert['severity'].upper()}*\n"
                    f"Category: `{alert['category']}`\n"
                    f"Message: {alert['message']}\n"
                    f"ID: `{alert['id']}`")
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_ALERT_BOT}/sendMessage",
                json={"chat_id": ALERT_CHANNEL_ID, "text": text, "parse_mode": "Markdown"},
                timeout=10
            )
        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")

    def send_alert(self, severity: str, category: str, message: str, details: dict = None):
        alert = self.state.add_alert(severity, category, message, details)
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        return alert

    def monitor_api_usage(self, service: str, endpoint: str, response_time: float, status_code: int):
        key = f"{service}:{endpoint}"
        if key not in self.state.data["api_usage"]:
            self.state.data["api_usage"][key] = {
                "count": 0, "errors": 0, "avg_response": 0.0, "last_seen": None
            }

        usage = self.state.data["api_usage"][key]
        usage["count"] += 1
        usage["last_seen"] = datetime.utcnow().isoformat()

        if status_code >= 400:
            usage["errors"] += 1

        usage["avg_response"] = (usage["avg_response"] * (usage["count"] - 1) + response_time) / usage["count"]

        if usage["count"] > 1000 and usage["errors"] / usage["count"] > 0.1:
            self.send_alert("high", "api_anomaly", 
                f"High error rate on {key}: {usage['errors']}/{usage['count']}",
                {"error_rate": usage["errors"] / usage["count"]})

        if response_time > usage["avg_response"] * 5:
            self.send_alert("medium", "api_performance",
                f"Slow response on {key}: {response_time:.2f}s (avg: {usage['avg_response']:.2f}s)")

        self.state._save()

    def scan_for_secrets(self, text: str, source: str = "unknown") -> List[Dict]:
        findings = []
        for pattern in BLOCKED_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                secret_hash = hashlib.sha256(match.group().encode()).hexdigest()[:16]
                finding = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": source,
                    "pattern": pattern[:50],
                    "hash": secret_hash,
                    "position": match.span(),
                }
                findings.append(finding)
                self.send_alert("critical", "exposed_secret",
                    f"Potential secret exposed in {source}",
                    {"hash": secret_hash, "source": source})

        self.state.data["repo_secrets_scan"].extend(findings)
        self.state.data["repo_secrets_scan"] = self.state.data["repo_secrets_scan"][-500:]
        self.state._save()
        return findings

    def audit_oauth_connection(self, provider: str, app_name: str, scopes: List[str], granted_at: str):
        audit = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "app_name": app_name,
            "scopes": scopes,
            "granted_at": granted_at,
            "risk_score": self._calculate_oauth_risk(scopes),
        }
        self.state.data["oauth_audit"].append(audit)
        self.state._save()

        if audit["risk_score"] > 7:
            self.send_alert("high", "oauth_risk",
                f"High-risk OAuth app: {app_name} on {provider}",
                {"scopes": scopes, "risk_score": audit["risk_score"]})

    def _calculate_oauth_risk(self, scopes: List[str]) -> int:
        risk = 0
        high_risk = ["repo", "delete_repo", "admin:org", "admin:repo_hook", "admin:ssh_signing_key"]
        medium_risk = ["write:packages", "delete:packages", "admin:gpg_key"]

        for scope in scopes:
            if any(hr in scope for hr in high_risk):
                risk += 3
            elif any(mr in scope for mr in medium_risk):
                risk += 2
            else:
                risk += 1

        return min(risk, 10)

    def check_suspicious_ip(self, ip: str, user_agent: str, endpoint: str):
        blocked_prefixes = ["10.0.0.", "192.168.", "127.0.0."]
        if any(ip.startswith(prefix) for prefix in blocked_prefixes):
            self.send_alert("medium", "suspicious_access",
                f"Internal IP accessing external endpoint: {ip}",
                {"ip": ip, "endpoint": endpoint, "user_agent": user_agent})

    def generate_incident_report(self, days: int = 7) -> Dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        alerts = [a for a in self.state.data["alerts"] 
                  if datetime.fromisoformat(a["timestamp"]) > cutoff]

        by_severity = {}
        by_category = {}
        for alert in alerts:
            by_severity[alert["severity"]] = by_severity.get(alert["severity"], 0) + 1
            by_category[alert["category"]] = by_category.get(alert["category"], 0) + 1

        return {
            "period_days": days,
            "total_alerts": len(alerts),
            "unacknowledged": len([a for a in alerts if not a["acknowledged"]]),
            "by_severity": by_severity,
            "by_category": by_category,
            "top_threats": sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:5],
            "recommendations": self._generate_recommendations(alerts),
        }

    def _generate_recommendations(self, alerts: List[Dict]) -> List[str]:
        recs = []
        categories = set(a["category"] for a in alerts)

        if "exposed_secret" in categories:
            recs.append("Rotate all exposed secrets immediately. Enable secret scanning.")
        if "oauth_risk" in categories:
            recs.append("Audit and revoke high-risk OAuth applications.")
        if "api_anomaly" in categories:
            recs.append("Investigate API anomalies. Consider rate limiting.")
        if "suspicious_access" in categories:
            recs.append("Review access logs. Consider IP allowlisting.")

        if not recs:
            recs.append("No critical issues detected. Continue monitoring.")

        return recs

    def boot(self):
        print("🔒 Security Guardian initialized")
        print(f"   State: {SECURITY_STATE_PATH}")
        print(f"   Alerts: {len(self.state.data['alerts'])} total")
        print(f"   Unacknowledged: {len(self.state.get_unacknowledged_alerts())}")
        self.send_alert("low", "system", "Security Guardian booted and monitoring")

# ─── SINGLETON INSTANCE ─────────────────────────────────────────

guardian = SecurityGuardian()
