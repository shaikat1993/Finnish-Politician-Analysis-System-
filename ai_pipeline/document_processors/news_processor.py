"""
News Document Processor
Transforms news article data into LangChain documents optimized for AI processing.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

class NewsProcessor:
    """
    Processes news article data from our collectors into LangChain documents
    with rich metadata for AI analysis and semantic search.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "]
        )
    
    def process_news_articles(self, articles_data: List[Dict], source: str) -> List[Document]:
        """
        Transform news article data into LangChain documents
        
        Args:
            articles_data: List of article dictionaries from collectors
            source: Source name (yle, helsingin_sanomat, iltalehti, etc.)
            
        Returns:
            List of LangChain Document objects
        """
        documents = []
        
        for article in articles_data:
            try:
                # Create main article document
                main_doc = self._create_article_document(article, source)
                documents.append(main_doc)
                
                # Create chunked documents for long articles
                if self._is_long_article(article):
                    chunked_docs = self._create_chunked_documents(article, source)
                    documents.extend(chunked_docs)
                    
            except Exception as e:
                self.logger.error(f"Error processing article {article.get('title', 'Unknown')}: {str(e)}")
        
        self.logger.info(f"Processed {len(documents)} news documents from {source}")
        return documents
    
    def _create_article_document(self, article: Dict, source: str) -> Document:
        """Create the main news article document"""
        
        # Build comprehensive content for embedding
        content_parts = []
        
        # Title and metadata
        title = article.get('title', 'Untitled Article')
        content_parts.append(f"News Article: {title}")
        
        # Author and publication info
        if article.get('author'):
            content_parts.append(f"Author: {article['author']}")
        if article.get('published_date'):
            content_parts.append(f"Published: {article['published_date']}")
        
        # Summary/lead
        if article.get('summary'):
            content_parts.append(f"Summary: {article['summary']}")
        elif article.get('lead'):
            content_parts.append(f"Lead: {article['lead']}")
        
        # Main content
        content = article.get('content', article.get('description', ''))
        if content:
            # Clean and format content
            cleaned_content = self._clean_article_content(content)
            content_parts.append(f"Content: {cleaned_content}")
        
        # Tags and categories
        if article.get('tags'):
            tags = article['tags']
            if isinstance(tags, list):
                content_parts.append(f"Tags: {', '.join(tags)}")
            else:
                content_parts.append(f"Tags: {tags}")
        
        if article.get('category'):
            content_parts.append(f"Category: {article['category']}")
        
        # Political relevance indicators
        political_keywords = self._extract_political_keywords(article)
        if political_keywords:
            content_parts.append(f"Political Keywords: {', '.join(political_keywords)}")
        
        # Join all content
        full_content = "\n".join(content_parts)
        
        # Create comprehensive metadata
        metadata = {
            'type': 'news_article',
            'source': source,
            'title': title,
            'author': article.get('author'),
            'published_date': article.get('published_date'),
            'url': article.get('url'),
            'article_id': article.get('id', f"{source}_{self._generate_id(title)}"),
            'category': article.get('category'),
            'tags': article.get('tags', []),
            'word_count': len(full_content.split()),
            'political_relevance': self._calculate_political_relevance(article),
            'sentiment': self._analyze_basic_sentiment(article),
            'mentioned_politicians': self._extract_politician_mentions(article),
            'processed_at': datetime.now().isoformat(),
            'searchable_terms': self._extract_searchable_terms(article)
        }
        
        return Document(
            page_content=full_content,
            metadata=metadata
        )
    
    def _is_long_article(self, article: Dict) -> bool:
        """Check if article is long enough to benefit from chunking"""
        content = article.get('content', article.get('description', ''))
        return len(content.split()) > 800
    
    def _create_chunked_documents(self, article: Dict, source: str) -> List[Document]:
        """Create chunked documents for long articles"""
        documents = []
        
        content = article.get('content', article.get('description', ''))
        title = article.get('title', 'Untitled Article')
        base_id = article.get('id', f"{source}_{self._generate_id(title)}")
        
        # Split content into chunks
        chunks = self.text_splitter.split_text(content)
        
        for i, chunk in enumerate(chunks):
            chunk_doc = Document(
                page_content=f"Article: {title}\nChunk {i+1}: {chunk}",
                metadata={
                    'type': 'news_article_chunk',
                    'source': source,
                    'parent_article_id': base_id,
                    'title': title,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'author': article.get('author'),
                    'published_date': article.get('published_date'),
                    'url': article.get('url'),
                    'processed_at': datetime.now().isoformat()
                }
            )
            documents.append(chunk_doc)
        
        return documents
    
    def _clean_article_content(self, content: str) -> str:
        """Clean and format article content"""
        if not content:
            return ""
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common news artifacts
        content = re.sub(r'\(Reuters\)|\(AP\)|\(STT\)', '', content)
        
        # Limit length for embedding optimization
        words = content.split()
        if len(words) > 2000:
            content = ' '.join(words[:2000]) + "..."
        
        return content.strip()
    
    def _extract_political_keywords(self, article: Dict) -> List[str]:
        """Extract political keywords from article"""
        political_terms = [
            'eduskunta', 'kansanedustaja', 'ministeri', 'pääministeri',
            'hallitus', 'oppositio', 'puolue', 'vaalit', 'äänestys',
            'lakiesitys', 'budjetti', 'politiikka', 'demokratia',
            'sdp', 'kokoomus', 'keskusta', 'perussuomalaiset', 'vihreät',
            'vasemmistoliitto', 'rkp', 'kristillisdemokraatit'
        ]
        
        found_keywords = []
        
        # Check title and content
        text_to_check = f"{article.get('title', '')} {article.get('content', '')} {article.get('summary', '')}".lower()
        
        for term in political_terms:
            if term in text_to_check:
                found_keywords.append(term)
        
        return found_keywords[:10]  # Limit to top 10
    
    def _calculate_political_relevance(self, article: Dict) -> float:
        """Calculate political relevance score (0-1)"""
        score = 0.0
        
        # Check for political keywords
        political_keywords = self._extract_political_keywords(article)
        score += min(len(political_keywords) * 0.1, 0.5)
        
        # Check category
        if article.get('category'):
            political_categories = ['politics', 'politiikka', 'government', 'hallitus']
            if any(cat in article['category'].lower() for cat in political_categories):
                score += 0.3
        
        # Check for politician mentions
        politician_mentions = self._extract_politician_mentions(article)
        score += min(len(politician_mentions) * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _analyze_basic_sentiment(self, article: Dict) -> str:
        """Basic sentiment analysis"""
        # Simple keyword-based sentiment
        positive_words = ['hyvä', 'onnistunut', 'positiivinen', 'kehitys', 'parannus']
        negative_words = ['huono', 'epäonnistunut', 'negatiivinen', 'ongelma', 'kriisi']
        
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_politician_mentions(self, article: Dict) -> List[str]:
        """Extract mentions of politicians from article"""
        # Common Finnish politician names and titles
        politician_indicators = [
            'kansanedustaja', 'ministeri', 'pääministeri', 'puheenjohtaja',
            'marin', 'orpo', 'andersson', 'halla-aho', 'kulmuni'
        ]
        
        mentioned = []
        text = f"{article.get('title', '')} {article.get('content', '')}".lower()
        
        for indicator in politician_indicators:
            if indicator in text:
                mentioned.append(indicator)
        
        return mentioned[:5]  # Limit to top 5
    
    def _extract_searchable_terms(self, article: Dict) -> List[str]:
        """Extract key terms for enhanced searchability"""
        terms = []
        
        # Title words
        if article.get('title'):
            title_words = article['title'].split()
            terms.extend([word.strip('.,!?') for word in title_words if len(word) > 3])
        
        # Tags
        if article.get('tags'):
            tags = article['tags']
            if isinstance(tags, list):
                terms.extend(tags)
            else:
                terms.append(str(tags))
        
        # Category
        if article.get('category'):
            terms.append(article['category'])
        
        # Author
        if article.get('author'):
            terms.append(article['author'])
        
        # Political keywords
        political_keywords = self._extract_political_keywords(article)
        terms.extend(political_keywords)
        
        # Remove duplicates and empty terms
        terms = list(set(term.strip().lower() for term in terms if term and term.strip()))
        
        return terms[:25]  # Limit to top 25 terms
    
    def _generate_id(self, title: str) -> str:
        """Generate a simple ID from title"""
        return re.sub(r'[^a-zA-Z0-9]', '_', title.lower())[:50]
