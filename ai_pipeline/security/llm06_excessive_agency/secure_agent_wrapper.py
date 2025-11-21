"""
Secure Agent Executor Wrapper for LLM06 Permission Enforcement

Wraps LangChain AgentExecutor to add transparent permission checking
before tool execution, implementing OWASP LLM06:2025 mitigations.
"""

import logging
from typing import Any, Dict, List, Optional
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool

from .agent_permission_manager import AgentPermissionManager, OperationType

logger = logging.getLogger(__name__)


class SecureAgentExecutor(AgentExecutor):
    """
    Secured AgentExecutor with LLM06 Permission Enforcement

    Extends LangChain's AgentExecutor to add transparent permission checking
    before any tool execution. Implements defense-in-depth by:

    1. Intercepting all tool calls before execution
    2. Checking permissions via AgentPermissionManager
    3. Blocking unauthorized tool usage
    4. Maintaining complete audit trail
    5. Preserving original tool functionality when permitted

    The security layer is transparent to the agent - tools appear to work
    normally when permitted, but are blocked when denied.

    Example Usage:
        ```python
        permission_manager = AgentPermissionManager()

        executor = SecureAgentExecutor(
            agent=my_agent,
            tools=my_tools,
            agent_id="query_agent",
            permission_manager=permission_manager,
            verbose=True
        )

        # Tools are automatically secured
        result = executor.invoke({"input": "search for something"})
        ```
    """

    def __init__(
        self,
        *args,
        agent_id: str,
        permission_manager: AgentPermissionManager,
        **kwargs
    ):
        """
        Initialize Secure Agent Executor

        Args:
            agent_id: Identifier for this agent (must match permission policy)
            permission_manager: Permission manager instance for checking permissions
            *args: Arguments passed to AgentExecutor
            **kwargs: Keyword arguments passed to AgentExecutor
        """
        # Wrap tools before passing to parent
        if 'tools' in kwargs:
            # Store security components temporarily
            temp_agent_id = agent_id
            temp_permission_manager = permission_manager

            kwargs['tools'] = self._wrap_tools_with_permissions_static(
                kwargs['tools'], temp_agent_id, temp_permission_manager
            )

        super().__init__(*args, **kwargs)

        # Store security components after parent initialization
        object.__setattr__(self, 'agent_id', agent_id)
        object.__setattr__(self, 'permission_manager', permission_manager)

        logger.info(
            "SecureAgentExecutor initialized for agent %s with %d secured tools",
            agent_id, len(self.tools) if hasattr(self, 'tools') else 0
        )

    @staticmethod
    def _wrap_tools_with_permissions_static(
        tools: List[BaseTool],
        agent_id: str,
        permission_manager: AgentPermissionManager
    ) -> List[BaseTool]:
        """
        Static version of tool wrapping for initialization

        Args:
            tools: List of tools to wrap
            agent_id: Agent identifier
            permission_manager: Permission manager instance

        Returns:
            List of wrapped tools with permission checking
        """
        wrapped_tools = []

        for tool in tools:
            wrapped_tool = SecureAgentExecutor._create_secured_tool_static(
                tool, agent_id, permission_manager
            )
            wrapped_tools.append(wrapped_tool)

        logger.debug(
            "Wrapped %d tools with permission checking for agent %s",
            len(tools), agent_id
        )

        return wrapped_tools

    @staticmethod
    def _create_secured_tool_static(
        tool: BaseTool,
        agent_id: str,
        permission_manager: AgentPermissionManager
    ) -> BaseTool:
        """
        Create a secured version of a tool with permission checking (static version)

        Args:
            tool: Original tool to secure
            agent_id: Agent identifier
            permission_manager: Permission manager instance

        Returns:
            Secured version of the tool
        """
        # Store reference to original methods
        original_run = tool._run
        original_arun = tool._arun if hasattr(tool, '_arun') else None

        # Determine operation type based on tool name/type
        operation_type = SecureAgentExecutor._determine_operation_type_static(tool)

        def secured_run(query: str, **kwargs) -> str:
            """Secured synchronous tool execution"""
            # Check permission before execution
            allowed, reason = permission_manager.check_permission(
                agent_id=agent_id,
                tool_name=tool.name,
                operation=operation_type,
                context={"query": query, **kwargs}
            )

            if not allowed:
                error_msg = f"[PERMISSION DENIED] {reason}"
                logger.warning(
                    "Agent %s denied access to tool %s: %s",
                    agent_id, tool.name, reason
                )
                return error_msg

            # Permission granted - execute original tool
            logger.debug(
                "Agent %s executing tool %s with permission",
                agent_id, tool.name
            )
            return original_run(query, **kwargs)

        async def secured_arun(*args, **kwargs) -> str:
            """Secured asynchronous tool execution"""
            # Extract the query/input parameter flexibly
            query_value = ""

            # Try to get from positional args
            if args:
                query_value = str(args[0])
            # Try to get from kwargs (common parameter names)
            elif 'input' in kwargs:
                query_value = str(kwargs['input'])
            elif 'query' in kwargs:
                query_value = str(kwargs['query'])
            elif kwargs:
                # Use first kwarg value if nothing else matches
                query_value = str(next(iter(kwargs.values())))

            # Check permission before execution
            allowed, reason = permission_manager.check_permission(
                agent_id=agent_id,
                tool_name=tool.name,
                operation=operation_type,
                context={"query": query_value, **kwargs}
            )

            if not allowed:
                error_msg = f"[PERMISSION DENIED] {reason}"
                logger.warning(
                    "Agent %s denied access to tool %s: %s",
                    agent_id, tool.name, reason
                )
                return error_msg

            # Permission granted - execute original tool
            logger.debug(
                "Agent %s executing tool %s with permission",
                agent_id, tool.name
            )

            if original_arun:
                return await original_arun(*args, **kwargs)
            else:
                # Fallback to sync version if async not available
                return original_run(*args, **kwargs)

        # Replace tool methods with secured versions
        tool._run = secured_run
        if original_arun:
            tool._arun = secured_arun

        return tool

    @staticmethod
    def _determine_operation_type_static(tool: BaseTool) -> OperationType:
        """
        Static version of operation type determination

        Args:
            tool: Tool to categorize

        Returns:
            OperationType for the tool
        """
        tool_name_lower = tool.name.lower()

        # Categorize based on tool name patterns
        if any(keyword in tool_name_lower for keyword in ['search', 'google', 'duckduckgo', 'bing']):
            return OperationType.SEARCH

        if any(keyword in tool_name_lower for keyword in ['query', 'database', 'db', 'neo4j']):
            return OperationType.DATABASE_QUERY

        if any(keyword in tool_name_lower for keyword in ['wikipedia', 'news', 'api', 'fetch']):
            return OperationType.EXTERNAL_API

        if any(keyword in tool_name_lower for keyword in ['analysis', 'analyze', 'process']):
            return OperationType.EXECUTE

        if any(keyword in tool_name_lower for keyword in ['write', 'create', 'insert', 'update']):
            return OperationType.WRITE

        if any(keyword in tool_name_lower for keyword in ['delete', 'remove']):
            return OperationType.DELETE

        # Default to READ for safety
        return OperationType.READ

    def _wrap_tools_with_permissions(self, tools: List[BaseTool]) -> List[BaseTool]:
        """
        Wrap each tool with permission checking

        Creates a new version of each tool that checks permissions before
        executing the original tool logic. The wrapped tool:

        1. Preserves the original tool's name, description, and interface
        2. Adds permission check before execution
        3. Returns error message if permission denied
        4. Calls original tool if permission granted

        Args:
            tools: List of tools to wrap

        Returns:
            List of wrapped tools with permission checking
        """
        wrapped_tools = []

        for tool in tools:
            wrapped_tool = self._create_secured_tool(tool)
            wrapped_tools.append(wrapped_tool)

        logger.debug(
            "Wrapped %d tools with permission checking for agent %s",
            len(tools), self.agent_id
        )

        return wrapped_tools

    def _create_secured_tool(self, tool: BaseTool) -> BaseTool:
        """
        Create a secured version of a tool with permission checking

        Args:
            tool: Original tool to secure

        Returns:
            Secured version of the tool
        """
        # Store reference to original methods
        original_run = tool._run
        original_arun = tool._arun if hasattr(tool, '_arun') else None

        # Determine operation type based on tool name/type
        operation_type = self._determine_operation_type(tool)

        def secured_run(query: str, **kwargs) -> str:
            """Secured synchronous tool execution"""
            # Check permission before execution
            allowed, reason = self.permission_manager.check_permission(
                agent_id=self.agent_id,
                tool_name=tool.name,
                operation=operation_type,
                context={"query": query, **kwargs}
            )

            if not allowed:
                error_msg = f"[PERMISSION DENIED] {reason}"
                logger.warning(
                    "Agent %s denied access to tool %s: %s",
                    self.agent_id, tool.name, reason
                )
                return error_msg

            # Permission granted - execute original tool
            logger.debug(
                "Agent %s executing tool %s with permission",
                self.agent_id, tool.name
            )
            return original_run(query, **kwargs)

        async def secured_arun(*args, **kwargs) -> str:
            """Secured asynchronous tool execution"""
            # Extract the query/input parameter flexibly
            query_value = ""

            # Try to get from positional args
            if args:
                query_value = str(args[0])
            # Try to get from kwargs (common parameter names)
            elif 'input' in kwargs:
                query_value = str(kwargs['input'])
            elif 'query' in kwargs:
                query_value = str(kwargs['query'])
            elif kwargs:
                # Use first kwarg value if nothing else matches
                query_value = str(next(iter(kwargs.values())))

            # Check permission before execution
            allowed, reason = self.permission_manager.check_permission(
                agent_id=self.agent_id,
                tool_name=tool.name,
                operation=operation_type,
                context={"query": query_value, **kwargs}
            )

            if not allowed:
                error_msg = f"[PERMISSION DENIED] {reason}"
                logger.warning(
                    "Agent %s denied access to tool %s: %s",
                    self.agent_id, tool.name, reason
                )
                return error_msg

            # Permission granted - execute original tool
            logger.debug(
                "Agent %s executing tool %s with permission",
                self.agent_id, tool.name
            )

            if original_arun:
                return await original_arun(*args, **kwargs)
            else:
                # Fallback to sync version if async not available
                return original_run(*args, **kwargs)

        # Replace tool methods with secured versions
        tool._run = secured_run
        if original_arun:
            tool._arun = secured_arun

        return tool

    def _determine_operation_type(self, tool: BaseTool) -> OperationType:
        """
        Determine the operation type for a tool based on its characteristics

        This helps categorize tools for permission checking. The mapping is:
        - Search tools -> SEARCH
        - Database tools -> DATABASE_QUERY
        - External API tools -> EXTERNAL_API
        - Analysis tools -> EXECUTE
        - Default -> READ

        Args:
            tool: Tool to categorize

        Returns:
            OperationType for the tool
        """
        tool_name_lower = tool.name.lower()

        # Categorize based on tool name patterns
        if any(keyword in tool_name_lower for keyword in ['search', 'google', 'duckduckgo', 'bing']):
            return OperationType.SEARCH

        if any(keyword in tool_name_lower for keyword in ['query', 'database', 'db', 'neo4j']):
            return OperationType.DATABASE_QUERY

        if any(keyword in tool_name_lower for keyword in ['wikipedia', 'news', 'api', 'fetch']):
            return OperationType.EXTERNAL_API

        if any(keyword in tool_name_lower for keyword in ['analysis', 'analyze', 'process']):
            return OperationType.EXECUTE

        if any(keyword in tool_name_lower for keyword in ['write', 'create', 'insert', 'update']):
            return OperationType.WRITE

        if any(keyword in tool_name_lower for keyword in ['delete', 'remove']):
            return OperationType.DELETE

        # Default to READ for safety
        return OperationType.READ

    def get_permission_metrics(self) -> Dict[str, Any]:
        """
        Get permission metrics for this agent

        Returns:
            Dictionary with permission metrics
        """
        return self.permission_manager.get_metrics()

    def get_audit_log(self, result_filter: Optional[str] = None) -> List:
        """
        Get audit log for this agent

        Args:
            result_filter: Filter by "allowed" or "denied" (optional)

        Returns:
            List of audit entries for this agent
        """
        return self.permission_manager.get_audit_log(
            agent_id=self.agent_id,
            result_filter=result_filter
        )

    def reset_session(self) -> None:
        """Reset rate limiting session for this agent"""
        self.permission_manager.reset_session(self.agent_id)
        logger.info("Reset session for agent %s", self.agent_id)
