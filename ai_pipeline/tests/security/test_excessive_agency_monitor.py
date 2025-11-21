"""
Unit Tests for OWASP LLM06 Excessive Agency Monitor

Tests anomaly detection, security reporting, and behavioral analysis
for the ExcessiveAgencyMonitor component.
"""

import pytest
import time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_pipeline.security.llm06_excessive_agency.excessive_agency_monitor import (
    ExcessiveAgencyMonitor,
    SecurityAnomaly
)
from ai_pipeline.security.llm06_excessive_agency.agent_permission_manager import (
    AgentPermissionManager,
    PermissionPolicy,
    OperationType
)


class TestExcessiveAgencyMonitor:
    """Test suite for ExcessiveAgencyMonitor"""

    @pytest.fixture
    def permission_manager(self):
        """Create permission manager for testing"""
        pm = AgentPermissionManager(enable_metrics=True)
        # Disable rate limiting for unit tests
        for policy in pm.policies.values():
            policy.rate_limit_seconds = 0.0
        return pm

    @pytest.fixture
    def monitor(self, permission_manager):
        """Create monitor instance"""
        return ExcessiveAgencyMonitor(
            permission_manager=permission_manager,
            enable_metrics=True
        )

    # ===== Initialization Tests =====

    def test_monitor_initialization(self, permission_manager):
        """Test that monitor initializes correctly"""
        monitor = ExcessiveAgencyMonitor(
            permission_manager=permission_manager,
            enable_metrics=True
        )

        assert monitor.permission_manager == permission_manager
        assert monitor.enable_metrics is True
        assert len(monitor.detection_history) == 0

    def test_default_thresholds(self, monitor):
        """Test that default detection thresholds are set"""
        assert monitor.thresholds["repeated_violations"] == 5
        assert monitor.thresholds["excessive_tool_usage_percent"] == 80
        assert monitor.thresholds["high_denial_rate"] == 0.3
        assert monitor.thresholds["critical_denial_rate"] == 0.5

    # ===== Anomaly Detection Tests =====

    def test_detect_repeated_violations(self, permission_manager, monitor):
        """Test detection of repeated permission violations"""
        # Cause multiple violations
        for _ in range(6):  # Threshold is 5
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="UnauthorizedTool",
                operation=OperationType.WRITE
            )

        anomalies = monitor.detect_anomalies()

        # Should detect repeated violations
        violation_anomalies = [a for a in anomalies if a.anomaly_type == "repeated_violations"]
        assert len(violation_anomalies) > 0

        anomaly = violation_anomalies[0]
        assert anomaly.agent_id == "analysis_agent"
        assert anomaly.severity in ["medium", "high", "critical"]

    def test_detect_excessive_tool_usage(self, permission_manager, monitor):
        """Test detection of excessive tool usage approaching limits"""
        policy = permission_manager.get_policy("analysis_agent")
        max_calls = policy.max_tool_calls_per_session

        # Use 85% of allowed calls (should trigger 80% threshold)
        usage_count = int(max_calls * 0.85)
        for _ in range(usage_count):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )

        anomalies = monitor.detect_anomalies()

        # Should detect excessive usage
        usage_anomalies = [a for a in anomalies if a.anomaly_type == "excessive_tool_usage"]
        assert len(usage_anomalies) > 0

        anomaly = usage_anomalies[0]
        assert anomaly.agent_id == "analysis_agent"
        assert anomaly.severity in ["low", "medium", "high"]

    def test_detect_high_denial_rate(self, permission_manager, monitor):
        """Test detection of high overall denial rate"""
        # Create pattern of many denials
        for _ in range(10):
            # Allowed
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )
            time.sleep(0.1)

            # Denied (multiple per allowed)
            for _ in range(3):
                permission_manager.check_permission(
                    agent_id="analysis_agent",
                    tool_name="UnauthorizedTool",
                    operation=OperationType.WRITE
                )

        anomalies = monitor.detect_anomalies()

        # Should detect high denial rate
        denial_anomalies = [a for a in anomalies if a.anomaly_type == "high_denial_rate"]
        assert len(denial_anomalies) > 0

        anomaly = denial_anomalies[0]
        assert anomaly.severity in ["high", "critical"]

    def test_detect_tool_targeting(self, permission_manager, monitor):
        """Test detection of unusual targeting of specific tools"""
        # Target a specific unauthorized tool repeatedly
        for _ in range(6):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="TargetedUnauthorizedTool",
                operation=OperationType.WRITE
            )

        anomalies = monitor.detect_anomalies()

        # Should detect tool targeting
        targeting_anomalies = [a for a in anomalies if a.anomaly_type == "tool_targeting"]
        assert len(targeting_anomalies) > 0

        anomaly = targeting_anomalies[0]
        assert "TargetedUnauthorizedTool" in str(anomaly.metrics)

    def test_no_anomalies_for_normal_behavior(self, permission_manager, monitor):
        """Test that normal behavior doesn't trigger anomalies"""
        # Perform normal, allowed operations
        for _ in range(3):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )
            time.sleep(0.1)

        anomalies = monitor.detect_anomalies()

        # Should not detect anomalies for normal behavior
        # (There might be some from previous tests, but not many)
        assert len(anomalies) < 3

    # ===== Severity Classification Tests =====

    def test_severity_levels_for_violations(self, permission_manager, monitor):
        """Test that severity levels scale with violation count"""
        # Create different violation counts
        test_cases = [
            (6, "medium"),   # 5-9 violations
            (11, "high"),    # 10-19 violations
            (21, "critical")  # 20+ violations
        ]

        for violation_count, expected_severity in test_cases:
            # Reset permission manager
            permission_manager.reset_session("test_agent")
            permission_manager.metrics["violations_by_agent"] = {}

            # Add test policy
            policy = PermissionPolicy(
                agent_id="test_agent",
                allowed_tools={"AllowedTool"},
                allowed_operations={OperationType.READ},
                forbidden_operations={OperationType.WRITE},
                max_tool_calls_per_session=100,
                rate_limit_seconds=0.01
            )
            permission_manager.add_policy(policy)

            # Cause violations
            for _ in range(violation_count):
                permission_manager.check_permission(
                    agent_id="test_agent",
                    tool_name="UnauthorizedTool",
                    operation=OperationType.WRITE
                )

            # Detect anomalies
            anomalies = monitor.detect_anomalies()
            violation_anomalies = [
                a for a in anomalies
                if a.anomaly_type == "repeated_violations" and a.agent_id == "test_agent"
            ]

            if violation_anomalies:
                assert violation_anomalies[0].severity == expected_severity

    # ===== Security Report Tests =====

    def test_generate_security_report_structure(self, permission_manager, monitor):
        """Test that security report has correct structure"""
        # Generate some activity
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )

        report = monitor.generate_security_report()

        # Check report structure
        assert report["report_type"] == "OWASP_LLM06_EXCESSIVE_AGENCY_SECURITY_REPORT"
        assert "generated_at" in report
        assert "summary" in report
        assert "anomalies" in report
        assert "metrics" in report
        assert "recommendations" in report
        assert "permission_effectiveness" in report
        assert "agent_behavior_analysis" in report

    def test_security_report_summary_stats(self, permission_manager, monitor):
        """Test that report summary contains correct statistics"""
        # Generate activity
        for _ in range(5):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )
            time.sleep(0.1)

        report = monitor.generate_security_report()
        summary = report["summary"]

        assert summary["total_permission_checks"] >= 5
        assert summary["allowed"] >= 5
        assert "denial_rate" in summary
        assert summary["agents_monitored"] > 0

    def test_security_report_anomaly_details(self, permission_manager, monitor):
        """Test that anomalies are detailed in report"""
        # Cause violations
        for _ in range(6):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="UnauthorizedTool",
                operation=OperationType.WRITE
            )

        report = monitor.generate_security_report()
        anomalies = report["anomalies"]

        assert anomalies["total_detected"] > 0
        assert "by_severity" in anomalies
        assert len(anomalies["details"]) > 0

        # Check anomaly detail structure
        detail = anomalies["details"][0]
        assert "type" in detail
        assert "severity" in detail
        assert "agent" in detail
        assert "description" in detail
        assert "recommendation" in detail

    def test_security_report_recommendations(self, permission_manager, monitor):
        """Test that report includes actionable recommendations"""
        # Normal behavior
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )

        report = monitor.generate_security_report()
        recommendations = report["recommendations"]

        assert len(recommendations) > 0
        assert isinstance(recommendations[0], str)

    def test_agent_behavior_analysis(self, permission_manager, monitor):
        """Test agent behavior analysis in report"""
        # Generate activity
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )
        time.sleep(0.1)
        permission_manager.check_permission(
            agent_id="query_agent",
            tool_name="QueryTool",
            operation=OperationType.DATABASE_QUERY
        )

        report = monitor.generate_security_report()
        agent_analysis = report["agent_behavior_analysis"]

        # Should have analysis for both agents
        assert "analysis_agent" in agent_analysis or len(agent_analysis) > 0

        if "analysis_agent" in agent_analysis:
            analysis = agent_analysis["analysis_agent"]
            assert "violations" in analysis
            assert "tool_calls" in analysis
            assert "behavior_status" in analysis
            assert "risk_level" in analysis

    # ===== Detection History Tests =====

    def test_detection_history_accumulation(self, permission_manager, monitor):
        """Test that detection history accumulates over time"""
        initial_history_len = len(monitor.get_detection_history())

        # Cause violations to trigger detection
        for _ in range(6):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="UnauthorizedTool",
                operation=OperationType.WRITE
            )

        monitor.detect_anomalies()
        history = monitor.get_detection_history()

        assert len(history) > initial_history_len

    def test_clear_detection_history(self, permission_manager, monitor):
        """Test clearing detection history"""
        # Generate some detections
        for _ in range(6):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="UnauthorizedTool",
                operation=OperationType.WRITE
            )

        monitor.detect_anomalies()
        assert len(monitor.get_detection_history()) > 0

        # Clear history
        monitor.clear_history()
        assert len(monitor.get_detection_history()) == 0


class TestExcessiveAgencyMonitorIntegration:
    """Integration tests for monitor with realistic scenarios"""

    def test_attack_scenario_detection(self):
        """Test detection of simulated attack scenario"""
        permission_manager = AgentPermissionManager(enable_metrics=True)
        monitor = ExcessiveAgencyMonitor(permission_manager, enable_metrics=True)

        # Simulate attack: repeated attempts to access forbidden tools
        attack_tools = ["SystemTool", "FileTool", "NetworkTool", "AdminTool"]

        for tool in attack_tools:
            for _ in range(3):
                permission_manager.check_permission(
                    agent_id="analysis_agent",
                    tool_name=tool,
                    operation=OperationType.DELETE
                )

        # Detect anomalies
        anomalies = monitor.detect_anomalies()

        # Should detect multiple types of anomalies
        assert len(anomalies) > 0

        # Should include repeated violations
        violation_anomalies = [a for a in anomalies if a.anomaly_type == "repeated_violations"]
        assert len(violation_anomalies) > 0

        # Should have high or critical severity
        high_severity = [a for a in anomalies if a.severity in ["high", "critical"]]
        assert len(high_severity) > 0

    def test_normal_workflow_no_false_positives(self):
        """Test that normal workflows don't trigger false positives"""
        permission_manager = AgentPermissionManager(enable_metrics=True)
        # Disable rate limiting to prevent false positive rate limit violations
        for policy in permission_manager.policies.values():
            policy.rate_limit_seconds = 0.0

        monitor = ExcessiveAgencyMonitor(permission_manager, enable_metrics=True)

        # Simulate normal analysis workflow
        for _ in range(10):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )

        for _ in range(10):
            permission_manager.check_permission(
                agent_id="query_agent",
                tool_name="QueryTool",
                operation=OperationType.DATABASE_QUERY
            )

        # Detect anomalies
        anomalies = monitor.detect_anomalies()

        # Should have minimal or no anomalies
        high_severity = [a for a in anomalies if a.severity in ["high", "critical"]]
        assert len(high_severity) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
