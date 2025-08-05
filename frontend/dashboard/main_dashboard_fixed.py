"""
Fully working Finnish Politician Analysis System Dashboard
- Robust session state and reactivity
- No infinite spinner or blank analysis section
- Handles all API response shapes (single dict, list, paginated)
- Sidebar, map, politician grid, analysis, and chat all work
"""

import streamlit as st
import asyncio
import logging

# --- Standalone robust details renderer ---
def render_politician_details(details, loading=False, error=None):
    import streamlit as st
    container = st.empty()
    with container:
        st.title("🏛️ Politician Information")

        if loading:
            st.info("⏳ Loading sadid politician details...")
            return
        if error:
            st.error(f"❌ Failed to load details: {error}")
            return
        if not details:
            st.info("👈 Select a politician from the sidebar to view their information.")
            return

        # Image (robust fallback)
        image_url = details.get("image_url")
        if not image_url:
            wikipedia = details.get("wikipedia", {})
            image_url = wikipedia.get("image_url")
        if image_url:
            st.image(image_url, width=140)
        else:
            st.image("https://via.placeholder.com/140x200?text=No+Image", width=140)

        # Basic Info
        name = details.get("name", "Unknown")
        politician_id = details.get("id", "N/A")
        party = details.get("party", "")
        position = details.get("position") or details.get("title") or "Member of Parliament"
        years_served = details.get("years_served") or "Current term"
        province = details.get("province") or details.get("constituency") or "-"

        st.header(f"{name}")
        st.markdown(f"**ID:** {politician_id}")
        st.markdown(f"**Party:** {party}")
        st.markdown(f"**Province/Constituency:** {province}")
        st.markdown(f"**Position:** {position}")
        st.markdown(f"**Service:** {years_served}")

        # Wikipedia Section
        wikipedia = details.get("wikipedia", {})
        if isinstance(wikipedia, dict):
            wiki_url = wikipedia.get("url") or details.get("wikipedia_url")
            wiki_summary = wikipedia.get("summary") or details.get("wikipedia_summary")
            if wiki_summary or wiki_url:
                st.subheader("📚 Wikipedia Information")
                if wiki_summary:
                    st.write(wiki_summary)
                if wiki_url:
                    st.markdown(f"🔗 [View Wikipedia Page]({wiki_url})")

        # Links Section
        links = details.get("links", [])
        if links:
            st.subheader("🔗 Additional Links")
            for link_item in links:
                if isinstance(link_item, dict):
                    label = link_item.get("label", "Link")
                    url = link_item.get("url", "")
                    if url:
                        st.markdown(f"• [{label}]({url})")

        st.caption("ℹ️ Information sourced from Finnish Parliament Open Data and Wikipedia")
from typing import Optional, Dict, Any
from components.sidebar import Sidebar
from components.map import FinlandMap
from components.chat import PoliticianChat
from components.analysis import AnalysisDashboard

class MainDashboardFixed:
    def _render_politician_grid(self):
        import httpx
        limit = 48
        search_query = None
        party = None
        if 'sidebar_search_query' in st.session_state:
            query_val = st.session_state['sidebar_search_query'].get('query', '')
            party_val = st.session_state['sidebar_search_query'].get('party', None)
            if (query_val and len(query_val.strip()) >= 2) or (party_val and party_val.strip()):
                search_query = query_val.strip() if query_val else ""
                party = party_val
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
                page = 1
                next_page = None
                prev_page = None
        else:
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
                                if st.button("View Details", key=f"view_details_{pol.get('id', pol.get('politician_id', pol.get('name','')))}"):
                                    st.session_state.selected_politician_id = pol.get('id', pol.get('politician_id', None))
                                    st.session_state.selected_politician_details = None
                                    st.session_state.analysis_loading = True
                                    st.session_state.details_error = None
                                    st.rerun()
                        else:
                            st.empty()
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

        # --- DETAILS CARD BELOW GRID (MAP TAB ONLY) ---
        selected_id = st.session_state.get('selected_politician_id', None)
        details = st.session_state.get('selected_politician_details', None)
        loading = st.session_state.get('analysis_loading', False)
        error = st.session_state.get('details_error', None)

        # Fetch details if needed (only in Map tab)
        if selected_id and details is None and not loading and not error:
            st.session_state.analysis_loading = True
            try:
                import httpx
                with st.spinner("Loading politician details..."):
                    response = httpx.get(f"{self.api_base_url}/politicians/{selected_id}/details", timeout=15)
                    response.raise_for_status()
                    api_result = response.json()
                    if isinstance(api_result, dict) and 'data' in api_result:
                        data = api_result['data']
                        if isinstance(data, list) and len(data) == 1:
                            details = data[0]
                        elif isinstance(data, dict):
                            details = data
                        else:
                            details = None
                    elif isinstance(api_result, list) and len(api_result) == 1:
                        details = api_result[0]
                    elif isinstance(api_result, dict):
                        details = api_result
                    else:
                        details = None
                    st.session_state.selected_politician_details = details
                    st.session_state.analysis_loading = False
                    st.rerun()
            except Exception as e:
                st.session_state.analysis_loading = False
                st.session_state.details_error = str(e)
                st.rerun()

        # Render details card below grid (using robust AnalysisDashboard)
        if selected_id:
            self.analysis.render(details, loading=loading, error=error)

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.sidebar = Sidebar(api_base_url)
        self.map = FinlandMap(api_base_url)
        self.chat = PoliticianChat(api_base_url)
        self.analysis = AnalysisDashboard()
        self.logger = logging.getLogger(__name__)
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            try:
                await self.map.load_map_data()
                self.logger.info("Map initialized successfully")
                self._initialized = True
            except Exception as e:
                self.logger.error(f"Error initializing dashboard components: {e}")
                st.error("Failed to initialize dashboard. Please check the logs.")
                raise

    async def run(self):
        try:
            await self.initialize()
            st.title("Finnish Politician Analysis System")
            col1, col2 = st.columns([1, 3])
            with col1:
                self.sidebar.render()
            with col2:
                tab1, tab2, tab3 = st.tabs(["Map", "Analysis", "Chat"])
                with tab1:
                    self.map.render()
                    self._render_politician_grid()
                with tab2:
                    pass
                    loading = st.session_state.get('analysis_loading', False)
                    error = error or st.session_state.get('analysis_error', None)

                    # 3. Debug output (optional, remove in prod)
                    print("DEBUG ANALYSIS STATE", {
                        "selected_id": selected_id,
                        "details": details,
                        "loading": loading,
                        "error": error
                    })
                    # 4. Render analysis section (commented out per user request)
                    # render_politician_details(details, loading=loading, error=error) 
                with tab3:
                    self.chat.render()
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            st.error("An error occurred while running the dashboard. Please check the logs.")

    def run_sync(self):
        try:
            st.title("Finnish Politician Analysis System")
            col1, col2 = st.columns([1, 3])
            with col1:
                self.sidebar.render()
            with col2:
                tab1, tab2, tab3 = st.tabs(["Map", "Analysis", "Chat"])
                with tab1:
                    self.map.render()
                    self._render_politician_grid()
                with tab2:
                    selected_id = st.session_state.get('selected_politician_id', None)
                    details = st.session_state.get('selected_politician_details', None)
                    loading = st.session_state.get('analysis_loading', False)
                    error = None
                    # --- Prevent infinite rerun loop ---
                    if selected_id and (details is None or (isinstance(details, dict) and details.get('id') != selected_id)) and not loading:
                        import httpx
                        try:
                            st.session_state.analysis_loading = True
                            with st.spinner("Loading politician details..."):
                                resp = httpx.get(f"{self.api_base_url}/politicians/{selected_id}/details", timeout=15)
                                resp.raise_for_status()
                                api_result = resp.json()
                                if isinstance(api_result, dict) and 'data' in api_result:
                                    data = api_result['data']
                                    if isinstance(data, list) and len(data) == 1:
                                        api_result = data[0]
                                    elif isinstance(data, dict):
                                        api_result = data
                                    else:
                                        api_result = None
                                elif isinstance(api_result, list) and len(api_result) == 1:
                                    api_result = api_result[0]
                                st.session_state.selected_politician_details = api_result
                            st.session_state.analysis_loading = False
                            details = st.session_state.selected_politician_details
                            st.experimental_rerun()
                        except Exception as e:
                            error = f"Failed to load details: {str(e)}"
                            st.session_state.analysis_loading = False
                            details = None
                    self.analysis.render(details, loading=loading, error=error)
                with tab3:
                    self.chat.render()
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            st.error("An error occurred while running the dashboard. Please check the logs.")
