import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import logging
from bs4 import BeautifulSoup

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_collector import PoliticianCollector
from config.api_endpoints import APIConfig

@dataclass
class MunicipalPolitician:
    politician_id: str
    name: str
    municipality: str
    position: str
    party: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    term_start: Optional[str] = None
    term_end: Optional[str] = None

@dataclass
class Municipality:
    municipality_id: str
    name: str
    region: str
    population: Optional[int] = None
    website: Optional[str] = None

class KuntaliitoCollector(PoliticianCollector):
    """Collector for Kuntaliitto (Association of Finnish Municipalities) data using centralized configuration"""
    
    def __init__(self):
        super().__init__('kuntaliitto')

    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        return self.get_municipalities()

    def get_politicians(self, municipality: str = None) -> List[Dict[str, Any]]:
        """Get politicians for municipalities (required by PoliticianCollector)"""
        # For Kuntaliitto, we return municipality data as our 'politicians' are municipal leaders
        municipalities = self.get_municipalities()
        
        if municipality:
            # Filter by specific municipality
            return [m for m in municipalities if municipality.lower() in m.get('name', '').lower()]
        
        return municipalities

    def get_municipalities(self) -> List[Dict[str, Any]]:
        """Get list of Finnish municipalities"""
        try:
            self.logger.info("Fetching municipalities from Kuntaliitto")
            response = self.make_request('municipalities')
            
            soup = BeautifulSoup(response.content, 'html.parser')
            municipalities = []
            
            # Look for municipality listings
            municipality_elements = soup.find_all(['div', 'li', 'tr'], class_=lambda x: x and any(
                term in x.lower() for term in ['municipality', 'kunta', 'city', 'kaupunki']
            ))
            
            for element in municipality_elements:
                municipality = self._parse_municipality_element(element)
                if municipality:
                    municipalities.append(municipality)
            
            # Fallback: scrape from links
            if not municipalities:
                municipality_links = soup.find_all('a', href=lambda x: x and 'kunta' in x.lower())
                for link in municipality_links:
                    name = link.get_text().strip()
                    if name and len(name) > 2:
                        municipality = Municipality(
                            municipality_id=str(hash(name)),
                            name=name,
                            region='Unknown',
                            website=link.get('href')
                        )
                        municipalities.append(municipality)
            
            self.logger.info(f"Successfully fetched {len(municipalities)} municipalities")
            return municipalities
            
        except Exception as e:
            self.logger.error(f"Error fetching municipalities: {str(e)}")
            return self._get_default_municipalities()

    def _get_default_municipalities(self) -> List[Dict[str, Any]]:
        """Get default list of major Finnish municipalities"""
        major_municipalities = [
            {'name': 'Helsinki', 'region': 'Uusimaa', 'population': 656920},
            {'name': 'Espoo', 'region': 'Uusimaa', 'population': 297132},
            {'name': 'Tampere', 'region': 'Pirkanmaa', 'population': 244029},
            {'name': 'Vantaa', 'region': 'Uusimaa', 'population': 239216},
            {'name': 'Oulu', 'region': 'Pohjois-Pohjanmaa', 'population': 208939},
            {'name': 'Turku', 'region': 'Varsinais-Suomi', 'population': 195301},
            {'name': 'Jyväskylä', 'region': 'Keski-Suomi', 'population': 143400},
            {'name': 'Lahti', 'region': 'Päijät-Häme', 'population': 119450},
            {'name': 'Kuopio', 'region': 'Pohjois-Savo', 'population': 118667},
            {'name': 'Pori', 'region': 'Satakunta', 'population': 83796}
        ]
        
        municipalities = []
        for muni_data in major_municipalities:
            municipality = {
                'municipality_id': str(hash(muni_data['name'])),
                'name': muni_data['name'],
                'region': muni_data['region'],
                'population': muni_data['population'],
                'source': 'kuntaliitto'
            }
            municipalities.append(municipality)
        
        return municipalities

    def get_municipal_politicians(self, municipality_name: str) -> List[MunicipalPolitician]:
        """Get politicians for a specific municipality"""
        try:
            # Try to find municipality website or politician listings
            search_terms = [
                f"{municipality_name} kaupunginvaltuusto",
                f"{municipality_name} kunnanvaltuusto",
                f"{municipality_name} luottamushenkilöt"
            ]
            
            politicians = []
            for search_term in search_terms:
                found_politicians = self._search_municipal_politicians(search_term, municipality_name)
                politicians.extend(found_politicians)
                if politicians:
                    break
            
            self.logger.info(f"Found {len(politicians)} politicians for {municipality_name}")
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error fetching politicians for {municipality_name}: {str(e)}")
            return []

    def _search_municipal_politicians(self, search_term: str, municipality: str) -> List[MunicipalPolitician]:
        """Search for municipal politicians"""
        try:
            # Try municipality website first
            municipality_url = f"https://www.{municipality.lower()}.fi"
            
            try:
                response = self.session.get(municipality_url)
                if response.status_code == 200:
                    return self._scrape_municipality_website(response.content, municipality)
            except:
                pass
            
            # Fallback to general search
            search_url = "https://www.google.com/search"
            params = {
                'q': f"{search_term} site:*.fi",
                'num': 10
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                return self._parse_search_results(response.content, municipality)
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error searching for politicians: {str(e)}")
            return []

    def _scrape_municipality_website(self, content: bytes, municipality: str) -> List[MunicipalPolitician]:
        """Scrape politicians from municipality website"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            politicians = []
            
            # Look for politician or council member listings
            politician_elements = soup.find_all(['div', 'li', 'tr'], class_=lambda x: x and any(
                term in x.lower() for term in ['council', 'valtuusto', 'politician', 'member', 'jäsen']
            ))
            
            for element in politician_elements:
                politician = self._parse_politician_element(element, municipality)
                if politician:
                    politicians.append(politician)
            
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error scraping municipality website: {str(e)}")
            return []

    def _parse_municipality_element(self, element) -> Optional[Municipality]:
        """Parse municipality from HTML element"""
        try:
            name_elem = element.find(['h1', 'h2', 'h3', 'a', 'span'])
            if not name_elem:
                return None
            
            name = name_elem.get_text().strip()
            if not name or len(name) < 2:
                return None
            
            return Municipality(
                municipality_id=str(hash(name)),
                name=name,
                region='Unknown'
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing municipality element: {str(e)}")
            return None

    def _parse_politician_element(self, element, municipality: str) -> Optional[MunicipalPolitician]:
        """Parse politician from HTML element"""
        try:
            name_elem = element.find(['h1', 'h2', 'h3', 'span'], class_=lambda x: x and 'name' in x.lower())
            if not name_elem:
                name_elem = element.find(['h1', 'h2', 'h3', 'span'])
            
            if not name_elem:
                return None
            
            name = name_elem.get_text().strip()
            if not name or len(name) < 3:
                return None
            
            # Try to find position
            position_elem = element.find(['span', 'div'], class_=lambda x: x and any(
                term in x.lower() for term in ['position', 'title', 'asema', 'tehtävä']
            ))
            position = position_elem.get_text().strip() if position_elem else 'Council Member'
            
            # Try to find party
            party_elem = element.find(['span', 'div'], class_=lambda x: x and 'party' in x.lower())
            party = party_elem.get_text().strip() if party_elem else None
            
            politician = MunicipalPolitician(
                politician_id=str(hash(f"{name}_{municipality}")),
                name=name,
                municipality=municipality,
                position=position,
                party=party
            )
            
            return politician
            
        except Exception as e:
            self.logger.error(f"Error parsing politician element: {str(e)}")
            return None

    def _parse_search_results(self, content: bytes, municipality: str) -> List[MunicipalPolitician]:
        """Parse search results for politicians"""
        # This would be implemented to parse Google search results
        # For now, return empty list to avoid scraping Google directly
        return []

    def save_data(self, data: List, filename: str):
        """Save data to JSON file"""
        try:
            json_data = []
            for item in data:
                if hasattr(item, '__dict__'):
                    item_dict = item.__dict__.copy()
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

# Example usage
if __name__ == "__main__":
    collector = KuntaliitoCollector()
    
    # Get municipalities
    municipalities = collector.get_municipalities()
    print(f"Found {len(municipalities)} municipalities")
    
    # Get politicians for Helsinki
    if municipalities:
        helsinki_politicians = collector.get_municipal_politicians("Helsinki")
        print(f"Found {len(helsinki_politicians)} politicians in Helsinki")
        
        # Save data
        collector.save_data(municipalities, "municipalities.json")
        collector.save_data(helsinki_politicians, "helsinki_politicians.json")

