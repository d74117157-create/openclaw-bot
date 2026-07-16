"""
Security Guardian — Main orchestrator.
Runs all monitors on their configured schedules and distributes alerts.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List

from .config import GuardianConfig
from .monitors import (
    AccountActivityMonitor,
    OAuthAuditor,
    SecretScanner,
    DependencyVulnerabilityScanner,
    DeploymentMonitor
)
from .alerts import AlertManager
from .reporter import IncidentReporter

logger = logging.getLogger("guardian")


class SecurityGuardian:
    """
    Central security orchestrator for OpenClaw Superswarm.

    Usage:
        config = GuardianConfig()
        guardian = SecurityGuardian(config)
        await guardian.run_full_scan()
        await guardian.start_continuous_monitoring()
    """

    def __init__(self, config: GuardianConfig = None):
        self.config = config or GuardianConfig()
        self.monitors = [
            AccountActivityMonitor(self.config),
            OAuthAuditor(self.config),
            SecretScanner(self.config),
            DependencyVulnerabilityScanner(self.config),
            DeploymentMonitor(self.config)
        ]
        self.reporter = IncidentReporter(self.config)
        self._running = False
        issues = self.config.validate()
        for issue in issues:
            logger.warning(issue)

    async def run_full_scan(self) -> List:
        """Run all monitors immediately and return all findings."""
        logger.info("🛡️ Starting full security scan...")
        all_findings = []
        for monitor in self.monitors:
            findings = await monitor.run()
            all_findings.extend(findings)
        if all_findings:
            report_path = self.reporter.save_report(
                all_findings,
                title=f"Full Security Scan — {datetime.utcnow().isoformat()}"
            )
            logger.info(f"📄 Report saved: {report_path}")
        critical_findings = [f for f in all_findings if f.severity == "CRITICAL"]
        if critical_findings:
            async with AlertManager(self.config) as alert_mgr:
                for finding in critical_findings:
                    await alert_mgr.send_alert(finding)
        logger.info(f"🛡️ Full scan complete. {len(all_findings)} findings ({len(critical_findings)} critical)")
        return all_findings

    async def start_continuous_monitoring(self):
        """Start continuous monitoring loop."""
        self._running = True
        logger.info("🛡️ Security Guardian continuous monitoring started")
        last_runs = {monitor: datetime.min for monitor in self.monitors}
        while self._running:
            now = datetime.utcnow()
            all_findings = []
            for monitor in self.monitors:
                interval = monitor.get_interval()
                elapsed = (now - last_runs[monitor]).total_seconds()
                if elapsed >= interval:
                    findings = await monitor.run()
                    all_findings.extend(findings)
                    last_runs[monitor] = now
            if all_findings:
                critical = [f for f in all_findings if f.severity == "CRITICAL"]
                async with AlertManager(self.config) as alert_mgr:
                    if critical:
                        for finding in critical:
                            await alert_mgr.send_alert(finding)
                    else:
                        await alert_mgr.send_digest(all_findings)
            await asyncio.sleep(60)

    def stop(self):
        """Stop continuous monitoring."""
        self._running = False
        logger.info("🛡️ Security Guardian monitoring stopped")


async def main():
    """CLI entry point for Security Guardian."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    config = GuardianConfig()
    guardian = SecurityGuardian(config)
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        await guardian.start_continuous_monitoring()
    else:
        findings = await guardian.run_full_scan()
        sys.exit(1 if any(f.severity == "CRITICAL" for f in findings) else 0)


if __name__ == "__main__":
    asyncio.run(main())
