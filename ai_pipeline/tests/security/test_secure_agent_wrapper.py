"""
Unit Tests for OWASP LLM06 Secure Agent Executor

Tests the SecureAgentExecutor wrapper that adds transparent permission
enforcement to LangChain agents.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_pipeline.security.llm06_excessive_agency.secure_agent_wrapper import SecureAgentExecutor
from ai_pipeline.security.llm06_excessive_agency.agent_permission_manager import (
    AgentPermissionManager,
    PermissionPolicy,
    OperationType
)

try:
    from langchain.tools import BaseTool
    from langchain.agents import AgentExecutor, BaseSingleActionAgent
    from langchain_core.agents import AgentAction, AgentFinish
    from langchain.schema import AgentAction as LegacyAgentAction, AgentFinish as LegacyAgentFinish
    from typing import List, Tuple, Any, Union
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseTool = object
    BaseSingleActionAgent = object


# Minimal test agent implementation for LangChain compatibility
if LANGCHAIN_AVAILABLE:
    class MinimalTestAgent(BaseSingleActionAgent):
        """Minimal agent implementation for testing SecureAgentExecutor"""

        @property
        def input_keys(self) -> List[str]:
            return ["input"]

        def plan(
            self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any
        ) -> Union[AgentAction, AgentFinish]:
            """Return a simple finish action"""
            return AgentFinish(return_values={"output": "test response"}, log="test log")

        async def aplan(
            self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any
        ) -> Union[AgentAction, AgentFinish]:
            """Async version of plan"""
            return self.plan(intermediate_steps, **kwargs)


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
class TestSecureAgentExecutor:
    """Test suite for SecureAgentExecutor LLM06 wrapper"""

    class MockTool(BaseTool):
        """Mock tool for testing"""
        name: str = "MockTool"
        description: str = "Mock tool for testing"

        def _run(self, query: str) -> str:
            return f"MockTool executed: {query}"

        async def _arun(self, query: str) -> str:
            return self._run(query)

    @pytest.fixture
    def permission_manager(self):
        """Create permission manager with test policy"""
        manager = AgentPermissionManager(enable_metrics=True)

        # Disable rate limiting for all policies
        for policy in manager.policies.values():
            policy.rate_limit_seconds = 0.0

        # Add test policy
        test_policy = PermissionPolicy(
            agent_id="test_agent",
            allowed_tools={"MockTool"},
            allowed_operations={OperationType.READ, OperationType.EXECUTE},
            forbidden_operations={OperationType.WRITE, OperationType.DELETE},
            max_tool_calls_per_session=100,
            rate_limit_seconds=0.0  # No rate limiting for tests
        )
        manager.add_policy(test_policy)

        return manager

    @pytest.fixture
    def mock_agent(self):
        """Create minimal test LangChain agent"""
        return MinimalTestAgent()

    @pytest.fixture
    def mock_tool(self):
        """Create mock tool"""
        return self.MockTool()

    def test_executor_initialization(self, mock_agent, mock_tool, permission_manager):
        """Test that SecureAgentExecutor initializes correctly"""
        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[mock_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        assert executor.agent_id == "test_agent"
        assert executor.permission_manager == permission_manager
        assert len(executor.tools) == 1

    def test_tool_wrapping(self, mock_agent, mock_tool, permission_manager):
        """Test that tools are wrapped with permission checking"""
        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[mock_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Tool should still work (wrapping doesn't break functionality)
        wrapped_tool = executor.tools[0]
        result = wrapped_tool._run("test query")
        assert "MockTool executed" in result

        # Verify permission manager tracked the execution
        metrics = permission_manager.get_metrics()
        assert metrics["total_permission_checks"] > 0

    def test_allowed_tool_execution(self, mock_agent, mock_tool, permission_manager):
        """Test that allowed tools can execute"""
        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[mock_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Execute tool directly
        wrapped_tool = executor.tools[0]
        result = wrapped_tool._run("test query")

        # Should execute successfully
        assert "MockTool executed" in result
        assert "test query" in result

    def test_denied_tool_execution(self, mock_agent, permission_manager):
        """Test that denied tools are blocked"""
        # Create tool not in allowed list
        class UnauthorizedTool(BaseTool):
            name: str = "UnauthorizedTool"
            description: str = "Tool not in policy"

            def _run(self, query: str) -> str:
                return "Should not execute"

        unauthorized_tool = UnauthorizedTool()

        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[unauthorized_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Try to execute unauthorized tool
        wrapped_tool = executor.tools[0]
        result = wrapped_tool._run("test query")

        # Should be denied
        assert "PERMISSION DENIED" in result

    def test_operation_type_detection(self, mock_agent, permission_manager):
        """Test that operation types are correctly detected from tool names"""
        # Create tools with different name patterns
        class SearchTool(BaseTool):
            name: str = "DuckDuckGoSearchRun"
            description: str = "Search tool"

            def _run(self, query: str) -> str:
                return "search result"

        class DatabaseTool(BaseTool):
            name: str = "Neo4jQueryTool"
            description: str = "Database tool"

            def _run(self, query: str) -> str:
                return "db result"

        # Add policies that allow these operation types (no rate limiting for test)
        policy = PermissionPolicy(
            agent_id="test_agent_ops",
            allowed_tools={"DuckDuckGoSearchRun", "Neo4jQueryTool"},
            allowed_operations={
                OperationType.SEARCH,
                OperationType.DATABASE_QUERY,
                OperationType.READ
            },
            forbidden_operations={OperationType.WRITE, OperationType.DELETE},
            max_tool_calls_per_session=100,
            rate_limit_seconds=0.0  # No rate limiting for fast test execution
        )
        permission_manager.add_policy(policy)

        search_tool = SearchTool()
        db_tool = DatabaseTool()

        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[search_tool, db_tool],
            agent_id="test_agent_ops",
            permission_manager=permission_manager,
            verbose=True
        )

        # Verify operation types were detected correctly
        # (This is implicit - if wrong types were detected, permission would be denied)
        wrapped_search = executor.tools[0]
        wrapped_db = executor.tools[1]

        search_result = wrapped_search._run("search query")
        db_result = wrapped_db._run("db query")

        assert "PERMISSION DENIED" not in search_result
        assert "PERMISSION DENIED" not in db_result

    def test_get_permission_metrics(self, mock_agent, mock_tool, permission_manager):
        """Test that permission metrics can be retrieved"""
        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[mock_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Execute some operations
        wrapped_tool = executor.tools[0]
        wrapped_tool._run("query 1")

        # Get metrics
        metrics = executor.get_permission_metrics()

        assert "total_permission_checks" in metrics
        assert metrics["total_permission_checks"] >= 1

    def test_get_audit_log(self, mock_agent, mock_tool, permission_manager):
        """Test that audit log can be retrieved"""
        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[mock_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Execute some operations
        wrapped_tool = executor.tools[0]
        wrapped_tool._run("query 1")

        # Get audit log
        audit_log = executor.get_audit_log()

        assert len(audit_log) >= 1
        assert audit_log[0].agent_id == "test_agent"

    def test_session_reset(self, mock_agent, mock_tool, permission_manager):
        """Test that session can be reset"""
        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[mock_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Execute some operations
        wrapped_tool = executor.tools[0]
        for _ in range(5):
            wrapped_tool._run("query")

        # Reset session
        executor.reset_session()

        # Should be able to execute again without rate limit issues
        result = wrapped_tool._run("after reset")
        assert "PERMISSION DENIED" not in result

    @pytest.mark.asyncio
    async def test_async_tool_execution(self, mock_agent, mock_tool, permission_manager):
        """Test async tool execution with permission checking"""
        executor = SecureAgentExecutor(
            agent=mock_agent,
            tools=[mock_tool],
            agent_id="test_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Execute async
        wrapped_tool = executor.tools[0]
        result = await wrapped_tool._arun("async query")

        assert "MockTool executed" in result
        assert "async query" in result


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
class TestSecureAgentExecutorIntegration:
    """Integration tests for SecureAgentExecutor"""

    def test_multiple_tools_with_mixed_permissions(self):
        """Test multiple tools where some are allowed and some are denied"""
        permission_manager = AgentPermissionManager(enable_metrics=True)

        class AllowedTool(BaseTool):
            name: str = "AllowedTool"
            description: str = "Allowed"

            def _run(self, query: str) -> str:
                return "allowed result"

        class DeniedTool(BaseTool):
            name: str = "DeniedTool"
            description: str = "Denied"

            def _run(self, query: str) -> str:
                return "denied result"

        # Policy only allows AllowedTool
        policy = PermissionPolicy(
            agent_id="mixed_agent",
            allowed_tools={"AllowedTool"},
            allowed_operations={OperationType.READ},
            forbidden_operations=set(),
            max_tool_calls_per_session=100,
            rate_limit_seconds=0.1
        )
        permission_manager.add_policy(policy)

        # Use real MinimalTestAgent instead of MagicMock
        test_agent = MinimalTestAgent()
        executor = SecureAgentExecutor(
            agent=test_agent,
            tools=[AllowedTool(), DeniedTool()],
            agent_id="mixed_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Allowed tool should work
        allowed_result = executor.tools[0]._run("query")
        assert "PERMISSION DENIED" not in allowed_result

        # Denied tool should be blocked
        denied_result = executor.tools[1]._run("query")
        assert "PERMISSION DENIED" in denied_result

    def test_rate_limiting_enforcement(self):
        """Test that rate limiting is enforced through wrapper"""
        permission_manager = AgentPermissionManager(enable_metrics=True)

        class RateLimitedTool(BaseTool):
            name: str = "RateLimitedTool"
            description: str = "Rate limited"

            def _run(self, query: str) -> str:
                return f"result: {query}"

        # Policy with strict rate limit
        policy = PermissionPolicy(
            agent_id="rate_limited_agent",
            allowed_tools={"RateLimitedTool"},
            allowed_operations={OperationType.READ},
            forbidden_operations=set(),
            max_tool_calls_per_session=3,  # Very low limit
            rate_limit_seconds=0.1
        )
        permission_manager.add_policy(policy)

        # Use real MinimalTestAgent instead of MagicMock
        test_agent = MinimalTestAgent()
        executor = SecureAgentExecutor(
            agent=test_agent,
            tools=[RateLimitedTool()],
            agent_id="rate_limited_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        tool = executor.tools[0]

        # First 3 calls should succeed
        import time
        for i in range(3):
            result = tool._run(f"query {i}")
            assert "PERMISSION DENIED" not in result
            time.sleep(0.11)

        # 4th call should be denied due to session limit
        result = tool._run("query 4")
        assert "PERMISSION DENIED" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
