"""
Excessive Agency Monitoring and Detection System

Monitors agent behavior for anomalous patterns that may indicate
excessive agency violations or security issues. Part of OWASP LLM06:2025 mitigation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .agent_permission_manager import AgentPermissionManager

logger = logging.getLogger(__name__)


@dataclass
class SecurityAnomaly:
    """Data class for detected security anomalies"""
    anomaly_type: str
    severity: str  # "low", "medium", "high", "critical"
    agent_id: str
    description: str
    metrics: Dict[str, Any]
    timestamp: str
    recommendation: str


class ExcessiveAgencyMonitor:
    """
    Monitor and detect excessive agency patterns in agent behavior

    Analyzes permission system data to identify:
    1. Repeated permission violations (potential attack or misconfiguration)
    2. Excessive tool usage (potential abuse or runaway agent)
    3. Unusual access patterns (deviation from normal behavior)
    4. Rate limit violations (potential DOS or abuse)

    Provides security insights for research and production monitoring.

    Example Usage:
        ```python
        permission_manager = AgentPermissionManager()
        monitor = ExcessiveAgencyMonitor(permission_manager)

        # After some agent activity...
        anomalies = monitor.detect_anomalies()

        for anomaly in anomalies:
            if anomaly.severity in ["high", "critical"]:
                alert_security_team(anomaly)
        ```
    """

    def __init__(
        self,
        permission_manager: AgentPermissionManager,
        enable_metrics: bool = True
    ):
        """
        Initialize the Excessive Agency Monitor

        Args:
            permission_manager: Permission manager instance to monitor
            enable_metrics: Whether to collect monitoring metrics
        """
        self.permission_manager = permission_manager
        self.enable_metrics = enable_metrics
        self.logger = logging.getLogger(__name__)
        self.detection_history: List[SecurityAnomaly] = []

        # Anomaly detection thresholds
        self.thresholds = {
            "repeated_violations": 5,  # Number of violations to trigger alert
            "excessive_tool_usage_percent": 80,  # % of max calls
            "high_denial_rate": 0.3,  # 30% denial rate is concerning
            "critical_denial_rate": 0.5,  # 50% denial rate is critical
            "rate_limit_violations": 3  # Number of rate limit hits
        }

        self.logger.info("ExcessiveAgencyMonitor initialized")

    def detect_anomalies(self) -> List[SecurityAnomaly]:
        """
        Detect anomalies in agent permission patterns

        Analyzes current permission metrics to identify security concerns.
        Returns list of detected anomalies sorted by severity.

        Returns:
            List of SecurityAnomaly objects, sorted by severity
        """
        anomalies: List[SecurityAnomaly] = []
        metrics = self.permission_manager.get_metrics()

        # Check 1: Repeated permission violations by agent
        anomalies.extend(self._detect_repeated_violations(metrics))

        # Check 2: Excessive tool usage (approaching limits)
        anomalies.extend(self._detect_excessive_tool_usage(metrics))

        # Check 3: High denial rates
        anomalies.extend(self._detect_high_denial_rate(metrics))

        # Check 4: Specific tool targeting (unusual patterns)
        anomalies.extend(self._detect_tool_targeting(metrics))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 4))

        # Store in history
        self.detection_history.extend(anomalies)

        if anomalies:
            self.logger.warning(
                "Detected %d security anomalies: %s",
                len(anomalies),
                [f"{a.anomaly_type}({a.severity})" for a in anomalies]
            )

        return anomalies

    def _detect_repeated_violations(
        self,
        metrics: Dict[str, Any]
    ) -> List[SecurityAnomaly]:
        """Detect agents with repeated permission violations"""
        anomalies = []
        violations_by_agent = metrics.get("violations_by_agent", {})

        for agent_id, violation_count in violations_by_agent.items():
            if violation_count >= self.thresholds["repeated_violations"]:
                # Determine severity based on violation count
                if violation_count >= 20:
                    severity = "critical"
                elif violation_count >= 10:
                    severity = "high"
                else:
                    severity = "medium"

                anomalies.append(SecurityAnomaly(
                    anomaly_type="repeated_violations",
                    severity=severity,
                    agent_id=agent_id,
                    description=(
                        f"Agent '{agent_id}' has {violation_count} permission violations. "
                        f"This may indicate an attack attempt or misconfiguration."
                    ),
                    metrics={"violation_count": violation_count},
                    timestamp=datetime.now().isoformat(),
                    recommendation=(
                        f"Review permission policy for '{agent_id}'. "
                        f"Check audit log for violation patterns. "
                        f"Consider temporarily disabling agent if suspected attack."
                    )
                ))

        return anomalies

    def _detect_excessive_tool_usage(
        self,
        metrics: Dict[str, Any]
    ) -> List[SecurityAnomaly]:
        """Detect agents approaching tool usage limits"""
        anomalies = []
        tool_call_stats = metrics.get("tool_call_stats", {})

        for agent_id, stats in tool_call_stats.items():
            call_count = stats.get("count", 0)

            # Get agent policy to check against limit
            policy = self.permission_manager.get_policy(agent_id)
            if not policy:
                continue

            usage_percent = (call_count / policy.max_tool_calls_per_session) * 100

            if usage_percent >= self.thresholds["excessive_tool_usage_percent"]:
                # Determine severity
                if usage_percent >= 95:
                    severity = "high"
                elif usage_percent >= 90:
                    severity = "medium"
                else:
                    severity = "low"

                anomalies.append(SecurityAnomaly(
                    anomaly_type="excessive_tool_usage",
                    severity=severity,
                    agent_id=agent_id,
                    description=(
                        f"Agent '{agent_id}' has used {call_count}/{policy.max_tool_calls_per_session} "
                        f"({usage_percent:.1f}%) of allowed tool calls. "
                        f"May indicate runaway agent or abuse."
                    ),
                    metrics={
                        "call_count": call_count,
                        "limit": policy.max_tool_calls_per_session,
                        "usage_percent": usage_percent
                    },
                    timestamp=datetime.now().isoformat(),
                    recommendation=(
                        f"Monitor '{agent_id}' closely. "
                        f"Consider resetting session if approaching limit. "
                        f"Review agent logic for infinite loops."
                    )
                ))

        return anomalies

    def _detect_high_denial_rate(
        self,
        metrics: Dict[str, Any]
    ) -> List[SecurityAnomaly]:
        """Detect unusually high denial rates"""
        anomalies = []
        denial_rate = metrics.get("denial_rate", 0)
        total_checks = metrics.get("total_permission_checks", 0)

        # Only check if we have enough data
        if total_checks < 10:
            return anomalies

        severity = None
        if denial_rate >= self.thresholds["critical_denial_rate"]:
            severity = "critical"
        elif denial_rate >= self.thresholds["high_denial_rate"]:
            severity = "high"

        if severity:
            anomalies.append(SecurityAnomaly(
                anomaly_type="high_denial_rate",
                severity=severity,
                agent_id="system",
                description=(
                    f"System-wide denial rate is {denial_rate:.1%} "
                    f"({metrics['denied']}/{total_checks} checks). "
                    f"This may indicate misconfigured permissions or attack activity."
                ),
                metrics={
                    "denial_rate": denial_rate,
                    "total_denied": metrics["denied"],
                    "total_checks": total_checks
                },
                timestamp=datetime.now().isoformat(),
                recommendation=(
                    "Review permission policies for all agents. "
                    "Check audit log for common denial reasons. "
                    "Ensure agent tool sets match permission policies."
                )
            ))

        return anomalies

    def _detect_tool_targeting(
        self,
        metrics: Dict[str, Any]
    ) -> List[SecurityAnomaly]:
        """Detect unusual targeting of specific tools"""
        anomalies = []
        violations_by_tool = metrics.get("violations_by_tool", {})

        for tool_name, violation_count in violations_by_tool.items():
            # Flag tools with many violations
            if violation_count >= 5:
                severity = "high" if violation_count >= 10 else "medium"

                anomalies.append(SecurityAnomaly(
                    anomaly_type="tool_targeting",
                    severity=severity,
                    agent_id="system",
                    description=(
                        f"Tool '{tool_name}' has {violation_count} access violations. "
                        f"Agents are repeatedly trying to access unauthorized tool."
                    ),
                    metrics={"tool": tool_name, "violations": violation_count},
                    timestamp=datetime.now().isoformat(),
                    recommendation=(
                        f"Review why agents are targeting '{tool_name}'. "
                        f"Either add tool to agent permissions or fix agent logic. "
                        f"Check if tool name is being referenced incorrectly."
                    )
                ))

        return anomalies

    def generate_security_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive security report for LLM06

        Returns detailed analysis of permission system effectiveness,
        detected anomalies, and recommendations.

        Returns:
            Dictionary containing comprehensive security report
        """
        anomalies = self.detect_anomalies()
        metrics = self.permission_manager.get_metrics()
        audit_log = self.permission_manager.get_audit_log()

        # Count anomalies by severity
        anomaly_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for anomaly in anomalies:
            anomaly_counts[anomaly.severity] += 1

        # Generate recommendations
        recommendations = self._generate_recommendations(anomalies, metrics)

        report = {
            "report_type": "OWASP_LLM06_EXCESSIVE_AGENCY_SECURITY_REPORT",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_permission_checks": metrics.get("total_permission_checks", 0),
                "allowed": metrics.get("allowed", 0),
                "denied": metrics.get("denied", 0),
                "denial_rate": metrics.get("denial_rate", 0),
                "agents_monitored": len(metrics.get("agents_monitored", [])),
                "audit_log_entries": len(audit_log)
            },
            "anomalies": {
                "total_detected": len(anomalies),
                "by_severity": anomaly_counts,
                "details": [
                    {
                        "type": a.anomaly_type,
                        "severity": a.severity,
                        "agent": a.agent_id,
                        "description": a.description,
                        "recommendation": a.recommendation,
                        "metrics": a.metrics,
                        "timestamp": a.timestamp
                    }
                    for a in anomalies
                ]
            },
            "metrics": metrics,
            "recommendations": recommendations,
            "permission_effectiveness": self._calculate_effectiveness(metrics),
            "agent_behavior_analysis": self._analyze_agent_behavior(metrics)
        }

        return report

    def _generate_recommendations(
        self,
        anomalies: List[SecurityAnomaly],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable security recommendations"""
        recommendations = []

        # Add anomaly-specific recommendations
        for anomaly in anomalies:
            if anomaly.severity in ["critical", "high"]:
                recommendations.append(anomaly.recommendation)

        # General recommendations based on metrics
        denial_rate = metrics.get("denial_rate", 0)
        if denial_rate > 0.1:
            recommendations.append(
                "Consider reviewing agent permission policies - "
                f"{denial_rate:.1%} denial rate suggests misalignment."
            )

        if metrics.get("approval_requests", 0) > 0:
            recommendations.append(
                f"{metrics['approval_requests']} operations required approval - "
                "review if approval thresholds are appropriate."
            )

        if not recommendations:
            recommendations.append(
                "No critical issues detected. System operating within normal parameters."
            )

        return recommendations

    def _calculate_effectiveness(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate effectiveness of permission system"""
        total_checks = metrics.get("total_permission_checks", 0)

        if total_checks == 0:
            return {"status": "insufficient_data"}

        return {
            "permission_enforcement_active": True,
            "total_checks": total_checks,
            "violation_prevention_rate": metrics.get("denial_rate", 0),
            "status": "active" if total_checks > 0 else "inactive",
            "agents_protected": len(metrics.get("agents_monitored", []))
        }

    def _analyze_agent_behavior(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent behavior patterns"""
        violations_by_agent = metrics.get("violations_by_agent", {})
        tool_call_stats = metrics.get("tool_call_stats", {})

        agent_analysis = {}

        for agent_id in metrics.get("agents_monitored", []):
            violations = violations_by_agent.get(agent_id, 0)
            tool_calls = tool_call_stats.get(agent_id, {}).get("count", 0)

            policy = self.permission_manager.get_policy(agent_id)

            agent_analysis[agent_id] = {
                "violations": violations,
                "tool_calls": tool_calls,
                "max_tool_calls": policy.max_tool_calls_per_session if policy else "unknown",
                "behavior_status": "compliant" if violations < 3 else "concerning",
                "risk_level": self._calculate_agent_risk_level(violations, tool_calls)
            }

        return agent_analysis

    def _calculate_agent_risk_level(
        self,
        violations: int,
        tool_calls: int
    ) -> str:
        """Calculate risk level for an agent"""
        if violations >= 10:
            return "high"
        elif violations >= 5:
            return "medium"
        elif violations >= 3 or tool_calls > 80:
            return "low"
        else:
            return "minimal"

    def get_detection_history(self) -> List[SecurityAnomaly]:
        """Get history of all detected anomalies"""
        return self.detection_history

    def clear_history(self) -> None:
        """Clear detection history"""
        self.detection_history = []
        self.logger.info("Cleared anomaly detection history")
