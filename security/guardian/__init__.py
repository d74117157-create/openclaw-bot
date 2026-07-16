"""
Security Guardian Agent for OpenClaw Superswarm
Monitors, audits, alerts, and protects the entire platform.
"""

__version__ = "1.0.0"
__author__ = "OpenClaw Security Team"

from .guardian import SecurityGuardian
from .monitors import (
    AccountActivityMonitor,
    OAuthAuditor,
    SecretScanner,
    DependencyVulnerabilityScanner,
    DeploymentMonitor
)
from .alerts import AlertManager
from .reporter import IncidentReporter

__all__ = [
    "SecurityGuardian",
    "AccountActivityMonitor",
    "OAuthAuditor", 
    "SecretScanner",
    "DependencyVulnerabilityScanner",
    "DeploymentMonitor",
    "AlertManager",
    "IncidentReporter",
]
