"""
Main entry point for FPAS Streamlit application
"""

import asyncio
import logging
import os
import streamlit as st
from dashboard.main_dashboard import MainDashboard


def get_api_base_url() -> str:
    """
    Get the base URL without any path components.
    The API version prefix (/api/v1) should be added in the API calls.
    
    Returns:
        str: The base URL for the API (e.g., "http://localhost:8000")
    """
    # Try to get from environment variable first
    api_base_url = os.environ.get("API_BASE_URL")
    
    # If not set, determine based on environment
    if not api_base_url:
        # Check if running in Docker
        if os.path.exists('/.dockerenv'):
            api_base_url = "http://api:8000"
        else:
            api_base_url = "http://localhost:8000"
    
    # Ensure the URL is clean (no trailing slashes or paths)
    api_base_url = api_base_url.rstrip('/')
    
    # Remove any existing /api/v1 if present
    if api_base_url.endswith('/api/v1'):
        api_base_url = api_base_url[:-7]
    
    return api_base_url


def main():
    """Main application function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get API URL based on environment
    api_base_url = get_api_base_url()
    # Only append /api/v1 if it's not already in the base URL
    api_url = f"{api_base_url}/api/v1"
    
    # Log the API URL for debugging
    logging.info(f"Using API URL: {api_url}")
    
    # Initialize dashboard with session state
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = MainDashboard(api_url)
        st.session_state.initialized = False
    
    dashboard = st.session_state.dashboard
    
    try:
        # Initialize dashboard components if not already done
        if not st.session_state.initialized:
            with st.spinner("Initializing dashboard components..."):
                try:
                    asyncio.run(dashboard.initialize())
                    st.session_state.initialized = True
                    st.rerun()
                except Exception as init_error:
                    st.error(f"Initialization failed: {str(init_error)}")
                    raise
        
        # Run dashboard
        dashboard.run_sync()
        
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        st.error("An error occurred. Please check the logs for details.")


if __name__ == "__main__":
    main()
