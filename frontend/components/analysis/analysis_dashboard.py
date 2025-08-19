"""
Simple and minimal politician dashboard
Clean display of politician information from API response
"""

import streamlit as st
from typing import Optional, Dict
import logging

class AnalysisDashboard:
    """Simple dashboard for politician information display"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _get_party_name(self, party_code: str) -> str:
        party_map = {
            'vas': 'Vasemmistoliitto',
            'kok': 'Kansallinen Kokoomus',
            'ps': 'Perussuomalaiset',
            'kesk': 'Keskusta',
            'sdp': 'Suomen Sosialidemokraattinen Puolue',
            'vihr': 'Vihreä liitto',
            'rkp': 'Svenska folkpartiet',
            'kd': 'Kristillisdemokraatit',
            'liik': 'Liike Nyt'
        }
        return party_map.get(str(party_code).lower(), party_code.upper()) if party_code else "Not specified"

    def render(self, politician_details: Optional[Dict] = None, loading: bool = False, error: Optional[str] = None):
        container = st.empty()
        with container:
            st.title("🏛️ Politician Information")
            # --- DEBUG: Show session state ---
            
        # Loading, error, or empty state
        if loading:
            st.info("⏳ Loading shaikat politician details...")
            return
        if error:
            st.error(f"❌ Failed to load details: {error}")
            return
        if not politician_details:
            st.info("👈 Select a politician from the sidebar to view their information.")
            return

        # Errors from API
        errors = politician_details.get('errors', [])
        if errors:
            with st.expander("⚠️ Data Source Issues"):
                st.warning("Some information may be incomplete due to the following issues:")
                for err in errors:
                    st.code(err)

        # --- IMAGE (robust fallback) ---
        image_url = politician_details.get("image_url")
        if not image_url:
            wikipedia = politician_details.get("wikipedia", {})
            image_url = wikipedia.get("image_url")
        
        # Try to get image from session state if not found in current details
        if not image_url and 'selected_politician_image' in st.session_state:
            image_url = st.session_state['selected_politician_image']
            
        if image_url:
            st.image(image_url, width=140)
        else:
            st.image("https://via.placeholder.com/140x200?text=No+Image", width=140)

        # --- BASIC INFO ---
        name = politician_details.get("name", "Unknown")
        politician_id = politician_details.get("id", "N/A")
        party_code = politician_details.get("party", "")
        party_name = self._get_party_name(party_code)
        position = politician_details.get("position") or politician_details.get("title") or "Member of Parliament"
        years_served = politician_details.get("years_served") or "Current term"
        province = politician_details.get("province") or politician_details.get("constituency") or "-"
        
        st.header(f"{name}")
        st.markdown(f"**ID:** {politician_id}")
        st.markdown(f"**Party:** {party_name}")
        st.markdown(f"**Province/Constituency:** {province}")
        st.markdown(f"**Position:** {position}")
        st.markdown(f"**Service:** {years_served}")

        # --- WIKIPEDIA ---
        wikipedia = politician_details.get("wikipedia", {})
        if isinstance(wikipedia, dict):
            wiki_url = wikipedia.get("url") or politician_details.get("wikipedia_url")
            wiki_summary = wikipedia.get("summary") or politician_details.get("wikipedia_summary")
            if wiki_summary or wiki_url:
                st.subheader("📚 Wikipedia Information")
                if wiki_summary:
                    st.write(wiki_summary)
                if wiki_url:
                    st.markdown(f"🔗 [View Wikipedia Page]({wiki_url})")

        # --- NEWS ---
        news = politician_details.get("news", [])
        if news:
            st.subheader("📰 Latest News")
            
            # Create columns for better layout
            for i, article in enumerate(news):
                title = article.get("title", "Untitled")
                url = article.get("url", "")
                source = article.get("source", "")
                
                # Format the date properly
                date_str = "Unknown date"
                published_date = article.get("published_date") or article.get("published_at")
                if published_date:
                    try:
                        # If it's a datetime object
                        if hasattr(published_date, 'strftime'):
                            date_str = published_date.strftime("%d.%m.%Y")
                        # If it's a string, try to parse it
                        elif isinstance(published_date, str):
                            from datetime import datetime
                            date_obj = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                            date_str = date_obj.strftime("%d.%m.%Y")
                    except Exception:
                        date_str = str(published_date)
                
                # Add source icon based on the news source
                source_icon = "📄"
                if "yle" in str(source).lower():
                    source_icon = "🔷"
                elif "helsingin" in str(source).lower() or "hs.fi" in str(source).lower():
                    source_icon = "🔶"
                elif "iltalehti" in str(source).lower():
                    source_icon = "🔴"
                elif "mtv" in str(source).lower():
                    source_icon = "🔵"
                elif "ilta-sanomat" in str(source).lower() or "is.fi" in str(source).lower():
                    source_icon = "🟠"
                
                # Create a card-like effect with expander
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if url:
                            st.markdown(f"### [{title}]({url})")
                        else:
                            st.markdown(f"### {title}")
                    with col2:
                        st.markdown(f"<div style='text-align: right'>{source_icon} {source}<br>{date_str}</div>", unsafe_allow_html=True)
                    
                    # Add a divider between articles
                    if i < len(news) - 1:
                        st.markdown("---")
        
        # --- LINKS ---
        links = politician_details.get("links", [])
        if links:
            st.subheader("🔗 Additional Links")
            for link_item in links:
                if isinstance(link_item, dict):
                    label = link_item.get("label", "Link")
                    url = link_item.get("url", "")
                    if url:
                        st.markdown(f"• [{label}]({url})")

        st.caption("ℹ️ Information sourced from Finnish Parliament Open Data and Wikipedia")