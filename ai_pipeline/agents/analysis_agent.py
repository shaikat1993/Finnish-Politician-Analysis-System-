"""
AnalysisAgent - Specialized LangChain Agent for Content Analysis
Handles all AI-powered analysis of political content and data.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..tools.coordination_tools import AnalysisTool
from ..memory.shared_memory import SharedAgentMemory

class AnalysisAgent:
    """
    Specialized LangChain agent for content analysis operations.
    
    Responsibilities:
    - Analyze politician profiles and voting patterns
    - Analyze news articles for political sentiment and topics
    - Extract key insights and trends from political data
    - Generate summaries and reports
    - Perform comparative analysis between politicians and parties
    """
    
    def __init__(self, shared_memory: SharedAgentMemory, openai_api_key: str = None):
        self.agent_id = "analysis_agent"
        self.shared_memory = shared_memory
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,  # Slightly higher for creative analysis
            openai_api_key=openai_api_key
        )
        
        # Initialize tools
        self.tools = [AnalysisTool()]
        
        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            ),
            verbose=True,
            max_iterations=5
        )
        
        self.logger.info(f"AnalysisAgent initialized with {len(self.tools)} tools")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the analysis agent"""
        return """You are a specialized Analysis Agent for the Finnish Politician Analysis System.

Your primary responsibilities:
1. Analyze politician profiles, voting records, and political positions
2. Analyze news articles for sentiment, topics, and political implications
3. Extract key insights and trends from political data
4. Generate comprehensive summaries and reports
5. Perform comparative analysis between politicians, parties, and policies

Key principles:
- Provide objective, fact-based analysis
- Identify patterns and trends in political data
- Generate actionable insights for users
- Maintain political neutrality and avoid bias
- Support conclusions with evidence from the data

Analysis capabilities:
- Sentiment analysis of political content
- Topic modeling and trend identification
- Voting pattern analysis
- Political position mapping
- Coalition and alliance detection
- Media coverage analysis
- Public opinion trend analysis

When performing analysis:
- Use the AnalysisTool for all analysis operations
- Provide detailed explanations of your findings
- Include confidence scores where appropriate
- Cite specific data sources and evidence
- Store results in shared memory for other agents

You work as part of a multi-agent system. Your analysis results help other agents make informed decisions."""

    async def analyze_politicians(self, politician_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Analyze politician profiles and voting patterns
        
        Args:
            politician_data: List of politician data to analyze
            
        Returns:
            Analysis results with insights and patterns
        """
        try:
            self.logger.info("Starting politician analysis")
            
            # Get data from shared memory if not provided
            if not politician_data:
                memories = await self.shared_memory.get_memories(
                    memory_type="collection_result",
                    agent_id="data_collection_agent"
                )
                politician_data = [m.content for m in memories if "politician" in m.content.get("operation", "")]
            
            # Execute analysis using agent
            result = await self.executor.ainvoke({
                "input": f"Analyze politician data: {len(politician_data)} politicians. Focus on voting patterns, political positions, and key characteristics."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_analysis",
                    "data_count": len(politician_data) if politician_data else 0,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="analysis_result"
            )
            
            self.logger.info("Politician analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in politician analysis: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_analysis",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    async def analyze_news(self, news_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Analyze news articles for political sentiment and topics
        
        Args:
            news_data: List of news articles to analyze
            
        Returns:
            Analysis results with sentiment and topic insights
        """
        try:
            self.logger.info("Starting news analysis")
            
            # Get data from shared memory if not provided
            if not news_data:
                memories = await self.shared_memory.get_memories(
                    memory_type="collection_result",
                    agent_id="data_collection_agent"
                )
                news_data = [m.content for m in memories if "news" in m.content.get("operation", "")]
            
            # Execute analysis using agent
            result = await self.executor.ainvoke({
                "input": f"Analyze news articles: {len(news_data)} articles. Focus on political sentiment, key topics, and media coverage patterns."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "news_analysis",
                    "data_count": len(news_data) if news_data else 0,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="analysis_result"
            )
            
            self.logger.info("News analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in news analysis: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "news_analysis",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    async def generate_insights(self, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate comprehensive insights from all available analysis
        
        Args:
            analysis_type: Type of insights to generate
            
        Returns:
            Generated insights and recommendations
        """
        try:
            self.logger.info(f"Generating {analysis_type} insights")
            
            # Get all analysis results from shared memory
            analysis_memories = await self.shared_memory.get_memories(
                memory_type="analysis_result",
                agent_id=self.agent_id
            )
            
            # Execute insight generation using agent
            result = await self.executor.ainvoke({
                "input": f"Generate {analysis_type} insights from {len(analysis_memories)} analysis results. Identify key trends, patterns, and actionable recommendations."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "insight_generation",
                    "analysis_type": analysis_type,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="insight_result"
            )
            
            self.logger.info("Insight generation completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in insight generation: {str(e)}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "AnalysisAgent",
            "capabilities": [
                "politician_profile_analysis",
                "voting_pattern_analysis",
                "news_sentiment_analysis",
                "topic_modeling",
                "trend_identification",
                "comparative_analysis",
                "insight_generation"
            ],
            "tools": [tool.name for tool in self.tools],
            "status": "active"
        }
