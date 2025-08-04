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
class VaalikoneCandidate:
    candidate_id: str
    name: str
    party: str
    constituency: str
    election_year: str
    answers: Dict[str, str]  # question_id -> answer
    profile_url: Optional[str] = None
    image_url: Optional[str] = None

@dataclass
class VaalikoneQuestion:
    question_id: str
    question_text: str
    category: str
    election_year: str

class VaalikoneCollector(PoliticianCollector):
    """Collector for Vaalikone (YLE Election Compass) data"""
    
    def __init__(self):
        super().__init__('vaalikone')
    
    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        election_type = kwargs.get('election_type', 'eduskuntavaalit')
        return self.get_politicians(election_type)

    def get_politicians(self, election_type: str = 'eduskuntavaalit') -> List[Dict[str, Any]]:
        """Get politicians from Vaalikone for specified election type"""
        try:
            self.logger.info(f"Fetching politicians for {election_type} from Vaalikone")
            elections = self.get_available_elections()
            
            # Find matching election
            target_election = None
            for election in elections:
                if election_type.lower() in election.get('name', '').lower():
                    target_election = election
                    break
            
            if not target_election:
                self.logger.warning(f"No election found for type: {election_type}")
                return self._get_default_politicians()
            
            # Get politicians for this election
            politicians = self._fetch_election_politicians(target_election)
            print(f"Collected {len(politicians)} politicians from Eduskunta")
            for p in politicians[:10]:
                 print(p)
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error fetching politicians: {str(e)}")
            return self._get_default_politicians()

    def get_available_elections(self) -> List[Dict[str, str]]:
        """Get list of available elections from Vaalikone"""
        try:
            response = self.make_request('elections')
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Error fetching elections: {str(e)}")
            return self._get_default_elections()

    def _get_default_politicians(self) -> List[Dict[str, Any]]:
        """Get default list of politicians when API fails"""
        return [
            {
                'politician_id': 'vaalikone_001',
                'name': 'Sample Politician',
                'party': 'Sample Party',
                'election_type': 'eduskuntavaalit',
                'source': 'vaalikone',
                'answers': [],
                'profile_url': None
            }
        ]

    def _fetch_election_politicians(self, election: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch politicians for a specific election"""
        try:
            # Try to get candidates for this election
            election_id = election.get('id', election.get('name', '').replace(' ', '_'))
            response = self.make_request('candidates', params={'election': election_id})
            
            politicians = []
            candidates_data = response.json()
            
            for candidate in candidates_data.get('candidates', []):
                politician = {
                    'politician_id': candidate.get('id', str(hash(candidate.get('name', '')))),
                    'name': candidate.get('name', ''),
                    'party': candidate.get('party', ''),
                    'election_type': election.get('name', ''),
                    'source': 'vaalikone',
                    'answers': candidate.get('answers', []),
                    'profile_url': candidate.get('profile_url')
                }
                politicians.append(politician)
            
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error fetching election politicians: {str(e)}")
            return self._get_default_politicians()

    def _get_default_elections(self) -> List[Dict[str, str]]:
        """Get default elections when scraping fails"""
        return [
            {
                'name': 'Eduskuntavaalit 2023',
                'id': 'eduskuntavaalit_2023',
                'year': '2023'
            },
            {
                'name': 'Kuntavaalit 2021',
                'id': 'kuntavaalit_2021', 
                'year': '2021'
            }
        ]

    def _scrape_elections(self) -> List[Dict[str, str]]:
        """Scrape elections from main page as fallback"""
        try:
            response = self.session.get(self.get_base_url())
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            elections = []
            
            # Look for election links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if 'eduskuntavaalit' in href or 'kuntavaalit' in href or 'europarlamenttivaalit' in href:
                    elections.append({
                        'name': link.get_text().strip(),
                        'url': href,
                        'year': self._extract_year_from_text(link.get_text())
                    })
            
            return elections
            
        except Exception as e:
            self.logger.error(f"Error scraping elections: {str(e)}")
            return []

    def get_candidates(self, election_id: str) -> List[VaalikoneCandidate]:
        """Get candidates for a specific election"""
        try:
            # Use proper endpoint URL from base collector
            base_url = self.get_endpoint_url('base')
            url = f"{base_url}/api/candidates/{election_id}"
            
            response = self.session.get(url)
            
            if response.status_code == 404:
                # Try alternative URL structure
                url = f"{base_url}/{election_id}/ehdokkaat"
                return self._scrape_candidates(url)
            
            response.raise_for_status()
            data = response.json()
            
            candidates = []
            for candidate_data in data.get('candidates', []):
                candidate = self._parse_candidate(candidate_data, election_id)
                if candidate:
                    candidates.append(candidate)
            
            self.logger.info(f"Successfully fetched {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error fetching candidates: {str(e)}")
            # Return fallback candidate data
            return self._get_fallback_candidates(election_id)
    
    def _get_fallback_candidates(self, election_id: str) -> List[VaalikoneCandidate]:
        """Get fallback candidate data when API fails"""
        try:
            # Return sample candidates for testing
            fallback_candidates = [
                VaalikoneCandidate(
                    candidate_id=f"fallback_{election_id}_001",
                    name="Sample Candidate 1",
                    party="Kokoomus",
                    constituency="Uusimaa",
                    election_year=election_id,
                    answers={"q1": "agree", "q2": "disagree"},
                    profile_url=None,
                    image_url=None
                ),
                VaalikoneCandidate(
                    candidate_id=f"fallback_{election_id}_002",
                    name="Sample Candidate 2",
                    party="SDP",
                    constituency="Pirkanmaa",
                    election_year=election_id,
                    answers={"q1": "disagree", "q2": "agree"},
                    profile_url=None,
                    image_url=None
                )
            ]
            
            self.logger.info(f"Generated {len(fallback_candidates)} fallback candidates for {election_id}")
            return fallback_candidates
            
        except Exception as e:
            self.logger.error(f"Error generating fallback candidates: {str(e)}")
            return []

    def _scrape_candidates(self, url: str) -> List[VaalikoneCandidate]:
        """Scrape candidates from election page"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            candidates = []
            
            # Look for candidate cards or listings
            candidate_elements = soup.find_all(['div', 'article'], class_=lambda x: x and 'candidate' in x.lower())
            
            for element in candidate_elements:
                candidate = self._parse_candidate_element(element, url)
                if candidate:
                    candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error scraping candidates from {url}: {str(e)}")
            return []

    def get_questions(self, election_id: str) -> List[VaalikoneQuestion]:
        """Get questions for a specific election"""
        try:
            url = f"{self.get_base_url()}/api/questions/{election_id}"
            response = self.session.get(url)
            
            if response.status_code == 404:
                # Try scraping approach
                return self._scrape_questions(election_id)
            
            response.raise_for_status()
            data = response.json()
            
            questions = []
            for question_data in data.get('questions', []):
                question = VaalikoneQuestion(
                    question_id=str(question_data.get('id', '')),
                    question_text=question_data.get('text', ''),
                    category=question_data.get('category', ''),
                    election_year=election_id
                )
                questions.append(question)
            
            self.logger.info(f"Successfully fetched {len(questions)} questions")
            return questions
            
        except Exception as e:
            self.logger.error(f"Error fetching questions: {str(e)}")
            return []

    def _scrape_questions(self, election_id: str) -> List[VaalikoneQuestion]:
        """Scrape questions from election page"""
        try:
            url = f"{self.get_base_url()}/{election_id}/kysymykset"
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            questions = []
            
            # Look for question elements
            question_elements = soup.find_all(['div', 'li'], class_=lambda x: x and 'question' in x.lower())
            
            for i, element in enumerate(question_elements):
                question_text = element.get_text().strip()
                if question_text:
                    question = VaalikoneQuestion(
                        question_id=str(i + 1),
                        question_text=question_text,
                        category='general',
                        election_year=election_id
                    )
                    questions.append(question)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error scraping questions: {str(e)}")
            return []

    def _parse_candidate(self, data: Dict, election_id: str) -> Optional[VaalikoneCandidate]:
        """Parse candidate data from API response"""
        try:
            return VaalikoneCandidate(
                candidate_id=str(data.get('id', '')),
                name=data.get('name', ''),
                party=data.get('party', ''),
                constituency=data.get('constituency', ''),
                election_year=election_id,
                answers=data.get('answers', {}),
                profile_url=data.get('profile_url'),
                image_url=data.get('image_url')
            )
        except Exception as e:
            self.logger.error(f"Error parsing candidate data: {str(e)}")
            return None

    def _parse_candidate_element(self, element, base_url: str) -> Optional[VaalikoneCandidate]:
        """Parse candidate from HTML element"""
        try:
            name = element.find(['h2', 'h3', 'span'], class_=lambda x: x and 'name' in x.lower())
            party = element.find(['span', 'div'], class_=lambda x: x and 'party' in x.lower())
            
            if name:
                return VaalikoneCandidate(
                    candidate_id=str(hash(name.get_text().strip())),
                    name=name.get_text().strip(),
                    party=party.get_text().strip() if party else '',
                    constituency='',
                    election_year=self._extract_year_from_text(base_url),
                    answers={}
                )
        except Exception as e:
            self.logger.error(f"Error parsing candidate element: {str(e)}")
            
        return None

    def _extract_year_from_text(self, text: str) -> str:
        """Extract year from text"""
        import re
        years = re.findall(r'20\d{2}', text)
        return years[0] if years else str(datetime.now().year)

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
    collector = VaalikoneCollector()
    
    # Get available elections
    elections = collector.get_available_elections()
    print(f"Found {len(elections)} elections")
    
    if elections:
        # Get candidates for the first election
        election_id = elections[0].get('year', '2023')
        candidates = collector.get_candidates(election_id)
        print(f"Found {len(candidates)} candidates")
        
        # Save data
        collector.save_data(candidates, f"vaalikone_candidates_{election_id}.json")

