"""
Enhanced Chat component with AI assistant for politician analysis
Integrates directly with AI pipeline and provides research-grade visualization
"""

import sys
import os
import requests
import streamlit as st
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import time
import asyncio

# Import research components
try:
    from frontend.components.research.ai_pipeline_service import EliteAIPipelineService
    from frontend.components.research.agent_visualizer import AgentVisualizer
    RESEARCH_COMPONENTS_AVAILABLE = True
except ImportError:
    RESEARCH_COMPONENTS_AVAILABLE = False


class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    # Enhanced fields for research mode
    reasoning: List[Any] = Field(default_factory=list)
    sources: List[Any] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    direct_access: bool = False


class EnhancedPoliticianChat:
    """
    Enhanced Chat component with AI assistant and research capabilities
    
    Features:
    - Direct integration with AI pipeline when available
    - Visualization of agent reasoning chains
    - Security metrics display
    - Source citation visualization
    - Experiment tracking
    """
    
    def __init__(self, api_base_url: str):
        """
        Initialize enhanced chat component
        
        Args:
            api_base_url: Base URL for API fallback
        """
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(__name__)
        self.selected_politician: Optional[str] = None
        
        # Initialize research components if available
        self.research_mode_available = RESEARCH_COMPONENTS_AVAILABLE
        if self.research_mode_available:
            self.pipeline_service = EliteAIPipelineService(api_base_url)
            self.visualizer = AgentVisualizer()
        
        # Initialize session state for research mode
        if "research_mode_enabled" not in st.session_state:
            st.session_state.research_mode_enabled = False
    
    def _fetch_analysis(self, politician_id: str) -> Dict[str, Any]:
        """
        Fetch AI analysis for politician using orchestrator backend via HTTP.
        
        Args:
            politician_id: Politician ID to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            self.logger.info(f"Fetching analysis for politician: {politician_id}")
            with st.spinner("Analyzing politician..."):
                try:
                    # Ensure context_ids is never empty
                    context_ids = [politician_id] if politician_id else ["general"]
                    
                    response = requests.post(
                        f"{self.api_base_url}/analysis/custom",
                        json={
                            "query": f"Full analysis for {politician_id}",
                            "context_ids": context_ids,
                            "detailed_response": True
                        },
                        timeout=15
                    )
                    self.logger.info(f"Initial API response status: {response.status_code}")
                    response.raise_for_status()
                    data = response.json()
                    
                    # If backend is async, poll status endpoint
                    if data.get("status") == "accepted" and data.get("status_url"):
                        status_url = data["status_url"]
                        self.logger.info(f"Received status URL: {status_url}")
                        start_time = time.time()
                        max_wait = 30  # seconds
                        poll_interval = 1.5
                        
                        while True:
                            try:
                                poll_url = f"{self.api_base_url}/analysis{status_url.split('/analysis')[-1]}"
                                self.logger.info(f"Polling status at: {poll_url}")
                                poll_response = requests.get(
                                    poll_url,
                                    timeout=10
                                )
                                poll_response.raise_for_status()
                                poll_data = poll_response.json()
                                
                                if poll_data.get("status") == "completed":
                                    # AI answer is ready
                                    self.logger.info("Analysis completed successfully")
                                    data = poll_data.get("result", poll_data)
                                    break
                                elif poll_data.get("status") == "failed":
                                    self.logger.error(f"Analysis failed: {poll_data.get('error', 'Unknown error')}")
                                    return {"error": f"Analysis failed: {poll_data.get('error', 'Unknown error')}"}
                                elif time.time() - start_time > max_wait:
                                    self.logger.warning("Analysis timed out")
                                    return {"error": "Analysis timed out. Please try again."}
                                
                                self.logger.info(f"Status: {poll_data.get('status')} - waiting {poll_interval}s")
                                time.sleep(poll_interval)
                            except requests.RequestException as e:
                                self.logger.error(f"Error during status polling: {str(e)}")
                                return {"error": f"Error checking analysis status: {str(e)}"}
                    
                    # Format response to match direct access format
                    return {
                        "output": data.get("output") or data.get("answer") or data.get("result", ""),
                        "reasoning": data.get("reasoning", []),
                        "sources": data.get("sources", []),
                        "metrics": {
                            "latency_ms": 0,
                            "security_score": 1.0,
                            "reasoning_steps": 0,
                            "sources_used": len(data.get("sources", [])),
                        },
                        "direct_access": False
                    }
                except requests.ConnectionError:
                    self.logger.error(f"Connection error to API at {self.api_base_url}")
                    # API service is unavailable - use fallback mode
                    return {
                        "output": f"Analysis is currently unavailable because the API service at {self.api_base_url} is not running. " +
                                f"Please ensure the API service is running to get a full analysis of {politician_id}.",
                        "reasoning": ["API service unavailable, using fallback mode"],
                        "sources": [],
                        "metrics": {
                            "latency_ms": 0,
                            "security_score": 1.0,
                            "reasoning_steps": 0,
                            "sources_used": 0,
                        },
                        "direct_access": False
                    }
                except requests.Timeout:
                    self.logger.error("API request timed out")
                    return {"error": "Analysis timed out. Please try again."}
                except requests.HTTPError as e:
                    self.logger.error(f"HTTP error: {str(e)}")
                    return {"error": f"API error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Unexpected error fetching analysis: {str(e)}")
            return {"error": str(e)}
    
    def _generate_response(self, message: str, politician: Optional[str] = None) -> Union[str, Dict[str, Any]]:
        """
        Generate response using direct access or API fallback
        
        Args:
            message: User query
            politician: Politician ID for context
            
        Returns:
            Response text or full response object in research mode
        """
        if not politician:
            return "Please select a politician first."
        
        # Use direct access if research mode is enabled and available
        if (self.research_mode_available and 
            st.session_state.research_mode_enabled and 
            self.pipeline_service.direct_mode_available):
            
            try:
                with st.spinner("Thinking with direct agent access..."):
                    result = self.pipeline_service.query_agent_sync(
                        query=message,
                        context_ids=[politician],
                        detailed=False
                    )
                return result
            except Exception as e:
                self.logger.error(f"Error in direct query: {str(e)}")
                # Fall back to API
        
        # Use API method
        try:
            with st.spinner("Thinking..."):
                try:
                    # Ensure context_ids is never empty
                    context_ids = [politician] if politician else ["general"]
                    
                    # Ensure query meets minimum length requirement (10 characters)
                    query = message
                    if len(query) < 10:
                        query = f"{query} about {politician}".ljust(10)
                    
                    response = requests.post(
                        f"{self.api_base_url}/analysis/custom",
                        json={
                            "query": query,
                            "context_ids": context_ids,
                            "detailed_response": False
                        },
                        timeout=10
                    )
                    self.logger.info(f"Initial API response status: {response.status_code}")
                    response.raise_for_status()
                    data = response.json()
                    
                    # If backend is async, poll status endpoint
                    if data.get("status") == "accepted" and data.get("status_url"):
                        status_url = data["status_url"]
                        self.logger.info(f"Received status URL: {status_url}")
                        start_time = time.time()
                        max_wait = 30  # seconds
                        poll_interval = 1.5
                        
                        while True:
                            try:
                                poll_url = f"{self.api_base_url}/analysis{status_url.split('/analysis')[-1]}"
                                self.logger.info(f"Polling status at: {poll_url}")
                                poll_response = requests.get(
                                    poll_url,
                                    timeout=10
                                )
                                poll_response.raise_for_status()
                                poll_data = poll_response.json()
                                
                                if poll_data.get("status") == "completed":
                                    # AI answer is ready
                                    self.logger.info("Analysis completed successfully")
                                    data = poll_data.get("result", poll_data)
                                    break
                                elif poll_data.get("status") == "failed":
                                    self.logger.error(f"Analysis failed: {poll_data.get('error', 'Unknown error')}")
                                    return f"[Agent Error] {poll_data.get('error', 'Unknown error')}"
                                elif time.time() - start_time > max_wait:
                                    self.logger.warning("Analysis timed out")
                                    return "Sorry, the AI took too long to respond. Please try again."
                                
                                self.logger.info(f"Status: {poll_data.get('status')} - waiting {poll_interval}s")
                                time.sleep(poll_interval)
                            except requests.RequestException as e:
                                self.logger.error(f"Error during status polling: {str(e)}")
                                return f"[Agent Error] {str(e)}"
                except requests.ConnectionError:
                    self.logger.error(f"Connection error to API at {self.api_base_url}")
                    # API service is unavailable - use fallback mode
                    return self._generate_fallback_response(message, politician)
                except requests.Timeout:
                    self.logger.error("API request timed out")
                    return "Sorry, the AI took too long to respond. Please try again."
                except requests.HTTPError as e:
                    self.logger.error(f"HTTP error: {str(e)}")
                    return f"[Agent Error] {str(e)}"
        except Exception as e:
            self.logger.error(f"Unexpected error generating response: {str(e)}")
            return f"[Agent Error] {str(e)}"
        
        # Format response to match direct access format if in research mode
        if self.research_mode_available and st.session_state.research_mode_enabled:
            return {
                "output": data.get("output") or data.get("answer") or data.get("result", ""),
                "reasoning": data.get("reasoning", []),
                "sources": data.get("sources", []),
                "metrics": {
                    "latency_ms": 0,  # Not available from API
                    "security_score": 1.0,  # Not available from API
                    "reasoning_steps": 0,  # Not available from API
                    "sources_used": len(data.get("sources", [])),
                },
                "direct_access": False
            }
        else:
            # Format as string for standard mode
            answer = data.get('output') or data.get('answer') or data.get('result') or ''
            sources = data.get('sources')
            reasoning = data.get('reasoning')
            
            output = answer
            if reasoning:
                output += f"\n\n**Reasoning:** {reasoning}"
            if sources:
                output += f"\n\n**Sources:** {sources}"
                
            return output or str(data) or "Sorry, I couldn't find an answer for that."
    
    def _generate_fallback_response(self, message: str, politician: str) -> Union[str, Dict[str, Any]]:
        """
        Generate a fallback response when API is unavailable
        
        Args:
            message: User query
            politician: Politician ID for context
            
        Returns:
            Fallback response
        """
        # Create a simple fallback response
        fallback_output = f"I'm currently operating in offline mode due to API unavailability. " \
                         f"Basic information about {politician} is available, but detailed analysis " \
                         f"requires the API service to be running.\n\n" \
                         f"Your question was: {message}\n\n" \
                         f"To get a complete answer, please ensure the API service is running at {self.api_base_url}."
        
        # If in research mode, format as a research response
        if self.research_mode_available and st.session_state.research_mode_enabled:
            return {
                "output": fallback_output,
                "reasoning": ["API service unavailable, using fallback mode"],
                "sources": [],
                "metrics": {
                    "latency_ms": 0,
                    "security_score": 1.0,
                    "reasoning_steps": 0,
                    "sources_used": 0,
                },
                "direct_access": False
            }
        else:
            return fallback_output
    
    def _generate_suggested_questions(self, politician: str) -> List[str]:
        """
        Generate suggested questions for a politician
        
        Args:
            politician: Politician name or ID
            
        Returns:
            List of suggested questions
        """
        # Basic questions that work for any politician
        basic_questions = [
            f"What is {politician}'s voting record?",
            f"What are {politician}'s main political positions?",
            f"Which committees does {politician} serve on?",
            f"What recent news mentions {politician}?",
            f"What is {politician}'s background before politics?"
        ]
        
        # Try to get politician-specific questions if we have details
        if "selected_politician_details" in st.session_state and st.session_state.selected_politician_details:
            details = st.session_state.selected_politician_details
            party = details.get("party")
            if party:
                basic_questions.append(f"How does {politician}'s voting align with other {party} members?")
            
            province = details.get("province") or details.get("constituency")
            if province:
                basic_questions.append(f"What are the main issues in {province} that {politician} works on?")
            
            # News-related questions if news articles exist
            news = details.get("news", [])
            if news and len(news) > 0:
                basic_questions.append(f"What do recent news articles say about {politician}?")
        
        return basic_questions
    
    def _render_research_controls(self):
        # """Render research mode controls in sidebar"""
        # st.sidebar.markdown("## Research Controls")
        
        # # Research mode toggle
        # st.session_state.research_mode_enabled = st.sidebar.checkbox(
        #     "Enable Research Mode",
        #     value=st.session_state.research_mode_enabled
        # )
        
        if st.session_state.research_mode_enabled:
            # Show direct access status
            if self.pipeline_service.direct_mode_available:
                st.sidebar.success("✅ Direct Agent Access Available")
            else:
                st.sidebar.warning("⚠️ Using API Fallback")
            
            # Show LangSmith status
            if self.pipeline_service.is_langsmith_enabled():
                st.sidebar.success("✅ LangSmith Tracing Enabled")
            else:
                st.sidebar.info("ℹ️ LangSmith Not Available")
            
            # Add visualization toggles
            self.visualizer.toggle_settings()
            
            # Add metrics display
            metrics = self.pipeline_service.get_agent_metrics(limit=5)
            if metrics:
                st.sidebar.markdown("### Recent Metrics")
                for i, metric in enumerate(metrics[-3:]):
                    with st.sidebar.expander(f"Query {i+1}", expanded=False):
                        st.metric("Response Time", f"{metric.get('latency_ms', 0):.1f} ms")
                        st.metric("Security Score", f"{metric.get('security_score', 1.0)*100:.1f}%")
    
    def _enhance_response_with_predictions(self, response: str, politician: str) -> str:
        """
        Enhance response with predictive insights when appropriate
        
        Args:
            response: Original response text
            politician: Politician name
            
        Returns:
            Enhanced response with predictive insights
        """
        # Only add predictions if lazy mode is enabled
        if not st.session_state.get("lazy_mode_enabled", False):
            return response
            
        try:
            # Check if response is suitable for predictions
            prediction_triggers = ["position", "policy", "vote", "future", "opinion", "stance"]
            
            # Only add predictions for responses discussing relevant topics
            if any(trigger in response.lower() for trigger in prediction_triggers):
                prediction = self._generate_prediction(politician)
                if prediction:
                    # Add predictive insight as a separate section
                    enhanced_response = f"{response}\n\n**Predictive Insight:** {prediction}"
                    return enhanced_response
            
            return response
        except Exception as e:
            # Log error but don't disrupt the user experience
            self.logger.error(f"Error generating prediction: {e}")
            return response  # Return original response if prediction fails
    
    def _generate_prediction(self, politician: str) -> str:
        """
        Generate a prediction based on politician data
        
        Args:
            politician: Politician name
            
        Returns:
            Prediction text or empty string if no prediction can be made
        """
        try:
            # Get politician details if available
            details = None
            if "selected_politician_details" in st.session_state:
                details = st.session_state.selected_politician_details
            
            # Base predictions that don't require specific details
            base_predictions = [
                f"Based on voting patterns, {politician} is likely to focus on economic policies in upcoming sessions.",
                f"Analysis suggests {politician} may take a more prominent role in parliamentary debates this year.",
                f"Comparing with similar career trajectories, {politician} could seek committee leadership in the next term."
            ]
            
            # If we have details, generate more specific predictions
            if details:
                specific_predictions = []
                
                # Party-based predictions
                party = details.get("party")
                if party:
                    specific_predictions.append(
                        f"As a member of {party}, {politician} will likely align with the party's position on upcoming economic reforms."
                    )
                
                # News-based predictions
                news = details.get("news", [])
                if news and len(news) > 2:
                    topics = ["healthcare", "education", "environment", "economy", "immigration", "security"]
                    mentioned_topics = []
                    
                    # Simple topic detection from news headlines
                    for article in news:
                        title = article.get("title", "").lower() if article.get("title") else ""
                        for topic in topics:
                            if topic in title and topic not in mentioned_topics:
                                mentioned_topics.append(topic)
                    
                    if mentioned_topics:
                        topic = mentioned_topics[0]  # Use first detected topic
                        specific_predictions.append(
                            f"Recent news coverage suggests {politician} may focus more on {topic} policy in the near future."
                        )
                
                # Use specific prediction if available, otherwise use base prediction
                if specific_predictions:
                    import random
                    return random.choice(specific_predictions)
            
            # Fall back to base predictions
            import random
            return random.choice(base_predictions)
            
        except Exception as e:
            self.logger.error(f"Error in prediction generation: {e}")
            return ""  # Return empty string if prediction fails
    
    def _setup_autocomplete(self, politician_name: str):
        """
        Set up auto-complete for chat input
        
        Args:
            politician_name: Name of the politician for context-aware suggestions
        """
        # Only set up if lazy mode is enabled
        if not st.session_state.get("lazy_mode_enabled", False):
            return
            
        # Common question prefixes
        prefixes = [
            f"What is {politician_name}'s position on",
            f"When did {politician_name} first",
            f"How has {politician_name} voted on",
            f"Why does {politician_name} support",
            f"Can you compare {politician_name} with",
            f"What are {politician_name}'s views on",
            f"Has {politician_name} ever commented on",
            f"What is {politician_name}'s background in",
            f"How long has {politician_name} been in"
        ]
        
        # Add party-specific questions if available
        if "selected_politician_details" in st.session_state:
            details = st.session_state.selected_politician_details
            party = details.get("party")
            if party:
                prefixes.append(f"How does {politician_name} compare to other {party} members")
                prefixes.append(f"What is {politician_name}'s role in the {party}")
        
        # Convert to JavaScript-friendly format
        import json
        prefixes_json = json.dumps(prefixes)
        
        # Create JavaScript for auto-complete
        js = f"""
        <script>
        // Auto-complete for politician questions
        document.addEventListener('DOMContentLoaded', function() {{
            // Wait for Streamlit to fully load
            setTimeout(function() {{
                const prefixes = {prefixes_json};
                const inputField = document.querySelector('.stChatInput input');
                
                if (inputField) {{
                    // Create suggestion element
                    const suggestionDiv = document.createElement('div');
                    suggestionDiv.style.position = 'absolute';
                    suggestionDiv.style.zIndex = '1000';
                    suggestionDiv.style.backgroundColor = 'white';
                    suggestionDiv.style.border = '1px solid #ddd';
                    suggestionDiv.style.borderRadius = '4px';
                    suggestionDiv.style.padding = '5px';
                    suggestionDiv.style.display = 'none';
                    suggestionDiv.style.width = 'calc(100% - 20px)';
                    suggestionDiv.style.maxHeight = '200px';
                    suggestionDiv.style.overflowY = 'auto';
                    suggestionDiv.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                    
                    // Add suggestion element to DOM
                    inputField.parentNode.style.position = 'relative';
                    inputField.parentNode.appendChild(suggestionDiv);
                    
                    // Handle input changes
                    inputField.addEventListener('input', function() {{
                        const value = this.value.toLowerCase();
                        if (value.length > 2) {{
                            // Find matching prefixes
                            const matches = prefixes.filter(prefix => 
                                prefix.toLowerCase().startsWith(value) || 
                                prefix.toLowerCase().includes(value)
                            );
                            
                            if (matches.length > 0) {{
                                // Show suggestions
                                suggestionDiv.innerHTML = '';
                                matches.slice(0, 5).forEach(match => {{
                                    const item = document.createElement('div');
                                    item.textContent = match;
                                    item.style.padding = '5px';
                                    item.style.cursor = 'pointer';
                                    item.style.borderBottom = '1px solid #eee';
                                    item.addEventListener('click', function() {{
                                        inputField.value = match;
                                        suggestionDiv.style.display = 'none';
                                        inputField.focus();
                                    }});
                                    item.addEventListener('mouseover', function() {{
                                        this.style.backgroundColor = '#f0f0f0';
                                    }});
                                    item.addEventListener('mouseout', function() {{
                                        this.style.backgroundColor = 'transparent';
                                    }});
                                    suggestionDiv.appendChild(item);
                                }});
                                suggestionDiv.style.display = 'block';
                            }} else {{
                                suggestionDiv.style.display = 'none';
                            }}
                        }} else {{
                            suggestionDiv.style.display = 'none';
                        }}
                    }});
                    
                    // Hide suggestions when clicking outside
                    document.addEventListener('click', function(e) {{
                        if (e.target !== inputField && e.target !== suggestionDiv) {{
                            suggestionDiv.style.display = 'none';
                        }}
                    }});
                    
                    // Handle keyboard navigation
                    inputField.addEventListener('keydown', function(e) {{
                        if (suggestionDiv.style.display === 'block') {{
                            const items = suggestionDiv.querySelectorAll('div');
                            let activeIndex = -1;
                            
                            // Find currently active item
                            for (let i = 0; i < items.length; i++) {{
                                if (items[i].style.backgroundColor === '#f0f0f0') {{
                                    activeIndex = i;
                                    break;
                                }}
                            }}
                            
                            if (e.key === 'ArrowDown') {{
                                e.preventDefault();
                                if (activeIndex < items.length - 1) {{
                                    if (activeIndex >= 0) items[activeIndex].style.backgroundColor = 'transparent';
                                    items[activeIndex + 1].style.backgroundColor = '#f0f0f0';
                                }}
                            }} else if (e.key === 'ArrowUp') {{
                                e.preventDefault();
                                if (activeIndex > 0) {{
                                    items[activeIndex].style.backgroundColor = 'transparent';
                                    items[activeIndex - 1].style.backgroundColor = '#f0f0f0';
                                }}
                            }} else if (e.key === 'Enter' && activeIndex >= 0) {{
                                e.preventDefault();
                                inputField.value = items[activeIndex].textContent;
                                suggestionDiv.style.display = 'none';
                            }} else if (e.key === 'Escape') {{
                                suggestionDiv.style.display = 'none';
                            }}
                        }}
                    }});
                }}
            }}, 1000); // Wait for Streamlit to initialize
        }});
        </script>
        """
        
        # Inject JavaScript into the page
        st.components.v1.html(js, height=0)
    
    def render(self, selected_politician: Optional[str] = None):
        """
        Render the enhanced chat interface
        
        Args:
            selected_politician: Currently selected politician
        """
        politician = selected_politician or st.session_state.get("selected_politician")
        st.title("AI Assistant")
        
        # Show research controls if available
        # if self.research_mode_available:
        #     self._render_research_controls()
        
        # Force rerun when politician changes
        if "_last_selected_politician" not in st.session_state:
            st.session_state["_last_selected_politician"] = None
        if politician and st.session_state["_last_selected_politician"] != politician:
            st.session_state["_last_selected_politician"] = politician
            st.session_state["chat_messages"] = {}  # Optionally clear chat on switch
            st.rerun()
        
        if not politician:
            st.warning("Please select a politician from the map to start chatting.")
            return
        
        st.markdown(f"**Chatting about:** :blue[{politician}]")
        
        # Chat history in session state
        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = {}
        if politician not in st.session_state["chat_messages"]:
            st.session_state["chat_messages"][politician] = []
        chat_history = st.session_state["chat_messages"][politician]
        
        # Render chat history
        for message in chat_history:
            with st.chat_message(message.role):
                if self.research_mode_available and st.session_state.research_mode_enabled:
                    # Enhanced visualization in research mode
                    if message.role == "assistant" and hasattr(message, "reasoning"):
                        response_data = {
                            "output": message.content,
                            "reasoning": message.reasoning,
                            "sources": message.sources,
                            "metrics": message.metrics,
                            "direct_access": message.direct_access
                        }
                        self.visualizer.visualize_response(response_data)
                    else:
                        st.write(message.content)
                else:
                    # Standard display
                    st.write(message.content)
        
        # Add suggested questions if lazy mode is enabled
        if st.session_state.get("lazy_mode_enabled", False) and politician:
            st.markdown("### 💡 Suggested Questions")
            questions = self._generate_suggested_questions(politician)
            
            # Display in two columns for better space usage
            col1, col2 = st.columns(2)
            for i, question in enumerate(questions):
                with col1 if i % 2 == 0 else col2:
                    if st.button(question, key=f"suggested_q_{i}"):
                        # Add user message to history
                        chat_history.append(ChatMessage(role="user", content=question))
                        
                        # Generate response
                        with st.chat_message("assistant"):
                            response = self._generate_response(question, politician)
                            
                            if self.research_mode_available and st.session_state.research_mode_enabled:
                                # Enhanced visualization in research mode
                                if isinstance(response, dict):
                                    # Store full response data in chat history
                                    chat_history.append(ChatMessage(
                                        role="assistant",
                                        content=response.get("output", ""),
                                        reasoning=response.get("reasoning", []),
                                        sources=response.get("sources", []),
                                        metrics=response.get("metrics", {}),
                                        direct_access=response.get("direct_access", False)
                                    ))
                                    # Visualize response
                                    self.visualizer.visualize_response(response)
                                else:
                                    # Fallback to standard display
                                    chat_history.append(ChatMessage(role="assistant", content=response))
                                    st.write(response)
                            else:
                                # Standard display
                                chat_history.append(ChatMessage(role="assistant", content=response))
                                st.write(response)
                        
                        st.rerun()  # Ensures UI updates instantly
        
        # Set up auto-complete for chat input
        self._setup_autocomplete(politician)
        
        # User input with dynamic placeholder
        chat_placeholder = f"Ask about {politician}..."
        if prompt := st.chat_input(chat_placeholder):
            # Add user message to history
            chat_history.append(ChatMessage(role="user", content=prompt))
            
            # Generate response
            with st.chat_message("assistant"):
                response = self._generate_response(prompt, politician)
                
                if self.research_mode_available and st.session_state.research_mode_enabled:
                    # Enhanced visualization in research mode
                    if isinstance(response, dict):
                        # Store full response data in chat history
                        chat_history.append(ChatMessage(
                            role="assistant",
                            content=response.get("output", ""),
                            reasoning=response.get("reasoning", []),
                            sources=response.get("sources", []),
                            metrics=response.get("metrics", {}),
                            direct_access=response.get("direct_access", False)
                        ))
                        # Visualize response
                        self.visualizer.visualize_response(response)
                    else:
                        # Fallback to standard display
                        chat_history.append(ChatMessage(role="assistant", content=response))
                        st.write(response)
                else:
                    # Standard display
                    chat_history.append(ChatMessage(role="assistant", content=response))
                    st.write(self._enhance_response_with_predictions(response, politician))
            
            st.rerun()  # Ensures UI updates instantly
        
        # Analysis controls
        st.subheader("Advanced Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Show Full Analysis"):
                analysis = self._fetch_analysis(politician)
                
                if self.research_mode_available and st.session_state.research_mode_enabled:
                    # Enhanced visualization in research mode
                    self.visualizer.visualize_response(analysis)
                else:
                    # Standard display
                    st.json(analysis)
        
        # Add experiment controls in research mode
        if self.research_mode_available and st.session_state.research_mode_enabled:
            with col2:
                if st.button("Create Experiment"):
                    with st.expander("Prompt Engineering Experiment", expanded=True):
                        st.subheader("Create New Experiment")
                        
                        # Simple experiment form
                        exp_name = st.text_input("Experiment Name", "Test Experiment")
                        exp_desc = st.text_area("Description", "Testing different prompt formats")
                        
                        # Create experiment variables
                        st.markdown("### Variables")
                        st.markdown("Define variables to test in your prompts")
                        
                        var1_name = st.text_input("Variable 1 Name", "tone")
                        var1_values = st.text_input("Variable 1 Values (comma separated)", "formal,casual,academic")
                        
                        var2_name = st.text_input("Variable 2 Name", "detail_level")
                        var2_values = st.text_input("Variable 2 Values (comma separated)", "high,medium,low")
                        
                        template = st.text_area(
                            "Prompt Template", 
                            "Analyze the politician's voting record with a {tone} tone and {detail_level} detail level."
                        )
                        
                        if st.button("Run Experiment"):
                            # Create experiment
                            experiment_id = self.pipeline_service.create_experiment(
                                name=exp_name,
                                description=exp_desc,
                                variables={
                                    var1_name: var1_values.split(","),
                                    var2_name: var2_values.split(",")
                                }
                            )
                            
                            # Run experiment
                            results = self.pipeline_service.run_experiment(
                                experiment_id=experiment_id,
                                query_template=template,
                                context_ids=[politician]
                            )
                            
                            # Show results
                            experiment = self.pipeline_service.get_experiment(experiment_id)
                            self.visualizer.visualize_experiment_results(experiment)
        
        # Show metrics history in research mode
        if self.research_mode_available and st.session_state.research_mode_enabled:
            with st.expander("Metrics History", expanded=False):
                metrics = self.pipeline_service.get_agent_metrics()
                self.visualizer.visualize_metrics_history(metrics)
        
        # Show suggested questions
        suggested_questions = self._generate_suggested_questions(politician)
        with st.expander("Suggested Questions", expanded=False):
            for question in suggested_questions:
                st.write(question)
