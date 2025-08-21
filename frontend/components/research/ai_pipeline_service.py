"""
Elite AI Pipeline Service for Research
Provides direct integration with AI agents while ensuring system stability
"""

import os
import sys
import logging
import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import httpx
import streamlit as st
from pydantic import BaseModel, Field

# Optional LangSmith integration
try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False


class AgentMetrics(BaseModel):
    """Metrics collected during agent execution"""
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0
    security_score: float = 1.0  # 0-1 scale, 1 being most secure
    reasoning_steps: int = 0
    sources_used: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str = ""
    

class ExperimentResult(BaseModel):
    """Results from a prompt engineering experiment"""
    experiment_id: str
    prompt_template: str
    parameters: Dict[str, Any]
    metrics: AgentMetrics
    output: str
    success: bool = True
    error: Optional[str] = None


class EliteAIPipelineService:
    """
    Elite AI Pipeline Service for academic research
    
    Provides direct integration with the AI pipeline agents while
    ensuring system stability through robust fallback mechanisms.
    
    Features:
    - Direct orchestrator access when available
    - Graceful API fallback
    - Comprehensive metrics collection
    - LangSmith integration (when available)
    - Experiment tracking
    """
    
    def __init__(self, api_base_url: str):
        """
        Initialize the Elite AI Pipeline Service
        
        Args:
            api_base_url: Base URL for the API fallback
        """
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(__name__)
        
        # Initialize metrics storage in session state
        if "agent_metrics" not in st.session_state:
            st.session_state.agent_metrics = []
            
        if "experiments" not in st.session_state:
            st.session_state.experiments = {}
            
        # Try to initialize direct access to agent orchestrator
        self.direct_mode_available = False
        try:
            # Add parent directory to path to allow importing from ai_pipeline
            parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
                
            # Try to import the agent orchestrator
            from ai_pipeline.agent_orchestrator import AgentOrchestrator
            from ai_pipeline.agents.analysis_agent import AnalysisAgent
            from ai_pipeline.agents.query_agent import QueryAgent
            from ai_pipeline.memory.shared_memory import SharedAgentMemory
            
            # Initialize shared memory and orchestrator
            self.shared_memory = SharedAgentMemory()
            self.orchestrator = AgentOrchestrator(shared_memory=self.shared_memory)
            
            # Get direct access to agents for advanced operations
            self.analysis_agent = self.orchestrator.analysis_agent
            self.query_agent = self.orchestrator.query_agent
            
            self.direct_mode_available = True
            self.logger.info("Direct orchestrator access initialized successfully")
        except Exception as e:
            self.logger.warning(f"Could not initialize direct orchestrator access: {e}")
            self.logger.info("Will use API fallback for all operations")
        
        # Initialize LangSmith if available
        self.langsmith_enabled = LANGSMITH_AVAILABLE and "LANGCHAIN_API_KEY" in os.environ
        if self.langsmith_enabled:
            try:
                self.langsmith_client = LangSmithClient()
                self.logger.info("LangSmith integration enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LangSmith client: {e}")
                self.langsmith_enabled = False
    
    async def _direct_query(self, query: str, context_ids: List[str] = None, 
                           detailed: bool = False) -> Dict[str, Any]:
        """
        Query the AI pipeline directly through the orchestrator
        
        Args:
            query: User query
            context_ids: List of politician IDs for context
            detailed: Whether to return detailed analysis
            
        Returns:
            Agent response with metrics
        """
        start_time = time.time()
        try:
            # Use the appropriate agent based on query type
            if "analysis" in query.lower() or detailed:
                result = await self.analysis_agent.generate_insights(
                    analysis_type="comprehensive" if detailed else "focused"
                )
                agent_id = "analysis_agent"
            else:
                result = await self.query_agent.search_politicians(
                    query=query, 
                    search_type="hybrid"
                )
                agent_id = "query_agent"
                
            # Get security metrics from the agent's last execution
            security_metrics = {}
            try:
                # Access metrics collected by security decorators
                from ai_pipeline.security.metrics_collector import SecurityMetricsCollector
                collector = SecurityMetricsCollector()
                security_metrics = collector.get_latest_metrics(agent_id)
            except Exception as e:
                self.logger.warning(f"Could not retrieve security metrics: {e}")
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # Collect metrics
            metrics = AgentMetrics(
                tokens_input=security_metrics.get("tokens_input", 0),
                tokens_output=security_metrics.get("tokens_output", 0),
                latency_ms=execution_time,
                security_score=security_metrics.get("security_score", 1.0),
                reasoning_steps=len(result.get("intermediate_steps", [])),
                sources_used=len(result.get("sources", [])),
                agent_id=agent_id,
                timestamp=datetime.now()
            )
            
            # Store metrics in session state
            st.session_state.agent_metrics.append(metrics.dict())
            
            # Format response
            response = {
                "output": result.get("output") or result.get("answer") or result.get("result", ""),
                "reasoning": result.get("reasoning") or result.get("intermediate_steps", []),
                "sources": result.get("sources", []),
                "metrics": metrics.dict(),
                "direct_access": True
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in direct query: {e}")
            raise
    
    async def _api_query(self, query: str, context_ids: List[str] = None, 
                        detailed: bool = False) -> Dict[str, Any]:
        """
        Query the AI pipeline through the API (fallback method)
        
        Args:
            query: User query
            context_ids: List of politician IDs for context
            detailed: Whether to return detailed analysis
            
        Returns:
            Agent response
        """
        start_time = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/analysis/custom",
                    json={
                        "query": query,
                        "context_ids": context_ids or [],
                        "detailed_response": detailed
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                # If backend is async, poll status endpoint
                if data.get("status") == "accepted" and data.get("status_url"):
                    status_url = data["status_url"]
                    max_wait = 60  # seconds
                    poll_interval = 1.5
                    
                    while True:
                        poll_response = await client.get(
                            f"{self.api_base_url}/analysis{status_url.split('/analysis')[-1]}", 
                            timeout=10
                        )
                        poll_data = poll_response.json()
                        
                        if poll_data.get("status") == "completed":
                            # AI answer is ready
                            data = poll_data.get("result", poll_data)
                            break
                        elif poll_data.get("status") == "failed":
                            raise Exception(f"API error: {poll_data.get('error', 'Unknown error')}")
                        elif time.time() - start_time > max_wait:
                            raise Exception("API timeout")
                            
                        await asyncio.sleep(poll_interval)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # Create metrics with limited information
            metrics = AgentMetrics(
                tokens_input=0,  # Not available from API
                tokens_output=0,  # Not available from API
                latency_ms=execution_time,
                security_score=1.0,  # Not available from API
                reasoning_steps=0,  # Not available from API
                sources_used=len(data.get("sources", [])),
                agent_id="api",
                timestamp=datetime.now()
            )
            
            # Store metrics in session state
            st.session_state.agent_metrics.append(metrics.dict())
            
            # Format response
            response = {
                "output": data.get("output") or data.get("answer") or data.get("result", ""),
                "reasoning": data.get("reasoning", []),
                "sources": data.get("sources", []),
                "metrics": metrics.dict(),
                "direct_access": False
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in API query: {e}")
            raise
    
    async def query_agent(self, query: str, context_ids: List[str] = None, 
                         detailed: bool = False) -> Dict[str, Any]:
        """
        Query the AI pipeline with automatic fallback
        
        Args:
            query: User query
            context_ids: List of politician IDs for context
            detailed: Whether to return detailed analysis
            
        Returns:
            Agent response with metrics and reasoning
        """
        # Try direct access first if available
        if self.direct_mode_available:
            try:
                return await self._direct_query(query, context_ids, detailed)
            except Exception as e:
                self.logger.warning(f"Direct query failed: {e}, falling back to API")
        
        # Fallback to API
        try:
            return await self._api_query(query, context_ids, detailed)
        except Exception as e:
            self.logger.error(f"API query failed: {e}")
            # Return error response
            return {
                "output": f"Error: {str(e)}",
                "reasoning": [],
                "sources": [],
                "metrics": AgentMetrics().dict(),
                "error": str(e),
                "direct_access": False
            }
    
    def query_agent_sync(self, query: str, context_ids: List[str] = None, 
                        detailed: bool = False) -> Dict[str, Any]:
        """
        Synchronous version of query_agent for use in Streamlit
        
        Args:
            query: User query
            context_ids: List of politician IDs for context
            detailed: Whether to return detailed analysis
            
        Returns:
            Agent response with metrics and reasoning
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.query_agent(query, context_ids, detailed))
        finally:
            loop.close()
    
    def create_experiment(self, name: str, description: str, 
                         variables: Dict[str, List[Any]]) -> str:
        """
        Create a new prompt engineering experiment
        
        Args:
            name: Experiment name
            description: Experiment description
            variables: Dictionary of variables and their possible values
            
        Returns:
            Experiment ID
        """
        experiment_id = f"exp_{int(time.time())}"
        
        st.session_state.experiments[experiment_id] = {
            "id": experiment_id,
            "name": name,
            "description": description,
            "variables": variables,
            "results": [],
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
        
        return experiment_id
    
    def run_experiment(self, experiment_id: str, query_template: str, 
                      context_ids: List[str] = None) -> List[ExperimentResult]:
        """
        Run a prompt engineering experiment
        
        Args:
            experiment_id: Experiment ID
            query_template: Query template with {variable} placeholders
            context_ids: List of politician IDs for context
            
        Returns:
            List of experiment results
        """
        if experiment_id not in st.session_state.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = st.session_state.experiments[experiment_id]
        variables = experiment["variables"]
        
        # Generate all combinations of variables
        import itertools
        variable_names = list(variables.keys())
        variable_values = [variables[name] for name in variable_names]
        combinations = list(itertools.product(*variable_values))
        
        results = []
        st.session_state.experiments[experiment_id]["status"] = "running"
        
        for combo in combinations:
            # Create parameter dictionary
            params = {name: value for name, value in zip(variable_names, combo)}
            
            # Format query with parameters
            try:
                query = query_template.format(**params)
            except KeyError as e:
                self.logger.error(f"Invalid template variable: {e}")
                continue
            
            # Run query
            try:
                response = self.query_agent_sync(query, context_ids)
                
                result = ExperimentResult(
                    experiment_id=experiment_id,
                    prompt_template=query_template,
                    parameters=params,
                    metrics=AgentMetrics(**response["metrics"]),
                    output=response["output"],
                    success=True
                )
            except Exception as e:
                result = ExperimentResult(
                    experiment_id=experiment_id,
                    prompt_template=query_template,
                    parameters=params,
                    metrics=AgentMetrics(),
                    output="",
                    success=False,
                    error=str(e)
                )
            
            results.append(result)
            st.session_state.experiments[experiment_id]["results"].append(result.dict())
        
        st.session_state.experiments[experiment_id]["status"] = "completed"
        return results
    
    def get_agent_metrics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent agent metrics
        
        Args:
            limit: Maximum number of metrics to return
            
        Returns:
            List of agent metrics
        """
        metrics = st.session_state.agent_metrics
        return metrics[-limit:] if metrics else []
    
    def get_experiments(self) -> Dict[str, Any]:
        """
        Get all experiments
        
        Returns:
            Dictionary of experiments
        """
        return st.session_state.experiments
    
    def get_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get a specific experiment
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Experiment data
        """
        if experiment_id not in st.session_state.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        return st.session_state.experiments[experiment_id]
    
    def visualize_agent_reasoning(self, response: Dict[str, Any]) -> None:
        """
        Visualize agent reasoning in Streamlit
        
        Args:
            response: Agent response from query_agent
        """
        output = response.get("output", "")
        reasoning = response.get("reasoning", [])
        sources = response.get("sources", [])
        metrics = response.get("metrics", {})
        
        # Display output
        st.markdown("### Agent Response")
        st.write(output)
        
        # Display reasoning if available
        if reasoning:
            with st.expander("View Agent Reasoning", expanded=False):
                if isinstance(reasoning, list):
                    for i, step in enumerate(reasoning):
                        st.markdown(f"**Step {i+1}:**")
                        st.write(step)
                else:
                    st.write(reasoning)
        
        # Display sources if available
        if sources:
            with st.expander("View Sources", expanded=False):
                if isinstance(sources, list):
                    for i, source in enumerate(sources):
                        st.markdown(f"**Source {i+1}:**")
                        st.write(source)
                else:
                    st.write(sources)
        
        # Display metrics if available
        if metrics:
            with st.expander("View Performance Metrics", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Response Time", f"{metrics.get('latency_ms', 0):.1f} ms")
                with col2:
                    st.metric("Security Score", f"{metrics.get('security_score', 0)*100:.1f}%")
                with col3:
                    st.metric("Reasoning Steps", metrics.get("reasoning_steps", 0))
                
                if metrics.get("tokens_input", 0) > 0:
                    st.metric("Input Tokens", metrics.get("tokens_input", 0))
                if metrics.get("tokens_output", 0) > 0:
                    st.metric("Output Tokens", metrics.get("tokens_output", 0))
    
    def is_langsmith_enabled(self) -> bool:
        """Check if LangSmith integration is enabled"""
        return self.langsmith_enabled
    
    def get_langsmith_traces(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent LangSmith traces
        
        Args:
            limit: Maximum number of traces to return
            
        Returns:
            List of LangSmith traces
        """
        if not self.langsmith_enabled:
            return []
        
        try:
            # Get recent runs
            runs = self.langsmith_client.list_runs(
                project_name="Finnish Politician Analysis System",
                limit=limit
            )
            return list(runs)
        except Exception as e:
            self.logger.error(f"Error retrieving LangSmith traces: {e}")
            return []
