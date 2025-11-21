"""
Unit Tests for OWASP LLM06 Agent Permission Manager

Tests comprehensive permission control, rate limiting, and audit logging
for the AgentPermissionManager component.
"""

import pytest
import time
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_pipeline.security.llm06_excessive_agency.agent_permission_manager import (
    AgentPermissionManager,
    PermissionPolicy,
    OperationType,
    ApprovalLevel
)


class TestAgentPermissionManager:
    """Test suite for AgentPermissionManager LLM06 mitigation"""

    @pytest.fixture
    def permission_manager(self):
        """Create fresh permission manager for each test"""
        pm = AgentPermissionManager(enable_metrics=True, strict_mode=False)
        # Disable rate limiting for unit tests
        for policy in pm.policies.values():
            policy.rate_limit_seconds = 0.0
        return pm

    @pytest.fixture
    def strict_permission_manager(self):
        """Create strict mode permission manager"""
        pm = AgentPermissionManager(enable_metrics=True, strict_mode=True)
        # Disable rate limiting for unit tests
        for policy in pm.policies.values():
            policy.rate_limit_seconds = 0.0
        return pm

    @pytest.fixture
    def permission_manager_with_rate_limiting(self):
        """Create permission manager with rate limiting enabled for rate limit tests"""
        return AgentPermissionManager(enable_metrics=True, strict_mode=False)

    # ===== Policy Tests =====

    def test_default_policies_exist(self, permission_manager):
        """Test that default policies are created for known agents"""
        analysis_policy = permission_manager.get_policy("analysis_agent")
        query_policy = permission_manager.get_policy("query_agent")

        assert analysis_policy is not None
        assert query_policy is not None
        assert analysis_policy.agent_id == "analysis_agent"
        assert query_policy.agent_id == "query_agent"

    def test_analysis_agent_policy_constraints(self, permission_manager):
        """Test that analysis agent has correct read-only constraints"""
        policy = permission_manager.get_policy("analysis_agent")

        # Should allow read and execute
        assert OperationType.READ in policy.allowed_operations
        assert OperationType.EXECUTE in policy.allowed_operations

        # Should forbid write, delete, external API
        assert OperationType.WRITE in policy.forbidden_operations
        assert OperationType.DELETE in policy.forbidden_operations
        assert OperationType.EXTERNAL_API in policy.forbidden_operations

        # Should only have AnalysisTool
        assert "AnalysisTool" in policy.allowed_tools
        assert len(policy.allowed_tools) == 1

    def test_query_agent_policy_constraints(self, permission_manager):
        """Test that query agent has correct query-focused constraints"""
        policy = permission_manager.get_policy("query_agent")

        # Should allow read, database query, search, external API
        assert OperationType.READ in policy.allowed_operations
        assert OperationType.DATABASE_QUERY in policy.allowed_operations
        assert OperationType.SEARCH in policy.allowed_operations
        assert OperationType.EXTERNAL_API in policy.allowed_operations

        # Should forbid write and delete
        assert OperationType.WRITE in policy.forbidden_operations
        assert OperationType.DELETE in policy.forbidden_operations

        # Should have multiple query tools
        assert "QueryTool" in policy.allowed_tools
        assert "WikipediaQueryRun" in policy.allowed_tools
        assert "DuckDuckGoSearchRun" in policy.allowed_tools

    def test_custom_policy_creation(self, permission_manager):
        """Test adding custom permission policy"""
        custom_policy = PermissionPolicy(
            agent_id="custom_agent",
            allowed_tools={"CustomTool"},
            allowed_operations={OperationType.READ},
            forbidden_operations={OperationType.WRITE, OperationType.DELETE},
            max_tool_calls_per_session=50
        )

        permission_manager.add_policy(custom_policy)
        retrieved_policy = permission_manager.get_policy("custom_agent")

        assert retrieved_policy is not None
        assert retrieved_policy.agent_id == "custom_agent"
        assert "CustomTool" in retrieved_policy.allowed_tools

    # ===== Permission Check Tests =====

    def test_allowed_tool_access(self, permission_manager):
        """Test that allowed tools are permitted"""
        allowed, reason = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )

        assert allowed is True
        assert reason == "Permission granted"

    def test_forbidden_tool_access(self, permission_manager):
        """Test that forbidden tools are denied"""
        allowed, reason = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="WikipediaQueryRun",  # Not in allowed tools
            operation=OperationType.READ
        )

        assert allowed is False
        assert "not in allowed tools" in reason

    def test_forbidden_operation_type(self, permission_manager):
        """Test that forbidden operations are denied"""
        allowed, reason = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.WRITE  # Forbidden for analysis agent
        )

        assert allowed is False
        assert "explicitly forbidden" in reason

    def test_unknown_agent_denied(self, permission_manager):
        """Test that unknown agents are denied access"""
        allowed, reason = permission_manager.check_permission(
            agent_id="unknown_agent",
            tool_name="AnyTool",
            operation=OperationType.READ
        )

        assert allowed is False
        assert "No permission policy found" in reason

    # ===== Rate Limiting Tests =====

    def test_rate_limiting_session_limit(self, permission_manager):
        """Test that session limits are enforced"""
        policy = permission_manager.get_policy("analysis_agent")
        max_calls = policy.max_tool_calls_per_session

        # Make exactly max_calls requests (should all succeed)
        for i in range(max_calls):
            allowed, _ = permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )
            assert allowed is True

        # Next request should fail due to session limit
        allowed, reason = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )

        assert allowed is False
        assert "Rate limit exceeded" in reason or "exceeded session limit" in reason.lower()

    def test_rate_limiting_time_based(self, permission_manager_with_rate_limiting):
        """Test that time-based rate limiting works"""
        permission_manager = permission_manager_with_rate_limiting
        # Reset session to ensure clean state
        permission_manager.reset_session()

        policy = permission_manager.get_policy("analysis_agent")
        rate_limit = policy.rate_limit_seconds

        # First call should succeed
        allowed1, _ = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )
        assert allowed1 is True

        # Immediate second call should fail
        allowed2, reason2 = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )
        assert allowed2 is False
        assert "Rate limit" in reason2 or "rate limit" in reason2.lower()

        # After waiting, should succeed
        time.sleep(rate_limit + 0.1)
        allowed3, _ = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )
        assert allowed3 is True

    def test_session_reset(self, permission_manager):
        """Test that session reset clears counters"""
        # Make some requests
        for _ in range(5):
            permission_manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )
            time.sleep(0.1)

        # Reset session
        permission_manager.reset_session("analysis_agent")

        # Should be able to make requests again without rate limit issues
        allowed, _ = permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )
        assert allowed is True

    # ===== Audit Logging Tests =====

    def test_audit_log_captures_allowed(self, permission_manager):
        """Test that allowed operations are logged"""
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ,
            context={"test": "allowed_operation"}
        )

        audit_log = permission_manager.get_audit_log(
            agent_id="analysis_agent",
            result_filter="allowed"
        )

        assert len(audit_log) > 0
        entry = audit_log[-1]
        assert entry.agent_id == "analysis_agent"
        assert entry.tool_name == "AnalysisTool"
        assert entry.result == "allowed"

    def test_audit_log_captures_denied(self, permission_manager):
        """Test that denied operations are logged"""
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="ForbiddenTool",
            operation=OperationType.WRITE,
            context={"test": "denied_operation"}
        )

        audit_log = permission_manager.get_audit_log(
            agent_id="analysis_agent",
            result_filter="denied"
        )

        assert len(audit_log) > 0
        entry = audit_log[-1]
        assert entry.agent_id == "analysis_agent"
        assert entry.result == "denied"
        assert "ForbiddenTool" in entry.tool_name or "WRITE" in entry.operation

    def test_audit_log_filtering(self, permission_manager):
        """Test audit log filtering by agent and result"""
        # Make mixed allowed and denied requests
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )
        time.sleep(0.1)
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="ForbiddenTool",
            operation=OperationType.WRITE
        )

        # Get all entries for analysis_agent
        all_entries = permission_manager.get_audit_log(agent_id="analysis_agent")
        allowed_entries = permission_manager.get_audit_log(
            agent_id="analysis_agent",
            result_filter="allowed"
        )
        denied_entries = permission_manager.get_audit_log(
            agent_id="analysis_agent",
            result_filter="denied"
        )

        assert len(all_entries) >= 2
        assert len(allowed_entries) >= 1
        assert len(denied_entries) >= 1

    # ===== Metrics Tests =====

    def test_metrics_collection(self, permission_manager):
        """Test that metrics are collected correctly"""
        # Make some requests
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="AnalysisTool",
            operation=OperationType.READ
        )
        time.sleep(0.1)
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="ForbiddenTool",
            operation=OperationType.WRITE
        )

        metrics = permission_manager.get_metrics()

        assert metrics["total_permission_checks"] >= 2
        assert metrics["allowed"] >= 1
        assert metrics["denied"] >= 1
        assert "denial_rate" in metrics
        assert 0 <= metrics["denial_rate"] <= 1

    def test_violation_tracking(self, permission_manager):
        """Test that violations are tracked by agent and tool"""
        # Cause a violation
        permission_manager.check_permission(
            agent_id="analysis_agent",
            tool_name="ForbiddenTool",
            operation=OperationType.WRITE
        )

        metrics = permission_manager.get_metrics()

        assert "analysis_agent" in metrics["violations_by_agent"]
        assert metrics["violations_by_agent"]["analysis_agent"] >= 1
        assert "ForbiddenTool" in metrics["violations_by_tool"]

    # ===== Approval Workflow Tests =====

    def test_approval_requirement_logging(self, permission_manager):
        """Test that approval requirements are logged"""
        # DuckDuckGoSearchRun requires LOGGING approval for query_agent
        allowed, _ = permission_manager.check_permission(
            agent_id="query_agent",
            tool_name="DuckDuckGoSearchRun",
            operation=OperationType.SEARCH
        )

        assert allowed is True  # Still allowed, just logged
        metrics = permission_manager.get_metrics()
        assert metrics["approval_requests"] >= 1

    # ===== Strict Mode Tests =====

    def test_strict_mode_reduces_limits(self):
        """Test that strict mode applies stricter limits"""
        # Create fresh managers without rate limiting disabled for this comparison
        normal_manager = AgentPermissionManager(enable_metrics=True, strict_mode=False)
        strict_manager = AgentPermissionManager(enable_metrics=True, strict_mode=True)

        strict_policy = strict_manager.get_policy("analysis_agent")
        normal_policy = normal_manager.get_policy("analysis_agent")

        # Strict mode should have lower limits
        assert strict_policy.max_tool_calls_per_session < normal_policy.max_tool_calls_per_session
        assert strict_policy.rate_limit_seconds > normal_policy.rate_limit_seconds


# ===== Integration Tests =====

class TestPermissionManagerIntegration:
    """Integration tests for permission manager in realistic scenarios"""

    def test_multi_agent_isolation(self):
        """Test that different agents have isolated rate limits"""
        manager = AgentPermissionManager(enable_metrics=True)
        # Disable rate limiting for fast test execution
        for policy in manager.policies.values():
            policy.rate_limit_seconds = 0.0

        # analysis_agent makes requests
        for _ in range(5):
            manager.check_permission(
                agent_id="analysis_agent",
                tool_name="AnalysisTool",
                operation=OperationType.READ
            )

        # query_agent should still be able to make requests (tests isolation)
        allowed, _ = manager.check_permission(
            agent_id="query_agent",
            tool_name="QueryTool",
            operation=OperationType.DATABASE_QUERY
        )

        assert allowed is True

    def test_realistic_workflow_simulation(self):
        """Test a realistic workflow with multiple agents"""
        manager = AgentPermissionManager(enable_metrics=True)
        # Disable rate limiting for fast test execution
        for policy in manager.policies.values():
            policy.rate_limit_seconds = 0.0

        # Simulate analysis workflow
        operations = [
            ("analysis_agent", "AnalysisTool", OperationType.READ),
            ("analysis_agent", "AnalysisTool", OperationType.EXECUTE),
            ("query_agent", "QueryTool", OperationType.DATABASE_QUERY),
            ("query_agent", "WikipediaQueryRun", OperationType.SEARCH),
            ("query_agent", "DuckDuckGoSearchRun", OperationType.SEARCH),
        ]

        success_count = 0
        for agent_id, tool_name, operation in operations:
            allowed, _ = manager.check_permission(
                agent_id=agent_id,
                tool_name=tool_name,
                operation=operation
            )
            if allowed:
                success_count += 1

        # All legitimate operations should succeed
        assert success_count == len(operations)

        # Verify metrics
        metrics = manager.get_metrics()
        assert metrics["total_permission_checks"] >= len(operations)
        assert metrics["allowed"] >= success_count


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
