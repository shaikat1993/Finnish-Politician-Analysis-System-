import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import logging
import sys
import os
from bs4 import BeautifulSoup
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_collector import PoliticianCollector
from config.api_endpoints import APIConfig

@dataclass
class Politician:
    politician_id: str
    name: str
    party: str
    constituency: str
    term_start: str
    term_end: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

@dataclass
class VotingRecord:
    vote_id: str
    politician_id: str
    session_id: str
    vote_date: datetime
    topic: str
    vote: str  # "yes", "no", "absent", "abstain"
    description: Optional[str] = None

@dataclass
class ParliamentarySession:
    session_id: str
    date: datetime
    topic: str
    description: str
    document_url: Optional[str] = None

class EduskuntaCollector(PoliticianCollector):
    """Collector for Finnish Parliament (Eduskunta) open data using centralized configuration"""
    
    def __init__(self):
        super().__init__('eduskunta')

    def get_politicians(self, term: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get politicians from canonical eduskunta_politicians.json file (source of truth).
        Returns:
            List of politician dictionaries with numeric id and politician_id fields.
        """
        import os, json
        try:
            json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'eduskunta_politicians.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                politicians = json.load(f)
            # Ensure every dict has 'id' and 'politician_id' as string
            for p in politicians:
                pid = str(p.get('politician_id', ''))
                p['id'] = pid
                p['politician_id'] = pid
            self.logger.info(f"Loaded {len(politicians)} politicians from eduskunta_politicians.json")
            return politicians
        except Exception as e:
            self.logger.error(f"Error loading politicians from eduskunta_politicians.json: {str(e)}")
            return []

    def get_voting_records(
        self, 
        politician_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get voting records from Eduskunta API
        
        Args:
            politician_id: Specific politician ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of voting record dictionaries
        """
        try:
            params = {}
            if start_date:
                params['alkupvm'] = start_date
            if end_date:
                params['loppupvm'] = end_date
            
            self.logger.info("Fetching voting records from Eduskunta API")
            response = self.make_request('voting_records', params=params)
            data = response.json()
            
            voting_records = []
            for vote_data in data.get('aanestykset', []):
                records = self._parse_voting_record(vote_data, politician_id)
                voting_records.extend(records)
            
            self.logger.info(f"Successfully fetched {len(voting_records)} voting records")
            return voting_records
            
        except Exception as e:
            self.logger.error(f"Error fetching voting records: {str(e)}")
            return []

    def get_parliamentary_sessions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ParliamentarySession]:
        """
        Get parliamentary sessions from Eduskunta API
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of ParliamentarySession objects
        """
        try:
            url = f"{self.get_base_url()}/istunnot"
            params = {}
            
            if start_date:
                params['alkupvm'] = start_date
            if end_date:
                params['loppupvm'] = end_date
            
            self.logger.info(f"Fetching parliamentary sessions from: {url}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            sessions = []
            
            for session_data in data.get('istunnot', []):
                session = self._parse_session(session_data)
                if session:
                    sessions.append(session)
            
            self.logger.info(f"Successfully fetched {len(sessions)} parliamentary sessions")
            return sessions
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching parliamentary sessions: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return []

    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        term = kwargs.get('term')
        return self.get_politicians(term)
    
    def _parse_politician(self, data: Dict) -> Optional[Dict[str, Any]]:
        """Parse politician data from API response"""
        try:
            name = f"{data.get('etunimi', '')} {data.get('sukunimi', '')}".strip()
            
            # Extract basic politician data
            politician_data = {
                'politician_id': str(data.get('henkiloId', '')),
                'name': name,
                'party': data.get('puolue', {}).get('lyhenne', ''),
                'constituency': data.get('vaalipiiri', {}).get('nimi', ''),
                'term_start': data.get('vaalitulos', {}).get('vaalikausi', {}).get('alkupvm', ''),
                'term_end': data.get('vaalitulos', {}).get('vaalikausi', {}).get('loppupvm'),
                'role': data.get('asema', ''),
                'email': data.get('sahkoposti'),
                'phone': data.get('puhelin'),
                'website': data.get('kotisivu'),
                'source': 'eduskunta'
            }
            
            # Attempt to retrieve politician image
            image_url = self._get_politician_image(name, politician_data)
            if image_url:
                politician_data['image_url'] = image_url
            
            return politician_data
            
        except Exception as e:
            self.logger.error(f"Error parsing politician data: {str(e)}")
            return None
    
    def _get_politician_image(self, name: str, politician_data: Dict) -> str:
        """Retrieve politician image with multiple fallback strategies.
        
        Args:
            name: Full name of the politician
            politician_data: Dictionary containing politician metadata
            
        Returns:
            str: URL to the politician's image or a fallback placeholder
        """
        def try_image_url(url: str) -> Optional[str]:
            """Helper to validate and return a working image URL"""
            try:
                if self._validate_image_url(url):
                    self.logger.info(f"Found valid image URL: {url}")
                    return url
            except Exception as e:
                self.logger.debug(f"Image URL {url} failed: {str(e)}")
            return None

        # 1. Try existing URL if present
        existing_url = politician_data.get('kuva') or politician_data.get('image')
        if existing_url and (url := try_image_url(existing_url)):
            return url

        # 2. Try Eduskunta's official image service with multiple name formats
        name_variants = self._generate_name_variants(name)
        for variant in name_variants:
            for ext in ['jpg', 'jpeg', 'png']:
                # Try different URL patterns
                base_urls = [
                    f"https://www.eduskunta.fi/globalassets/henkilo-kuvat/{variant}.{ext}",
                    f"https://www.eduskunta.fi/globalassets/eduskunta-ja-tyot/valiokunnat/henkilokuvat/{variant}.{ext}",
                ]
                for url in base_urls:
                    if result := try_image_url(url):
                        return result

        # 3. Try Wikipedia API
        try:
            wiki_url = f"https://fi.wikipedia.org/w/api.php?action=query&titles={name.replace(' ', '%20')}&prop=pageimages&format=json&pithumbsize=500"
            response = self.session.get(wiki_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('pages', {})
                for page in pages.values():
                    if 'thumbnail' in page and 'source' in page['thumbnail']:
                        if result := try_image_url(page['thumbnail']['source']):
                            return result
        except Exception as e:
            self.logger.debug(f"Wikipedia API failed: {str(e)}")

        # 4. Generate a professional placeholder as last resort
        return self._generate_placeholder_image(name)
        
    def _generate_name_variants(self, name: str) -> List[str]:
        """Generate common name variants for URL construction"""
        name = name.lower().strip()
        variants = [name.replace(' ', '-')]  # alexander-stubb
        
        # Try with and without special characters
        special_chars = {'ä': 'a', 'ö': 'o', 'å': 'a', 'é': 'e', 'ü': 'u'}
        normalized = name
        for char, replacement in special_chars.items():
            normalized = normalized.replace(char, replacement)
        if normalized != name:
            variants.append(normalized.replace(' ', '-'))
        
        # Try with first name initial
        parts = name.split()
        if len(parts) > 1:
            variants.append(f"{parts[0][0]}-{'-'.join(parts[1:])}")  # a-stubb
        
        return list(set(variants))  # Remove duplicates

    def _generate_placeholder_image(self, name: str) -> str:
        """Generate a professional placeholder image with initials"""
        initials = self._get_politician_initials(name)
        color = self._get_politician_color(name)
        return f"https://ui-avatars.com/api/?name={initials}&background={color}&color=fff&size=300&font-size=0.5"
    
    def _get_politician_initials(self, name: str) -> str:
        """Generate politician initials from name"""
        try:
            parts = name.strip().split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[-1][0]}".upper()
            elif len(parts) == 1:
                return parts[0][:2].upper()
            else:
                return "MP"
        except:
            return "MP"
    
    def _get_politician_color(self, name: str) -> str:
        """Generate consistent color for politician based on name hash"""
        try:
            # Professional color palette for politicians
            colors = [
                "1f4e79",  # Navy Blue
                "c41e3a",  # Crimson
                "2c5aa0",  # Royal Blue
                "0066cc",  # Blue
                "228b22",  # Forest Green
                "ff6347",  # Tomato
                "dc143c",  # Crimson
                "4169e1",  # Royal Blue
                "8b4513",  # Saddle Brown
                "32cd32",  # Lime Green
                "00ff00",  # Green
                "ff1493"   # Deep Pink
            ]
            
            # Use name hash to consistently assign color
            hash_value = hash(name.lower()) % len(colors)
            return colors[hash_value]
            
        except:
            return "0066cc"  # Default blue
    
    def _validate_image_url(self, url: str) -> bool:
        """Validate if image URL is accessible"""
        try:
            if not url or not url.startswith(('http://', 'https://')):
                return False
            
            # Quick HEAD request to check if image exists
            response = self.session.head(url, timeout=5)
            return response.status_code == 200 and 'image' in response.headers.get('content-type', '').lower()
            
        except:
            return False
    
    def _scrape_current_mps(self) -> List[Dict[str, Any]]:
        """Fetch current MPs from the official Eduskunta Open Data API (live data), assigning a valid constituency to each."""
        try:
            seating_url = "https://avoindata.eduskunta.fi/api/v1/seating/"
            people_url = "https://avoindata.eduskunta.fi/api/v1/people/"
            self.logger.info(f"Fetching live MPs from: {seating_url}")
            response = self.session.get(seating_url, timeout=10)
            response.raise_for_status()
            seating_data = response.json()
            # Fetch all people to build hetekaId->constituency mapping
            self.logger.info(f"Fetching MP constituency data from: {people_url}")
            people_response = self.session.get(people_url, timeout=10)
            people_response.raise_for_status()
            people_data = people_response.json()
            hetekaid_to_constituency = {}
            for person in people_data:
                heteka_id = person.get("hetekaId")
                constituency = person.get("constituency") or person.get("district")
                if heteka_id and constituency:
                    hetekaid_to_constituency[heteka_id] = constituency
            politicians = []
            skipped = 0
            for mp in seating_data:
                heteka_id = mp.get("hetekaId")
                name = f"{mp.get('firstname', '').strip()} {mp.get('lastname', '').strip()}".strip()
                constituency = hetekaid_to_constituency.get(heteka_id)
                if not constituency or not constituency.strip():
                    self.logger.warning(f"No constituency found for MP '{name}' (hetekaId: {heteka_id}). Skipping MP.")
                    skipped += 1
                    continue
                politician = {
                    "id": str(heteka_id),
                    "politician_id": str(heteka_id),
                    "name": name,
                    "party": mp.get("party", "Unknown"),
                    "constituency": constituency,
                    "seat_number": mp.get("seatNumber"),
                    "minister": mp.get("minister", False),
                    "image_url": f"https://avoindata.eduskunta.fi/{mp.get('pictureUrl')}" if mp.get("pictureUrl") else None,
                    "source": "eduskunta_open_data",
                    "active": True
                }
                politicians.append(politician)
            self.logger.info(f"Fetched {len(politicians)} MPs from Eduskunta Open Data API with valid constituencies. Skipped {skipped} MPs without constituency.")
            return politicians
        except Exception as e:
            self.logger.error(f"Failed to fetch MPs from Eduskunta Open Data API: {str(e)}")
            self.logger.info("Using fallback politician data from known current MPs")
            return self._get_current_finnish_politicians()
    
    # DISABLED: Fallback data should not be used for canonical import. Only get_politicians() with eduskunta_politicians.json is allowed.
    # def _get_current_finnish_politicians(self) -> List[Dict[str, Any]]:
    #     """Get current Finnish politicians from reliable sources (2023-2027 term)"""
    #     ...
    #     return politicians

        """Get current Finnish politicians from reliable sources (2023-2027 term)"""
        try:
            # Current Finnish politicians from 2023 election results
            current_politicians = [
                {
                    'name': 'Petteri Orpo',
                    'party': 'Kokoomus',
                    'constituency': 'Uusimaa',
                    'position': 'Prime Minister'
                },
                {
                    'name': 'Riikka Purra', 
                    'party': 'Perussuomalaiset',
                    'constituency': 'Uusimaa',
                    'position': 'Deputy Prime Minister, Minister of Finance'
                },
                {
                    'name': 'Elina Valtonen',
                    'party': 'Kokoomus', 
                    'constituency': 'Uusimaa',
                    'position': 'Minister for Foreign Affairs'
                },
                {
                    'name': 'Antti Häkkänen',
                    'party': 'Kokoomus',
                    'constituency': 'Uusimaa', 
                    'position': 'Minister of Defence'
                },
                {
                    'name': 'Mari-Elina Henriksson',
                    'party': 'RKP',
                    'constituency': 'Uusimaa',
                    'position': 'Minister of Justice'
                },
                {
                    'name': 'Sanni Grahn-Laasonen',
                    'party': 'Kokoomus',
                    'constituency': 'Uusimaa',
                    'position': 'Minister of Education and Culture'
                },
                {
                    'name': 'Krista Kiuru',
                    'party': 'SDP',
                    'constituency': 'Uusimaa',
                    'position': 'MP, Former Minister'
                },
                {
                    'name': 'Annika Saarikko',
                    'party': 'Keskusta',
                    'constituency': 'Varsinais-Suomi',
                    'position': 'Party Leader'
                },
                {
                    'name': 'Li Andersson',
                    'party': 'Vasemmistoliitto',
                    'constituency': 'Uusimaa',
                    'position': 'Party Leader'
                },
                {
                    'name': 'Sofia Virta',
                    'party': 'Vihreät',
                    'constituency': 'Uusimaa',
                    'position': 'Party Leader'
                },
                {
                    'name': 'Ville Tavio',
                    'party': 'Perussuomalaiset',
                    'constituency': 'Pirkanmaa',
                    'position': 'MP'
                },
                {
                    'name': 'Jukka Kopra',
                    'party': 'Kokoomus',
                    'constituency': 'Pirkanmaa',
                    'position': 'MP'
                },
                {
                    'name': 'Tytti Tuppurainen',
                    'party': 'SDP',
                    'constituency': 'Pirkanmaa',
                    'position': 'MP, Former Minister'
                },
                {
                    'name': 'Mikko Kinnunen',
                    'party': 'Keskusta',
                    'constituency': 'Keski-Suomi',
                    'position': 'MP'
                },
                {
                    'name': 'Jani Mäkelä',
                    'party': 'Perussuomalaiset',
                    'constituency': 'Uusimaa',
                    'position': 'MP'
                }
            ]
            
            # Convert to standardized format
            politicians = []
            for politician in current_politicians:
                politician_id = self._generate_politician_id(politician['name'])
                
                politician_data = {
                    'politician_id': politician_id,
                    'name': politician['name'],
                    'party': politician['party'],
                    'constituency': politician['constituency'],
                    'position': politician.get('position', 'Member of Parliament'),
                    'term_start': '2023',
                    'term_end': '2027',
                    'role': politician.get('position', 'MP'),
                    'source': 'eduskunta_fallback',
                    'active': True
                }
                
                # Add image URL
                image_url = self._get_politician_image(politician['name'], politician_data)
                if image_url:
                    politician_data['image_url'] = image_url
                
                politicians.append(politician_data)
            
            self.logger.info(f"Generated {len(politicians)} politicians from fallback data")
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error generating fallback politician data: {str(e)}")
            return []
    
    # DISABLED: Scraping alternative sources is not allowed for canonical import. Only get_politicians() with eduskunta_politicians.json is allowed.
    # def _scrape_alternative_sources(self) -> List[Dict[str, Any]]:
    #     ...
    #     return []

        """Scrape from alternative official sources"""
        try:
            politicians = []
            
            # Try party-specific pages
            party_urls = [
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/Kokoomus.aspx",
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/SDP.aspx",
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/Perussuomalaiset.aspx",
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/Keskusta.aspx",
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/Vihreat.aspx",
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/Vasemmistoliitto.aspx",
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/RKP.aspx",
                "https://www.eduskunta.fi/FI/kansanedustajat/Sivut/KD.aspx"
            ]
            
            for url in party_urls:
                try:
                    party_politicians = self._scrape_party_page(url)
                    politicians.extend(party_politicians)
                except Exception as e:
                    self.logger.warning(f"Failed to scrape {url}: {str(e)}")
                    continue
            
            self.logger.info(f"Scraped {len(politicians)} politicians from alternative sources")
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error scraping alternative sources: {str(e)}")
            return []
    
    # DISABLED: Scraping party pages is not allowed for canonical import. Only get_politicians() with eduskunta_politicians.json is allowed.
    # def _scrape_party_page(self, url: str) -> List[Dict[str, Any]]:
    #     ...
    #     return []

        """Scrape politicians from a party-specific page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            politicians = []
            
            # Extract party name from URL
            party_name = url.split('/')[-1].replace('.aspx', '')
            
            # Look for politician links and names
            politician_links = soup.find_all('a', href=re.compile(r'/kansanedustajat/.*'))
            
            for link in politician_links:
                politician_data = self._extract_politician_from_link(link, party_name)
                if politician_data:
                    politicians.append(politician_data)
            
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error scraping party page {url}: {str(e)}")
            return []
    
    # DISABLED: Extraction from HTML elements is not allowed for canonical import. Only get_politicians() with eduskunta_politicians.json is allowed.
    # def _extract_politician_from_element(self, element) -> Optional[Dict[str, Any]]:
    #     ...
    #     return None

        """Extract politician data from HTML element"""
        try:
            # Try to find name
            name = None
            name_element = element.find(['h1', 'h2', 'h3', 'h4', 'span', 'a'], string=re.compile(r'[A-ZÄÖÅa-zäöå]+ [A-ZÄÖÅa-zäöå]+'))
            
            if name_element:
                name = name_element.get_text().strip()
            elif element.get_text():
                # Try to extract name from text content
                text = element.get_text().strip()
                name_match = re.search(r'([A-ZÄÖÅa-zäöå]+ [A-ZÄÖÅa-zäöå]+)', text)
                if name_match:
                    name = name_match.group(1)
            
            if not name or len(name.split()) < 2:
                return None
            
            # Generate politician data
            politician_id = self._generate_politician_id(name)
            
            # Try to extract additional info
            party = self._extract_party_from_element(element)
            constituency = self._extract_constituency_from_element(element)
            
            politician_data = {
                'politician_id': politician_id,
                'name': name,
                'party': party or 'Unknown',
                'constituency': constituency or 'Unknown',
                'term_start': '2023',  # Current term
                'term_end': None,
                'role': 'Member of Parliament',
                'source': 'eduskunta_scraping',
                'active': True
            }
            
            # Add image URL
            image_url = self._get_politician_image(name, politician_data)
            if image_url:
                politician_data['image_url'] = image_url
            
            return politician_data
            
        except Exception as e:
            self.logger.error(f"Error extracting politician from element: {str(e)}")
            return None
    
    # DISABLED: Extraction from HTML links is not allowed for canonical import. Only get_politicians() with eduskunta_politicians.json is allowed.
    # def _extract_politician_from_link(self, link_element, party_name: str) -> Optional[Dict[str, Any]]:
    #     ...
    #     return None

        """Extract politician data from link element"""
        try:
            name = link_element.get_text().strip()
            
            if not name or len(name.split()) < 2:
                return None
            
            politician_id = self._generate_politician_id(name)
            
            politician_data = {
                'politician_id': politician_id,
                'name': name,
                'party': party_name,
                'constituency': 'Unknown',
                'term_start': '2023',
                'term_end': None,
                'role': 'Member of Parliament',
                'source': 'eduskunta_scraping',
                'active': True
            }
            
            # Add image URL
            image_url = self._get_politician_image(name, politician_data)
            if image_url:
                politician_data['image_url'] = image_url
            
            return politician_data
            
        except Exception as e:
            self.logger.error(f"Error extracting politician from link: {str(e)}")
            return None
    
    # DISABLED: ID generation from name is not allowed for canonical import. Only get_politicians() with eduskunta_politicians.json is allowed.
    # def _generate_politician_id(self, name: str) -> str:
    #     ...
    #     return ""

        """Generate consistent politician ID from name"""
        try:
            # Convert to lowercase, replace spaces with hyphens, remove special chars
            politician_id = name.lower()
            politician_id = re.sub(r'[äåö]', lambda m: {'ä': 'a', 'å': 'a', 'ö': 'o'}[m.group()], politician_id)
            politician_id = re.sub(r'[^a-z0-9\s-]', '', politician_id)
            politician_id = re.sub(r'\s+', '-', politician_id)
            return politician_id
        except:
            return f"politician-{hash(name) % 10000}"
    
    def _extract_party_from_element(self, element) -> Optional[str]:
        """Extract party information from HTML element"""
        try:
            text = element.get_text().lower()
            
            # Common Finnish party abbreviations and names
            party_mapping = {
                'kokoomus': 'Kokoomus',
                'kok': 'Kokoomus',
                'sdp': 'SDP',
                'sosiaalidemokraatit': 'SDP',
                'perussuomalaiset': 'Perussuomalaiset',
                'ps': 'Perussuomalaiset',
                'keskusta': 'Keskusta',
                'kesk': 'Keskusta',
                'vihreät': 'Vihreät',
                'vihr': 'Vihreät',
                'vasemmistoliitto': 'Vasemmistoliitto',
                'vas': 'Vasemmistoliitto',
                'rkp': 'RKP',
                'kd': 'KD',
                'kristillisdemokraatit': 'KD'
            }
            
            for key, party in party_mapping.items():
                if key in text:
                    return party
            
            return None
            
        except:
            return None
    
    def _extract_constituency_from_element(self, element) -> Optional[str]:
        """Extract constituency information from HTML element"""
        try:
            text = element.get_text()
            
            # Match any constituency ending with 'vaalipiiri' (case-insensitive, covers all real cases)
            constituency_pattern = r'([A-ZÄÖÅa-zäöå \-]+vaalipiiri)'
            match = re.search(constituency_pattern, text, re.I)
            if match:
                return match.group(1).strip()
            return None
            
        except:
            return None

    def _parse_voting_record(self, data: Dict, politician_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse voting record data from API response"""
        records = []
        try:
            vote_id = str(data.get('aanestysId', ''))
            session_id = str(data.get('istuntoId', ''))
            vote_date_str = data.get('aanestyspvm', '')
            topic = data.get('otsikko', '')
            description = data.get('selite', '')
            
            # Parse date
            vote_date = datetime.fromisoformat(vote_date_str.replace('Z', '+00:00')) if vote_date_str else datetime.now()
            
            # Parse individual votes
            for vote_data in data.get('aanestystulos', []):
                member_id = str(vote_data.get('henkiloId', ''))
                
                # Filter by politician_id if specified
                if politician_id and member_id != politician_id:
                    continue
                
                vote_value = vote_data.get('aanestys', '').lower()
                
                record = {
                    'vote_id': vote_id,
                    'politician_id': member_id,
                    'session_id': session_id,
                    'vote_date': vote_date.isoformat() if vote_date else None,
                    'topic': topic,
                    'vote': vote_value,
                    'description': description,
                    'source': 'eduskunta'
                }
                records.append(record)
                
        except Exception as e:
            self.logger.error(f"Error parsing voting record: {str(e)}")
            
        return records

    def _parse_session(self, data: Dict) -> Optional[ParliamentarySession]:
        """Parse parliamentary session data from API response"""
        try:
            session_date_str = data.get('istuntopvm', '')
            session_date = datetime.fromisoformat(session_date_str.replace('Z', '+00:00')) if session_date_str else datetime.now()
            
            return ParliamentarySession(
                session_id=str(data.get('istuntoId', '')),
                date=session_date,
                topic=data.get('otsikko', ''),
                description=data.get('selite', ''),
                document_url=data.get('dokumenttiUrl')
            )
        except Exception as e:
            self.logger.error(f"Error parsing session data: {str(e)}")
            return None

    def save_data(self, data: List, filename: str):
        """Save data to JSON file"""
        try:
            # Convert dataclass objects to dictionaries
            json_data = []
            for item in data:
                if hasattr(item, '__dict__'):
                    item_dict = item.__dict__.copy()
                    # Convert datetime objects to strings
                    for key, value in item_dict.items():
                        if isinstance(value, datetime):
                            item_dict[key] = value.isoformat()
                    json_data.append(item_dict)
                else:
                    json_data.append(item)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Data saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving data to {filename}: {str(e)}")

    def get_politician_by_name(self, name: str) -> Optional[Politician]:
        """Get a specific politician by name"""
        politicians = self.get_politicians()
        for politician in politicians:
            if name.lower() in politician.name.lower():
                return politician
        return None

    def get_recent_votes(self, days: int = 30) -> List[VotingRecord]:
        """Get recent voting records from the last N days"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_voting_records(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

# Example usage
if __name__ == "__main__":
    collector = EduskuntaCollector()
    
    # Get current politicians
    politicians = collector.get_politicians()
    print(f"Found {len(politicians)} politicians")
    
    # Save to file
    collector.save_data(politicians, "eduskunta_politicians.json")
    
    # Get recent voting records
    recent_votes = collector.get_recent_votes(days=7)
    print(f"Found {len(recent_votes)} recent votes")
    
    # Save voting records
    collector.save_data(recent_votes, "eduskunta_votes.json")
