"""
Main entry point for FPAS Streamlit application
"""

import asyncio
import logging
import streamlit as st
from dashboard.main_dashboard import MainDashboard


def main():
    """Main application function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize dashboard with session state
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = MainDashboard("http://localhost:8000/api/v1")
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
