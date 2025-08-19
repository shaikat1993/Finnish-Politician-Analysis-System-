import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import logging
import time
import random

class YleWebScraperCollector:
    """
    Collector for scraping news articles from yle.fi/uutiset (Yle News front page).
    Returns a list of article dicts with title, url, summary, published_date (if available).
    """
    def __init__(self):
        self.base_url = "https://yle.fi"
        self.news_section = "/uutiset"
        self.logger = logging.getLogger("YleWebScraperCollector")
        self.timeout = 10  # Default timeout in seconds
        self.max_retries = 3

    def _make_request_with_retry(self, url: str, headers: Dict[str, str]) -> requests.Response:
        """Make HTTP request with exponential backoff retry logic"""
        retries = 0
        while retries <= self.max_retries:
            try:
                self.logger.debug(f"Making request to {url}, attempt {retries+1}/{self.max_retries+1}")
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except (requests.RequestException, requests.Timeout) as e:
                retries += 1
                if retries > self.max_retries:
                    self.logger.error(f"Failed after {self.max_retries} retries: {e}")
                    raise
                wait_time = (2 ** retries) + random.uniform(0, 1)  # Exponential backoff with jitter
                self.logger.warning(f"Request failed: {e}. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)

    def get_politician_articles(self, politician_name: str, start_date: str = None, end_date: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scrapes the Yle news section for articles mentioning the politician by name.
        """
        try:
            # Use Yle's search page to find all articles mentioning the politician
            # Use Google site search as a fallback
            query = f"site:yle.fi {politician_name}"
            google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
            start_time = time.time()
            try:
                resp = self._make_request_with_retry(google_url, headers)
                soup = BeautifulSoup(resp.text, "html.parser")
            except Exception as e:
                self.logger.error(f"Failed to fetch Google search results: {e}")
                return []
            
            self.logger.info(f"Google search completed in {time.time() - start_time:.2f}s")
            articles = []

            # Parse Google search results for Yle news articles
            for g in soup.select('div.g'):
                a = g.find('a', href=True)
                if not a:
                    continue
                url = a['href']
                # Only include Yle news/article URLs
                if not (url.startswith('https://yle.fi/uutiset/') or url.startswith('https://yle.fi/a/')):
                    continue
                title = a.get_text(strip=True)
                if not title:
                    continue
                article = {
                    "title": title,
                    "url": url,
                    "source": "yle",
                }
                # Optionally, fetch article page for summary/date
                try:
                    art_start_time = time.time()
                    art_resp = self._make_request_with_retry(url, headers)
                    art_soup = BeautifulSoup(art_resp.content, "html.parser")
                    # Try to get summary/lead
                    summary = art_soup.find("meta", attrs={"name": "description"})
                    if summary:
                        article["summary"] = summary["content"]
                    # Try to get published date
                    pub_time = art_soup.find("meta", attrs={"property": "article:published_time"})
                    if pub_time:
                        article["published_date"] = pub_time["content"]
                    self.logger.debug(f"Article details fetched in {time.time() - art_start_time:.2f}s")
                except Exception as e:
                    self.logger.warning(f"Could not fetch article details: {e}")
                articles.append(article)
                if len(articles) >= limit:
                    break
            self.logger.info(f"Found {len(articles)} articles about {politician_name} using Google site search")
            return articles

        except Exception as e:
            self.logger.error(f"Error scraping Yle.fi: {e}")
            return []
