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

def render_politician_details(details, loading=False, error=None):
    container = st.empty()
    with container:
        st.title("🏛️ Politician Information")
        if loading:
            st.info("⏳ Loading politician details...")
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
        
        # Try to get image from session state if not found in current details
        if not image_url and 'selected_politician_image' in st.session_state:
            image_url = st.session_state['selected_politician_image']
            
        # Use MainDashboard's validation method
        # Since this is a standalone function, we can't use self._is_valid_image_url
        # So we'll implement the validation inline
        is_valid_url = False
        if image_url and isinstance(image_url, str):
            if image_url.startswith(('http://', 'https://')):
                # Reject placeholder URLs
                if 'placeholder.com' not in image_url.lower():
                    # Reject common invalid values
                    invalid_values = ['0', 'none', 'null', 'undefined', 'n/a']
                    if image_url.lower() not in invalid_values:
                        is_valid_url = True
        
        if is_valid_url:
            # Use HTML to control both width and height with proper aspect ratio
            st.markdown(f"""
            <div style="width:140px; height:180px; overflow:hidden; border-radius:5px;">
                <img src="{image_url}" style="width:100%; height:100%; object-fit:cover; object-position:top;">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="width:140px; height:180px; overflow:hidden; border-radius:5px;">
                <img src="https://via.placeholder.com/140x180?text=No+Image" style="width:100%; height:100%; object-fit:cover;">
            </div>
            """, unsafe_allow_html=True)
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
        # NEWS Section
        news = details.get("news", [])
        if news:
            st.subheader("📰 Recent News")
            for article in news:
                title = article.get("title") or article.get("headline") or "Untitled"
                url = article.get("url")
                date = article.get("date") or article.get("published_date") or ""
                source = article.get("source") or ""
                summary = article.get("summary") or article.get("content") or ""
                image_url = article.get("image_url") or (article.get("media", [None])[0] if isinstance(article.get("media"), list) and article.get("media") else None)
                # Title as link
                if url:
                    st.markdown(f"**[{title}]({url})**")
                else:
                    st.markdown(f"**{title}**")
                # Date and source
                caption = " | ".join(filter(None, [date, source]))
                if caption:
                    st.caption(caption)
                # Summary
                if summary:
                    st.write(summary if len(summary) < 400 else summary[:400] + "…")
                # Image (optional)
                if image_url:
                    st.image(image_url, width=120)
                st.markdown("---")
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

class MainDashboard:
    def set_selected_politician(self, details):
        name = details.get('name') or details.get('full_name') or details.get('id')
        if name:
            st.session_state['selected_politician'] = name
        else:
            st.session_state['selected_politician'] = str(details)
        
        # Save image URL in session state to persist across reloads
        image_url = details.get("image_url")
        if not image_url:
            wikipedia = details.get("wikipedia", {})
            if isinstance(wikipedia, dict):
                image_url = wikipedia.get("image_url")
        
        # Only save valid image URLs to session state
        if image_url and isinstance(image_url, str) and image_url.startswith(('http://', 'https://')):
            st.session_state['selected_politician_image'] = image_url

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
                                # Get image URL with fallback to session state
                                image_url = pol.get("image_url")
                                pol_id = pol.get('id', pol.get('politician_id', None))
                                
                                # If this is the selected politician and we have a saved image, use it
                                if not image_url and pol_id and pol_id == st.session_state.get('selected_politician_id') and 'selected_politician_image' in st.session_state:
                                    image_url = st.session_state['selected_politician_image']
                                
                                # Validate image URL to prevent broken images
                                is_valid_url = False
                                if image_url and isinstance(image_url, str):
                                    if image_url.startswith(('http://', 'https://')):
                                        # Reject placeholder URLs
                                        if 'placeholder.com' not in image_url.lower():
                                            # Reject common invalid values
                                            invalid_values = ['0', 'none', 'null', 'undefined', 'n/a']
                                            if image_url.lower() not in invalid_values:
                                                is_valid_url = True
                                
                                if is_valid_url:
                                    # Use HTML to control both width and height with proper aspect ratio
                                    st.markdown(f"""
                                    <div style="width:100px; height:130px; overflow:hidden; border-radius:5px;">
                                        <img src="{image_url}" style="width:100%; height:100%; object-fit:cover; object-position:top;">
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("""
                                    <div style="width:100px; height:130px; overflow:hidden; border-radius:5px;">
                                        <img src="https://via.placeholder.com/100x130?text=No+Image" style="width:100%; height:100%; object-fit:cover;">
                                    </div>
                                    """, unsafe_allow_html=True)
                                # Use a fixed-height div for the name to ensure consistent alignment
                                st.markdown(f"""
                                <div style="height:40px; overflow:hidden; display:flex; flex-direction:column; justify-content:center;">
                                    <div style="line-height:1.2; font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;">
                                        {pol.get('name','')}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.caption(f"{pol.get('party','')}")
                                if st.button("View Details", key=f"view_details_{pol.get('id', pol.get('politician_id', pol.get('name','')))}"):
                                    st.session_state.selected_politician_id = pol.get('id', pol.get('politician_id', None))
                                    st.session_state.selected_politician_details = None
                                    
                                    # Save image URL to session state immediately when selecting from grid
                                    image_url = pol.get("image_url")
                                    if image_url:
                                        st.session_state['selected_politician_image'] = image_url
                                    
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
                        details = response.json()
                    st.session_state.selected_politician_details = details
                    self.set_selected_politician(details)
                    st.session_state.analysis_loading = False
                    st.rerun()
            except Exception as e:
                st.session_state.analysis_loading = False
                st.session_state.details_error = str(e)
                st.rerun()
        # Render details card below grid (using robust AnalysisDashboard)
        if selected_id:
            self.analysis.render(details, loading=loading, error=error)

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
                    selected_id = st.session_state.get('selected_politician_id', None)
                    details = st.session_state.get('selected_politician_details', None)
                    loading = st.session_state.get('analysis_loading', False)
                    error = None
                    if selected_id and (details is None or details.get('id') != selected_id):
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
                                self.set_selected_politician(api_result)
                            st.session_state.analysis_loading = False
                            details = st.session_state.selected_politician_details
                            st.experimental_rerun()  # Force UI update after fetch
                        except Exception as e:
                            error = f"Failed to load details: {str(e)}"
                            st.session_state.analysis_loading = False
                            details = None
                    # Always set selected_politician if details present
                    if details:
                        self.set_selected_politician(details)
                    self.analysis.render(details, loading=loading, error=error)
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
                    if selected_id and (details is None or details.get('id') != selected_id):
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
                                self.set_selected_politician(api_result)
                            st.session_state.analysis_loading = False
                            details = st.session_state.selected_politician_details
                            st.experimental_rerun()  # Force UI update after fetch
                        except Exception as e:
                            error = f"Failed to load details: {str(e)}"
                            st.session_state.analysis_loading = False
                            details = None
                    # Always set selected_politician if details present
                    if details:
                        self.set_selected_politician(details)
                    self.analysis.render(details, loading=loading, error=error)
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