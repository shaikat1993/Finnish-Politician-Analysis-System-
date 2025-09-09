"""
LazyMode component for FPAS
Provides automated functionality for users who want quick access to data
"""

import streamlit as st
import logging
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
from typing import Optional, Dict, Any, List

class LazyMode:
    """
    LazyMode component that provides automated reports, visualizations,
    and predictive features with minimal user effort
    """
    
    def __init__(self, api_base_url: str):
        """Initialize with API base URL"""
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(__name__)
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize session state variables"""
        if "lazy_mode_enabled" not in st.session_state:
            st.session_state.lazy_mode_enabled = False
        if "auto_generated_reports" not in st.session_state:
            st.session_state.auto_generated_reports = {}
        if "auto_visualizations" not in st.session_state:
            st.session_state.auto_visualizations = {}
        if "top_politicians" not in st.session_state:
            st.session_state.top_politicians = []
    
    def toggle_lazy_mode(self):
        """Toggle lazy mode on/off"""
        st.session_state.lazy_mode_enabled = not st.session_state.lazy_mode_enabled
        if st.session_state.lazy_mode_enabled:
            self.logger.info("Lazy mode enabled")
        else:
            self.logger.info("Lazy mode disabled")
    
    def render_control(self):
        """Render the lazy mode control in sidebar"""
        st.sidebar.markdown("## 😴 Lazy Mode")
        enabled = st.sidebar.toggle(
            "Enable Lazy Mode",
            value=st.session_state.lazy_mode_enabled,
            help="Automatically generate reports and visualizations"
        )
        
        # Handle state change
        if enabled != st.session_state.lazy_mode_enabled:
            st.session_state.lazy_mode_enabled = enabled
            if enabled:
                spinner = st.spinner("Loading lazy mode...")
                with spinner:
                    self._fetch_top_politicians()
                    self._generate_standard_visualizations()
                st.sidebar.success("Lazy mode enabled!")
            else:
                st.sidebar.info("Lazy mode disabled.")
    
    def is_enabled(self) -> bool:
        """Check if lazy mode is enabled"""
        return st.session_state.get("lazy_mode_enabled", False)
        
    def _fetch_top_politicians(self, limit: int = 10):
        """Fetch top politicians by popularity or recent activity"""
        try:
            response = httpx.get(
                f"{self.api_base_url}/politicians/",
                params={"limit": limit, "page": 1},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract politicians from response
            politicians = []
            if isinstance(data, dict) and "data" in data:
                politicians = data["data"]
            elif isinstance(data, list):
                politicians = data
                
            st.session_state.top_politicians = politicians
            self.logger.info(f"Fetched {len(politicians)} top politicians")
        except Exception as e:
            self.logger.error(f"Failed to fetch top politicians: {e}")
            st.session_state.top_politicians = []
            
    def _fetch_politician_details(self, politician_id: str) -> Dict[str, Any]:
        """Fetch details for a specific politician"""
        try:
            response = httpx.get(
                f"{self.api_base_url}/politicians/{politician_id}/details",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract politician details from response
            if isinstance(data, dict) and "data" in data:
                if isinstance(data["data"], list) and len(data["data"]) > 0:
                    return data["data"][0]
                elif isinstance(data["data"], dict):
                    return data["data"]
            elif isinstance(data, dict):
                return data
            elif isinstance(data, list) and len(data) > 0:
                return data[0]
                
            return {}
        except Exception as e:
            self.logger.error(f"Failed to fetch politician details: {e}")
            return {}
    
    def _fetch_parties(self) -> List[Dict[str, Any]]:
        """Fetch political parties data"""
        try:
            response = httpx.get(
                f"{self.api_base_url}/politicians/parties",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract parties from response
            if isinstance(data, dict) and "parties" in data:
                return data["parties"]
            elif isinstance(data, list):
                return data
            
            # If API returns empty or unexpected format, generate from politicians
            return self._generate_parties_from_politicians()
                
        except Exception as e:
            self.logger.error(f"Failed to fetch parties: {e}")
            # Fallback to generating from politicians
            return self._generate_parties_from_politicians()
    
    def _generate_parties_from_politicians(self) -> List[Dict[str, Any]]:
        """Generate party data from politicians if API fails"""
        if "top_politicians" not in st.session_state or not st.session_state.top_politicians:
            # Sample data if no politicians available
            return [
                {"party": "Party A", "count": 45},
                {"party": "Party B", "count": 30},
                {"party": "Party C", "count": 15},
                {"party": "Party D", "count": 10}
            ]
            
        # Count politicians by party
        party_counts = {}
        for politician in st.session_state.top_politicians:
            party = politician.get("party", "Unknown")
            if party not in party_counts:
                party_counts[party] = 0
            party_counts[party] += 1
        
        # Convert to list of dicts
        return [{"party": party, "count": count} for party, count in party_counts.items()]
    
    def _fetch_provinces(self) -> List[Dict[str, Any]]:
        """Fetch provinces data"""
        try:
            response = httpx.get(
                f"{self.api_base_url}/provinces/",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract provinces from response
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            elif isinstance(data, list):
                return data
            
            # If API returns empty or unexpected format, generate from politicians
            return self._generate_provinces_from_politicians()
                
        except Exception as e:
            self.logger.error(f"Failed to fetch provinces: {e}")
            # Fallback to generating from politicians
            return self._generate_provinces_from_politicians()
    
    def _generate_provinces_from_politicians(self) -> List[Dict[str, Any]]:
        """Generate province data from politicians if API fails"""
        if "top_politicians" not in st.session_state or not st.session_state.top_politicians:
            # Sample data if no politicians available
            return [
                {"name": "Uusimaa", "politician_count": 35, "population": 1700000},
                {"name": "Pirkanmaa", "politician_count": 20, "population": 520000},
                {"name": "Varsinais-Suomi", "politician_count": 15, "population": 480000},
                {"name": "Pohjois-Pohjanmaa", "politician_count": 12, "population": 410000},
                {"name": "Keski-Suomi", "politician_count": 10, "population": 270000}
            ]
            
        # Count politicians by province/constituency
        province_counts = {}
        for politician in st.session_state.top_politicians:
            province = politician.get("province") or politician.get("constituency") or "Unknown"
            if province not in province_counts:
                province_counts[province] = {
                    "name": province,
                    "politician_count": 0,
                    "population": 0  # We don't have this data from politicians
                }
            province_counts[province]["politician_count"] += 1
        
        # Convert to list
        return list(province_counts.values())
    
    def _generate_standard_visualizations(self):
        """Generate standard visualizations"""
        # Party Distribution removed as requested
        self._generate_province_distribution()
        self._generate_activity_timeline()
    
    def _generate_party_distribution(self):
        """Generate party distribution visualization"""
        parties = self._fetch_parties()
        
        if not parties:
            self.logger.warning("No party data available for visualization")
            return
        
        try:
            # Create DataFrame for visualization
            df = pd.DataFrame(parties)
            
            # Create pie chart
            fig = px.pie(
                df,
                values="count" if "count" in df.columns else "politician_count",
                names="party",
                title="Party Distribution in Parliament",
                color_discrete_sequence=px.colors.qualitative.Bold,
                hole=0.4
            )
            
            # Update layout for better appearance
            fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                margin=dict(t=50, b=50, l=20, r=20)
            )
            
            # Store visualization
            st.session_state.auto_visualizations["party_distribution"] = fig
            self.logger.info("Generated party distribution visualization")
        except Exception as e:
            self.logger.error(f"Failed to generate party distribution visualization: {e}")
    
    def _generate_province_distribution(self):
        """Generate province distribution visualization"""
        provinces = self._fetch_provinces()
        
        if not provinces:
            self.logger.warning("No province data available for visualization")
            return
        
        try:
            # Extract relevant data
            province_data = []
            for province in provinces:
                province_data.append({
                    "province": province.get("name", "Unknown"),
                    "politicians": province.get("politician_count", 0),
                    "population": province.get("population", 0)
                })
            
            # Create DataFrame for visualization
            df = pd.DataFrame(province_data)
            
            # Sort by politician count for better visualization
            df = df.sort_values("politicians", ascending=False)
            
            # Create bar chart
            fig = px.bar(
                df,
                x="province",
                y="politicians",
                title="Politicians by Province",
                color="population",
                color_continuous_scale=px.colors.sequential.Viridis,
                labels={"province": "Province", "politicians": "Number of Politicians", "population": "Population"}
            )
            
            # Update layout for better appearance
            fig.update_layout(
                xaxis_tickangle=-45,
                margin=dict(t=50, b=100, l=50, r=50)
            )
            
            # Store visualization
            st.session_state.auto_visualizations["province_distribution"] = fig
            self.logger.info("Generated province distribution visualization")
        except Exception as e:
            self.logger.error(f"Failed to generate province distribution visualization: {e}")
    
    def _generate_activity_timeline(self):
        """Generate politician activity timeline"""
        try:
            # Try to get activity data from API
            try:
                response = httpx.get(
                    f"{self.api_base_url}/politicians/activity",
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract activity data
                if isinstance(data, dict):
                    months = data.get("months", [])
                    activities = data.get("activities", [])
                    speeches = data.get("speeches", [])
                    votes = data.get("votes", [])
                    
                    if months and activities and speeches and votes:
                        # Use API data
                        pass
                    else:
                        # Generate from news if API data is incomplete
                        months, activities, speeches, votes = self._generate_activity_data_from_news()
                else:
                    # Generate from news if API data is not in expected format
                    months, activities, speeches, votes = self._generate_activity_data_from_news()
            except Exception as e:
                self.logger.error(f"Failed to fetch activity data: {e}")
                # Generate from news if API fails
                months, activities, speeches, votes = self._generate_activity_data_from_news()
            
            # Create DataFrame for visualization
            df = pd.DataFrame({
                "Month": months,
                "Parliamentary Activities": activities,
                "Speeches": speeches,
                "Votes": votes
            })
            
            # Create line chart
            fig = go.Figure()
            
            # Add traces for each activity type
            fig.add_trace(go.Scatter(
                x=df["Month"],
                y=df["Parliamentary Activities"],
                mode="lines+markers",
                name="Activities",
                line=dict(color="royalblue", width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=df["Month"],
                y=df["Speeches"],
                mode="lines+markers",
                name="Speeches",
                line=dict(color="firebrick", width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=df["Month"],
                y=df["Votes"],
                mode="lines+markers",
                name="Votes",
                line=dict(color="green", width=3)
            ))
            
            # Update layout for better appearance
            fig.update_layout(
                title="Parliamentary Activity Timeline (Last 6 Months)",
                xaxis_title="Month",
                yaxis_title="Count",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                margin=dict(t=50, b=100, l=50, r=50),
                hovermode="x unified"
            )
            
            # Store visualization
            st.session_state.auto_visualizations["activity_timeline"] = fig
            self.logger.info("Generated activity timeline visualization")
        except Exception as e:
            self.logger.error(f"Failed to generate activity timeline visualization: {e}")
            
    def _generate_activity_data_from_news(self):
        """Generate activity data from news articles"""
        # Default sample data
        default_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        default_activities = [12, 18, 15, 22, 19, 25]
        default_speeches = [8, 14, 10, 18, 15, 20]
        default_votes = [20, 25, 18, 30, 22, 35]
        
        # Check if we have any politician details with news
        news_counts_by_month = {}
        
        # Get all cached politician details that have news
        for key, details in st.session_state.get("auto_generated_reports", {}).items():
            if not isinstance(details, dict):
                continue
                
            news = details.get("news", [])
            if not news:
                continue
                
            # Count news by month
            for article in news:
                date_str = article.get("date") or article.get("published_date")
                if not date_str:
                    continue
                    
                try:
                    # Try to extract month from date string
                    if isinstance(date_str, str):
                        # Try to extract month name
                        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                        
                        # Check for month name in date string
                        month = None
                        for i, name in enumerate(month_names):
                            if name in date_str:
                                month = name
                                break
                        
                        # If no month name found, try to extract from numeric format
                        if not month and "-" in date_str:
                            parts = date_str.split("-")
                            if len(parts) >= 2:
                                try:
                                    month_num = int(parts[1])
                                    if 1 <= month_num <= 12:
                                        month = month_names[month_num - 1]
                                except ValueError:
                                    pass
                        
                        if month:
                            if month not in news_counts_by_month:
                                news_counts_by_month[month] = 0
                            news_counts_by_month[month] += 1
                except Exception:
                    continue
        
        # If we have news data, use it
        if news_counts_by_month:
            # Get months in order
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            
            # Filter to only months with data
            months = [m for m in months if m in news_counts_by_month]
            
            # If we have less than 3 months with data, use default
            if len(months) < 3:
                return default_months, default_activities, default_speeches, default_votes
            
            # Get counts for each month
            activities = [news_counts_by_month.get(m, 0) for m in months]
            
            # Generate synthetic data for speeches and votes based on news counts
            import random
            speeches = [max(1, int(count * random.uniform(0.5, 0.8))) for count in activities]
            votes = [max(1, int(count * random.uniform(1.0, 1.5))) for count in activities]
            
            return months, activities, speeches, votes
        
        # If no news data, return default
        return default_months, default_activities, default_speeches, default_votes
    
    def render_reports(self):
        """Render automated politician reports"""
        if not self.is_enabled():
            st.info("Enable Lazy Mode in the sidebar to see automated reports")
            return
        
        st.header("📊 Automated Politician Reports")
        st.write("Here are the top politicians in Finland:")
        
        if not st.session_state.top_politicians:
            with st.spinner("Fetching top politicians..."):
                self._fetch_top_politicians()
        
        if not st.session_state.top_politicians:
            st.error("Failed to fetch politician data. Please try again later.")
            return
            
        # Display top politicians in a clean format
        for i, politician in enumerate(st.session_state.top_politicians):
            politician_id = politician.get("id")
            politician_name = politician.get("name", "Unknown")
            
            with st.expander(f"{i+1}. {politician_name} ({politician.get('party', '')})"):
                col1, col2 = st.columns([1, 3])
                
                # Image
                with col1:
                    image_url = politician.get("image_url")
                    if image_url and isinstance(image_url, str):
                        st.image(image_url, width=100)
                    else:
                        st.markdown("No image available")
                
                # Basic details
                with col2:
                    st.markdown(f"**Party:** {politician.get('party', 'Unknown')}")
                    st.markdown(f"**Position:** {politician.get('position', politician.get('title', 'Member of Parliament'))}")
                    st.markdown(f"**Province/Constituency:** {politician.get('province', politician.get('constituency', 'Unknown'))}")
                    
                    # Add "View Full Details" button
                    if st.button("View Full Details", key=f"lazy_view_details_{politician_id}_{i}"):
                        st.session_state.selected_politician_id = politician_id
                        st.session_state.selected_politician_details = None
                        st.session_state.analysis_loading = True
                        st.rerun()
                
                # Check if we have detailed report cached
                report_key = f"report_{politician_id}"
                if report_key not in st.session_state.auto_generated_reports:
                    # Fetch more details if not cached
                    with st.spinner(f"Generating report for {politician_name}..."):
                        details = self._fetch_politician_details(politician_id)
                        
                        # Cache the details
                        if details:
                            st.session_state.auto_generated_reports[report_key] = details
                
                # Display detailed report if available
                if report_key in st.session_state.auto_generated_reports:
                    details = st.session_state.auto_generated_reports[report_key]
                    
                    # Wikipedia summary
                    wikipedia = details.get("wikipedia", {})
                    if isinstance(wikipedia, dict) and wikipedia.get("summary"):
                        st.subheader("📚 Background")
                        st.write(wikipedia.get("summary"))
                    
                    # News articles
                    news = details.get("news", [])
                    if news:
                        st.subheader("📰 Recent News")
                        for article in news[:3]:  # Show only top 3 news
                            title = article.get("title") or article.get("headline") or "Untitled"
                            url = article.get("url")
                            date = article.get("date") or article.get("published_date") or ""
                            source = article.get("source") or ""
                            
                            # Title as link
                            if url:
                                st.markdown(f"**[{title}]({url})**")
                            else:
                                st.markdown(f"**{title}**")
                            
                            # Date and source
                            caption = " | ".join(filter(None, [date, source]))
                            if caption:
                                st.caption(caption)
                        
                        if len(news) > 3:
                            st.caption(f"... and {len(news) - 3} more news articles")
                    
                    # Links
                    links = details.get("links", [])
                    if links:
                        st.subheader("🔗 Additional Resources")
                        for link in links:
                            if isinstance(link, dict):
                                label = link.get("label", "Link")
                                url = link.get("url", "")
                                if url:
                                    st.markdown(f"• [{label}]({url})")
    
    def render_visualizations(self):
        """Render auto-generated visualizations"""
        if not self.is_enabled():
            st.info("Enable Lazy Mode in the sidebar to see auto-generated visualizations")
            return
        
        st.header("📈 Auto-Generated Visualizations")
        
        # Check if visualizations exist, generate if not
        if "auto_visualizations" not in st.session_state or not st.session_state.auto_visualizations:
            with st.spinner("Generating visualizations..."):
                self._generate_standard_visualizations()
        
        # Display visualizations in tabs
        tabs = st.tabs(["Province Distribution", "Activity Timeline"])
        
        with tabs[0]:
            if "province_distribution" in st.session_state.auto_visualizations:
                st.plotly_chart(st.session_state.auto_visualizations["province_distribution"], use_container_width=True)
            else:
                with st.spinner("Generating province distribution..."):
                    self._generate_province_distribution()
                if "province_distribution" in st.session_state.auto_visualizations:
                    st.plotly_chart(st.session_state.auto_visualizations["province_distribution"], use_container_width=True)
                else:
                    st.error("Failed to generate province distribution visualization")
        
        with tabs[1]:
            if "activity_timeline" in st.session_state.auto_visualizations:
                st.plotly_chart(st.session_state.auto_visualizations["activity_timeline"], use_container_width=True)
            else:
                with st.spinner("Generating activity timeline..."):
                    self._generate_activity_timeline()
                if "activity_timeline" in st.session_state.auto_visualizations:
                    st.plotly_chart(st.session_state.auto_visualizations["activity_timeline"], use_container_width=True)
                else:
                    st.error("Failed to generate activity timeline visualization")
    
    def render(self):
        """Render all lazy mode features"""
        if not self.is_enabled():
            st.info("Enable Lazy Mode in the sidebar to access automatic reports and visualizations")
            if st.button("Enable Lazy Mode"):
                st.session_state.lazy_mode_enabled = True
                st.rerun()
            return
        
        # Render tabs for different features
        tabs = st.tabs(["Reports", "Visualizations"])
        
        with tabs[0]:
            self.render_reports()
        
        with tabs[1]:
            self.render_visualizations()
