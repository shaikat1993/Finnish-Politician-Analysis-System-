import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import quote

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_collector import NewsCollector
from config.api_endpoints import APIConfig

from base_collector import NewsCollector
from config.api_endpoints import APIConfig

@dataclass
class NewsArticle:
    id: str
    title: str
    url: str
    published_date: datetime
    modified_date: datetime
    authors: List[str]
    keywords: List[str]
    content: str
    media: List[str]
    language: str

@dataclass
class SearchParams:
    query: str
    language: str = "fi"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 100
    offset: int = 0

class YleNewsCollector(NewsCollector):
    """YLE News Collector using centralized configuration"""
    
    def __init__(self, app_id: str = None, app_key: str = None):
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Use provided credentials or load from environment
        # Use user-provided Yle API keys directly for now
        self.app_id = "1505ae5c88646c2dc2395d482b82a0d9"
        self.app_key = "b350a8b"
        
        if not self.app_id or not self.app_key:
            raise ValueError("YLE API credentials (app_id and app_key) are required")
            
        super().__init__('yle')

    def make_request(self, endpoint: str, params: Dict = None, **kwargs):
        """Override base make_request to add YLE API credentials"""
        if params is None:
            params = {}
        
        # Add YLE API credentials to all requests
        params['app_id'] = self.app_id
        params['app_key'] = self.app_key
        
        return super().make_request(endpoint, params=params, **kwargs)

    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        query = kwargs.get('query', 'politiikka')
        limit = kwargs.get('limit', 50)
        return self.search_articles(query, limit)
    
    def test_connection(self) -> bool:
        """Test YLE API connection"""
        try:
            response = self.make_request('articles', params={'limit': 1})
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"YLE connection test failed: {str(e)}")
            return False

    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for news articles based on query"""
        query_params = {
            "q": query,
            "language": "fi",
            "limit": limit,
            "offset": 0
        }
        
        try:
            response = self.make_request('articles', params=query_params)
            data = response.json()
            articles = []
            
            for item in data.get("data", []):
                article = self._parse_article(item)
                if article:
                    articles.append(article)
            
            self.logger.info(f"Successfully fetched {len(articles)} articles from YLE")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error searching YLE articles: {str(e)}")
            return []
    
    def search_articles_advanced(self, params: SearchParams) -> List[NewsArticle]:
        """Advanced search with SearchParams object (backward compatibility)"""
        query_params = {
            "q": params.query,
            "language": params.language,
            "limit": params.limit,
            "offset": params.offset
        }
        
        if params.start_date:
            query_params["starttime"] = params.start_date
        if params.end_date:
            query_params["endtime"] = params.end_date
        
        try:
            response = self.make_request('articles', params=query_params)
            data = response.json()
            articles = []
            
            for item in data.get("data", []):
                article = self._parse_article_to_dataclass(item)
                if article:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error in advanced search: {str(e)}")
            return []

    def get_politician_articles(self, politician_name: str, start_date: str = None, end_date: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get articles mentioning a specific politician"""
        query_params = {
            "q": politician_name,
            "language": "fi",
            "limit": limit
        }
        
        if start_date:
            query_params["starttime"] = start_date
        if end_date:
            query_params["endtime"] = end_date
        
        try:
            # Use Yle programs/items endpoint for news search
            response = self.make_request('contents', params=query_params)
            data = response.json()
            articles = []
            
            for item in data.get("data", []):
                # Compose article dict from Yle item structure
                title = item.get('title', {}).get('fi') or item.get('title', '')
                url = f"https://areena.yle.fi/{item.get('id', '')}" if item.get('id') else ''
                published = None
                if item.get('publicationEvent') and len(item['publicationEvent']) > 0:
                    published = item['publicationEvent'][0].get('startTime')
                article = {
                    'title': title,
                    'url': url,
                    'published_date': published,
                    'source': 'yle',
                    'raw': item
                }
                if title and url:
                    articles.append(article)
            if not articles:
                self.logger.warning(f"No articles found, raw Yle response: {data}")
            self.logger.info(f"Found {len(articles)} articles about {politician_name}")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching politician articles: {str(e)}")
            return []
    
    def get_politician_articles_legacy(self, politician_name: str, start_date: str, end_date: str) -> List[NewsArticle]:
        """Legacy method for backward compatibility"""
        search_params = SearchParams(
            query=politician_name,
            language="fi",
            start_date=start_date,
            end_date=end_date,
            limit=100
        )
        return self.search_articles_advanced(search_params)

    def save_to_json(self, data: List[Dict], filename: str):
        """Save collected news articles to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _parse_article(self, item: Dict) -> Optional[Dict[str, Any]]:
        """Parse article data from YLE API response to dictionary"""
        try:
            # Parse publication date
            published_date = datetime.now()
            if "datePublished" in item:
                published_date = datetime.fromisoformat(item["datePublished"].replace('Z', '+00:00'))
            elif "published" in item:
                published_date = datetime.fromisoformat(item["published"].replace('Z', '+00:00'))
            
            # Handle different response formats
            title = ""
            if "headline" in item:
                title = item["headline"].get("full", "") if isinstance(item["headline"], dict) else str(item["headline"])
            elif "title" in item:
                title = item["title"].get("fi", "") if isinstance(item["title"], dict) else str(item["title"])
            
            url = ""
            if "url" in item:
                url = item["url"].get("full", "") if isinstance(item["url"], dict) else str(item["url"])
            
            content = ""
            if "content" in item:
                content = item["content"].get("full", "") if isinstance(item["content"], dict) else str(item["content"])
            
            return {
                'article_id': str(item.get("id", "")),
                'title': title,
                'url': url,
                'published_date': published_date.isoformat(),
                'modified_date': item.get("dateContentModified", item.get("modified", "")),
                'authors': [author.get("name", "") for author in item.get("author", [])] or [str(a) for a in item.get("authors", [])],
                'keywords': [tag.get("title", {}).get("fi", "") for tag in item.get("subject", [])] or item.get("keywords", []),
                'content': content,
                'media': [media.get("url", {}).get("full", "") for media in item.get("media", [])] or [str(m) for m in item.get("media", [])],
                'language': item.get("language", ["fi"])[0] if isinstance(item.get("language"), list) else item.get("language", "fi"),
                'source': 'yle'
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing YLE article: {str(e)}")
            return None

    def _parse_article_to_dataclass(self, item: Dict) -> Optional[NewsArticle]:
        """Parse article data from YLE API response to dataclass (backward compatibility)"""
        try:
            # Parse publication date
            published_date = datetime.now()
            if "datePublished" in item:
                published_date = datetime.fromisoformat(item["datePublished"].replace('Z', '+00:00'))
            elif "published" in item:
                published_date = datetime.fromisoformat(item["published"].replace('Z', '+00:00'))
            
            # Handle different response formats
            title = ""
            if "headline" in item:
                title = item["headline"].get("full", "") if isinstance(item["headline"], dict) else str(item["headline"])
            elif "title" in item:
                title = item["title"].get("fi", "") if isinstance(item["title"], dict) else str(item["title"])
            
            url = ""
            if "url" in item:
                url = item["url"].get("full", "") if isinstance(item["url"], dict) else str(item["url"])
            
            content = ""
            if "content" in item:
                content = item["content"].get("full", "") if isinstance(item["content"], dict) else str(item["content"])
            
            return NewsArticle(
                id=str(item.get("id", "")),
                title=title,
                url=url,
                published_date=published_date,
                modified_date=datetime.fromisoformat(item.get("dateContentModified", item.get("modified", ""))),
                authors=[author.get("name", "") for author in item.get("author", [])] or [str(a) for a in item.get("authors", [])],
                keywords=[tag.get("title", {}).get("fi", "") for tag in item.get("subject", [])] or item.get("keywords", []),
                content=content,
                media=[media.get("url", {}).get("full", "") for media in item.get("media", [])] or [str(m) for m in item.get("media", [])],
                language=item.get("language", ["fi"])[0] if isinstance(item.get("language"), list) else item.get("language", "fi")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing YLE article to dataclass: {str(e)}")
            return None

if __name__ == "__main__":
    # Example usage
    api_key = "your_yle_api_key"  # Replace with actual API key
    collector = YleNewsCollector(api_key)
    
    try:
        # Get news articles about a politician
        politician_name = "Sanna Marin"
        start_date = "2024-01-01"
        end_date = "2024-12-31"
        
        articles = collector.get_politician_articles(
            politician_name=politician_name,
            start_date=start_date,
            end_date=end_date
        )
        
        # Save articles to file
        collector.save_to_json(articles, "news_articles.json")
        
        print(f"Collected {len(articles)} articles about {politician_name}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
