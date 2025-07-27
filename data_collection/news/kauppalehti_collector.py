import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import logging
from bs4 import BeautifulSoup
import feedparser

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_collector import NewsCollector
from config.api_endpoints import APIConfig

@dataclass
class KauppalehtiArticle:
    article_id: str
    title: str
    url: str
    published_date: datetime
    author: Optional[str]
    content: str
    summary: str
    category: str
    tags: List[str]
    image_url: Optional[str] = None

class KauppalehtiCollector(NewsCollector):
    """Collector for Kauppalehti business news articles"""
    

    
    def __init__(self):
        super().__init__('kauppalehti')
        # Use centralized RSS feeds configuration
        self.rss_feeds = {feed.category: feed.url for feed in APIConfig.RSS_FEEDS['kauppalehti']}

    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        limit = kwargs.get('limit', 20)
        return self.get_latest_articles(limit)

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_articles_from_rss(self, category: str = 'politiikka', limit: int = 50) -> List[KauppalehtiArticle]:
        """Get articles from RSS feeds"""
        try:
            if category not in self.rss_feeds:
                self.logger.warning(f"Category {category} not found. Available: {list(self.rss_feeds.keys())}")
                category = 'politiikka'
            
            feed_url = self.rss_feeds[category]
            self.logger.info(f"Fetching RSS feed: {feed_url}")
            
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries[:limit]:
                article = self._parse_rss_entry(entry, category)
                if article:
                    articles.append(article)
            
            self.logger.info(f"Successfully fetched {len(articles)} articles from RSS")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching RSS articles: {str(e)}")
            return []

    def search_articles(self, query: str, limit: int = 20) -> List[KauppalehtiArticle]:
        """Search for articles using Kauppalehti search"""
        try:
            search_url = f"{self.get_base_url()}/haku"
            params = {'q': query}
            
            self.logger.info(f"Searching Kauppalehti for: {query}")
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Find article elements in search results
            article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(
                term in x.lower() for term in ['article', 'story', 'news', 'item', 'result']
            ))
            
            for element in article_elements[:limit]:
                article = self._parse_search_result(element)
                if article:
                    articles.append(article)
            
            self.logger.info(f"Found {len(articles)} articles in search results")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error searching articles: {str(e)}")
            return []

    def get_politician_articles(self, politician_name: str, limit: int = 20) -> List[KauppalehtiArticle]:
        """Get articles mentioning a specific politician"""
        return self.search_articles(politician_name, limit)

    def _parse_rss_entry(self, entry, category: str) -> Optional[KauppalehtiArticle]:
        """Parse RSS feed entry"""
        try:
            # Parse published date
            published_date = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from time import mktime
                published_date = datetime.fromtimestamp(mktime(entry.published_parsed))
            
            # Extract content
            content = ''
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if isinstance(entry.content, list) else entry.content
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Clean HTML from content
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.get_text().strip()
            
            article = KauppalehtiArticle(
                article_id=str(hash(entry.link)),
                title=entry.title,
                url=entry.link,
                published_date=published_date,
                author=getattr(entry, 'author', None),
                content=content,
                summary=getattr(entry, 'summary', content[:200] + '...' if len(content) > 200 else content),
                category=category,
                tags=[]
            )
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {str(e)}")
            return None

    def _parse_search_result(self, element) -> Optional[KauppalehtiArticle]:
        """Parse search result element"""
        try:
            # Find title and URL
            title_elem = element.find(['h1', 'h2', 'h3', 'a'])
            if not title_elem:
                return None
            
            title = title_elem.get_text().strip()
            url = title_elem.get('href', '')
            
            # Make URL absolute
            if url.startswith('/'):
                url = self.get_base_url() + url
            
            # Find content/summary
            content_elem = element.find(['p', 'div'], class_=lambda x: x and any(
                term in x.lower() for term in ['summary', 'excerpt', 'content', 'description']
            ))
            content = content_elem.get_text().strip() if content_elem else ''
            
            article = KauppalehtiArticle(
                article_id=str(hash(url)),
                title=title,
                url=url,
                published_date=datetime.now(),
                author=None,
                content=content,
                summary=content[:200] + '...' if len(content) > 200 else content,
                category='search_result',
                tags=[]
            )
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error parsing search result: {str(e)}")
            return None

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
    collector = KauppalehtiCollector()
    
    # Get political articles from RSS
    articles = collector.get_articles_from_rss('politiikka', limit=10)
    print(f"Found {len(articles)} political articles")
    
    # Save data
    collector.save_data(articles, "kauppalehti_articles.json")
    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        # TODO: Implement main data collection logic
        return []

