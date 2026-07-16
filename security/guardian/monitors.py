"""
Security Monitors — Continuous surveillance of all attack surfaces.
"""
import os
import re
import json
import hashlib
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

import aiohttp

logger = logging.getLogger("guardian.monitors")


@dataclass
class SecurityFinding:
    """Standardized security finding format."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    title: str
    description: str
    resource: str
    recommendation: str
    timestamp: str
    evidence: Dict[str, Any]
    remediation_status: str = "open"

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_markdown(self) -> str:
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "🔵"}
        return f"""
{emoji.get(self.severity, "⚪")} **{self.severity}** — {self.title}
**Category:** {self.category}
**Resource:** `{self.resource}`
**Description:** {self.description}
**Recommendation:** {self.recommendation}
**Evidence:** ```json\n{json.dumps(self.evidence, indent=2)}\n```
**Status:** {self.remediation_status}
**Detected:** {self.timestamp}
"""


class BaseMonitor(ABC):
    """Abstract base for all security monitors."""

    def __init__(self, config: Any):
        self.config = config
        self.findings: List[SecurityFinding] = []
        self.last_run: Optional[datetime] = None

    @abstractmethod
    async def scan(self) -> List[SecurityFinding]:
        """Execute the monitor's scan logic."""
        pass

    @abstractmethod
    def get_interval(self) -> int:
        """Return scan interval in seconds."""
        pass

    async def run(self) -> List[SecurityFinding]:
        """Execute scan and update state."""
        logger.info(f"Starting {self.__class__.__name__} scan...")
        try:
            self.findings = await self.scan()
            self.last_run = datetime.utcnow()
            logger.info(f"{self.__class__.__name__} found {len(self.findings)} findings")
            return self.findings
        except Exception as e:
            logger.error(f"{self.__class__.__name__} failed: {e}")
            error_finding = SecurityFinding(
                severity="HIGH",
                category="monitor_failure",
                title=f"{self.__class__.__name__} Scan Failed",
                description=str(e),
                resource=self.__class__.__name__,
                recommendation="Check monitor logs and configuration",
                timestamp=datetime.utcnow().isoformat(),
                evidence={"error": str(e)}
            )
            return [error_finding]


class AccountActivityMonitor(BaseMonitor):
    """Monitor for suspicious account activity across all platforms."""

    SUSPICIOUS_PATTERNS = [
        (r"(failed|invalid|incorrect).*login", "FAILED_LOGIN"),
        (r"(unauthorized|unauthenticated).*access", "UNAUTHORIZED_ACCESS"),
        (r"password.*(reset|change|update)", "PASSWORD_CHANGE"),
        (r"(new|unknown|unrecognized).*device", "NEW_DEVICE"),
        (r"(suspicious|unusual).*activity", "SUSPICIOUS_ACTIVITY"),
        (r"(oauth|token|api.*key).*revoked", "TOKEN_REVOKED"),
    ]

    def get_interval(self) -> int:
        return self.config.account_check_interval

    async def scan(self) -> List[SecurityFinding]:
        findings = []
        findings.extend(self._scan_environment_variables())
        findings.extend(self._scan_token_exposure())
        findings.extend(self._scan_file_permissions())
        findings.extend(self._scan_ssh_keys())
        return findings

    def _scan_environment_variables(self) -> List[SecurityFinding]:
        findings = []
        env = dict(os.environ)
        weak_patterns = ["password", "secret", "token", "key"]
        for key, value in env.items():
            if any(p in key.lower() for p in weak_patterns):
                if value and len(value) < 8:
                    findings.append(SecurityFinding(
                        severity="HIGH",
                        category="weak_credential",
                        title=f"Weak Credential Detected: {key}",
                        description=f"Environment variable '{key}' has a weak value (length: {len(value)})",
                        resource=f"env:{key}",
                        recommendation="Rotate to a strong, randomly generated value immediately",
                        timestamp=datetime.utcnow().isoformat(),
                        evidence={"key": key, "length": len(value), "hint": value[:3] + "***" if value else ""}
                    ))
        suspicious_domains = ["ngrok", "pastebin", "requestbin", "webhook.site"]
        for key, value in env.items():
            if value and isinstance(value, str):
                for domain in suspicious_domains:
                    if domain in value.lower():
                        findings.append(SecurityFinding(
                            severity="CRITICAL",
                            category="suspicious_endpoint",
                            title=f"Suspicious Endpoint in Environment: {key}",
                            description=f"Environment variable '{key}' contains a known suspicious domain",
                            resource=f"env:{key}",
                            recommendation="Investigate immediately — possible C2 or exfiltration endpoint",
                            timestamp=datetime.utcnow().isoformat(),
                            evidence={"key": key, "domain": domain, "value_preview": value[:50]}
                        ))
        return findings

    def _scan_token_exposure(self) -> List[SecurityFinding]:
        findings = []
        try:
            with open("/proc/self/cmdline", "r") as f:
                cmdline = f.read()
            token_patterns = [
                (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
                (r"xoxb-[a-zA-Z0-9-]{50,}", "Slack Bot Token"),
                (r"\d{10}:[A-Za-z0-9_-]{35}", "Telegram Bot Token"),
                (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
                (r"gsk_[a-zA-Z0-9]{52}", "Groq API Key"),
                (r"AIzaSy[A-Za-z0-9_-]{33}", "Google API Key"),
            ]
            for pattern, token_type in token_patterns:
                if re.search(pattern, cmdline):
                    findings.append(SecurityFinding(
                        severity="CRITICAL",
                        category="token_exposure",
                        title=f"{token_type} Exposed in Process Command Line",
                        description="A sensitive token was found in the process command line, visible to all users",
                        resource="process:cmdline",
                        recommendation="Restart process with tokens loaded from secure environment only",
                        timestamp=datetime.utcnow().isoformat(),
                        evidence={"token_type": token_type, "cmdline_preview": cmdline[:100]}
                    ))
        except Exception:
            pass
        return findings

    def _scan_file_permissions(self) -> List[SecurityFinding]:
        findings = []
        sensitive_files = [
            ".env", ".env.local", ".env.production",
            "secrets.json", "config.json", "credentials.json",
            "id_rsa", "id_ed25519", ".ssh/config",
            "token.txt", "api_key.txt"
        ]
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "__pycache__", ".venv", "venv"]]
            if any(skip in root for skip in [".git", "node_modules", "__pycache__"]):
                continue
            for file in files:
                if any(file.endswith(suffix) or file == exact for suffix in [".pem", ".key", ".p12"] for exact in sensitive_files):
                    filepath = os.path.join(root, file)
                    try:
                        stat = os.stat(filepath)
                        mode = stat.st_mode
                        if mode & 0o004 or mode & 0o002:
                            findings.append(SecurityFinding(
                                severity="HIGH",
                                category="insecure_permissions",
                                title=f"Insecure Permissions on Sensitive File",
                                description=f"File '{filepath}' is world-readable or world-writable",
                                resource=filepath,
                                recommendation=f"Run: chmod 600 {filepath}",
                                timestamp=datetime.utcnow().isoformat(),
                                evidence={"filepath": filepath, "permissions": oct(mode)[-3:]}
                            ))
                    except Exception:
                        pass
        return findings

    def _scan_ssh_keys(self) -> List[SecurityFinding]:
        findings = []
        ssh_dir = Path.home() / ".ssh"
        auth_keys = ssh_dir / "authorized_keys"
        if auth_keys.exists():
            content = auth_keys.read_text()
            keys = [line for line in content.split("\n") if line.strip() and not line.startswith("#")]
            state_file = Path(self.config.state_file)
            known_hashes = set()
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                    known_hashes = set(state.get("known_ssh_keys", []))
                except Exception:
                    pass
            for key in keys:
                key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
                if known_hashes and key_hash not in known_hashes:
                    findings.append(SecurityFinding(
                        severity="CRITICAL",
                        category="unauthorized_ssh_key",
                        title="Unauthorized SSH Key Detected",
                        description="A new SSH public key was found that was not previously known",
                        resource=str(auth_keys),
                        recommendation="Verify the key belongs to you. If not, remove it immediately",
                        timestamp=datetime.utcnow().isoformat(),
                        evidence={"key_hash": key_hash, "key_preview": key[:60] + "..."}
                    ))
            new_hashes = [hashlib.sha256(k.encode()).hexdigest()[:16] for k in keys]
            state = {"known_ssh_keys": new_hashes, "last_scan": datetime.utcnow().isoformat()}
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state, indent=2))
        return findings


class OAuthAuditor(BaseMonitor):
    """Audit OAuth connections and permissions across platforms."""

    def get_interval(self) -> int:
        return self.config.oauth_check_interval

    async def scan(self) -> List[SecurityFinding]:
        findings = []
        findings.extend(await self._audit_github_oauth())
        findings.extend(await self._audit_github_token_scopes())
        return findings

    async def _audit_github_oauth(self) -> List[SecurityFinding]:
        findings = []
        if not self.config.github_token:
            return findings
        headers = {"Authorization": f"token {self.config.github_token}", "Accept": "application/vnd.github.v3+json"}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.github.com/applications/grants", headers=headers) as resp:
                if resp.status == 200:
                    grants = await resp.json()
                    for grant in grants:
                        app = grant.get("app", {})
                        scopes = grant.get("scopes", [])
                        dangerous_scopes = ["delete_repo", "admin:org", "admin:public_key", "admin:repo_hook"]
                        found_dangerous = [s for s in scopes if s in dangerous_scopes]
                        if found_dangerous:
                            findings.append(SecurityFinding(
                                severity="HIGH",
                                category="excessive_oauth_scope",
                                title=f"Dangerous OAuth Scope Granted: {app.get('name', 'Unknown App')}",
                                description=f"GitHub OAuth app has dangerous scopes: {', '.join(found_dangerous)}",
                                resource=f"github:oauth:{app.get('client_id', 'unknown')}",
                                recommendation="Revoke this OAuth authorization unless absolutely necessary",
                                timestamp=datetime.utcnow().isoformat(),
                                evidence={"app_name": app.get("name"), "scopes": scopes, "dangerous": found_dangerous}
                            ))
                        created_at = grant.get("created_at", "")
                        if created_at:
                            try:
                                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                                if datetime.now().astimezone() - created > timedelta(days=90):
                                    findings.append(SecurityFinding(
                                        severity="MEDIUM",
                                        category="stale_oauth_grant",
                                        title=f"Stale OAuth Authorization: {app.get('name', 'Unknown')}",
                                        description="OAuth authorization is older than 90 days and may be forgotten",
                                        resource=f"github:oauth:{app.get('client_id', 'unknown')}",
                                        recommendation="Review and revoke old OAuth authorizations",
                                        timestamp=datetime.utcnow().isoformat(),
                                        evidence={"app_name": app.get("name"), "created_at": created_at}
                                    ))
                            except Exception:
                                pass
        return findings

    async def _audit_github_token_scopes(self) -> List[SecurityFinding]:
        findings = []
        if not self.config.github_token:
            return findings
        headers = {"Authorization": f"token {self.config.github_token}", "Accept": "application/vnd.github.v3+json"}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.github.com/user", headers=headers) as resp:
                scopes_header = resp.headers.get("X-OAuth-Scopes", "")
                scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
                dangerous = ["delete_repo", "admin:org", "admin:public_key", "admin:repo_hook", "gist"]
                found = [s for s in scopes if any(d in s for d in dangerous)]
                if found:
                    findings.append(SecurityFinding(
                        severity="MEDIUM",
                        category="excessive_token_scope",
                        title="GitHub Token Has Excessive Scopes",
                        description=f"Current GitHub token has potentially dangerous scopes: {', '.join(found)}",
                        resource="github:token:current",
                        recommendation="Create a new token with minimal required scopes (repo, workflow only)",
                        timestamp=datetime.utcnow().isoformat(),
                        evidence={"scopes": scopes, "dangerous": found}
                    ))
        return findings


class SecretScanner(BaseMonitor):
    """Scan repositories and files for exposed secrets."""

    SECRET_PATTERNS = [
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT", "CRITICAL"),
        (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token", "CRITICAL"),
        (r"ghu_[a-zA-Z0-9]{36}", "GitHub User Token", "CRITICAL"),
        (r"ghs_[a-zA-Z0-9]{36}", "GitHub Server-to-Server Token", "CRITICAL"),
        (r"ghr_[a-zA-Z0-9]{36}", "GitHub Refresh Token", "CRITICAL"),
        (r"xoxb-[a-zA-Z0-9-]{50,}", "Slack Bot Token", "CRITICAL"),
        (r"xoxp-[a-zA-Z0-9-]{50,}", "Slack User Token", "CRITICAL"),
        (r"xapp-[a-zA-Z0-9-]{50,}", "Slack App Token", "CRITICAL"),
        (r"\b\d{9,10}:[A-Za-z0-9_-]{35}\b", "Telegram Bot Token", "CRITICAL"),
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key", "CRITICAL"),
        (r"sk-proj-[a-zA-Z0-9_-]{100,}", "OpenAI Project Key", "CRITICAL"),
        (r"gsk_[a-zA-Z0-9]{52}", "Groq API Key", "CRITICAL"),
        (r"AIzaSy[A-Za-z0-9_-]{33}", "Google API Key", "CRITICAL"),
        (r"rnd_[a-zA-Z0-9]{30,}", "Render API Key", "HIGH"),
        (r"\b[A-Fa-f0-9]{64}\b", "Generic Hex Secret", "MEDIUM"),
        (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Private Key", "CRITICAL"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID", "CRITICAL"),
        (r"\b[0-9a-f]{32}\b", "Generic 32-char Secret", "MEDIUM"),
    ]

    SKIP_PATHS = [".git", "node_modules", "__pycache__", ".venv", "venv", "security/reports", "logs"]

    def get_interval(self) -> int:
        return self.config.secret_scan_interval

    async def scan(self) -> List[SecurityFinding]:
        findings = []
        findings.extend(self._scan_local_files())
        if self.config.github_token and self.config.github_repo:
            findings.extend(await self._scan_github_repo())
        return findings

    def _scan_local_files(self) -> List[SecurityFinding]:
        findings = []
        scanned = 0
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in self.SKIP_PATHS]
            if any(skip in root for skip in self.SKIP_PATHS):
                continue
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".json", ".yaml", ".yml", ".env", ".md", ".txt", ".sh", ".tf")):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        scanned += 1
                        for pattern, secret_type, severity in self.SECRET_PATTERNS:
                            matches = list(re.finditer(pattern, content, re.MULTILINE))
                            for match in matches:
                                line_start = content.rfind("\n", 0, match.start()) + 1
                                line = content[line_start:match.end()]
                                if "example" in line.lower() or "placeholder" in line.lower() or "fake" in line.lower():
                                    continue
                                findings.append(SecurityFinding(
                                    severity=severity,
                                    category="exposed_secret",
                                    title=f"Exposed {secret_type} in Source Code",
                                    description=f"A {secret_type} was found in {filepath}",
                                    resource=filepath,
                                    recommendation="1. Rotate secret. 2. Use env vars. 3. Add to .gitignore. 4. Use git-filter-repo to remove from history.",
                                    timestamp=datetime.utcnow().isoformat(),
                                    evidence={
                                        "file": filepath,
                                        "secret_type": secret_type,
                                        "line_preview": line.strip()[:100],
                                        "position": match.start()
                                    }
                                ))
                    except Exception:
                        pass
        logger.info(f"SecretScanner scanned {scanned} files, found {len(findings)} exposures")
        return findings

    async def _scan_github_repo(self) -> List[SecurityFinding]:
        findings = []
        if not self.config.github_token or not self.config.github_repo:
            return findings
        headers = {"Authorization": f"token {self.config.github_token}", "Accept": "application/vnd.github.v3+json"}
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/{self.config.github_repo}/secret-scanning/alerts"
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    alerts = await resp.json()
                    for alert in alerts:
                        if alert.get("state") == "open":
                            findings.append(SecurityFinding(
                                severity="CRITICAL",
                                category="github_secret_alert",
                                title=f"GitHub Secret Scanning Alert: {alert.get('secret_type', 'Unknown')}",
                                description="GitHub detected an exposed secret in the repository",
                                resource=f"github:secret:{alert.get('number')}",
                                recommendation="Rotate the secret and remove from git history",
                                timestamp=datetime.utcnow().isoformat(),
                                evidence={
                                    "alert_number": alert.get("number"),
                                    "secret_type": alert.get("secret_type"),
                                    "html_url": alert.get("html_url")
                                }
                            ))
                elif resp.status == 404:
                    logger.info("Secret scanning not enabled or no access for this repo")
                elif resp.status == 403:
                    logger.warning("Rate limited or insufficient permissions for secret scanning")
        return findings


class DependencyVulnerabilityScanner(BaseMonitor):
    """Scan Python dependencies for known vulnerabilities."""

    def get_interval(self) -> int:
        return self.config.dependency_check_interval

    async def scan(self) -> List[SecurityFinding]:
        findings = []
        findings.extend(self._scan_requirements_txt())
        findings.extend(await self._check_outdated_packages())
        return findings

    def _scan_requirements_txt(self) -> List[SecurityFinding]:
        findings = []
        known_bad = {
            "requests": [("2.20.0", "CVE-2018-18074", "HIGH", "Unintended disclosure of proxy credentials")],
            "urllib3": [("1.24.1", "CVE-2019-11324", "MEDIUM", "Certificate validation bypass")],
            "django": [("2.1.0", "CVE-2019-19844", "CRITICAL", "Account takeover via password reset")],
            "flask": [("0.12.2", "CVE-2018-1000656", "HIGH", "JSON encoding vulnerability")],
            "pillow": [("5.2.0", "CVE-2019-16865", "HIGH", "Buffer overflow in image processing")],
        }
        req_files = ["requirements.txt", "requirements-dev.txt", "requirements-prod.txt"]
        for req_file in req_files:
            if os.path.exists(req_file):
                try:
                    with open(req_file, "r") as f:
                        lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        match = re.match(r"^([a-zA-Z0-9_-]+)([<>=!~]+)?([0-9.]+)?", line)
                        if match:
                            pkg_name = match.group(1).lower()
                            version = match.group(3)
                            if pkg_name in known_bad and version:
                                for bad_version, cve, severity, desc in known_bad[pkg_name]:
                                    if version <= bad_version:
                                        findings.append(SecurityFinding(
                                            severity=severity,
                                            category="vulnerable_dependency",
                                            title=f"Vulnerable Dependency: {pkg_name}@{version}",
                                            description=f"{pkg_name} version {version} is affected by {cve}: {desc}",
                                            resource=req_file,
                                            recommendation=f"Upgrade {pkg_name} to a patched version immediately",
                                            timestamp=datetime.utcnow().isoformat(),
                                            evidence={"package": pkg_name, "version": version, "cve": cve, "file": req_file}
                                        ))
                except Exception as e:
                    logger.warning(f"Failed to scan {req_file}: {e}")
        return findings

    async def _check_outdated_packages(self) -> List[SecurityFinding]:
        return []


class DeploymentMonitor(BaseMonitor):
    """Monitor deployments for unauthorized or suspicious changes."""

    def get_interval(self) -> int:
        return self.config.deployment_check_interval

    async def scan(self) -> List[SecurityFinding]:
        findings = []
        findings.extend(self._monitor_critical_files())
        findings.extend(self._monitor_processes())
        return findings

    def _monitor_critical_files(self) -> List[SecurityFinding]:
        findings = []
        critical_files = [
            "start.sh", "requirements.txt", "Dockerfile", ".github/workflows/deploy.yml",
            "docker-compose.yml", "main.py", "app.py", "config.py"
        ]
        state_file = Path(self.config.state_file)
        known_hashes = {}
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                known_hashes = state.get("file_hashes", {})
            except Exception:
                pass
        current_hashes = {}
        for filepath in critical_files:
            if os.path.exists(filepath):
                content = Path(filepath).read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()[:16]
                current_hashes[filepath] = file_hash
                if filepath in known_hashes and known_hashes[filepath] != file_hash:
                    findings.append(SecurityFinding(
                        severity="CRITICAL",
                        category="unauthorized_file_change",
                        title=f"Critical File Modified: {filepath}",
                        description=f"File '{filepath}' was modified since last known state",
                        resource=filepath,
                        recommendation="Review the changes immediately. If unauthorized, revert and investigate.",
                        timestamp=datetime.utcnow().isoformat(),
                        evidence={"file": filepath, "previous_hash": known_hashes[filepath], "current_hash": file_hash}
                    ))
        state = {"file_hashes": current_hashes, "last_scan": datetime.utcnow().isoformat()}
        if state_file.exists():
            try:
                existing = json.loads(state_file.read_text())
                existing.update(state)
                state = existing
            except Exception:
                pass
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2))
        return findings

    def _monitor_processes(self) -> List[SecurityFinding]:
        findings = []
        try:
            import psutil
            suspicious_names = ["nc", "netcat", "nmap", "masscan", "miner", "xmrig", "crypto"]
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info.get('name', '')
                    cmdline = ' '.join(proc.info.get('cmdline', []) or [])
                    if any(s in name.lower() or s in cmdline.lower() for s in suspicious_names):
                        findings.append(SecurityFinding(
                            severity="CRITICAL",
                            category="suspicious_process",
                            title=f"Suspicious Process Detected: {name}",
                            description=f"Process matching suspicious patterns was detected",
                            resource=f"process:{proc.info.get('pid')}",
                            recommendation="Investigate immediately. Kill process if unauthorized.",
                            timestamp=datetime.utcnow().isoformat(),
                            evidence={"pid": proc.info.get('pid'), "name": name, "cmdline": cmdline[:200]}
                        ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            logger.warning("psutil not installed — process monitoring disabled")
        return findings
