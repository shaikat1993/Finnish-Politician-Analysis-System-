"""
Politician Document Processor
Transforms politician data into LangChain documents optimized for AI processing.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PoliticianProcessor:
    """
    Processes politician data from our collectors into LangChain documents
    with rich metadata for AI analysis and semantic search.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " "]
        )
    
    def process_politicians(self, politicians_data: List[Dict], source: str) -> List[Document]:
        """
        Transform politician data into LangChain documents
        
        Args:
            politicians_data: List of politician dictionaries from collectors
            source: Source name (eduskunta, vaalikone, kuntaliitto)
            
        Returns:
            List of LangChain Document objects
        """
        documents = []
        
        for politician in politicians_data:
            try:
                # Create main politician document
                main_doc = self._create_politician_document(politician, source)
                documents.append(main_doc)
                
                # Create additional documents for specific aspects if data is rich enough
                if self._has_rich_data(politician):
                    additional_docs = self._create_detailed_documents(politician, source)
                    documents.extend(additional_docs)
                    
            except Exception as e:
                self.logger.error(f"Error processing politician {politician.get('name', 'Unknown')}: {str(e)}")
        
        self.logger.info(f"Processed {len(documents)} politician documents from {source}")
        return documents
    
    def _create_politician_document(self, politician: Dict, source: str) -> Document:
        """Create the main politician document"""
        
        # Build comprehensive content for embedding
        content_parts = []
        
        # Basic info
        name = politician.get('name', 'Unknown Politician')
        party = politician.get('party', 'Unknown Party')
        content_parts.append(f"Politician: {name}")
        content_parts.append(f"Political Party: {party}")
        
        # Position and role
        if politician.get('position'):
            content_parts.append(f"Position: {politician['position']}")
        if politician.get('role'):
            content_parts.append(f"Role: {politician['role']}")
        
        # Geographic info
        if politician.get('constituency'):
            content_parts.append(f"Constituency: {politician['constituency']}")
        if politician.get('region'):
            content_parts.append(f"Region: {politician['region']}")
        
        # Biography and background
        if politician.get('bio'):
            content_parts.append(f"Biography: {politician['bio']}")
        if politician.get('background'):
            content_parts.append(f"Background: {politician['background']}")
        
        # Political positions and policies
        if politician.get('political_positions'):
            positions = politician['political_positions']
            if isinstance(positions, list):
                content_parts.append(f"Political Positions: {', '.join(positions)}")
            else:
                content_parts.append(f"Political Positions: {positions}")
        
        # Committee memberships
        if politician.get('committees'):
            committees = politician['committees']
            if isinstance(committees, list):
                content_parts.append(f"Committee Memberships: {', '.join(committees)}")
            else:
                content_parts.append(f"Committee Memberships: {committees}")
        
        # Contact and social media
        if politician.get('email'):
            content_parts.append(f"Email: {politician['email']}")
        if politician.get('website'):
            content_parts.append(f"Website: {politician['website']}")
        
        # Join all content
        full_content = "\n".join(content_parts)
        
        # Create comprehensive metadata
        metadata = {
            'type': 'politician',
            'source': source,
            'name': name,
            'party': party,
            'politician_id': politician.get('id', f"{source}_{name.replace(' ', '_')}"),
            'position': politician.get('position'),
            'constituency': politician.get('constituency'),
            'region': politician.get('region'),
            'email': politician.get('email'),
            'website': politician.get('website'),
            'processed_at': datetime.now().isoformat(),
            'data_completeness': self._calculate_completeness(politician),
            'searchable_terms': self._extract_searchable_terms(politician)
        }
        
        return Document(
            page_content=full_content,
            metadata=metadata
        )
    
    def _has_rich_data(self, politician: Dict) -> bool:
        """Check if politician has enough data for detailed documents"""
        rich_fields = ['bio', 'political_positions', 'committees', 'voting_record']
        return sum(1 for field in rich_fields if politician.get(field)) >= 2
    
    def _create_detailed_documents(self, politician: Dict, source: str) -> List[Document]:
        """Create additional detailed documents for rich politician data"""
        documents = []
        base_name = politician.get('name', 'Unknown')
        base_id = politician.get('id', f"{source}_{base_name.replace(' ', '_')}")
        
        # Biography document
        if politician.get('bio') and len(politician['bio']) > 200:
            bio_doc = Document(
                page_content=f"Biography of {base_name}: {politician['bio']}",
                metadata={
                    'type': 'politician_biography',
                    'source': source,
                    'politician_name': base_name,
                    'politician_id': base_id,
                    'document_subtype': 'biography',
                    'processed_at': datetime.now().isoformat()
                }
            )
            documents.append(bio_doc)
        
        # Political positions document
        if politician.get('political_positions'):
            positions = politician['political_positions']
            if isinstance(positions, list):
                positions_text = ". ".join(positions)
            else:
                positions_text = str(positions)
            
            if len(positions_text) > 100:
                positions_doc = Document(
                    page_content=f"Political positions of {base_name}: {positions_text}",
                    metadata={
                        'type': 'politician_positions',
                        'source': source,
                        'politician_name': base_name,
                        'politician_id': base_id,
                        'document_subtype': 'political_positions',
                        'processed_at': datetime.now().isoformat()
                    }
                )
                documents.append(positions_doc)
        
        # Committee work document
        if politician.get('committees'):
            committees = politician['committees']
            if isinstance(committees, list):
                committees_text = ". ".join(committees)
            else:
                committees_text = str(committees)
            
            committee_doc = Document(
                page_content=f"Committee work of {base_name}: {committees_text}",
                metadata={
                    'type': 'politician_committees',
                    'source': source,
                    'politician_name': base_name,
                    'politician_id': base_id,
                    'document_subtype': 'committees',
                    'processed_at': datetime.now().isoformat()
                }
            )
            documents.append(committee_doc)
        
        return documents
    
    def _calculate_completeness(self, politician: Dict) -> float:
        """Calculate data completeness score (0-1)"""
        important_fields = [
            'name', 'party', 'position', 'constituency', 'bio', 
            'political_positions', 'committees', 'email', 'website'
        ]
        
        filled_fields = sum(1 for field in important_fields if politician.get(field))
        return round(filled_fields / len(important_fields), 2)
    
    def _extract_searchable_terms(self, politician: Dict) -> List[str]:
        """Extract key terms for enhanced searchability"""
        terms = []
        
        # Basic terms
        if politician.get('name'):
            terms.extend(politician['name'].split())
        if politician.get('party'):
            terms.append(politician['party'])
        if politician.get('position'):
            terms.append(politician['position'])
        if politician.get('constituency'):
            terms.append(politician['constituency'])
        
        # Committee terms
        if politician.get('committees'):
            committees = politician['committees']
            if isinstance(committees, list):
                terms.extend(committees)
            else:
                terms.append(str(committees))
        
        # Remove duplicates and empty terms
        terms = list(set(term.strip() for term in terms if term and term.strip()))
        
        return terms[:20]  # Limit to top 20 terms
