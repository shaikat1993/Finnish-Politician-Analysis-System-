import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import wikipediaapi

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_collector import BaseCollector
from config.api_endpoints import APIConfig

@dataclass
class WikipediaPolitician:
    name: str
    wiki_id: str
    url: str
    summary: str
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    parties: List[str] = None
    positions: List[str] = None
    image_url: Optional[str] = None

@dataclass
class WikipediaCategory:
    name: str
    members: List[str]

class WikipediaCollector(BaseCollector):
    """Wikipedia collector for Finnish politician data using centralized configuration"""
    
    def __init__(self):
        super().__init__('wikipedia')
    
    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        query = kwargs.get('query', 'Finnish politicians')
        limit = kwargs.get('limit', 10)
        return self.search_politicians(query, limit)

    def get_politician_categories(self) -> List[WikipediaCategory]:
        """Get all Finnish politician categories from Wikipedia"""
        categories = []
        
        # Main politician categories
        main_categories = [
            "Suomen poliitikot",
            "Eduskuntajäsenet",
            "Suomen ministerit",
            "Suomen pääministerit"
        ]
        
        for category_name in main_categories:
            category = self.wiki.page(f"Category:{category_name}")
            if category.exists():
                members = []
                for member in category.categorymembers.values():
                    if member.ns == 0:  # Only get articles (namespace 0)
                        members.append(member.title)
                
                categories.append(WikipediaCategory(
                    name=category_name,
                    members=members
                ))
        
        return categories

    def get_politician_info(self, politician_name: str) -> Optional[WikipediaPolitician]:
        """Get detailed information about a specific politician"""
        page = self.wiki.page(politician_name)
        
        if not page.exists():
            return None
            
        # Parse infobox data
        infobox = self._parse_infobox(page.text)
        
        politician = WikipediaPolitician(
            name=politician_name,
            wiki_id=page.pageid,
            url=page.fullurl,
            summary=page.summary,
            birth_date=infobox.get("birth_date"),
            death_date=infobox.get("death_date"),
            parties=infobox.get("parties", []),
            positions=infobox.get("positions", []),
            image_url=self._get_image_url(page)
        )
        
        return politician

    def _parse_infobox(self, text: str) -> Dict[str, Any]:
        """Extract structured data from Wikipedia infobox"""
        infobox = {}
        
        # Simple parsing of common fields
        # In production, use a more robust parser like mwparserfromhell
        lines = text.split('\n')
        for line in lines:
            if "| syntynyt =" in line:
                infobox["birth_date"] = line.split("=")[1].strip()
            elif "| kuollut =" in line:
                infobox["death_date"] = line.split("=")[1].strip()
            elif "| puolue =" in line:
                infobox["parties"] = [line.split("=")[1].strip()]
            elif "| virka =" in line:
                infobox["positions"] = [line.split("=")[1].strip()]
        
        return infobox

    def _get_image_url(self, page) -> Optional[str]:
        """Get the main image URL from the page"""
        try:
            image = page.images[0]
            return image.fullurl
        except (IndexError, KeyError):
            return None

    def save_to_json(self, data: List[Dict], filename: str):
        """Save collected Wikipedia data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Example usage
    collector = WikipediaCollector()
    
    try:
        # Get politician categories
        categories = collector.get_politician_categories()
        
        # Get detailed info about a politician
        politician = collector.get_politician_info("Sanna Marin")
        
        # Save data
        collector.save_to_json([c.__dict__ for c in categories], "wiki_categories.json")
        if politician:
            collector.save_to_json([politician.__dict__], "wiki_politician.json")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        # TODO: Implement main data collection logic
        return []

    def search_politicians(self, query: str = 'Finnish politicians', limit: int = 10) -> List[Dict[str, Any]]:
        """Search for Finnish politicians on Wikipedia"""
        try:
            self.logger.info(f"Searching Wikipedia for: {query}")
            
            # Get politician categories
            categories = self.get_politician_categories()
            politicians = []
            
            # Collect politicians from categories
            for category in categories[:2]:  # Limit to first 2 categories
                for member_name in category.members[:limit//2]:  # Split limit across categories
                    politician_info = self.get_politician_info(member_name)
                    if politician_info:
                        politicians.append({
                            'name': politician_info.name,
                            'wiki_id': politician_info.wiki_id,
                            'url': politician_info.url,
                            'summary': politician_info.summary,
                            'birth_date': politician_info.birth_date,
                            'parties': politician_info.parties or [],
                            'positions': politician_info.positions or [],
                            'source': 'wikipedia',
                            'collected_at': datetime.now().isoformat()
                        })
                        
                        if len(politicians) >= limit:
                            break
                
                if len(politicians) >= limit:
                    break
            
            self.logger.info(f"Found {len(politicians)} politicians from Wikipedia")
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error searching Wikipedia: {str(e)}")
            return []

