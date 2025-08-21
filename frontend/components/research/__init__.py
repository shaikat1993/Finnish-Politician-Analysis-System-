"""
Research components for the Finnish Politician Analysis System
Provides advanced AI pipeline integration for academic research
"""

from .ai_pipeline_service import EliteAIPipelineService
from .agent_visualizer import AgentVisualizer

# Import LangSmithVisualizer conditionally to handle missing networkx dependency
try:
    from .langsmith_visualizer import LangSmithVisualizer
except ImportError:
    # Create a stub class to avoid errors when networkx is not available
    class LangSmithVisualizer:
        """Stub class when dependencies are missing"""
        def __init__(self, *args, **kwargs):
            import streamlit as st
            st.warning("⚠️ LangSmithVisualizer is not available. Missing dependencies: networkx")
            
        def render(self, *args, **kwargs):
            import streamlit as st
            st.warning("⚠️ LangSmithVisualizer is not available. Missing dependencies: networkx")
