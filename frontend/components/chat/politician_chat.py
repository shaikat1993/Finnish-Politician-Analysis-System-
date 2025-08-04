"""
Chat component with AI assistant for politician analysis
"""

import streamlit as st
import asyncio
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime


class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisResult(BaseModel):
    """Model for AI analysis results"""
    sector_involvement: Dict[str, float]  # Sector and percentage
    sentiment_score: float  # -1 to 1
    achievements: List[str]
    corruption_risk: float  # 0 to 1
    voting_recommendation: str
    additional_insights: List[str]


class PoliticianChat:
    """Chat component with AI assistant"""
    
    def __init__(self, api_base_url: str):
        """Initialize chat component"""
        self.api_base_url = api_base_url
        self.messages: List[ChatMessage] = []
        self.logger = logging.getLogger(__name__)
        self.selected_politician: Optional[str] = None
        
    async def _fetch_analysis(self, politician_id: str) -> AnalysisResult:
        """
        Fetch AI analysis for politician
        
        Args:
            politician_id: ID of politician to analyze
            
        Returns:
            AnalysisResult: AI analysis results
        """
        try:
            # In a real application, this would make an API call
            # For now, we'll return sample data
            return AnalysisResult(
                sector_involvement={
                    "Healthcare": 0.4,
                    "Education": 0.3,
                    "Economy": 0.2,
                    "Others": 0.1
                },
                sentiment_score=0.75,
                achievements=[
                    "Education Reform 2023",
                    "Healthcare Bill Support",
                    "Economic Policy Initiative"
                ],
                corruption_risk=0.15,
                voting_recommendation="Positive impact on healthcare and education",
                additional_insights=[
                    "Strong track record in healthcare",
                    "Active in education reform",
                    "Consistent economic policy stance"
                ]
            )
        except Exception as e:
            self.logger.error(f"Error fetching analysis: {str(e)}")
            raise
    
    def _generate_response(self, message: str) -> str:
        """
        Generate AI response to user message
        
        Args:
            message: User's message
            
        Returns:
            str: AI's response
        """
        try:
            if not self.selected_politician:
                return "Please select a politician first."
                
            # Parse message and generate response
            if "sector" in message.lower():
                return "This politician is primarily involved in Healthcare (40%), Education (30%), and Economy (20%)."
                
            elif "sentiment" in message.lower():
                return "The current sentiment about this politician is positive, with a score of 75%."
                
            elif "achievements" in message.lower():
                return "Key achievements include Education Reform 2023, Healthcare Bill Support, and Economic Policy Initiative."
                
            elif "corruption" in message.lower():
                return "The corruption risk assessment for this politician is low (15%)."
                
            elif "vote" in message.lower():
                return "Based on their track record in healthcare and education, this politician would be a good choice for voters concerned about these areas."
                
            else:
                return "I can help you with: sector involvement, sentiment analysis, achievements, corruption risk, and voting recommendations."
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I encountered an error. Please try again."
    
    def render(self):
        """Render the chat component"""
        st.title("AI Assistant")
        
        # Chat history
        for message in self.messages:
            with st.chat_message(message.role):
                st.write(message.content)
                
        # User input
        if prompt := st.chat_input("Ask about the politician..."):
            # Add user message
            user_message = ChatMessage(role="user", content=prompt)
            self.messages.append(user_message)
            
            # Generate and add AI response
            with st.chat_message("assistant"):
                response = self._generate_response(prompt)
                assistant_message = ChatMessage(role="assistant", content=response)
                self.messages.append(assistant_message)
                st.write(response)
                
        # Analysis controls
        st.subheader("Advanced Analysis")
        if self.selected_politician:
            if st.button("Show Full Analysis"):
                analysis = asyncio.run(self._fetch_analysis(self.selected_politician))
                st.json(analysis.dict())
        else:
            st.info("Please select a politician from the map to analyze.")
