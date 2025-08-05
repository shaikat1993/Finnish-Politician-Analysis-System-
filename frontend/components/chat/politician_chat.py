"""
Chat component with AI assistant for politician analysis
"""

import sys
import os
import requests
import streamlit as st
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
        self.logger = logging.getLogger(__name__)
        self.selected_politician: Optional[str] = None

    def _fetch_analysis(self, politician_id: str):
        """
        Fetch AI analysis for politician using orchestrator backend via HTTP.
        """
        try:
            with st.spinner("Analyzing politician..."):
                response = requests.post(
                    f"{self.api_base_url}/analysis/custom",
                    json={
                        "query": f"Full analysis for {politician_id}",
                        "context_ids": [politician_id],
                        "detailed_response": True
                    },
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
            return data
        except requests.Timeout:
            return {"error": "Analysis timed out. Please try again."}
        except Exception as e:
            self.logger.error(f"Error fetching analysis: {str(e)}")
            return {"error": str(e)}

    def _generate_response(self, message: str, politician: Optional[str] = None) -> str:
        import time
        if not politician:
            return "Please select a politician first."
        try:
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{self.api_base_url}/analysis/custom",
                    json={
                        "query": message,
                        "context_ids": [politician],
                        "detailed_response": False
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                # If backend is async, poll status endpoint
                if data.get("status") == "accepted" and data.get("status_url"):
                    status_url = data["status_url"]
                    start_time = time.time()
                    max_wait = 30  # seconds
                    poll_interval = 1.5
                    while True:
                        poll_response = requests.get(
                            f"{self.api_base_url}/analysis{status_url.split('/analysis')[-1]}", timeout=10
                        )
                        poll_data = poll_response.json()
                        if poll_data.get("status") == "completed":
                            # AI answer is ready
                            data = poll_data.get("result", poll_data)
                            break
                        elif poll_data.get("status") == "failed":
                            return f"[Agent Error] {poll_data.get('error', 'Unknown error')}"
                        elif time.time() - start_time > max_wait:
                            return "Sorry, the AI took too long to respond. Please try again."
                        time.sleep(poll_interval)
        except requests.Timeout:
            return "Sorry, the AI took too long to respond. Please try again."
        except Exception as e:
            return f"[Agent Error] {str(e)}"
        answer = data.get('output') or data.get('answer') or data.get('result') or ''
        sources = data.get('sources')
        reasoning = data.get('reasoning')
        output = answer
        if reasoning:
            output += f"\n\n**Reasoning:** {reasoning}"
        if sources:
            output += f"\n\n**Sources:** {sources}"
        return output or str(data) or "Sorry, I couldn't find an answer for that."

    def render(self, selected_politician: Optional[str] = None):
        politician = selected_politician or st.session_state.get("selected_politician")
        st.title("AI Assistant")

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
                st.write(message.content)

        # User input with dynamic placeholder
        chat_placeholder = f"Ask about {politician}..."
        if prompt := st.chat_input(chat_placeholder):
            chat_history.append(ChatMessage(role="user", content=prompt))
            with st.chat_message("assistant"):
                response = self._generate_response(prompt, politician)
                chat_history.append(ChatMessage(role="assistant", content=response))
                st.write(response)
            st.rerun()  # Ensures UI updates instantly

        # Analysis controls
        st.subheader("Advanced Analysis")
        if st.button("Show Full Analysis"):
            analysis = self._fetch_analysis(politician)
            st.json(analysis if isinstance(analysis, dict) else analysis.dict())
