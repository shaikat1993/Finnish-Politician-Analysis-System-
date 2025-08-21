"""
LangSmith Tracing Visualizer
Component for visualizing LangChain traces from LangSmith
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Union
import requests
import os
import json
from datetime import datetime, timedelta
import time
import networkx as nx
from pyvis.network import Network

# Constants
DEFAULT_LANGSMITH_API_URL = "https://api.smith.langchain.com"
DEFAULT_LANGSMITH_PROJECT = "fpas-analysis"


class LangSmithVisualizer:
    """
    Component for visualizing LangChain traces from LangSmith
    
    Features:
    - Fetch and display trace data from LangSmith
    - Visualize trace execution graphs
    - Show token usage and latency metrics
    - Compare different runs and trace patterns
    """
    
    def __init__(self, 
                api_key: Optional[str] = None,
                api_url: str = DEFAULT_LANGSMITH_API_URL,
                project_name: str = DEFAULT_LANGSMITH_PROJECT):
        """
        Initialize the LangSmith visualizer
        
        Args:
            api_key: LangSmith API key (defaults to LANGCHAIN_API_KEY env var)
            api_url: LangSmith API URL
            project_name: LangSmith project name
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.environ.get("LANGCHAIN_API_KEY")
        self.api_url = api_url
        self.project_name = project_name
        
        # Check if LangSmith integration is available
        self.is_available = self.api_key is not None
        
        # Initialize session state
        if "selected_run_id" not in st.session_state:
            st.session_state.selected_run_id = None
        
        if "time_range" not in st.session_state:
            st.session_state.time_range = "1d"  # Default to 1 day
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make API request to LangSmith
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response as dict
        """
        if not self.is_available:
            return {"error": "LangSmith API key not available"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        url = f"{self.api_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_runs(self, 
                limit: int = 50, 
                time_range: str = "1d",
                run_type: Optional[str] = None) -> List[Dict]:
        """
        Get runs from LangSmith
        
        Args:
            limit: Maximum number of runs to fetch
            time_range: Time range (e.g., "1h", "1d", "7d")
            run_type: Filter by run type
            
        Returns:
            List of runs
        """
        # Calculate start time based on time range
        now = datetime.now()
        
        if time_range == "1h":
            start_time = now - timedelta(hours=1)
        elif time_range == "6h":
            start_time = now - timedelta(hours=6)
        elif time_range == "1d":
            start_time = now - timedelta(days=1)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        elif time_range == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)
        
        # Format start time
        start_time_str = start_time.isoformat()
        
        # Set up parameters
        params = {
            "project_name": self.project_name,
            "start_time": start_time_str,
            "limit": limit
        }
        
        if run_type:
            params["run_type"] = run_type
        
        # Make API request
        response = self._make_api_request("runs", params)
        
        if "error" in response:
            return []
        
        return response.get("runs", [])
    
    def get_run_details(self, run_id: str) -> Dict:
        """
        Get details for a specific run
        
        Args:
            run_id: Run ID
            
        Returns:
            Run details
        """
        response = self._make_api_request(f"runs/{run_id}")
        
        if "error" in response:
            return {}
        
        return response
    
    def get_trace(self, run_id: str) -> List[Dict]:
        """
        Get trace for a specific run
        
        Args:
            run_id: Run ID
            
        Returns:
            Trace data
        """
        response = self._make_api_request(f"runs/{run_id}/trace")
        
        if "error" in response:
            return []
        
        return response.get("child_runs", [])
    
    def _build_trace_graph(self, trace_data: List[Dict]) -> nx.DiGraph:
        """
        Build a directed graph from trace data
        
        Args:
            trace_data: Trace data
            
        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()
        
        # Map of run_id to node index
        id_to_idx = {}
        
        # Add nodes
        for i, run in enumerate(trace_data):
            run_id = run.get("id")
            name = run.get("name", "Unknown")
            run_type = run.get("run_type", "Unknown")
            
            # Add node
            G.add_node(run_id, name=name, run_type=run_type, data=run)
            id_to_idx[run_id] = i
        
        # Add edges based on parent-child relationships
        for run in trace_data:
            run_id = run.get("id")
            parent_id = run.get("parent_run_id")
            
            if parent_id and parent_id in id_to_idx:
                G.add_edge(parent_id, run_id)
        
        return G
    
    def _create_trace_visualization(self, G: nx.DiGraph, height: str = "600px") -> None:
        """
        Create an interactive visualization of the trace graph
        
        Args:
            G: NetworkX directed graph
            height: Height of the visualization
        """
        # Create pyvis network
        net = Network(height=height, width="100%", directed=True, notebook=False)
        
        # Add nodes
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            name = node_data.get("name", "Unknown")
            run_type = node_data.get("run_type", "Unknown")
            
            # Set node color based on run type
            if run_type == "chain":
                color = "#3498db"  # Blue
            elif run_type == "llm":
                color = "#2ecc71"  # Green
            elif run_type == "tool":
                color = "#e74c3c"  # Red
            elif run_type == "retriever":
                color = "#9b59b6"  # Purple
            else:
                color = "#95a5a6"  # Gray
            
            net.add_node(node_id, label=name, title=f"{name} ({run_type})", color=color)
        
        # Add edges
        for edge in G.edges():
            net.add_edge(edge[0], edge[1])
        
        # Set physics layout
        net.barnes_hut(spring_length=200)
        
        # Generate HTML
        html = net.generate_html()
        
        # Display in Streamlit
        st.components.v1.html(html, height=height)
    
    def render_run_list(self, time_range: str = "1d", limit: int = 50) -> None:
        """
        Render list of recent runs
        
        Args:
            time_range: Time range (e.g., "1h", "1d", "7d")
            limit: Maximum number of runs to display
        """
        st.subheader("Recent Traces")
        
        # Time range selector
        col1, col2 = st.columns([3, 1])
        
        with col1:
            time_options = {
                "1h": "Last hour",
                "6h": "Last 6 hours",
                "1d": "Last day",
                "7d": "Last week",
                "30d": "Last 30 days"
            }
            
            selected_range = st.selectbox(
                "Time Range",
                options=list(time_options.keys()),
                format_func=lambda x: time_options[x],
                index=list(time_options.keys()).index(time_range)
            )
            
            st.session_state.time_range = selected_range
        
        with col2:
            st.number_input("Limit", min_value=10, max_value=100, value=limit, step=10, key="run_limit")
        
        # Fetch runs
        with st.spinner("Fetching traces..."):
            runs = self.get_runs(
                limit=st.session_state.get("run_limit", limit),
                time_range=st.session_state.time_range
            )
        
        if not runs:
            st.info("No traces found for the selected time range")
            return
        
        # Convert to DataFrame
        runs_data = []
        
        for run in runs:
            # Extract basic info
            run_id = run.get("id", "")
            name = run.get("name", "Unknown")
            run_type = run.get("run_type", "Unknown")
            status = run.get("status", "Unknown")
            
            # Extract timestamps
            start_time = run.get("start_time")
            end_time = run.get("end_time")
            
            # Calculate duration if both timestamps exist
            duration_ms = None
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                duration_ms = (end_dt - start_dt).total_seconds() * 1000
            
            # Extract token usage
            token_usage = run.get("extra", {}).get("token_usage", {})
            total_tokens = sum(token_usage.values()) if token_usage else None
            
            # Format timestamp
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                formatted_time = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_time = "Unknown"
            
            # Add to data
            runs_data.append({
                "id": run_id,
                "name": name,
                "type": run_type,
                "status": status,
                "time": formatted_time,
                "duration_ms": duration_ms,
                "tokens": total_tokens
            })
        
        # Create DataFrame
        df = pd.DataFrame(runs_data)
        
        # Display as table
        st.dataframe(
            df,
            column_config={
                "id": "Run ID",
                "name": "Name",
                "type": "Type",
                "status": "Status",
                "time": "Start Time",
                "duration_ms": st.column_config.NumberColumn(
                    "Duration (ms)",
                    format="%.1f ms"
                ),
                "tokens": "Tokens"
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Select run
        selected_id = st.selectbox(
            "Select Run to Visualize",
            options=df["id"].tolist(),
            format_func=lambda x: f"{df[df['id'] == x]['name'].values[0]} ({x})"
        )
        
        if selected_id:
            st.session_state.selected_run_id = selected_id
    
    def render_trace_visualization(self, run_id: str) -> None:
        """
        Render trace visualization for a specific run
        
        Args:
            run_id: Run ID
        """
        # Fetch trace data
        with st.spinner("Fetching trace data..."):
            trace_data = self.get_trace(run_id)
        
        if not trace_data:
            st.warning("No trace data available for this run")
            return
        
        # Get run details
        run_details = self.get_run_details(run_id)
        
        # Display run info
        st.subheader("Trace Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Name", run_details.get("name", "Unknown"))
        
        with col2:
            st.metric("Status", run_details.get("status", "Unknown"))
        
        with col3:
            # Calculate duration
            start_time = run_details.get("start_time")
            end_time = run_details.get("end_time")
            
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                duration_ms = (end_dt - start_dt).total_seconds() * 1000
                st.metric("Duration", f"{duration_ms:.1f} ms")
        
        # Display token usage if available
        token_usage = run_details.get("extra", {}).get("token_usage", {})
        if token_usage:
            st.subheader("Token Usage")
            
            # Create columns for each token type
            cols = st.columns(len(token_usage))
            
            for i, (token_type, count) in enumerate(token_usage.items()):
                with cols[i]:
                    st.metric(token_type.capitalize(), count)
        
        # Build trace graph
        G = self._build_trace_graph(trace_data)
        
        # Visualize trace
        st.subheader("Trace Visualization")
        self._create_trace_visualization(G)
        
        # Display trace statistics
        st.subheader("Trace Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Steps", len(trace_data))
        
        with col2:
            llm_calls = sum(1 for run in trace_data if run.get("run_type") == "llm")
            st.metric("LLM Calls", llm_calls)
        
        with col3:
            tool_calls = sum(1 for run in trace_data if run.get("run_type") == "tool")
            st.metric("Tool Calls", tool_calls)
        
        with col4:
            chain_calls = sum(1 for run in trace_data if run.get("run_type") == "chain")
            st.metric("Chain Calls", chain_calls)
        
        # Display trace timeline
        st.subheader("Trace Timeline")
        
        # Prepare timeline data
        timeline_data = []
        
        for run in trace_data:
            start_time = run.get("start_time")
            end_time = run.get("end_time")
            
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                
                timeline_data.append({
                    "Task": run.get("name", "Unknown"),
                    "Start": start_dt,
                    "Finish": end_dt,
                    "Type": run.get("run_type", "Unknown")
                })
        
        if timeline_data:
            df = pd.DataFrame(timeline_data)
            
            # Sort by start time
            df = df.sort_values("Start")
            
            # Create Gantt chart
            fig = px.timeline(
                df, 
                x_start="Start", 
                x_end="Finish", 
                y="Task",
                color="Type",
                title="Trace Timeline"
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Step",
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render(self):
        """Render the LangSmith visualizer UI"""
        st.title("LangSmith Trace Visualization")
        
        if not self.is_available:
            st.warning(
                "LangSmith API key not available. Set the LANGCHAIN_API_KEY environment variable "
                "or provide an API key to the constructor."
            )
            
            # Show demo mode option
            if st.button("Use Demo Mode"):
                st.session_state.demo_mode = True
            else:
                return
        
        # Render run list
        self.render_run_list(time_range=st.session_state.time_range)
        
        # Render trace visualization if a run is selected
        if st.session_state.selected_run_id:
            self.render_trace_visualization(st.session_state.selected_run_id)


# For standalone testing
if __name__ == "__main__":
    visualizer = LangSmithVisualizer()
    visualizer.render()
