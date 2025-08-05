import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import wikipediaapi
import unicodedata

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
        import wikipediaapi
        self.wiki = wikipediaapi.Wikipedia(language='en', user_agent='FinnishPoliticianAnalysisBot/1.0 (shaikat1993@gmail.com)')  # English Wikipedia with user agent
    
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
        """
        Get detailed information about a specific politician, with robust fallback logic and fuzzy matching.
        Logs every step for bulletproof debugging and root-cause analysis.
        """
        print(f"[DEBUG] get_politician_info CALLED for: {politician_name}")
        import mwparserfromhell
        from difflib import get_close_matches
        import logging
        logger = logging.getLogger("wikipedia_collector")
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        logger.info(f"[ENRICH] Start enrichment for: '{politician_name}'")
        print(f"[DEBUG] Logging active for: {politician_name}")

        def try_page(wiki, name, lang_label):
            logger.info(f"[ENRICH] Trying exact page: '{name}' (lang={lang_label})")
            page = wiki.page(name)
            if page.exists():
                logger.info(f"[ENRICH] Found exact page: '{name}' (lang={lang_label})")
                return page
            # Try normalized
            norm_name = self._normalize_name(name)
            if norm_name != name:
                logger.info(f"[ENRICH] Trying normalized: '{norm_name}' (lang={lang_label})")
                page = wiki.page(norm_name)
                if page.exists():
                    logger.info(f"[ENRICH] Found normalized page: '{norm_name}' (lang={lang_label})")
                    return page
            return None

        # Try Finnish Wikipedia first (most likely for Finnish MPs)
        import wikipediaapi
        wiki_fi = wikipediaapi.Wikipedia(language='fi', user_agent='FinnishPoliticianAnalysisBot/1.0 (shaikat1993@gmail.com)')
        page = try_page(wiki_fi, politician_name, 'fi')

        tokens = politician_name.split()
        # Fuzzy fallback: try removing middle names, try last name only
        if not page:
            if len(tokens) > 2:
                simple_name = f"{tokens[0]} {tokens[-1]}"
                page = try_page(wiki_fi, simple_name, 'fi')
            if not page and len(tokens) > 1:
                page = try_page(wiki_fi, tokens[-1], 'fi')

        # Try English Wikipedia if still not found
        if not page:
            wiki_en = self.wiki
            page = try_page(wiki_en, politician_name, 'en')
            if not page and len(tokens) > 2:
                simple_name = f"{tokens[0]} {tokens[-1]}"
                page = try_page(wiki_en, simple_name, 'en')
            if not page and len(tokens) > 1:
                page = try_page(wiki_en, tokens[-1], 'en')

        # Fuzzy search in both languages if still not found
        if not page:
            try:
                logger.info("[ENRICH] Fuzzy search in Finnish category")
                category = wiki_fi.page("Luokka:Suomen kansanedustajat")
                if category.exists():
                    candidates = [m.title for m in category.categorymembers.values() if m.ns == 0]
                    match = get_close_matches(politician_name, candidates, n=1, cutoff=0.75)
                    if match:
                        logger.info(f"[ENRICH] Fuzzy match in fi: '{match[0]}'")
                        page = wiki_fi.page(match[0])
            except Exception as e:
                logger.warning(f"[ENRICH] Fuzzy category search failed (fi): {e}")
        if not page:
            try:
                logger.info("[ENRICH] Fuzzy search in English category")
                category = self.wiki.page("Category:Members of the Parliament of Finland")
                if category.exists():
                    candidates = [m.title for m in category.categorymembers.values() if m.ns == 0]
                    match = get_close_matches(politician_name, candidates, n=1, cutoff=0.75)
                    if match:
                        logger.info(f"[ENRICH] Fuzzy match in en: '{match[0]}'")
                        page = self.wiki.page(match[0])
            except Exception as e:
                logger.warning(f"[ENRICH] Fuzzy category search failed (en): {e}")

        if not page or not page.exists():
            logger.warning(f"[ENRICH] No Wikipedia page found for: '{politician_name}'")
            return None

        # Use mwparserfromhell for robust infobox parsing
        try:
            wikicode = mwparserfromhell.parse(page.text)
            templates = [t for t in wikicode.filter_templates() if "Infobox" in t.name.lower()]
            infobox = {}
            if templates:
                t = templates[0]
                for param in t.params:
                    pname = str(param.name).strip().lower()
                    pval = str(param.value).strip()
                    if pname in ("syntynyt", "born"):
                        infobox["birth_date"] = pval
                    elif pname in ("kuollut", "died"):
                        infobox["death_date"] = pval
                    elif pname in ("puolue", "party"):
                        infobox["parties"] = [pval]
                    elif pname in ("virka", "position", "positions"):
                        infobox["positions"] = [pval]
            else:
                infobox = self._parse_infobox(page.text)
        except Exception as e:
            logger.error(f"[ENRICH] Infobox parsing failed for '{politician_name}': {e}")
            infobox = {}

        politician = WikipediaPolitician(
            name=politician_name,
            wiki_id=getattr(page, 'pageid', ''),
            url=page.fullurl,
            summary=page.summary,
            birth_date=infobox.get("birth_date"),
            death_date=infobox.get("death_date"),
            parties=infobox.get("parties", []),
            positions=infobox.get("positions", []),
            image_url=self._get_image_url(page)
        )
        logger.info(f"[ENRICH] SUCCESS: Enriched '{politician_name}' with Wikipedia URL: {politician.url}")
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
        """
        Get the main image URL for a Wikipedia page.
        1. Try Wikidata (P18 property)
        2. Fallback: Try Wikipedia 'pageimages' API
        Returns None if no image found.
        """
        # 1. Try Wikidata (P18)
        if hasattr(page, 'wikibase') and page.wikibase:
            wikidata_url = f'https://www.wikidata.org/wiki/Special:EntityData/{page.wikibase}.json'
            try:
                r = requests.get(wikidata_url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    entity = data['entities'][page.wikibase]
                    claims = entity.get('claims', {})
                    if 'P18' in claims:
                        image_name = claims['P18'][0]['mainsnak']['datavalue']['value']
                        from urllib.parse import quote
                        # Direct image URL from Wikimedia Commons
                        image_url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{quote(image_name)}'
                        return image_url
            except Exception as e:
                # Log error (optional)
                pass
        # 2. Fallback: Try Wikipedia API 'pageimages'
        try:
            # Use Wikipedia API to get thumbnail
            api_url = (
                f"https://{page.language}.wikipedia.org/w/api.php?action=query&titles="
                f"{requests.utils.quote(page.title)}&prop=pageimages&format=json&pithumbsize=500"
            )
            resp = requests.get(api_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                pages = data.get('query', {}).get('pages', {})
                for p in pages.values():
                    if 'thumbnail' in p and 'source' in p['thumbnail']:
                        return p['thumbnail']['source']
        except Exception as e:
            # Log error (optional)
            pass
        # No image found
        return None

    def _normalize_name(self, name):
        return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

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

