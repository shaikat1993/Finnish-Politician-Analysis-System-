"""
Finland map component with province visualization using Plotly
Docker-friendly, no JSON serialization issues
"""

import streamlit as st
import plotly.graph_objects as go
import json
import asyncio
import httpx
import os
import pandas as pd
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging


class ProvinceMarker(BaseModel):
    """Model for province markers"""
    id: str
    name: str
    lat: float
    lon: float
    politician_count: int
    population: int
    area: float


class FinlandMap:
    """Finland map component with province visualization"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1"):
        """Initialize Finland map"""
        self.api_base_url = api_base_url
        self.map_data = None
        self.geojson_data = None
        self.markers: List[ProvinceMarker] = []
        self.logger = logging.getLogger(__name__)
        self._map_loaded = False
        self._geojson_loaded = False
        self.total_politician_count = 0
        # Finland geographic bounds (optimized to show only Finland)
        self.finland_bounds = {
            'north': 70.0,
            'south': 59.8, 
            'west': 19.5,
            'east': 31.2
        }

    async def fetch_total_politician_count(self) -> int:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_base_url}/politicians/count")
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"Failed to fetch total politician count: {response.status_code}")
                    return 0
        except Exception as e:
            self.logger.error(f"Error fetching total politician count: {e}")
            return 0

    async def load_map_data(self):
        """Load map data asynchronously from backend API and GeoJSON"""
        try:
            # Load GeoJSON province boundaries first
            await self._load_geojson_data()
            
            # Clear existing markers
            self.markers = []
            
            # Fetch total politician count from API
            self.total_politician_count = await self.fetch_total_politician_count()
            self.logger.info(f"👥 Total politician count from API: {self.total_politician_count}")
            
            # Fetch live province data from dynamic backend
            self.logger.info("🔄 Fetching province data from API...")
            province_data = await self.fetch_province_data()
            self.logger.info(f"📡 API returned {len(province_data)} provinces")
            # Convert API response to ProvinceMarker objects
            successful_markers = 0
            for i, province in enumerate(province_data):
                try:
                    # Extract coordinates properly from the API response
                    coordinates = province.get("coordinates", {})
                    lat = coordinates.get("lat", 0.0) if isinstance(coordinates, dict) else province.get("lat", 0.0)
                    lng = coordinates.get("lon", 0.0) if isinstance(coordinates, dict) else province.get("lng", 0.0)
                    
                    self.logger.info(f"🏷️  Processing province {i+1}/{len(province_data)}: {province['id']} at ({lat}, {lng})")
                    
                    marker = ProvinceMarker(
                        id=province["id"],
                        name=province["name"],
                        lat=lat,
                        lon=lng,
                        politician_count=province["politician_count"],
                        population=province["population"],
                        area=province["area_km2"]
                    )
                    self.markers.append(marker)
                    successful_markers += 1
                    self.logger.info(f"✅ Created marker for {province['id']}")
                    
                except Exception as marker_error:
                    self.logger.error(f"❌ Failed to create marker for {province.get('id', 'unknown')}: {marker_error}")
                    # Continue processing other provinces instead of failing completely
                    continue
            
            self._map_loaded = True
            self.logger.info(f"🎯 Map data loaded successfully: {successful_markers}/{len(province_data)} province markers created from API")
            
            # Only use fallback if we got zero markers
            if successful_markers == 0:
                self.logger.warning("⚠️  No markers created from API data, using fallback")
                await self._load_fallback_data()
        
        except Exception as e:
            self.logger.error(f"💥 Critical error loading map data: {e}")
            import traceback
            self.logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            # Fallback to sample data on any error
            await self._load_fallback_data()
    
    async def fetch_province_data(self) -> List[Dict]:
        """
        Fetch live province data from backend API
        Returns comprehensive province data with official demographics
        """
        try:
            if not self.api_base_url:
                self.logger.warning("No API base URL configured, using fallback data")
                return self._get_fallback_data()
            
            # Fetch live province data from dynamic backend
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_base_url}/provinces/")
                
                if response.status_code == 200:
                    api_response = response.json()
                    
                    # Handle the API response structure: {"status": "success", "data": [...]}
                    if isinstance(api_response, dict) and "data" in api_response:
                        provinces = api_response["data"]
                    else:
                        provinces = api_response if isinstance(api_response, list) else []
                    
                    self.logger.info(f"✅ Fetched {len(provinces)} provinces from dynamic backend API")
                    
                    # Transform API data to map format
                    transformed_provinces = []
                    for province in provinces:
                        # Extract coordinates properly
                        coordinates = province.get('coordinates', {})
                        if isinstance(coordinates, dict):
                            lat = coordinates.get('lat', 0.0)
                            lng = coordinates.get('lon', 0.0)
                        else:
                            # Fallback coordinates for provinces without proper coordinates
                            fallback_coords = self._get_fallback_coordinates(province.get('id', ''))
                            lat = fallback_coords['lat']
                            lng = fallback_coords['lng']
                        
                        transformed_province = {
                            'id': province.get('id', ''),
                            'name': province.get('name', ''),
                            'name_fi': province.get('name_fi', ''),
                            'name_sv': province.get('name_sv', ''),
                            'name_en': province.get('name_en', ''),
                            'population': province.get('population', 0),
                            'area_km2': province.get('area_km2', 0),
                            'population_density': province.get('population_density', 0),
                            'politician_count': province.get('politician_count', 0),
                            'capital': province.get('capital', ''),
                            'coordinates': coordinates,
                            'lat': lat,
                            'lng': lng,
                            'source': province.get('source', 'Statistics Finland'),
                            'last_updated': province.get('last_updated', '')
                        }
                        
                        transformed_provinces.append(transformed_province)
                    
                    self.logger.info(f"📊 Live data includes {sum(p['politician_count'] for p in transformed_provinces)} total politicians")
                    return transformed_provinces
                    
                else:
                    self.logger.error(f"API request failed with status {response.status_code}")
                    return self._get_fallback_data()
                    
        except httpx.TimeoutException:
            self.logger.error("API request timed out, using fallback data")
            return self._get_fallback_data()
        except Exception as e:
            self.logger.error(f"Error fetching province data: {str(e)}")
            return self._get_fallback_data()
    
    def _get_fallback_coordinates(self, province_id: str) -> Dict[str, float]:
        """Get fallback coordinates for provinces"""
        fallback_coords = {
            'uusimaa': {'lat': 60.2, 'lng': 24.9},
            'varsinais-suomi': {'lat': 60.5, 'lng': 22.3},
            'satakunta': {'lat': 61.5, 'lng': 22.1},
            'kanta-hame': {'lat': 60.8, 'lng': 24.5},
            'pirkanmaa': {'lat': 61.5, 'lng': 23.8},
            'paijat-hame': {'lat': 61.0, 'lng': 25.7},
            'kymenlaakso': {'lat': 60.9, 'lng': 26.7},
            'etela-karjala': {'lat': 61.1, 'lng': 28.2},
            'etela-savo': {'lat': 62.0, 'lng': 27.6},
            'pohjois-savo': {'lat': 63.1, 'lng': 27.7},
            'pohjois-karjala': {'lat': 62.6, 'lng': 30.1},
            'keski-suomi': {'lat': 62.2, 'lng': 25.7},
            'etela-pohjanmaa': {'lat': 62.8, 'lng': 23.1},
            'pohjanmaa': {'lat': 63.1, 'lng': 21.6},
            'keski-pohjanmaa': {'lat': 63.8, 'lng': 23.1},
            'pohjois-pohjanmaa': {'lat': 64.9, 'lng': 25.5},
            'kainuu': {'lat': 64.2, 'lng': 27.7},
            'lappi': {'lat': 66.5, 'lng': 25.7},
            'ahvenanmaa': {'lat': 60.1, 'lng': 19.9}
        }
        return fallback_coords.get(province_id, {'lat': 64.0, 'lng': 26.0})
    
    def _get_fallback_data(self) -> List[Dict]:
        """
        Minimal fallback data if API is unavailable
        Only used as last resort - system should use live data
        """
        self.logger.warning("⚠️  Using fallback data - live API unavailable")
        
        return [
            {
                'id': 'uusimaa',
                'name': 'Uusimaa',
                'name_fi': 'Uusimaa',
                'name_sv': 'Nyland',
                'name_en': 'Uusimaa',
                'population': 1700000,
                'area_km2': 9616,
                'population_density': 177,
                'politician_count': 0,
                'capital': 'Helsinki',
                'lat': 60.2,
                'lng': 24.9,
                'source': 'Fallback Data',
                'last_updated': 'N/A'
            },
            {
                'id': 'pirkanmaa',
                'name': 'Pirkanmaa',
                'name_fi': 'Pirkanmaa',
                'name_sv': 'Birkaland',
                'name_en': 'Pirkanmaa',
                'population': 530000,
                'area_km2': 12581,
                'population_density': 42,
                'politician_count': 0,
                'capital': 'Tampere',
                'lat': 61.5,
                'lng': 23.8,
                'source': 'Fallback Data',
                'last_updated': 'N/A'
            },
            {
                'id': 'lappi',
                'name': 'Lappi',
                'name_fi': 'Lappi',
                'name_sv': 'Lappland',
                'name_en': 'Lapland',
                'population': 180000,
                'area_km2': 100367,
                'population_density': 2,
                'politician_count': 0,
                'capital': 'Rovaniemi',
                'lat': 66.5,
                'lng': 25.7,
                'source': 'Fallback Data',
                'last_updated': 'N/A'
            }
        ]
    
    async def _load_geojson_data(self):
        """Load GeoJSON province boundary data"""
        try:
            geojson_path = os.path.join(os.path.dirname(__file__), '../../data/finland-provinces.geojson')
            
            if os.path.exists(geojson_path):
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    self.geojson_data = json.load(f)
                self._geojson_loaded = True
                self.logger.info(f"GeoJSON data loaded successfully with {len(self.geojson_data.get('features', []))} province boundaries")
            else:
                self.logger.warning(f"GeoJSON file not found at {geojson_path}")
                self._geojson_loaded = False
                
        except Exception as e:
            self.logger.error(f"Error loading GeoJSON data: {e}")
            self._geojson_loaded = False
    
    async def _load_fallback_data(self):
        """Load fallback sample data when API is unavailable"""
        try:
            # Fallback sample data
            sample_provinces = [
                {"id": "uusimaa", "name": "Uusimaa", "lat": 60.1699, "lon": 24.9384, "politicians": 45, "population": 1700000, "area": 9440},
                {"id": "pirkanmaa", "name": "Pirkanmaa", "lat": 61.4991, "lon": 23.7871, "politicians": 20, "population": 530000, "area": 12581},
                {"id": "varsinais-suomi", "name": "Varsinais-Suomi", "lat": 60.4518, "lon": 22.2666, "politicians": 18, "population": 480000, "area": 10663}
            ]
            
            for province in sample_provinces:
                marker = ProvinceMarker(
                    id=province["id"],
                    name=province["name"],
                    lat=province["lat"],
                    lon=province["lon"],
                    politician_count=province["politicians"],
                    population=province["population"],
                    area=province["area"]
                )
                self.markers.append(marker)
            
            self._map_loaded = True
            self.logger.warning(f"Using fallback data with {len(self.markers)} province markers")
        except Exception as e:
            self.logger.error(f"Error loading fallback data: {e}")
            raise

    def add_marker(self, marker: ProvinceMarker):
        """Add a province marker to the map"""
        self.markers.append(marker)

    def create_province_popup_content(self, province: Dict) -> str:
        """
        Create enhanced popup content for provinces with live data
        Shows official demographics and politician counts
        """
        # Format population with thousands separator
        population_formatted = f"{province.get('population', 0):,}"
        area_formatted = f"{province.get('area_km2', 0):,.0f}"
        density_formatted = f"{province.get('population_density', 0):.1f}"
        politician_count = province.get('politician_count', 0)
        
        # Determine data source indicator
        source = province.get('source', 'Unknown')
        source_indicator = "🏛️" if "Statistics Finland" in source else "⚠️"
        
        # Last updated info
        last_updated = province.get('last_updated', 'N/A')
        if last_updated and last_updated != 'N/A':
            try:
                # Format date if it's a proper timestamp
                if 'T' in last_updated:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    last_updated = dt.strftime('%Y-%m-%d')
            except:
                pass
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 250px; max-width: 300px;">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
                {province.get('name_fi', province.get('name', 'Unknown Province'))}
            </h3>
            
            <div style="margin-bottom: 8px;">
                <strong>🏛️ Official Names:</strong><br>
                <span style="margin-left: 10px;">🇫🇮 {province.get('name_fi', 'N/A')}</span><br>
                <span style="margin-left: 10px;">🇸🇪 {province.get('name_sv', 'N/A')}</span><br>
                <span style="margin-left: 10px;">🇬🇧 {province.get('name_en', 'N/A')}</span>
            </div>
            
            <div style="margin-bottom: 8px;">
                <strong>📊 Demographics:</strong><br>
                <span style="margin-left: 10px;">👥 Population: {population_formatted}</span><br>
                <span style="margin-left: 10px;">📏 Area: {area_formatted} km²</span><br>
                <span style="margin-left: 10px;">🏘️ Density: {density_formatted} people/km²</span>
            </div>
            
            <div style="margin-bottom: 8px;">
                <strong>🏛️ Political Data:</strong><br>
                <span style="margin-left: 10px;">👨‍💼 Politicians: {politician_count}</span><br>
                <span style="margin-left: 10px;">🏛️ Capital: {province.get('capital', 'N/A')}</span>
            </div>
            
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #bdc3c7; font-size: 11px; color: #7f8c8d;">
                {source_indicator} Source: {source}<br>
                📅 Updated: {last_updated}
            </div>
        </div>
        """
        
        return popup_html
    
    def render(self):
        """Render enhanced Finland map using Plotly (Docker-friendly, no serialization issues)"""
        try:
            if not self._map_loaded:
                st.warning("Map data is loading...")
                return None
            
            # Debug logging
            self.logger.info(f"🗺️ Rendering Plotly map with {len(self.markers)} markers")
            if self._geojson_loaded:
                geojson_ids = [f['properties']['id'] for f in self.geojson_data.get('features', [])]
                self.logger.info(f"🗺️ GeoJSON province IDs: {geojson_ids}")
            
            # Prepare data for Plotly
            df = pd.DataFrame([
                {
                    'id': m.id,
                    'name': m.name,
                    'lat': m.lat,
                    'lon': m.lon,
                    'politician_count': m.politician_count,
                    'population': m.population,
                    'area': m.area,
                    'hover_text': f"<b>{m.name}</b><br>" +
                                  f"Population: {m.population:,}<br>" +
                                  f"Area: {m.area:,.1f} km²"
                }
                for m in self.markers
            ])            
            # Create figure
            fig = go.Figure()
            
            # Add province boundaries (choropleth) if GeoJSON loaded
            if self._geojson_loaded and self.geojson_data:
                self.logger.info(f"✅ Adding choropleth layer with {len(self.geojson_data.get('features', []))} provinces")
                fig.add_trace(go.Choroplethmapbox(
                    geojson=self.geojson_data,
                    locations=df['id'],
                    z=df['population'],  # Color by population (politician_count is all 0)
                    featureidkey="properties.id",
                    customdata=df[['name', 'area']],  # Province details for hover
                    colorscale=[
                        [0, '#e8f4f8'],      # Light blue for low population
                        [0.5, '#3498db'],    # Medium blue
                        [1, '#2c3e50']       # Dark blue for high population
                    ],
                    marker_opacity=0.5,
                    marker_line_width=2,
                    marker_line_color='#2c3e50',
                    hovertemplate='<b>%{customdata[0]}</b><br>' +
                                  'Population: %{z:,}<br>' +
                                  'Area: %{customdata[1]:,.1f} km²<br>' +
                                  '<extra></extra>',
                    showscale=False,
                    name='Provinces'
                ))
            
            # Add province center markers
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'],
                lon=df['lon'],
                mode='markers',
                marker=dict(
                    size=14,
                    color='#3498db',
                    opacity=0.9
                ),
                text=df['hover_text'],
                hoverinfo='text',
                name='Province Centers',
                customdata=df[['name', 'politician_count', 'population', 'area']]
            ))
            
            # Update layout to show ALL of Finland
            # Calculate exact center from bounds
            center_lat = (self.finland_bounds['north'] + self.finland_bounds['south']) / 2
            center_lon = (self.finland_bounds['west'] + self.finland_bounds['east']) / 2
            
            fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    center=dict(lat=center_lat, lon=center_lon),
                    zoom=4.0,  # Zoom level to show full Finland (all 19 provinces visible)
                ),
                height=600,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                hovermode='closest'
            )
            
            # Display map in Streamlit
            st.plotly_chart(fig, use_container_width=True, key="finland_map_plotly")
            
            # Enhanced summary statistics (same as before)
            total_politicians = sum(marker.politician_count for marker in self.markers)
            total_population = sum(marker.population for marker in self.markers)
            total_area = sum(marker.area for marker in self.markers)
            
            # Use API count if available, otherwise use sum from markers
            display_politician_count = self.total_politician_count if self.total_politician_count > 0 else total_politicians
            
            st.subheader("📊 Finland Overview")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="📍 Provinces", 
                    value=f"{len(self.markers)}",
                    help="Total number of Finnish provinces (maakunta)"
                )
                st.metric(
                    label="🏠 Population", 
                    value=f"{total_population:,}",
                    help="Total population across all provinces"
                )
            with col2:
                st.metric(
                    label="👥 Politicians", 
                    value=f"{display_politician_count}",
                    help="Total number of politicians in database"
                )
                st.metric(
                    label="🗺️ Total Area", 
                    value=f"{total_area:,.0f} km²",
                    help="Total area of all Finnish provinces"
                )
            
            return fig

        except Exception as e:
            self.logger.error(f"Error rendering Plotly map: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            st.error(f"Failed to render map: {str(e)}")
            return None
