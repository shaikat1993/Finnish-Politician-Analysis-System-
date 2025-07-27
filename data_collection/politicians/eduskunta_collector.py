import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import logging
import sys
import os

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
        Get list of politicians from Eduskunta API
        
        Args:
            term: Parliamentary term (e.g., "2023-2027")
        
        Returns:
            List of politician dictionaries
        """
        try:
            params = {}
            if term:
                params['vaalikausi'] = term
            
            self.logger.info("Fetching politicians from Eduskunta API")
            response = self.make_request('politicians', params=params)
            data = response.json()
            
            politicians = []
            for member_data in data.get('kansanedustajat', []):
                politician = self._parse_politician(member_data)
                if politician:
                    politicians.append(politician)
            
            self.logger.info(f"Successfully fetched {len(politicians)} politicians")
            return politicians
            
        except Exception as e:
            self.logger.error(f"Error fetching politicians: {str(e)}")
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
            return {
                'politician_id': str(data.get('henkiloId', '')),
                'name': f"{data.get('etunimi', '')} {data.get('sukunimi', '')}".strip(),
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
        except Exception as e:
            self.logger.error(f"Error parsing politician data: {str(e)}")
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
