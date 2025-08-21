"""
Agent Visualization Component for Research
Enhances the chat interface with reasoning chains and metrics display
"""

import streamlit as st
import pandas as pd
import altair as alt
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

class AgentVisualizer:
    """
    Agent Visualization Component
    
    Enhances the chat interface with:
    - Reasoning chain visualization
    - Security metrics display
    - Source citation visualization
    - Performance metrics
    """
    
    def __init__(self):
        """Initialize the agent visualizer"""
        # Initialize session state for visualization settings
        if "show_reasoning" not in st.session_state:
            st.session_state.show_reasoning = False
        if "show_metrics" not in st.session_state:
            st.session_state.show_metrics = False
        if "show_sources" not in st.session_state:
            st.session_state.show_sources = False
    
    def toggle_settings(self):
        """Display toggle settings for visualization options"""
        st.sidebar.markdown("### Agent Visualization Settings")
        
        # Create toggles for visualization options
        st.session_state.show_reasoning = st.sidebar.checkbox(
            "Show Agent Reasoning", 
            value=st.session_state.show_reasoning
        )
        
        st.session_state.show_metrics = st.sidebar.checkbox(
            "Show Performance Metrics", 
            value=st.session_state.show_metrics
        )
        
        st.session_state.show_sources = st.sidebar.checkbox(
            "Show Source Citations", 
            value=st.session_state.show_sources
        )
    
    def visualize_response(self, response: Dict[str, Any], container=None):
        """
        Visualize agent response with reasoning and metrics
        
        Args:
            response: Agent response from EliteAIPipelineService
            container: Optional Streamlit container to render in
        """
        # Use provided container or create a new one
        if container is None:
            container = st
        
        # Extract response components
        output = response.get("output", "")
        reasoning = response.get("reasoning", [])
        sources = response.get("sources", [])
        metrics = response.get("metrics", {})
        direct_access = response.get("direct_access", False)
        
        # Display the main response output
        container.markdown(output)
        
        # Show a badge indicating direct access or API fallback
        if direct_access:
            container.markdown(
                "<span style='background-color: #4CAF50; color: white; padding: 2px 6px; "
                "border-radius: 3px; font-size: 0.8em;'>Direct Agent Access</span>", 
                unsafe_allow_html=True
            )
        else:
            container.markdown(
                "<span style='background-color: #2196F3; color: white; padding: 2px 6px; "
                "border-radius: 3px; font-size: 0.8em;'>API Access</span>", 
                unsafe_allow_html=True
            )
        
        # Show reasoning if enabled and available
        if st.session_state.show_reasoning and reasoning:
            with container.expander("🧠 Agent Reasoning Process", expanded=True):
                self._render_reasoning_chain(reasoning, container)
        
        # Show sources if enabled and available
        if st.session_state.show_sources and sources:
            with container.expander("📚 Source Citations", expanded=True):
                self._render_sources(sources, container)
        
        # Show metrics if enabled and available
        if st.session_state.show_metrics and metrics:
            with container.expander("📊 Performance Metrics", expanded=True):
                self._render_metrics(metrics, container)
    
    def _render_reasoning_chain(self, reasoning: Any, container):
        """Render agent reasoning chain"""
        if isinstance(reasoning, list):
            for i, step in enumerate(reasoning):
                step_container = container.container()
                step_container.markdown(f"**Step {i+1}**")
                
                # Handle different step formats
                if isinstance(step, dict):
                    if "thought" in step:
                        step_container.markdown(f"*Thought:* {step['thought']}")
                    if "action" in step:
                        step_container.markdown(f"*Action:* {step['action']}")
                    if "observation" in step:
                        step_container.markdown(f"*Observation:* {step['observation']}")
                else:
                    step_container.markdown(step)
                
                # Add a divider between steps
                if i < len(reasoning) - 1:
                    container.markdown("---")
        else:
            # Handle non-list reasoning
            container.markdown(reasoning)
    
    def _render_sources(self, sources: Any, container):
        """Render source citations"""
        if isinstance(sources, list):
            for i, source in enumerate(sources):
                if isinstance(source, dict):
                    # Handle structured source format
                    title = source.get("title", f"Source {i+1}")
                    url = source.get("url", "")
                    content = source.get("content", "")
                    
                    container.markdown(f"**{title}**")
                    if url:
                        container.markdown(f"[Link]({url})")
                    if content:
                        container.markdown(content)
                else:
                    # Handle string source format
                    container.markdown(f"**Source {i+1}**")
                    container.markdown(source)
                
                # Add a divider between sources
                if i < len(sources) - 1:
                    container.markdown("---")
        else:
            # Handle non-list sources
            container.markdown(sources)
    
    def _render_metrics(self, metrics: Dict[str, Any], container):
        """Render performance metrics"""
        # Create a multi-column layout
        col1, col2, col3 = container.columns(3)
        
        # Display key metrics
        with col1:
            latency = metrics.get("latency_ms", 0)
            container.metric("Response Time", f"{latency:.1f} ms")
        
        with col2:
            security_score = metrics.get("security_score", 1.0)
            container.metric("Security Score", f"{security_score*100:.1f}%")
        
        with col3:
            steps = metrics.get("reasoning_steps", 0)
            container.metric("Reasoning Steps", steps)
        
        # Display token usage if available
        tokens_input = metrics.get("tokens_input", 0)
        tokens_output = metrics.get("tokens_output", 0)
        
        if tokens_input > 0 or tokens_output > 0:
            # Create token usage chart
            token_data = pd.DataFrame({
                "Type": ["Input", "Output"],
                "Tokens": [tokens_input, tokens_output]
            })
            
            chart = alt.Chart(token_data).mark_bar().encode(
                x=alt.X("Type", axis=alt.Axis(title=None)),
                y=alt.Y("Tokens", axis=alt.Axis(title="Token Count")),
                color=alt.Color("Type", legend=None)
            ).properties(
                height=200
            )
            
            container.altair_chart(chart, use_container_width=True)
    
    def visualize_metrics_history(self, metrics_history: List[Dict[str, Any]], container=None):
        """
        Visualize metrics history
        
        Args:
            metrics_history: List of metrics from EliteAIPipelineService
            container: Optional Streamlit container to render in
        """
        # Use provided container or create a new one
        if container is None:
            container = st
            
        if not metrics_history:
            container.info("No metrics history available yet.")
            return
            
        # Convert to DataFrame for visualization
        df = pd.DataFrame(metrics_history)
        
        # Convert timestamp strings to datetime objects if needed
        if "timestamp" in df.columns and isinstance(df["timestamp"].iloc[0], str):
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Create latency over time chart
        if "latency_ms" in df.columns:
            container.subheader("Response Time History")
            
            latency_chart = alt.Chart(df).mark_line().encode(
                x=alt.X("timestamp", axis=alt.Axis(title="Time")),
                y=alt.Y("latency_ms", axis=alt.Axis(title="Response Time (ms)"))
            ).properties(
                height=250
            )
            
            container.altair_chart(latency_chart, use_container_width=True)
        
        # Create security score over time chart
        if "security_score" in df.columns:
            container.subheader("Security Score History")
            
            security_chart = alt.Chart(df).mark_line().encode(
                x=alt.X("timestamp", axis=alt.Axis(title="Time")),
                y=alt.Y("security_score", axis=alt.Axis(title="Security Score", scale=alt.Scale(domain=[0, 1])))
            ).properties(
                height=250
            )
            
            container.altair_chart(security_chart, use_container_width=True)
        
        # Create token usage over time chart
        if "tokens_input" in df.columns and "tokens_output" in df.columns:
            container.subheader("Token Usage History")
            
            # Reshape data for grouped bar chart
            token_data = pd.melt(
                df, 
                id_vars=["timestamp"], 
                value_vars=["tokens_input", "tokens_output"],
                var_name="token_type", 
                value_name="token_count"
            )
            
            token_chart = alt.Chart(token_data).mark_bar().encode(
                x=alt.X("timestamp", axis=alt.Axis(title="Time")),
                y=alt.Y("token_count", axis=alt.Axis(title="Token Count")),
                color=alt.Color("token_type", legend=alt.Legend(title="Token Type"))
            ).properties(
                height=250
            )
            
            container.altair_chart(token_chart, use_container_width=True)
    
    def visualize_experiment_results(self, experiment: Dict[str, Any], container=None):
        """
        Visualize experiment results
        
        Args:
            experiment: Experiment data from EliteAIPipelineService
            container: Optional Streamlit container to render in
        """
        # Use provided container or create a new one
        if container is None:
            container = st
            
        # Extract experiment data
        name = experiment.get("name", "Unnamed Experiment")
        description = experiment.get("description", "")
        results = experiment.get("results", [])
        
        if not results:
            container.info("No experiment results available yet.")
            return
            
        # Display experiment information
        container.header(name)
        container.markdown(description)
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Extract parameters for comparison
        if "parameters" in results_df.columns:
            # Explode parameters into separate columns
            param_df = pd.json_normalize(results_df["parameters"])
            results_df = pd.concat([results_df, param_df], axis=1)
        
        # Extract metrics for comparison
        if "metrics" in results_df.columns:
            # Explode metrics into separate columns
            metrics_df = pd.json_normalize(results_df["metrics"])
            metrics_df = metrics_df.add_prefix("metric_")
            results_df = pd.concat([results_df, metrics_df], axis=1)
        
        # Show experiment results table
        container.subheader("Experiment Results")
        container.dataframe(results_df)
        
        # Create visualizations based on available data
        if "metric_latency_ms" in results_df.columns:
            container.subheader("Response Time by Parameter")
            
            # Get parameter columns
            param_cols = [col for col in results_df.columns if col not in 
                         ["experiment_id", "prompt_template", "parameters", 
                          "metrics", "output", "success", "error"]]
            
            # Create a chart for each parameter
            for param in param_cols:
                if param.startswith("metric_"):
                    continue
                    
                param_chart = alt.Chart(results_df).mark_bar().encode(
                    x=alt.X(param, axis=alt.Axis(title=param)),
                    y=alt.Y("metric_latency_ms", axis=alt.Axis(title="Response Time (ms)"))
                ).properties(
                    height=250,
                    title=f"Response Time by {param}"
                )
                
                container.altair_chart(param_chart, use_container_width=True)
        
        # Create security score comparison
        if "metric_security_score" in results_df.columns:
            container.subheader("Security Score by Parameter")
            
            # Get parameter columns
            param_cols = [col for col in results_df.columns if col not in 
                         ["experiment_id", "prompt_template", "parameters", 
                          "metrics", "output", "success", "error"]]
            
            # Create a chart for each parameter
            for param in param_cols:
                if param.startswith("metric_"):
                    continue
                    
                security_chart = alt.Chart(results_df).mark_bar().encode(
                    x=alt.X(param, axis=alt.Axis(title=param)),
                    y=alt.Y("metric_security_score", axis=alt.Axis(title="Security Score", scale=alt.Scale(domain=[0, 1])))
                ).properties(
                    height=250,
                    title=f"Security Score by {param}"
                )
                
                container.altair_chart(security_chart, use_container_width=True)
