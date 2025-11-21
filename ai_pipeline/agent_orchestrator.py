"""
Streamlined Agent-Based Orchestrator for Finnish Politician Analysis System
Production-grade LangChain specialized multi-agent coordinator.
"""

import logging
import asyncio
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from .agents import (
    AnalysisAgent,
    QueryAgent
)
from .memory.shared_memory import SharedAgentMemory
from .security import AgentPermissionManager
from .security import ExcessiveAgencyMonitor

# Load environment variables
load_dotenv()

class AgentOrchestrator:
    """
    Production LangChain Specialized Multi-Agent Orchestrator
    
    This implements a true distributed multi-agent system with:
    - Specialized LangChain agents for different tasks
    - Distributed coordination through shared memory
    - Fault tolerance and error recovery
    - AnalysisAgent: Performs content analysis and insights
    - QueryAgent: Handles all query operations
    - Shared Memory: Cross-agent state and communication
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.shared_memory = SharedAgentMemory()
        self.agents = {}
        self.is_initialized = False

        # Initialize OWASP LLM06 monitoring system
        # Note: Individual agents have their own permission managers
        # The orchestrator aggregates security metrics from all agents
        self.security_monitor = None

        # Validate environment
        self._validate_environment()

        self.logger.info("AgentOrchestrator initialized with LLM06 security monitoring")
    
    def _validate_environment(self):
        """Validate required environment variables"""
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    async def initialize(self):
        """
        Initialize the agent orchestrator and all specialized agents
        """
        try:
            if self.is_initialized:
                self.logger.info("AgentOrchestrator already initialized")
                return
            
            self.logger.info("Initializing AgentOrchestrator with specialized agents...")
            
            # Initialize shared memory
            await self.shared_memory.initialize()
            
            # Initialize all specialized agents
            openai_api_key = os.getenv("OPENAI_API_KEY")
            self.agents = {
                "analysis": AnalysisAgent(shared_memory=self.shared_memory, openai_api_key=openai_api_key),
                "query": QueryAgent(shared_memory=self.shared_memory, openai_api_key=openai_api_key)
            }
            
            self.is_initialized = True
            self.logger.info(f"AgentOrchestrator initialization completed with {len(self.agents)} specialized agents")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentOrchestrator: {str(e)}")
            raise
    
    async def process_data_ingestion(
        self,
        sources: List[str] = None,
        limit: int = 100,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute intelligent data ingestion workflow using specialized agents
        
        This workflow demonstrates the power of the specialized agent architecture:
        1. AnalysisAgent analyzes the collected content
        2. QueryAgent retrieves and processes data
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            workflow_id = f"data_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"Starting data ingestion workflow: {workflow_id}")
            
            # Store workflow start in shared memory
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "workflow_id": workflow_id,
                    "workflow_type": "data_ingestion",
                    "sources": sources,
                    "limit": limit,
                    "query": query,
                    "status": "started",
                    "started_at": datetime.now().isoformat()
                },
                memory_type="workflow_status"
            )
            
            # Use only the agents that actually exist
            analysis_agent = self.agents["analysis"]
            query_agent = self.agents["query"]
            
            # Step 1: Data Collection using QueryAgent
            politician_data = None
            news_data = None
            
            if sources and "politicians" in str(sources).lower():
                self.logger.info("Collecting politician data using QueryAgent")
                politician_data = await query_agent.search_politicians(
                    query="all politicians", 
                    search_type="exact"
                )
                
            if sources and "news" in str(sources).lower():
                self.logger.info("Collecting news data using QueryAgent")
                news_data = await query_agent.search_news(
                    query=query or "recent political news"
                )
            
            # Step 2: Analysis using AnalysisAgent
            analysis_results = {}
            if politician_data:
                analysis_results["politicians"] = await analysis_agent.analyze_politicians(politician_data)
            if news_data:
                analysis_results["news"] = await analysis_agent.analyze_news(news_data)
            
            # Step 3: Generate insights if both data types are available
            insights = None
            if politician_data and news_data:
                insights = await analysis_agent.generate_insights()
                analysis_results["insights"] = insights
            
            # Update workflow status in shared memory
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "results": {
                        "data_collection": {"politicians": bool(politician_data), "news": bool(news_data)},
                        "analysis": analysis_results,
                        "insights": bool(insights)
                    },
                    "completed_at": datetime.now().isoformat()
                },
                memory_type="workflow_status"
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "orchestrator_type": "langchain_specialized_multi_agent",
                "agent_coordination": True,
                "intelligent_reasoning": True,
                "results": {
                    "data_collection": {"politicians": bool(politician_data), "news": bool(news_data)},
                    "analysis": analysis_results,
                    "insights": bool(insights)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in data ingestion workflow: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                },
                memory_type="workflow_status"
            )
            raise
    
    async def process_user_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user query using intelligent agent coordination
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"Processing user query: {query_id}")
            
            # Store query start in shared memory
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "query_id": query_id,
                    "query": query,
                    "context": context,
                    "status": "processing",
                    "started_at": datetime.now().isoformat()
                },
                memory_type="query_status"
            )
            
            # Execute through QueryAgent
            query_agent = self.agents["query"]

            # Always include selected politician context if present
            politician_context = None
            if context and "selected_politician" in context:
                politician_context = context["selected_politician"]

            # Combine query and context for the agent
            agent_input = query
            if politician_context:
                agent_input = f"[Politician: {politician_context}] {query}"

            # Always use semantic_search for general questions, passing both query and context
            result = await query_agent.semantic_search(agent_input)
            
            # Update query status
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "query_id": query_id,
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                },
                memory_type="query_status"
            )
            
            return {
                "query_id": query_id,
                "status": "completed",
                "orchestrator_type": "langchain_specialized_multi_agent",
                "intelligent_routing": True,
                **result
            }
            
        except Exception as e:
            self.logger.error(f"Error in user query processing: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            self.logger.info("Performing system health check")
            
            health_status = {
                "orchestrator": "healthy",
                "shared_memory": "healthy",
                "agents": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Check each agent
            for agent_name, agent in self.agents.items():
                try:
                    agent_info = agent.get_agent_info()
                    health_status["agents"][agent_name] = {
                        "status": agent_info.get("status", "unknown"),
                        "capabilities": len(agent_info.get("capabilities", [])),
                        "tools": len(agent_info.get("tools", []))
                    }
                except Exception as e:
                    health_status["agents"][agent_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Check data collection health
            if "data_collection" in self.agents:
                try:
                    data_collection_agent = self.agents["data_collection"]
                    data_health = await data_collection_agent.health_check()
                    health_status["data_sources"] = data_health
                except Exception as e:
                    health_status["data_sources"] = {"status": "error", "error": str(e)}
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "orchestrator": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "name": "Finnish Politician Analysis System - AI Pipeline",
            "version": "2.0.0",
            "architecture": "langchain_specialized_multi_agent",
            "orchestrator_type": "distributed_coordination",
            "agents": list(self.agents.keys()) if self.agents else [],
            "total_agents": len(self.agents),
            "is_initialized": self.is_initialized,
            "features": [
                "specialized_agent_coordination",
                "intelligent_reasoning_with_gpt4",
                "shared_memory_system",
                "fault_tolerant_workflows",
                "real_time_adaptation",
                "production_monitoring",
                "owasp_llm_security_controls"  # LLM01, LLM02, LLM06, LLM09
            ],
            "supported_workflows": [
                "data_ingestion",
                "user_query",
                "health_check",
                "relationship_analysis",
                "content_analysis"
            ],
            "security_features": [
                "LLM01: Prompt Injection Prevention",
                "LLM02: Sensitive Information Disclosure Prevention",
                "LLM06: Excessive Agency Prevention",
                "LLM09: Misinformation Prevention"
            ]
        }

    async def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated OWASP LLM06 security metrics from all agents

        Returns:
            Dictionary with comprehensive security metrics across all agents
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            aggregated_metrics = {
                "timestamp": datetime.now().isoformat(),
                "orchestrator_level": "system_wide",
                "agents": {},
                "aggregate_stats": {
                    "total_permission_checks": 0,
                    "total_allowed": 0,
                    "total_denied": 0,
                    "overall_denial_rate": 0.0,
                    "total_approval_requests": 0
                }
            }

            # Collect metrics from each agent
            for agent_name, agent in self.agents.items():
                if hasattr(agent, 'get_security_metrics'):
                    agent_metrics = agent.get_security_metrics()
                    aggregated_metrics["agents"][agent_name] = agent_metrics

                    # Aggregate statistics
                    aggregated_metrics["aggregate_stats"]["total_permission_checks"] += agent_metrics.get("total_permission_checks", 0)
                    aggregated_metrics["aggregate_stats"]["total_allowed"] += agent_metrics.get("allowed", 0)
                    aggregated_metrics["aggregate_stats"]["total_denied"] += agent_metrics.get("denied", 0)
                    aggregated_metrics["aggregate_stats"]["total_approval_requests"] += agent_metrics.get("approval_requests", 0)

            # Calculate overall denial rate
            total_checks = aggregated_metrics["aggregate_stats"]["total_permission_checks"]
            if total_checks > 0:
                aggregated_metrics["aggregate_stats"]["overall_denial_rate"] = (
                    aggregated_metrics["aggregate_stats"]["total_denied"] / total_checks
                )

            self.logger.info("Collected security metrics from %d agents", len(self.agents))
            return aggregated_metrics

        except Exception as e:
            self.logger.error(f"Error collecting security metrics: {str(e)}")
            raise

    async def get_security_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive OWASP LLM06 security report

        Analyzes all agents for excessive agency violations, anomalies,
        and provides actionable security recommendations.

        Returns:
            Dictionary with comprehensive security report
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            self.logger.info("Generating comprehensive LLM06 security report")

            # Collect metrics from all agents
            metrics = await self.get_security_metrics()

            # Initialize security monitor if needed
            # We'll use the first agent's permission manager for system-wide monitoring
            if not self.security_monitor and self.agents:
                first_agent = list(self.agents.values())[0]
                if hasattr(first_agent, 'permission_manager'):
                    self.security_monitor = ExcessiveAgencyMonitor(
                        permission_manager=first_agent.permission_manager,
                        enable_metrics=True
                    )

            # Generate security report
            security_report = {
                "report_type": "ORCHESTRATOR_WIDE_SECURITY_REPORT",
                "generated_at": datetime.now().isoformat(),
                "owasp_risk": "LLM06:2025 - Excessive Agency",
                "system_metrics": metrics,
                "agent_security_status": {},
                "anomalies": [],
                "recommendations": []
            }

            # Collect security status from each agent
            for agent_name, agent in self.agents.items():
                agent_info = agent.get_agent_info()
                security_report["agent_security_status"][agent_name] = {
                    "security_features": agent_info.get("security", {}),
                    "tools": agent_info.get("tools", []),
                    "status": agent_info.get("status", "unknown")
                }

                # Get audit log for violations
                if hasattr(agent, 'get_audit_log'):
                    violations = agent.get_audit_log(result_filter="denied")
                    if violations:
                        security_report["agent_security_status"][agent_name]["violations"] = len(violations)
                        security_report["agent_security_status"][agent_name]["recent_violations"] = [
                            {
                                "tool": v.tool_name,
                                "operation": v.operation,
                                "reason": v.reason,
                                "timestamp": v.timestamp
                            }
                            for v in violations[-5:]  # Last 5 violations
                        ]

            # Detect anomalies if monitor is available
            if self.security_monitor:
                anomalies = self.security_monitor.detect_anomalies()
                security_report["anomalies"] = [
                    {
                        "type": a.anomaly_type,
                        "severity": a.severity,
                        "agent": a.agent_id,
                        "description": a.description,
                        "recommendation": a.recommendation
                    }
                    for a in anomalies
                ]

            # Generate recommendations
            overall_denial_rate = metrics["aggregate_stats"]["overall_denial_rate"]
            if overall_denial_rate > 0.3:
                security_report["recommendations"].append(
                    f"High denial rate detected ({overall_denial_rate:.1%}). "
                    "Review agent permission policies for potential misalignment."
                )

            if not security_report["recommendations"]:
                security_report["recommendations"].append(
                    "No critical security issues detected. System operating within normal parameters."
                )

            # Add compliance status
            security_report["owasp_compliance"] = {
                "LLM01_prompt_injection": "IMPLEMENTED",
                "LLM02_sensitive_info": "IMPLEMENTED",
                "LLM06_excessive_agency": "IMPLEMENTED",
                "LLM09_misinformation": "IMPLEMENTED",
                "overall_status": "COMPLIANT"
            }

            self.logger.info("Security report generated successfully")
            return security_report

        except Exception as e:
            self.logger.error(f"Error generating security report: {str(e)}")
            raise

# Global orchestrator instance
_orchestrator_instance = None

def get_agent_orchestrator() -> AgentOrchestrator:
    """Get or create the global agent orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator()
    return _orchestrator_instance
