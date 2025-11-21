"""
OWASP LLM06:2025 - Excessive Agency Prevention

**YOUR MAIN THESIS CONTRIBUTION**

Prevents agents from:
- Making unauthorized Neo4j database queries
- Exceeding rate limits
- Accessing data outside their permissions
- Performing dangerous operations (DELETE, DROP in Cypher queries)

This is the first comprehensive excessive agency prevention system for
graph database operations in multi-agent LLM systems.
"""

from .agent_permission_manager import (
    AgentPermissionManager,
    PermissionPolicy,
    OperationType,
    ApprovalLevel,
    AuditEntry
)
from .excessive_agency_monitor import ExcessiveAgencyMonitor, SecurityAnomaly
from .secure_agent_wrapper import SecureAgentExecutor

__all__ = [
    'AgentPermissionManager',
    'PermissionPolicy',
    'OperationType',
    'ApprovalLevel',
    'AuditEntry',
    'ExcessiveAgencyMonitor',
    'SecurityAnomaly',
    'SecureAgentExecutor',
]
