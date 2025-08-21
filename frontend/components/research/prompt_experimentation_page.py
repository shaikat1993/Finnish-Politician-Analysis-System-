"""
Prompt Experimentation Framework Page
Standalone page for research-grade prompt experimentation and analysis
"""

import streamlit as st
from typing import Optional
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import components
from frontend.components.research.prompt_experimentation import PromptExperimentationFramework


def main():
    """Main function to run the prompt experimentation page"""
    # Page configuration
    st.set_page_config(
        page_title="AI Prompt Experimentation",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stForm {
        background-color: white;
        padding: 20px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 20px;
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
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("Finnish Politician Analysis System")
    st.header("Prompt Experimentation Framework")
    st.markdown("""
    This research-grade framework allows you to systematically test different prompt variations 
    and analyze their impact on AI responses when analyzing Finnish politicians.
    """)
    
    # Initialize and render framework
    framework = PromptExperimentationFramework(experiments_dir="prompt_experiments")
    framework.render()


if __name__ == "__main__":
    main()
