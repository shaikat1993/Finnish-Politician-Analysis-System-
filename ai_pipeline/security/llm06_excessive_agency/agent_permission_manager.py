"""
OWASP LLM06:2025 - Excessive Agency Prevention System

Implements comprehensive permission control and access management for LLM agents
to prevent excessive agency vulnerabilities in multi-agent systems.

This module addresses OWASP LLM06:2025 (Excessive Agency) by implementing:
1. Least-privilege access control for agent tools
2. Operation type restrictions (read/write/execute/delete)
3. Approval workflows for sensitive operations
4. Rate limiting to prevent abuse
5. Comprehensive audit logging
6. Permission policy enforcement

Reference: OWASP Top 10 for LLM Applications 2025
https://owasp.org/www-project-top-10-for-large-language-model-applications/
"""

import logging
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Types of operations that agents can perform"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    EXTERNAL_API = "external_api"
    DATABASE_QUERY = "database_query"
    DATABASE_WRITE = "database_write"
    SEARCH = "search"

class ApprovalLevel(Enum):
    """Approval requirements for operations"""
    NONE = "none"              # No approval needed
    LOGGING = "logging"        # Log but allow
    CONFIRMATION = "confirmation"  # Require confirmation (simulated for research)
    HUMAN = "human"            # Require human approval (simulated for research)
    BLOCKED = "blocked"        # Always blocked

@dataclass
class PermissionPolicy:
    """
    Permission policy for an LLM agent

    Implements least-privilege principle by explicitly defining:
    - Which tools the agent can access
    - What types of operations are allowed
    - Which operations require approval
    - Rate limits to prevent abuse
    """
    agent_id: str
    allowed_tools: Set[str]
    allowed_operations: Set[OperationType]
    forbidden_operations: Set[OperationType]
    approval_requirements: Dict[str, ApprovalLevel] = field(default_factory=dict)
    max_tool_calls_per_session: int = 100
    rate_limit_seconds: float = 0.5
    description: str = ""

@dataclass
class AuditEntry:
    """Audit log entry for permission checks"""
    timestamp: str
    agent_id: str
    tool_name: str
    operation: str
    result: str  # "allowed" or "denied"
    reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

class AgentPermissionManager:
    """
    OWASP LLM06:2025 - Excessive Agency Prevention System

    Manages and enforces permission policies for LLM agents to prevent
    excessive agency vulnerabilities. Implements defense-in-depth through:

    1. Tool Access Control: Restrict which tools each agent can use
    2. Operation Type Enforcement: Control what types of actions are permitted
    3. Approval Workflows: Require approval for sensitive operations
    4. Rate Limiting: Prevent abuse through frequency limits
    5. Audit Logging: Complete audit trail of all permission checks
    6. Metrics Collection: Track permission violations for research

    Example Usage:
        ```python
        manager = AgentPermissionManager(enable_metrics=True)

        # Check if agent can use a tool
        allowed, reason = manager.check_permission(
            agent_id="query_agent",
            tool_name="DuckDuckGoSearchRun",
            operation=OperationType.EXTERNAL_API
        )

        if allowed:
            # Execute tool
            result = tool.run(query)
        else:
            logger.warning(f"Permission denied: {reason}")
        ```
    """

    def __init__(self, enable_metrics: bool = True, strict_mode: bool = False):
        """
        Initialize the Agent Permission Manager

        Args:
            enable_metrics: Whether to collect metrics for research
            strict_mode: If True, apply stricter permission policies
        """
        self.logger = logging.getLogger(__name__)
        self.enable_metrics = enable_metrics
        self.strict_mode = strict_mode
        self.policies = self._initialize_policies()
        self.audit_log: List[AuditEntry] = []
        self.tool_call_counts: Dict[str, Dict[str, Any]] = {}
        self.metrics = {
            "total_checks": 0,
            "allowed": 0,
            "denied": 0,
            "violations_by_agent": {},
            "violations_by_tool": {},
            "approval_requests": 0
        }

        self.logger.info(
            "AgentPermissionManager initialized with strict_mode=%s, metrics=%s",
            strict_mode, enable_metrics
        )

    def _initialize_policies(self) -> Dict[str, PermissionPolicy]:
        """
        Initialize permission policies for all agents

        Implements least-privilege principle:
        - Analysis Agent: Can only analyze data (read-only)
        - Query Agent: Can query databases and limited external search

        Returns:
            Dictionary mapping agent_id to PermissionPolicy
        """
        policies = {
            "analysis_agent": PermissionPolicy(
                agent_id="analysis_agent",
                allowed_tools={"AnalysisTool"},
                allowed_operations={
                    OperationType.READ,
                    OperationType.EXECUTE
                },
                forbidden_operations={
                    OperationType.WRITE,
                    OperationType.DELETE,
                    OperationType.DATABASE_WRITE,
                    OperationType.EXTERNAL_API
                },
                approval_requirements={},
                max_tool_calls_per_session=50,
                rate_limit_seconds=0.0,  # Disabled - agent iteration limits provide sufficient protection
                description="Analysis agent restricted to read-only analysis operations"
            ),
            "query_agent": PermissionPolicy(
                agent_id="query_agent",
                allowed_tools={
                    "QueryTool",
                    "wikipedia",  # Actual LangChain tool name
                    "duckduckgo_search",  # Actual LangChain tool name
                    "news_search",  # Actual LangChain tool name
                    "Neo4jQueryTool"  # Added for database query access
                },
                allowed_operations={
                    OperationType.READ,
                    OperationType.DATABASE_QUERY,
                    OperationType.SEARCH,
                    OperationType.EXTERNAL_API
                },
                forbidden_operations={
                    OperationType.WRITE,
                    OperationType.DELETE,
                    OperationType.DATABASE_WRITE
                },
                approval_requirements={
                    "duckduckgo_search": ApprovalLevel.LOGGING,
                    "news_search": ApprovalLevel.LOGGING
                },
                max_tool_calls_per_session=100,
                rate_limit_seconds=0.0,  # Disabled - agent iteration limits provide sufficient protection
                description="Query agent with database and limited external API access"
            )
        }

        # Apply stricter policies in strict mode
        if self.strict_mode:
            for policy in policies.values():
                policy.max_tool_calls_per_session = int(
                    policy.max_tool_calls_per_session * 0.5
                )
                policy.rate_limit_seconds *= 2.0
                # Elevate logging to confirmation
                for tool, level in policy.approval_requirements.items():
                    if level == ApprovalLevel.LOGGING:
                        policy.approval_requirements[tool] = ApprovalLevel.CONFIRMATION

        return policies

    def check_permission(
        self,
        agent_id: str,
        tool_name: str,
        operation: OperationType,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Check if agent has permission to perform operation with tool

        This is the main enforcement point for LLM06 mitigation. Performs:
        1. Policy lookup for the agent
        2. Tool access verification
        3. Operation type checking
        4. Rate limit enforcement
        5. Approval requirement checking
        6. Audit logging

        Args:
            agent_id: Identifier of the agent requesting permission
            tool_name: Name of the tool to be used
            operation: Type of operation to perform
            context: Optional context information for audit trail

        Returns:
            Tuple of (allowed: bool, reason: str)
            - allowed: True if permission is granted, False otherwise
            - reason: Human-readable explanation of the decision
        """
        if self.enable_metrics:
            self.metrics["total_checks"] += 1

        # Get policy for this agent
        policy = self.policies.get(agent_id)
        if not policy:
            reason = f"No permission policy found for agent '{agent_id}'"
            self._log_denial(agent_id, tool_name, operation, reason, context)
            return False, reason

        # Check 1: Tool access control
        if tool_name not in policy.allowed_tools:
            reason = (
                f"Tool '{tool_name}' not in allowed tools for {agent_id}. "
                f"Allowed tools: {policy.allowed_tools}"
            )
            self._log_denial(agent_id, tool_name, operation, reason, context)
            return False, reason

        # Check 2: Forbidden operations
        if operation in policy.forbidden_operations:
            reason = (
                f"Operation '{operation.value}' is explicitly forbidden for {agent_id}"
            )
            self._log_denial(agent_id, tool_name, operation, reason, context)
            return False, reason

        # Check 3: Allowed operations
        if operation not in policy.allowed_operations:
            reason = (
                f"Operation '{operation.value}' not in allowed operations for {agent_id}. "
                f"Allowed operations: {[op.value for op in policy.allowed_operations]}"
            )
            self._log_denial(agent_id, tool_name, operation, reason, context)
            return False, reason

        # Check 4: Rate limiting
        if not self._check_rate_limit(agent_id, policy):
            reason = f"Rate limit exceeded for {agent_id}"
            self._log_denial(agent_id, tool_name, operation, reason, context)
            return False, reason

        # Check 5: Approval requirements
        approval_level = policy.approval_requirements.get(tool_name, ApprovalLevel.NONE)
        if approval_level != ApprovalLevel.NONE:
            self._handle_approval_requirement(agent_id, tool_name, approval_level)

        # Permission granted
        self._log_approval(agent_id, tool_name, operation, context)
        return True, "Permission granted"

    def _check_rate_limit(self, agent_id: str, policy: PermissionPolicy) -> bool:
        """
        Check if agent has exceeded rate limit

        Implements rate limiting to prevent abuse of agent tools.
        Tracks per-agent statistics including:
        - Total tool calls in current session
        - Time of last tool call
        - Session start time

        Args:
            agent_id: Agent to check rate limit for
            policy: Permission policy for the agent

        Returns:
            True if within rate limit, False if exceeded
        """
        current_time = time.time()

        if agent_id not in self.tool_call_counts:
            self.tool_call_counts[agent_id] = {
                "count": 0,
                "last_call": 0,  # Initialize to 0 so first call isn't rate limited
                "session_start": current_time
            }

        stats = self.tool_call_counts[agent_id]

        # Check session limit
        if stats["count"] >= policy.max_tool_calls_per_session:
            self.logger.warning(
                "Agent %s exceeded session limit: %d/%d calls",
                agent_id, stats["count"], policy.max_tool_calls_per_session
            )
            return False

        # Check rate limit (minimum time between calls)
        # Skip rate limit check on first call (last_call == 0)
        if stats["last_call"] > 0:
            time_since_last = current_time - stats["last_call"]
            if time_since_last < policy.rate_limit_seconds:
                self.logger.warning(
                    "Agent %s rate limit: %.2fs since last call (min: %.2fs)",
                    agent_id, time_since_last, policy.rate_limit_seconds
                )
                return False
        else:
            self.logger.debug(
                "Agent %s first call - skipping rate limit check",
                agent_id
            )

        # Update counters
        stats["count"] += 1
        stats["last_call"] = current_time

        return True

    def _handle_approval_requirement(
        self,
        agent_id: str,
        tool_name: str,
        approval_level: ApprovalLevel
    ) -> None:
        """
        Handle approval requirements for tools

        In a production system, this would:
        - CONFIRMATION: Show UI prompt to user
        - HUMAN: Require human approval before proceeding

        For research purposes, we log the requirement without blocking.

        Args:
            agent_id: Agent requesting approval
            tool_name: Tool requiring approval
            approval_level: Level of approval required
        """
        if self.enable_metrics:
            self.metrics["approval_requests"] += 1

        if approval_level == ApprovalLevel.HUMAN:
            self.logger.info(
                "[APPROVAL REQUIRED] Agent %s requests HUMAN approval for tool %s",
                agent_id, tool_name
            )
        elif approval_level == ApprovalLevel.CONFIRMATION:
            self.logger.info(
                "[CONFIRMATION REQUIRED] Agent %s requests confirmation for tool %s",
                agent_id, tool_name
            )
        elif approval_level == ApprovalLevel.LOGGING:
            self.logger.info(
                "[LOGGED] Agent %s using monitored tool %s",
                agent_id, tool_name
            )

    def _log_approval(
        self,
        agent_id: str,
        tool_name: str,
        operation: OperationType,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log successful permission check"""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            tool_name=tool_name,
            operation=operation.value,
            result="allowed",
            reason="Permission policy satisfied",
            context=context or {}
        )
        self.audit_log.append(entry)

        if self.enable_metrics:
            self.metrics["allowed"] += 1

        self.logger.debug(
            "[AUDIT] Agent %s ALLOWED to use %s for %s",
            agent_id, tool_name, operation.value
        )

    def _log_denial(
        self,
        agent_id: str,
        tool_name: str,
        operation: OperationType,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log permission denial (security violation)"""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            tool_name=tool_name,
            operation=operation.value,
            result="denied",
            reason=reason,
            context=context or {}
        )
        self.audit_log.append(entry)

        if self.enable_metrics:
            self.metrics["denied"] += 1

            # Track violations by agent
            if agent_id not in self.metrics["violations_by_agent"]:
                self.metrics["violations_by_agent"][agent_id] = 0
            self.metrics["violations_by_agent"][agent_id] += 1

            # Track violations by tool
            if tool_name not in self.metrics["violations_by_tool"]:
                self.metrics["violations_by_tool"][tool_name] = 0
            self.metrics["violations_by_tool"][tool_name] += 1

        self.logger.warning(
            "[SECURITY VIOLATION] Agent %s DENIED %s for %s: %s",
            agent_id, tool_name, operation.value, reason
        )

    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        result_filter: Optional[str] = None
    ) -> List[AuditEntry]:
        """
        Get audit log entries with optional filtering

        Args:
            agent_id: Filter by agent ID (optional)
            result_filter: Filter by result ("allowed" or "denied") (optional)

        Returns:
            List of audit entries matching filters
        """
        filtered_log = self.audit_log

        if agent_id:
            filtered_log = [e for e in filtered_log if e.agent_id == agent_id]

        if result_filter:
            filtered_log = [e for e in filtered_log if e.result == result_filter]

        return filtered_log

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive permission system metrics

        Returns metrics for research and analysis including:
        - Total permission checks
        - Approval/denial rates
        - Violations by agent and tool
        - Rate limiting statistics

        Returns:
            Dictionary of metrics
        """
        if not self.enable_metrics:
            return {"metrics_collection": "disabled"}

        total_checks = self.metrics["total_checks"]

        return {
            "total_permission_checks": total_checks,
            "allowed": self.metrics["allowed"],
            "denied": self.metrics["denied"],
            "denial_rate": (
                self.metrics["denied"] / total_checks if total_checks > 0 else 0
            ),
            "violations_by_agent": self.metrics["violations_by_agent"],
            "violations_by_tool": self.metrics["violations_by_tool"],
            "approval_requests": self.metrics["approval_requests"],
            "agents_monitored": list(self.policies.keys()),
            "tool_call_stats": self.tool_call_counts,
            "audit_log_size": len(self.audit_log)
        }

    def reset_session(self, agent_id: Optional[str] = None) -> None:
        """
        Reset session counters for rate limiting

        Args:
            agent_id: Agent to reset (resets all if None)
        """
        if agent_id:
            if agent_id in self.tool_call_counts:
                current_time = time.time()
                self.tool_call_counts[agent_id] = {
                    "count": 0,
                    "last_call": 0,  # Reset to 0 so next call isn't rate limited
                    "session_start": current_time
                }
                self.logger.info("Reset session for agent %s", agent_id)
        else:
            self.tool_call_counts = {}
            self.logger.info("Reset sessions for all agents")

    def add_policy(self, policy: PermissionPolicy) -> None:
        """
        Add or update a permission policy for an agent

        Args:
            policy: Permission policy to add/update
        """
        self.policies[policy.agent_id] = policy
        self.logger.info(
            "Added/updated policy for agent %s: %s",
            policy.agent_id, policy.description
        )

    def get_policy(self, agent_id: str) -> Optional[PermissionPolicy]:
        """
        Get permission policy for an agent

        Args:
            agent_id: Agent to get policy for

        Returns:
            Permission policy or None if not found
        """
        return self.policies.get(agent_id)
