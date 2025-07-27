"""
Centralized API Endpoints and Service Configuration
This module contains all API URLs, endpoints, and service configurations
to ensure easy maintenance and avoid hardcoding across the application.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import os

@dataclass
class APIEndpoint:
    """Configuration for an API endpoint"""
    base_url: str
    endpoints: Dict[str, str]
    headers: Dict[str, str]
    rate_limit: Optional[int] = None  # requests per minute
    requires_auth: bool = False
    auth_type: Optional[str] = None  # 'api_key', 'bearer', 'basic'

@dataclass
class RSSFeed:
    """Configuration for RSS feeds"""
    name: str
    url: str
    category: str

class APIConfig:
    """Centralized API configuration for all data collectors"""
    
    # ===========================================
    # PRIMARY SOURCES - Government & Official
    # ===========================================
    
    EDUSKUNTA = APIEndpoint(
        base_url="https://avoindata.eduskunta.fi/api/v1",
        endpoints={
            "politicians": "/kansanedustajat",
            "voting_records": "/aanestykset",
            "sessions": "/istunnot",
            "committees": "/valiokunnat",
            "documents": "/asiakirjat"
        },
        headers={
            'User-Agent': 'FPAS-DataCollector/1.0',
            'Accept': 'application/json'
        },
        rate_limit=60,  # 60 requests per minute
        requires_auth=False
    )
    
    VAALIKONE = APIEndpoint(
        base_url="https://vaalikone.yle.fi",
        endpoints={
            "elections": "/api/elections",
            "candidates": "/api/candidates/{election_id}",
            "questions": "/api/questions/{election_id}",
            "answers": "/api/answers/{candidate_id}",
            "search": "/haku"
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/html'
        },
        rate_limit=30,
        requires_auth=False
    )
    
    KUNTALIITTO = APIEndpoint(
        base_url="https://www.kuntaliitto.fi",
        endpoints={
            "municipalities": "/tietopankit/kunnat",
            "municipal_data": "/api/kunnat/{municipality_id}",
            "politicians": "/luottamushenkilot"
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml'
        },
        rate_limit=20,
        requires_auth=False
    )
    
    # ===========================================
    # NEWS SOURCES - Major Finnish Media
    # ===========================================
    
    YLE = APIEndpoint(
        base_url="https://external.api.yle.fi/v1",
        endpoints={
            "articles": "/articles",
            "search": "/articles/search",
            "programs": "/programs",
            "categories": "/categories"
        },
        headers={
            "Accept": "application/json",
            "X-Api-Key": os.getenv('YLE_API_KEY', '')
        },
        rate_limit=100,
        requires_auth=True,
        auth_type='api_key'
    )
    
    HELSINGIN_SANOMAT = APIEndpoint(
        base_url="https://www.hs.fi",
        endpoints={
            "search": "/haku",
            "articles": "/api/articles",
            "categories": "/api/categories"
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8'
        },
        rate_limit=30,
        requires_auth=False
    )
    
    ILTALEHTI = APIEndpoint(
        base_url="https://www.iltalehti.fi",
        endpoints={
            "search": "/haku",
            "articles": "/api/articles",
            "categories": "/kategoriat"
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8'
        },
        rate_limit=30,
        requires_auth=False
    )
    
    MTV_UUTISET = APIEndpoint(
        base_url="https://www.mtvuutiset.fi",
        endpoints={
            "search": "/haku",
            "articles": "/api/articles",
            "categories": "/kategoriat"
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8'
        },
        rate_limit=30,
        requires_auth=False
    )
    
    KAUPPALEHTI = APIEndpoint(
        base_url="https://www.kauppalehti.fi",
        endpoints={
            "search": "/haku",
            "articles": "/api/articles",
            "categories": "/kategoriat",
            "companies": "/yritykset"
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8'
        },
        rate_limit=20,
        requires_auth=False
    )
    
    # ===========================================
    # SECONDARY SOURCES
    # ===========================================
    
    WIKIPEDIA = APIEndpoint(
        base_url="https://fi.wikipedia.org/w/api.php",
        endpoints={
            "query": "",
            "search": "",
            "page": "",
            "categories": ""
        },
        headers={
            'User-Agent': 'FPAS-WikiCollector/1.0 (https://github.com/fpas)',
            'Accept': 'application/json'
        },
        rate_limit=50,
        requires_auth=False
    )
    
    # ===========================================
    # RSS FEEDS CONFIGURATION
    # ===========================================
    
    RSS_FEEDS = {
        'yle': [
            RSSFeed('YLE Politiikka', 'https://feeds.yle.fi/uutiset/v1/majorNews.rss', 'politiikka'),
            RSSFeed('YLE Kotimaa', 'https://feeds.yle.fi/uutiset/v1/recent.rss', 'kotimaa'),
            RSSFeed('YLE Uutiset', 'https://feeds.yle.fi/uutiset/v1/recent.rss', 'uutiset')
        ],
        'helsingin_sanomat': [
            RSSFeed('HS Politiikka', 'https://www.hs.fi/rss/politiikka.xml', 'politiikka'),
            RSSFeed('HS Kotimaa', 'https://www.hs.fi/rss/kotimaa.xml', 'kotimaa'),
            RSSFeed('HS Pääkirjoitukset', 'https://www.hs.fi/rss/paakirjoitukset.xml', 'paakirjoitukset'),
            RSSFeed('HS Mielipide', 'https://www.hs.fi/rss/mielipide.xml', 'mielipide'),
            RSSFeed('HS Tuoreimmat', 'https://www.hs.fi/rss/tuoreimmat.xml', 'uutiset')
        ],
        'iltalehti': [
            RSSFeed('IL Politiikka', 'https://www.iltalehti.fi/rss/politiikka.xml', 'politiikka'),
            RSSFeed('IL Kotimaa', 'https://www.iltalehti.fi/rss/kotimaa.xml', 'kotimaa'),
            RSSFeed('IL Uutiset', 'https://www.iltalehti.fi/rss/uutiset.xml', 'uutiset'),
            RSSFeed('IL Tuoreimmat', 'https://www.iltalehti.fi/rss/tuoreimmat.xml', 'tuoreimmat')
        ],
        'mtv_uutiset': [
            RSSFeed('MTV Politiikka', 'https://www.mtvuutiset.fi/api/feed/rss/politiikka', 'politiikka'),
            RSSFeed('MTV Kotimaa', 'https://www.mtvuutiset.fi/api/feed/rss/kotimaa', 'kotimaa'),
            RSSFeed('MTV Uutiset', 'https://www.mtvuutiset.fi/api/feed/rss/uutiset', 'uutiset'),
            RSSFeed('MTV Tuoreimmat', 'https://www.mtvuutiset.fi/api/feed/rss/tuoreimmat', 'tuoreimmat')
        ],
        'kauppalehti': [
            RSSFeed('KL Politiikka', 'https://www.kauppalehti.fi/rss/politiikka', 'politiikka'),
            RSSFeed('KL Talous', 'https://www.kauppalehti.fi/rss/talous', 'talous'),
            RSSFeed('KL Uutiset', 'https://www.kauppalehti.fi/rss/uutiset', 'uutiset'),
            RSSFeed('KL Pääkirjoitukset', 'https://www.kauppalehti.fi/rss/paakirjoitukset', 'paakirjoitukset')
        ]
    }
    
    # ===========================================
    # MUNICIPALITY WEBSITES
    # ===========================================
    
    MUNICIPALITY_WEBSITES = {
        'Helsinki': 'https://www.hel.fi',
        'Espoo': 'https://www.espoo.fi',
        'Tampere': 'https://www.tampere.fi',
        'Vantaa': 'https://www.vantaa.fi',
        'Oulu': 'https://www.ouka.fi',
        'Turku': 'https://www.turku.fi',
        'Jyväskylä': 'https://www.jyvaskyla.fi',
        'Lahti': 'https://www.lahti.fi',
        'Kuopio': 'https://www.kuopio.fi',
        'Pori': 'https://www.pori.fi'
    }
    
    # ===========================================
    # ESSENTIAL UTILITY METHODS
    # ===========================================
    
    @classmethod
    def get_service_config(cls, service_name: str):
        """Get configuration for a service"""
        return getattr(cls, service_name.upper(), None)
    
    @classmethod
    def get_endpoint_url(cls, service: str, endpoint: str, **kwargs) -> str:
        """Get full URL for a specific endpoint"""
        service_config = getattr(cls, service.upper(), None)
        if not service_config:
            raise ValueError(f"Service '{service}' not found in configuration")
        
        if endpoint not in service_config.endpoints:
            raise ValueError(f"Endpoint '{endpoint}' not found for service '{service}'")
        
        base_url = service_config.base_url
        endpoint_path = service_config.endpoints[endpoint]
        
        # Format endpoint path with any provided parameters
        if kwargs:
            endpoint_path = endpoint_path.format(**kwargs)
        
        return f"{base_url}{endpoint_path}"
    
    @classmethod
    def get_headers(cls, service: str) -> Dict[str, str]:
        """Get headers for a specific service"""
        service_config = getattr(cls, service.upper(), None)
        if not service_config:
            raise ValueError(f"Service '{service}' not found in configuration")
        
        return service_config.headers.copy()
    
    @classmethod
    def get_rate_limit(cls, service: str) -> Optional[int]:
        """Get rate limit for a specific service"""
        service_config = getattr(cls, service.upper(), None)
        if not service_config:
            return None
        
        return service_config.rate_limit
    
    @classmethod
    def get_rss_feeds(cls, service: str, category: Optional[str] = None) -> List[RSSFeed]:
        """Get RSS feeds for a specific service and category"""
        if service not in cls.RSS_FEEDS:
            return []
        
        feeds = cls.RSS_FEEDS[service]
        if category:
            feeds = [feed for feed in feeds if feed.category == category]
        
        return feeds
    
    @classmethod
    def list_available_services(cls) -> List[str]:
        """List all available services"""
        return [
            'eduskunta', 'vaalikone', 'kuntaliitto',
            'yle', 'helsingin_sanomat', 'iltalehti', 'mtv_uutiset', 'kauppalehti',
            'wikipedia'
        ]
    
    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """Validate that required API keys are present"""
        validation_results = {}
        
        # Check YLE API key
        yle_key = os.getenv('YLE_API_KEY')
        validation_results['YLE_API_KEY'] = bool(yle_key and yle_key.strip())
        
        return validation_results


