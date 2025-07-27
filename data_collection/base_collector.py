"""
Base Collector Class
Provides common functionality for all data collectors using centralized API configuration.
"""

import time
import logging
import requests
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import json

from config.api_endpoints import APIConfig

class BaseCollector(ABC):
    """Base class for all data collectors with centralized configuration"""
    
    def __init__(self, service_name: str):
        """
        Initialize base collector
        
        Args:
            service_name: Name of the service (must match APIConfig service names)
        """
        self.service_name = service_name.lower()
        self.setup_logging()
        self.setup_session()
        self._last_request_time = 0
        
        # Validate service exists in configuration
        if self.service_name not in APIConfig.list_available_services():
            raise ValueError(f"Service '{service_name}' not found in API configuration")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    def setup_session(self):
        """Setup HTTP session with proper headers"""
        self.session = requests.Session()
        headers = APIConfig.get_headers(self.service_name)
        self.session.headers.update(headers)
    
    def get_endpoint_url(self, endpoint: str, **kwargs) -> str:
        """Get full URL for an endpoint"""
        return APIConfig.get_endpoint_url(self.service_name, endpoint, **kwargs)
    
    def make_request(self, endpoint: str, params: Optional[Dict] = None, **url_kwargs) -> requests.Response:
        """
        Make HTTP request with rate limiting and error handling
        
        Args:
            endpoint: Endpoint name from configuration
            params: Query parameters
            **url_kwargs: Parameters for URL formatting
        
        Returns:
            requests.Response object
        """
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Get URL
        url = self.get_endpoint_url(endpoint, **url_kwargs)
        
        try:
            self.logger.debug(f"Making request to: {url}")
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            
            self._last_request_time = time.time()
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            raise
    
    def _apply_rate_limit(self):
        """Apply rate limiting based on service configuration"""
        rate_limit = APIConfig.get_rate_limit(self.service_name)
        if not rate_limit:
            return
        
        # Calculate minimum time between requests (60 seconds / rate_limit)
        min_interval = 60.0 / rate_limit
        
        # Wait if necessary
        time_since_last = time.time() - self._last_request_time
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
    
    def get_rss_feeds(self, category: Optional[str] = None) -> List:
        """Get RSS feeds for this service"""
        return APIConfig.get_rss_feeds(self.service_name, category)
    
    def save_data(self, data: List, filename: str):
        """Save data to JSON file"""
        try:
            # Convert dataclass objects to dictionaries if needed
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
            raise
    
    @abstractmethod
    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Abstract method that each collector must implement
        
        Returns:
            List of collected data items
        """
        pass
    
    def test_connection(self) -> bool:
        """Test connection to the service"""
        try:
            # Try to make a simple request to test connectivity
            # This should be overridden by subclasses for service-specific testing
            response = self.session.get(APIConfig.get_endpoint_url(self.service_name, list(APIConfig.get_headers(self.service_name).keys())[0]))
            return response.status_code < 400
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

class NewsCollector(BaseCollector):
    """Base class for news collectors with RSS feed support"""
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
        
    def get_articles_from_rss(self, category: str = 'politiikka', limit: int = 50) -> List[Dict[str, Any]]:
        """Get articles from RSS feeds"""
        try:
            import feedparser
            
            feeds = self.get_rss_feeds(category)
            if not feeds:
                self.logger.warning(f"No RSS feeds found for category '{category}'")
                return []
            
            all_articles = []
            
            for feed in feeds:
                try:
                    self.logger.info(f"Fetching RSS feed: {feed.name}")
                    parsed_feed = feedparser.parse(feed.url)
                    
                    for entry in parsed_feed.entries[:limit]:
                        article = self._parse_rss_entry(entry, category)
                        if article:
                            all_articles.append(article)
                            
                except Exception as e:
                    self.logger.error(f"Error processing RSS feed {feed.name}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully fetched {len(all_articles)} articles from RSS")
            return all_articles
            
        except ImportError:
            self.logger.error("feedparser library not installed. Install with: pip install feedparser")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching RSS articles: {str(e)}")
            return []
    
    def _parse_rss_entry(self, entry, category: str) -> Optional[Dict[str, Any]]:
        """Parse RSS feed entry - should be overridden by subclasses"""
        try:
            # Basic parsing - subclasses should override for service-specific parsing
            published_date = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from time import mktime
                published_date = datetime.fromtimestamp(mktime(entry.published_parsed))
            
            return {
                'article_id': str(hash(entry.link)),
                'title': entry.title,
                'url': entry.link,
                'published_date': published_date.isoformat(),
                'content': getattr(entry, 'description', ''),
                'category': category,
                'source': self.service_name
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {str(e)}")
            return None
    
    @abstractmethod
    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for articles - must be implemented by subclasses"""
        pass

class PoliticianCollector(BaseCollector):
    """Base class for politician data collectors"""
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
    
    @abstractmethod
    def get_politicians(self, **kwargs) -> List[Dict[str, Any]]:
        """Get politician data - must be implemented by subclasses"""
        pass
