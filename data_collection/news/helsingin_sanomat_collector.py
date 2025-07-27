import requests
import json
from typing import Dict, List, Any, Optional
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

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_collector import NewsCollector

@dataclass
class HSArticle:
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

class HelsingingSanomatCollector(NewsCollector):
    """Collector for Helsingin Sanomat news articles using centralized configuration"""
    
    def __init__(self):
        super().__init__('helsingin_sanomat')
        # Use centralized RSS feeds configuration
        self.rss_feeds = {feed.category: feed.url for feed in APIConfig.RSS_FEEDS['helsingin_sanomat']}

    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        limit = kwargs.get('limit', 20)
        return self.get_latest_articles(limit)

    def get_articles_from_rss(self, category: str = 'politiikka', limit: int = 50) -> List[HSArticle]:
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

    def search_articles(self, query: str, limit: int = 20) -> List[HSArticle]:
        """Search for articles using HS.fi search"""
        try:
            search_url = f"{self.get_base_url()}/haku"
            params = {
                'query': query,
                'size': limit
            }
            
            self.logger.info(f"Searching HS.fi for: {query}")
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Find article elements in search results
            article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(
                term in x.lower() for term in ['article', 'story', 'news-item']
            ))
            
            for element in article_elements:
                article = self._parse_search_result(element)
                if article:
                    articles.append(article)
            
            self.logger.info(f"Found {len(articles)} articles in search results")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error searching articles: {str(e)}")
            return []

    def get_politician_articles(self, politician_name: str, limit: int = 20) -> List[HSArticle]:
        """Get articles mentioning a specific politician"""
        return self.search_articles(politician_name, limit)

    def _parse_rss_entry(self, entry, category: str) -> Optional[HSArticle]:
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
            
            article = HSArticle(
                article_id=str(hash(entry.link)),
                title=entry.title,
                url=entry.link,
                published_date=published_date,
                author=getattr(entry, 'author', None),
                content=content,
                summary=getattr(entry, 'summary', content[:200] + '...' if len(content) > 200 else content),
                category=category,
                tags=getattr(entry, 'tags', [])
            )
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {str(e)}")
            return None

    def _parse_search_result(self, element) -> Optional[HSArticle]:
        """Parse search result element"""
        try:
            # Find title
            title_elem = element.find(['h1', 'h2', 'h3', 'a'], class_=lambda x: x and 'title' in x.lower())
            if not title_elem:
                title_elem = element.find('a')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text().strip()
            url = title_elem.get('href', '')
            
            # Make URL absolute
            if url.startswith('/'):
                url = self.get_base_url() + url
            
            # Find summary/content
            content_elem = element.find(['p', 'div'], class_=lambda x: x and any(
                term in x.lower() for term in ['summary', 'excerpt', 'content', 'description']
            ))
            content = content_elem.get_text().strip() if content_elem else ''
            
            # Find author
            author_elem = element.find(['span', 'div'], class_=lambda x: x and 'author' in x.lower())
            author = author_elem.get_text().strip() if author_elem else None
            
            # Find date
            date_elem = element.find(['time', 'span'], class_=lambda x: x and 'date' in x.lower())
            published_date = datetime.now()
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text()
                try:
                    published_date = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
                except:
                    pass
            
            article = HSArticle(
                article_id=str(hash(url)),
                title=title,
                url=url,
                published_date=published_date,
                author=author,
                content=content,
                summary=content[:200] + '...' if len(content) > 200 else content,
                category='search_result',
                tags=[]
            )
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error parsing search result: {str(e)}")
            return None

    def get_full_article_content(self, article_url: str) -> Optional[str]:
        """Get full article content from article URL"""
        try:
            response = self.session.get(article_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article content
            content_selectors = APIConfig.CONTENT_SELECTORS['helsingin_sanomat']
            
            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove ads, related articles, etc.
                    for unwanted in content_elem.find_all(['aside', 'div'], class_=lambda x: x and any(
                        term in x.lower() for term in ['ad', 'advertisement', 'related', 'sidebar']
                    )):
                        unwanted.decompose()
                    
                    content = content_elem.get_text().strip()
                    break
            
            return content if content else None
            
        except Exception as e:
            self.logger.error(f"Error getting full article content from {article_url}: {str(e)}")
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
    collector = HelsingingSanomatCollector()
    
    # Get political articles from RSS
    articles = collector.get_articles_from_rss('politiikka', limit=10)
    print(f"Found {len(articles)} political articles")
    
    # Search for specific politician
    politician_articles = collector.search_articles('Sanna Marin', limit=5)
    print(f"Found {len(politician_articles)} articles about Sanna Marin")
    
    # Save data
    collector.save_data(articles, "hs_political_articles.json")
    def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Implement abstract method from base class"""
        # TODO: Implement main data collection logic
        return []

