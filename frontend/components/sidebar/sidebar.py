"""
Sidebar component for FPAS dashboard
"""

import streamlit as st
import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from .models import SidebarState, SearchQuery


class Sidebar:
    """Sidebar component for FPAS dashboard"""
    
    def __init__(self, api_base_url: str):
        """
        Initialize sidebar component
        
        Args:
            api_base_url: Base URL for the API
        """
        self.api_base_url = api_base_url

        self.state = SidebarState(search_query=SearchQuery(query=""))
        self.logger = logging.getLogger(__name__)
        

    def render(self):
        """Render the sidebar"""
        with st.sidebar:
            st.title("FPAS Dashboard")
            
            # Search bar
            with st.form("search_form"):
                search_query = st.text_input(
                    "Search Politicians",
                    value=self.state.search_query.query,
                    placeholder="Search by name, party, or sector"
                )
                
                # Fetch party list from backend
                import httpx
                try:
                    response = httpx.get(f"{self.api_base_url}/politicians/parties", timeout=10)
                    response.raise_for_status()
                    party_options = response.json()
                    if not party_options or not isinstance(party_options, list):
                        party_options = ["All"]
                    else:
                        party_options = ["All"] + [p for p in party_options if p and p != "All"]
                except Exception as e:
                    self.logger.error(f"Failed to fetch parties: {e}")
                    party_options = ["All"]

                # Party filter (optional, placeholder logic)
                party = st.selectbox(
                    "Filter by Party",
                    party_options,
                    index=0
                )
                
                # Time period filter (optional, placeholder logic)
                time_period = st.selectbox(
                    "Time Period",
                    ["All Time", "Last Year", "Last 6 Months", "Last 3 Months"]
                )
                
                # Fix: Add submit button to form
                submitted = st.form_submit_button("Search")
                
                if submitted:
                    st.session_state.sidebar_search_query = {
                        "query": search_query,
                        "party": party if party != "All" else None,
                        "time_period": time_period
                    }
                    # Reset pagination on new search
                    st.session_state.politician_page = 1
                    
        # No results are rendered here. The main grid will display search results based on st.session_state.

    def _search_politicians(self, search_query):
        """
        Robustly call the backend search API and return a list of politicians.
        Handles all errors and guarantees correct data for sidebar rendering.
        Only calls the API if the query is at least 2 characters.
        """
        import httpx
        query_str = search_query["query"] if isinstance(search_query, dict) else getattr(search_query, "query", "")
        if not query_str or len(query_str.strip()) < 2:
            return []  # Don't call API for empty or too-short queries
        try:
            params = {"query": query_str.strip()}
            if isinstance(search_query, dict):
                party = search_query.get("party")
                if party:
                    params["party"] = party
            response = httpx.get(f"{self.api_base_url}/politicians/search", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            self.logger.error(f"Search API error: {e}")
            return []


