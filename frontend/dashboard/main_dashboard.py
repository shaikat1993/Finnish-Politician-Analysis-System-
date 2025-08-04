"""
Main dashboard for FPAS
"""

import streamlit as st
import asyncio
import logging
from typing import Optional, Dict, Any
from components.sidebar import Sidebar
from components.map import FinlandMap
from components.chat import PoliticianChat
from components.analysis import AnalysisDashboard

class MainDashboard:
    def _render_politician_grid(self):
        """Fetch and render all politicians as a card grid below the map, with pagination or search results."""
        import httpx
        limit = 48  # Always define limit at the top so it's available in all branches
        # Always use st.session_state for sidebar search
        search_query = None
        party = None
        if 'sidebar_search_query' in st.session_state:
            query_val = st.session_state['sidebar_search_query'].get('query', '')
            party_val = st.session_state['sidebar_search_query'].get('party', None)
            # Trigger search if either name is 2+ chars or party is selected
            if (query_val and len(query_val.strip()) >= 2) or (party_val and party_val.strip()):
                search_query = query_val.strip() if query_val else ""
                party = party_val
        # If search is active, show filtered results (no pagination)
        if search_query is not None or (party is not None and party != ""): 
            try:
                params = {"query": search_query}
                if party:
                    params["party"] = party
                response = httpx.get(f"{self.api_base_url}/politicians/search", params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                politicians = data.get("data", [])
                total = len(politicians)
                page = 1
                next_page = None
                prev_page = None
            except Exception as e:
                self.logger.error(f"Failed to fetch search results: {e}")
                politicians = []
                total = 0
        else:
            # Elegant pagination state
            if 'politician_page' not in st.session_state:
                st.session_state.politician_page = 1
            current_page = st.session_state.politician_page
            limit = 48
            params = {"limit": limit, "page": current_page}
            try:
                response = httpx.get(f"{self.api_base_url}/politicians/", params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                politicians = data.get("data", [])
                total = data.get("total", 0)
                page = data.get("page", 1)
                next_page = data.get("next_page")
                prev_page = data.get("prev_page")
            except Exception as e:
                self.logger.error(f"Failed to fetch politicians: {e}")
                politicians = []
                total = 0
                page = 1
                next_page = None
                prev_page = None

        st.markdown("## 🇫🇮 Finnish Politicians")
        st.caption(f"Total politicians: {total}")
        if politicians:
            # Render grid with perfect alignment (4 per row, fill with spacers if needed)
            num_cols = 4
            rows = [politicians[i:i+num_cols] for i in range(0, len(politicians), num_cols)]
            for row in rows:
                cols = st.columns(num_cols)
                for idx in range(num_cols):
                    with cols[idx]:
                        if idx < len(row):
                            pol = row[idx]
                            with st.container():
                                if pol.get("image_url"):
                                    st.image(pol["image_url"], width=100)
                                else:
                                    st.image("https://via.placeholder.com/100x140?text=No+Image", width=100)
                                st.markdown(f"**{pol.get('name','')}**")
                                st.caption(f"{pol.get('party','')}")
                                if st.button(f"View details", key=f"main_view_{pol.get('id','')}"):
                                    st.session_state.selected_politician_id = pol.get('id','')
                                    st.rerun()
                        else:
                            # Empty cell for alignment
                            st.empty()
            # Centered pagination controls (only show for paginated list, not search)
            if not search_query:
                col1, col2, col3 = st.columns([2,1,2])
                with col1:
                    if prev_page and page > 1:
                        if st.button("⬅ Previous", key="prev_page"):
                            st.session_state.politician_page -= 1
                            st.rerun()
                with col2:
                    st.markdown(f"<div style='text-align:center;font-weight:bold;'>Page {page} of {((total-1)//limit)+1}</div>", unsafe_allow_html=True)
                with col3:
                    if next_page and (page * limit) < total:
                        if st.button("Next ➡", key="next_page"):
                            st.session_state.politician_page += 1
                            st.rerun()
        else:
            st.info("No politicians found.")

    """Main dashboard component"""
    
    def __init__(self, api_base_url: str):
        """
        Initialize main dashboard
        
        Args:
            api_base_url: Base URL for the API
        """
        self.api_base_url = api_base_url
        self.sidebar = Sidebar(api_base_url)
        self.map = FinlandMap(api_base_url)
        self.chat = PoliticianChat(api_base_url)
        self.analysis = AnalysisDashboard()

        self.logger = logging.getLogger(__name__)
        self._initialized = False

    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            try:
                # Initialize map data
                await self.map.load_map_data()
                self.logger.info("Map initialized successfully")
                self._initialized = True
            except Exception as e:
                self.logger.error(f"Error initializing dashboard components: {e}")
                st.error("Failed to initialize dashboard. Please check the logs.")
                raise

    async def run(self):
        """Run the dashboard"""
        try:
            # Initialize async components
            await self.initialize()
            
            # Render the dashboard
            st.title("Finnish Politician Analysis System")
            
            # Create main layout
            col1, col2 = st.columns([1, 3])
            
            with col1:
                self.sidebar.render()
                
            with col2:
                tab1, tab2, tab3 = st.tabs(["Map", "Analysis", "Chat"])
                
                with tab1:
                    self.map.render()
                    self._render_politician_grid()
                    
                with tab2:
                    self.analysis.render()
                    
                with tab3:
                    self.chat.render()
                    
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            st.error("An error occurred while running the dashboard. Please check the logs.")
    
    def run_sync(self):
        """Run the dashboard synchronously (assumes components are already initialized)"""
        try:
            # Render the dashboard
            st.title("Finnish Politician Analysis System")
            
            # Create main layout
            col1, col2 = st.columns([1, 3])
            
            with col1:
                self.sidebar.render()
                
            with col2:
                tab1, tab2, tab3 = st.tabs(["Map", "Analysis", "Chat"])
                
                with tab1:
                    self.map.render()
                    self._render_politician_grid()
                    
                with tab2:
                    self.analysis.render()
                    
                with tab3:
                    self.chat.render()
                    
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            st.error("An error occurred while running the dashboard. Please check the logs.")


def main():
    """Main entry point for the dashboard"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize and run the dashboard
    dashboard = MainDashboard("http://localhost:8000/api/v1")
    asyncio.run(dashboard.run())


if __name__ == "__main__":
    main()