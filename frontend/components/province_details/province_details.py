"""
Province Details Component for FPAS
Displays politician cards for the selected province
"""

import streamlit as st
import logging
import asyncio
import httpx
from typing import List, Optional
from pydantic import BaseModel, Field


class Politician(BaseModel):
    """Model representing a politician"""
    id: str = Field(..., description="Unique politician identifier")
    name: str = Field(..., description="Politician name")
    party: str = Field(default="", description="Political party")
    constituency: str = Field(default="", description="Electoral constituency")
    years_served: str = Field(default="", description="Years of service")
    position: str = Field(default="", description="Current position")
    bio: str = Field(default="", description="Short biography")
    image_url: str = Field(default="", description="Politician image URL")


class ProvinceDetails:
    """Component for displaying province details and politician cards"""
    
    def __init__(self, api_base_url: str):
        """
        Initialize province details component
        
        Args:
            api_base_url: Base URL for the API
        """
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(__name__)
        self._politicians_cache = {}
    
    def _normalize_province_id(self, province_id: str) -> str:
        """
        Normalize province ID to match backend expectations
        
        Args:
            province_id: Raw province ID from frontend
            
        Returns:
            str: Normalized province ID
        """
        # Convert to lowercase and handle common variations
        province_id = province_id.lower().strip()
        
        # Map common variations to standard province names
        province_mapping = {
            'uusimaa': 'uusimaa',
            'varsinais-suomi': 'varsinais-suomi',
            'varsinaissuomi': 'varsinais-suomi',
            'pirkanmaa': 'pirkanmaa',
            'pohjois-savo': 'pohjois-savo',
            'pohjoissavo': 'pohjois-savo',
            'pohjois-pohjanmaa': 'pohjois-pohjanmaa',
            'pohjoispohjanmaa': 'pohjois-pohjanmaa',
            'pohjanmaa': 'pohjanmaa',
            'kainuu': 'kainuu',
            'lappi': 'lappi',
            'pohjois-karjala': 'pohjois-karjala',
            'pohjoiskarjala': 'pohjois-karjala',
            'päijät-häme': 'päijät-häme',
            'päijäthäme': 'päijät-häme',
            'kanta-häme': 'kanta-häme',
            'kantahäme': 'kanta-häme',
            'keski-suomi': 'keski-suomi',
            'keskisuomi': 'keski-suomi',
            'etelä-savo': 'etelä-savo',
            'eteläsavo': 'etelä-savo',
            'etelä-pohjanmaa': 'etelä-pohjanmaa',
            'eteläpohjanmaa': 'etelä-pohjanmaa',
            'kymenlaakso': 'kymenlaakso',
            'etelä-karjala': 'etelä-karjala',
            'eteläkarjala': 'etelä-karjala',
            'satakunta': 'satakunta',
            'keski-pohjanmaa': 'keski-pohjanmaa',
            'keskipohjanmaa': 'keski-pohjanmaa',
            'ahvenanmaa': 'ahvenanmaa',
            'åland': 'ahvenanmaa'
        }
        
        # Return mapped value or original if no mapping found
        return province_mapping.get(province_id, province_id)
    
    async def fetch_politicians(self, province_id: str) -> List[Politician]:
        """
        Fetch politicians for a specific province
        
        Args:
            province_id: Province identifier
            
        Returns:
            List of Politician objects
        """
        # Normalize province ID first
        normalized_id = self._normalize_province_id(province_id)
        self.logger.info(f"🔍 Fetching politicians for province: original_id='{province_id}', normalized_id='{normalized_id}'")
        
        # Check cache with normalized ID
        if normalized_id in self._politicians_cache:
            self.logger.info(f"🔍 Using cached data for province_id: '{normalized_id}'")
            return self._politicians_cache[normalized_id]
        
        try:
            # Build API URL with query parameters
            api_url = f"{self.api_base_url}/provinces/{normalized_id}/politicians?limit=100"
            self.logger.info(f"🌐 Making API request to: {api_url}")
            
            # Make the API request with timeout and error handling
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url)
                
                # Log response status and headers for debugging
                self.logger.info(f"🔍 API response status: {response.status_code}")
                self.logger.debug(f"🔍 API response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.logger.debug(f"🔍 Raw API response: {data}")
                    
                    # Updated to match the actual API response structure
                    politicians_data = data.get('politicians', [])
                    self.logger.info(f"✅ Successfully fetched {len(politicians_data)} politicians for province '{normalized_id}'")
                    
                    politicians = []
                    for idx, politician_data in enumerate(politicians_data, 1):
                        try:
                            # Extract and validate required fields
                            name = str(politician_data.get('name', 'Unknown Politician')).strip()
                            if not name or name == 'Unknown Politician':
                                self.logger.warning(f"⚠️ Missing name for politician at index {idx}, skipping")
                                continue
                                
                            # Extract and validate image URL
                            image_url = politician_data.get('image_url', '')
                            if not image_url or not image_url.startswith(('http://', 'https://')):
                                # Generate initials for placeholder
                                name_parts = [p for p in name.split() if p[0].isupper()]
                                initials = ''.join([p[0] for p in name_parts[:2]]) if len(name_parts) > 1 else name[:2].upper()
                                name_hash = hash(name) % 0xFFFFFF
                                hex_color = f"{name_hash:06x}"
                                image_url = f"https://via.placeholder.com/300x400.png/{hex_color}/ffffff?text={initials}"
                                self.logger.info(f"🖼️  Generated placeholder for {name}")
                            
                            # Create politician object with the processed image URL
                            politician = Politician(
                                id=str(politician_data.get('id', f'unknown-{idx}')),
                                name=name,
                                party=str(politician_data.get('party', '')),
                                constituency=str(politician_data.get('constituency', '')),
                                years_served=str(politician_data.get('years_served', '')),
                                position=str(politician_data.get('position', '')),
                                bio=str(politician_data.get('bio', '')),
                                image_url=image_url  # Use the processed image URL
                            )
                            
                            self.logger.debug(f"✅ Processed politician: {name} ({politician.party})")
                            politicians.append(politician)
                            
                        except Exception as e:
                            self.logger.error(f"❌ Error processing politician at index {idx}: {str(e)}\nData: {politician_data}")
                            continue
                    
                    if politicians:
                        self.logger.info(f"✅ Successfully processed {len(politicians)} politicians for province '{normalized_id}'")
                        self._politicians_cache[normalized_id] = politicians
                        return politicians
                    
                    # If we get here, no politicians were found
                    self.logger.warning(f"⚠️ No politicians found in the API response for province '{normalized_id}'. Response: {data}")
                    
                    # Try alternative province IDs as fallback
                    alternative_ids = []
                    if '-' in normalized_id:
                        alternative_ids.append(normalized_id.replace('-', ''))
                    
                    # Log the fallback attempt
                    if alternative_ids:
                        self.logger.info(f"🔍 Trying alternative province IDs: {alternative_ids}")
                    
                    # Try alternative IDs before falling back to sample data
                    for alt_id in alternative_ids:
                        try:
                            alt_url = f"{self.api_base_url}/provinces/{alt_id}/politicians"
                            self.logger.info(f"🔍 Trying alternative API endpoint: {alt_url}")
                            
                            alt_response = await client.get(alt_url, timeout=10.0)
                            if alt_response.status_code == 200:
                                alt_data = alt_response.json()
                                alt_politicians = alt_data.get('politicians', [])
                                
                                if alt_politicians:
                                    self.logger.info(f"✅ Found {len(alt_politicians)} politicians with alternative ID {alt_id}")
                                    # Process the alternative data
                                    politicians = []
                                    for idx, pol_data in enumerate(alt_politicians, 1):
                                        try:
                                            name = str(pol_data.get('name', f'Politician {idx}')).strip()
                                            # Generate placeholder image if needed
                                            image_url = pol_data.get('image_url', '')
                                            if not image_url or not image_url.startswith(('http://', 'https://')):
                                                name_parts = [p for p in name.split() if p[0].isupper()]
                                                initials = ''.join([p[0] for p in name_parts[:2]]) if len(name_parts) > 1 else name[:2].upper()
                                                name_hash = hash(name) % 0xFFFFFF
                                                hex_color = f"{name_hash:06x}"
                                                image_url = f"https://via.placeholder.com/300x400.png/{hex_color}/ffffff?text={initials}"
                                            
                                            politicians.append(Politician(
                                                id=str(pol_data.get('id', f'pol_alt_{idx}')),
                                                name=name,
                                                party=str(pol_data.get('party', 'Unknown')),
                                                constituency=str(pol_data.get('constituency', normalized_id.title())),
                                                years_served=str(pol_data.get('years_served', '')),
                                                position=str(pol_data.get('position', 'Politician')),
                                                bio=str(pol_data.get('bio', '')),
                                                image_url=image_url
                                            ))
                                            
                                        except Exception as e:
                                            self.logger.error(f"❌ Error processing alternative politician {idx}: {str(e)}")
                                            continue
                                    
                                    if politicians:
                                        self._politicians_cache[normalized_id] = politicians
                                        return politicians
                                        
                        except Exception as e:
                            self.logger.error(f"❌ Error trying alternative ID {alt_id}: {str(e)}")
                            continue
                    
                    # If we get here, no data was found with any ID
                    self.logger.warning(f"⚠️ No politicians found for province '{normalized_id}' (tried: {', '.join([normalized_id] + alternative_ids)})")
                    return []
                
                # If we get here, the API call failed
                self.logger.error(f"❌ API request failed with status {response.status_code}: {response.text}")
                return []
                return []
                
        except httpx.RequestError as e:
            self.logger.error(f"🚨 Network error while fetching politicians: {str(e)}")
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Unexpected error fetching politicians: {str(e)}", exc_info=True)
            return []
                    
        except Exception as e:
            self.logger.error(f"Error fetching politicians for {province_id}: {str(e)}")
            return []
    
    def _create_sample_politicians_for_province(self, province_id: str) -> list:
        """Create sample politician data for a province until backend has proper filtering"""
        
        # Debug logging
        self.logger.info(f"🔍 DEBUG: _create_sample_politicians_for_province called with province_id: '{province_id}'")
        
        # Province name mapping - map various possible province IDs to sample data keys
        province_mapping = {
            # Possible API province IDs -> sample data keys
            'uusimaa': 'uusimaa',
            'Uusimaa': 'uusimaa', 
            'uusimaa-region': 'uusimaa',
            '01': 'uusimaa',
            'FI-18': 'uusimaa',
            
            'varsinais-suomi': 'varsinais-suomi',
            'Varsinais-Suomi': 'varsinais-suomi',
            'varsinais-suomi-region': 'varsinais-suomi',
            '02': 'varsinais-suomi',
            'FI-19': 'varsinais-suomi',
            
            'pirkanmaa': 'pirkanmaa',
            'Pirkanmaa': 'pirkanmaa',
            'pirkanmaa-region': 'pirkanmaa',
            '06': 'pirkanmaa',
            'FI-11': 'pirkanmaa'
        }
        
        # Get the mapped key for sample data lookup
        mapped_key = province_mapping.get(province_id, province_id.lower())
        self.logger.info(f"🔍 DEBUG: Mapped province_id '{province_id}' to sample key '{mapped_key}'")
        
        # Sample politician data by province
        sample_data = {
            'uusimaa': [
                {
                    'id': 'pol_001',
                    'name': 'Sauli Niinistö',
                    'party': 'Independent',
                    'constituency': 'Uusimaa',
                    'years_served': '2012-2024',
                    'position': 'President of Finland',
                    'bio': 'Former President of Finland, served two terms from 2012 to 2024.'
                },
                {
                    'id': 'pol_002',
                    'name': 'Sanna Marin',
                    'party': 'SDP',
                    'constituency': 'Uusimaa',
                    'years_served': '2015-Present',
                    'position': 'Member of Parliament',
                    'bio': 'Former Prime Minister of Finland (2019-2023), current MP.'
                },
                {
                    'id': 'pol_003',
                    'name': 'Alexander Stubb',
                    'party': 'Kokoomus',
                    'constituency': 'Uusimaa',
                    'years_served': '2004-Present',
                    'position': 'President of Finland',
                    'bio': 'Current President of Finland, former Prime Minister and EU Commissioner.'
                }
            ],
            'varsinais-suomi': [
                {
                    'id': 'pol_004',
                    'name': 'Paavo Väyrynen',
                    'party': 'Centre Party',
                    'constituency': 'Varsinais-Suomi',
                    'years_served': '1970-Present',
                    'position': 'Member of Parliament',
                    'bio': 'Veteran politician, longest-serving MP in Finnish history.'
                },
                {
                    'id': 'pol_005',
                    'name': 'Elina Valtonen',
                    'party': 'Kokoomus',
                    'constituency': 'Varsinais-Suomi',
                    'years_served': '2011-Present',
                    'position': 'Minister for Foreign Affairs',
                    'bio': 'Current Minister for Foreign Affairs, former Minister of Education.'
                }
            ],
            'pirkanmaa': [
                {
                    'id': 'pol_006',
                    'name': 'Antti Rinne',
                    'party': 'SDP',
                    'constituency': 'Pirkanmaa',
                    'years_served': '2015-2023',
                    'position': 'Former Prime Minister',
                    'bio': 'Former Prime Minister of Finland (2019), former trade union leader.'
                }
            ]
        }
        
        # Return sample data for the mapped province key, or empty list if not found
        result = sample_data.get(mapped_key, [])
        self.logger.info(f"🔍 DEBUG: Sample data lookup for '{mapped_key}' returned {len(result)} politicians")
        return result
    
    def _render_politician_card(self, politician: Politician) -> None:
        """
        Render a single politician card with enhanced image display and styling
        
        Args:
            politician: Politician object to render
        """
        with st.container():
            # Create columns for the card layout
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Add custom CSS for the image container
                st.markdown("""
                <style>
                    .politician-image {
                        width: 150px;
                        height: 200px;
                        object-fit: cover;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        transition: transform 0.3s ease;
                    }
                    .politician-image:hover {
                        transform: scale(1.03);
                    }
                    .politician-initials {
                        width: 150px;
                        height: 200px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        border-radius: 8px;
                        font-size: 48px;
                        font-weight: bold;
                        color: #2c3e50;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Try to display the image with error handling
                image_url = politician.image_url
                
                # Try to get image from session state if this is the selected politician
                if (not image_url or not image_url.startswith(('http://', 'https://'))) and \
                   'selected_politician_id' in st.session_state and \
                   politician.id == st.session_state.get('selected_politician_id') and \
                   'selected_politician_image' in st.session_state:
                    image_url = st.session_state['selected_politician_image']
                
                if image_url and image_url.startswith(('http://', 'https://')):
                    try:
                        # Use st.image with error handling
                        st.image(
                            image_url,
                            width=150,
                            use_container_width=False,
                            caption=politician.name
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to load image for {politician.name} from {image_url}: {str(e)}")
                        self._render_politician_initials(politician.name)
                else:
                    self.logger.debug(f"No valid image URL for {politician.name}, using initials")
                    self._render_politician_initials(politician.name)
            
            with col2:
                # Politician details
                st.markdown(f"### {politician.name}")
                
                # Party badge with color coding
                if politician.party:
                    party_colors = {
                        'kok': '#0057b7',  # Blue
                        'sd': '#e31937',    # Red
                        'ps': '#ffff00',    # Yellow
                        'kesk': '#00aa00',  # Green
                        'vihr': '#61b63a',  # Light Green
                        'vas': '#c20e0e',   # Dark Red
                        'r': '#ffcc00',     # Yellow
                        'kd': '#ffcc00',    # Yellow
                        'liik': '#ff00ff',  # Pink
                        'fp': '#000000'     # Black
                    }
                    
                    # Get party color or default to gray
                    party_key = politician.party.lower()
                    bg_color = party_colors.get(party_key, '#888888')
                    text_color = '#ffffff' if bg_color != '#ffff00' else '#000000'
                    
                    st.markdown(
                        f'<span style="display: inline-block; background-color: {bg_color}; '
                        f'color: {text_color}; padding: 2px 8px; border-radius: 12px; '
                        f'font-size: 0.9em; margin-bottom: 8px; display: inline-block;">'
                        f'{politician.party.upper()}</span>',
                        unsafe_allow_html=True
                    )
                
                # Constituency and position
                info_text = ""
                if politician.constituency:
                    info_text += f"**Constituency:** {politician.constituency}  \n"
                if politician.position:
                    info_text += f"**Position:** {politician.position}  \n"
                st.markdown(info_text)
                
                # Years served with icon
                if politician.years_served:
                    st.markdown(
                        f'<div style="display: flex; align-items: center; color: #666666; margin: 8px 0;">'
                        f'<span style="margin-right: 5px;">📅</span> {politician.years_served} years in office</div>',
                        unsafe_allow_html=True
                    )
                
                # Expandable bio section
                if politician.bio:
                    with st.expander("View Biography"):
                        st.write(politician.bio)
            
            # Add a subtle divider between cards
            st.markdown("<hr style='margin: 20px 0; border: 0.5px solid #f0f0f0;'>", unsafe_allow_html=True)
    
    def _render_politician_initials(self, name: str) -> None:
        """Render a placeholder with politician's initials"""
        # Extract initials (first letter of first two words, or first two letters of name)
        name_parts = [p for p in name.split() if p[0].isupper()]
        if len(name_parts) >= 2:
            initials = f"{name_parts[0][0]}{name_parts[-1][0]}"
        else:
            initials = name[:2].upper() if len(name) >= 2 else name.upper()
        
        # Generate a consistent color based on the name
        name_hash = hash(name) % 0xFFFFFF
        hex_color = f"{name_hash:06x}"
        
        # Create a visually appealing placeholder
        st.markdown(
            f'<div class="politician-initials" style="background: linear-gradient(135deg, #{hex_color} 0%, '
            f'#{hex_color}80 100%); color: white; font-weight: 600; font-size: 42px; '
            f'box-shadow: 0 2px 8px rgba(0,0,0,0.1);">{initials}</div>',
            unsafe_allow_html=True
        )

    def render(self, selected_province_id: Optional[str], selected_province_name: Optional[str]) -> None:
        """
        Render the province details component
        
        Args:
            selected_province_id: ID of the selected province
            selected_province_name: Name of the selected province
        """
        if not selected_province_id:
            st.info("👆 Select a province from the sidebar or map to view politicians")
            return
            
        st.header(f"🏛️ Politicians in {selected_province_name}")
        
        # Use session state to cache politicians
        cache_key = f"politicians_{selected_province_id}"
        
        if cache_key not in st.session_state:
            with st.spinner(f"Loading politicians for {selected_province_name}..."):
                try:
                    politicians = asyncio.run(self.fetch_politicians(selected_province_id))
                    st.session_state[cache_key] = politicians
                except Exception as e:
                    st.error(f"Failed to load politicians: {str(e)}")
                    return
        
        politicians = st.session_state[cache_key]
        
        if not politicians:
            st.warning(f"No politicians found for {selected_province_name}")
            return
        
        # Display summary
        st.markdown(f"**Found {len(politicians)} politicians in {selected_province_name}**")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            parties = list(set(p.party for p in politicians if p.party))
            selected_party = st.selectbox("Filter by Party", ["All"] + sorted(parties))
        
        with col2:
            positions = list(set(p.position for p in politicians if p.position))
            selected_position = st.selectbox("Filter by Position", ["All"] + sorted(positions))
        
        # Filter politicians
        filtered_politicians = politicians
        if selected_party != "All":
            filtered_politicians = [p for p in filtered_politicians if p.party == selected_party]
        if selected_position != "All":
            filtered_politicians = [p for p in filtered_politicians if p.position == selected_position]
        
        if filtered_politicians:
            st.markdown(f"**Showing {len(filtered_politicians)} politicians**")
            
            # Display politician cards
            for politician in filtered_politicians:
                self._render_politician_card(politician)
        else:
            st.warning("No politicians match the selected filters")
