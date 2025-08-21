"""
Research Dashboard
Main dashboard for research components in the Finnish Politician Analysis System
"""

import streamlit as st
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import components
from frontend.components.research.security_dashboard import SecurityMetricsDashboard
from frontend.components.research.prompt_experimentation import PromptExperimentationFramework
from frontend.components.research.langsmith_visualizer import LangSmithVisualizer
from frontend.components.research.agent_visualizer import AgentVisualizer


def main():
    """Main function to run the research dashboard"""
    # Page configuration
    st.set_page_config(
        page_title="FPAS Research Dashboard",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .stMetric label {
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .component-container {
        background-color: white;
        padding: 20px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("Finnish Politician Analysis System")
    st.header("Research Dashboard")
    st.markdown("""
    This dashboard provides access to advanced research tools for the Finnish Politician Analysis System.
    Select a component from the sidebar to get started.
    """)
    
    # Sidebar
    with st.sidebar:
        st.title("Research Tools")
        selected_component = st.radio(
            "Select Component",
            options=[
                "Overview",
                "Security Metrics",
                "Prompt Experimentation",
                "LangSmith Tracing",
                "Agent Visualization"
            ]
        )
    
    # Display selected component
    if selected_component == "Overview":
        display_overview()
    elif selected_component == "Security Metrics":
        display_security_metrics()
    elif selected_component == "Prompt Experimentation":
        display_prompt_experimentation()
    elif selected_component == "LangSmith Tracing":
        display_langsmith_tracing()
    elif selected_component == "Agent Visualization":
        display_agent_visualization()


def display_overview():
    """Display overview of research components"""
    st.subheader("Research Components Overview")
    
    # Create cards for each component
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("🔒 Security Metrics")
            st.markdown("""
            Monitor and analyze security metrics for the AI pipeline:
            - Hate speech detection rates
            - Content filtering effectiveness
            - Input/output sanitization metrics
            - Security incident tracking
            """)
            st.button("Open Security Dashboard", key="security_btn")
    
        with st.container(border=True):
            st.subheader("🧪 Prompt Experimentation")
            st.markdown("""
            Test and optimize prompts for the AI pipeline:
            - A/B testing of different prompt strategies
            - Performance comparison across models
            - Prompt version control and history
            - Result analysis and visualization
            """)
            st.button("Open Prompt Lab", key="prompt_btn")
    
    with col2:
        with st.container(border=True):
            st.subheader("📊 LangSmith Tracing")
            st.markdown("""
            Visualize and analyze LangChain traces:
            - Execution graph visualization
            - Token usage and latency metrics
            - Trace comparison and analysis
            - Performance optimization insights
            """)
            st.button("Open Trace Visualizer", key="trace_btn")
        
        with st.container(border=True):
            st.subheader("🔍 Agent Visualization")
            st.markdown("""
            Visualize agent reasoning and decision processes:
            - Step-by-step reasoning visualization
            - Tool usage patterns and effectiveness
            - Agent thought process analysis
            - Decision tree visualization
            """)
            st.button("Open Agent Visualizer", key="agent_btn")
    
    # System status
    st.subheader("System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("API Status", "Online", delta="100%")
    
    with col2:
        st.metric("Database Status", "Connected", delta="100%")
    
    with col3:
        st.metric("AI Pipeline", "Operational", delta="98%")
    
    with col4:
        st.metric("News Collectors", "Active", delta="97%")


def display_security_metrics():
    """Display security metrics dashboard"""
    st.subheader("Security Metrics Dashboard")
    
    # Initialize and render security dashboard
    dashboard = SecurityMetricsDashboard()
    dashboard.render()


def display_prompt_experimentation():
    """Display prompt experimentation framework"""
    st.subheader("Prompt Experimentation Framework")
    
    # Initialize and render prompt experimentation framework
    framework = PromptExperimentationFramework()
    framework.render()


def display_langsmith_tracing():
    """Display LangSmith tracing visualizer"""
    st.subheader("LangSmith Tracing Visualizer")
    
    # Get API key from environment or let user input it
    api_key = os.environ.get("LANGCHAIN_API_KEY")
    
    if not api_key:
        with st.sidebar:
            st.subheader("LangSmith Configuration")
            api_key = st.text_input("LangSmith API Key", type="password")
            project_name = st.text_input("Project Name", value="fpas-analysis")
    else:
        project_name = "fpas-analysis"  # Default project name
    
    # Initialize and render visualizer
    visualizer = LangSmithVisualizer(
        api_key=api_key,
        project_name=project_name
    )
    visualizer.render()


def display_agent_visualization():
    """Display agent visualization"""
    st.subheader("Agent Visualization")
    
    # Initialize and render agent visualizer
    visualizer = AgentVisualizer()
    visualizer.render()


if __name__ == "__main__":
    main()
