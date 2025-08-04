"""
Analysis dashboard component for politician data visualization
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime


class AnalysisDashboard:
    """Dashboard for politician analysis and visualization"""
    
    def __init__(self):
        """Initialize analysis dashboard"""
        self.logger = logging.getLogger(__name__)
        self.data: Optional[Dict] = None
        
    def _create_sector_chart(self, sector_data: Dict[str, float]) -> go.Figure:
        """
        Create sector involvement pie chart
        
        Args:
            sector_data: Dictionary of sector percentages
            
        Returns:
            go.Figure: Plotly figure
        """
        try:
            fig = go.Figure(
                data=[go.Pie(
                    labels=list(sector_data.keys()),
                    values=list(sector_data.values()),
                    hole=.3
                )]
            )
            fig.update_layout(
                title='Sector Involvement',
                showlegend=True,
                legend_title='Sectors',
                font=dict(
                    family="Arial",
                    size=12,
                    color="#000000"
                )
            )
            return fig
        except Exception as e:
            self.logger.error(f"Error creating sector chart: {str(e)}")
            raise
    
    def _create_sentiment_chart(self, sentiment_scores: List[float]) -> go.Figure:
        """
        Create sentiment trend line chart
        
        Args:
            sentiment_scores: List of sentiment scores
            
        Returns:
            go.Figure: Plotly figure
        """
        try:
            dates = pd.date_range(
                end=datetime.now(),
                periods=len(sentiment_scores),
                freq='D'
            )
            
            fig = go.Figure(
                data=[go.Scatter(
                    x=dates,
                    y=sentiment_scores,
                    mode='lines+markers',
                    name='Sentiment Score'
                )]
            )
            fig.update_layout(
                title='Sentiment Trend',
                xaxis_title='Date',
                yaxis_title='Sentiment Score',
                yaxis_range=[-1, 1]
            )
            return fig
        except Exception as e:
            self.logger.error(f"Error creating sentiment chart: {str(e)}")
            raise
    
    def _create_achievement_timeline(self, achievements: List[Dict]) -> go.Figure:
        """
        Create achievement timeline
        
        Args:
            achievements: List of achievement dictionaries
            
        Returns:
            go.Figure: Plotly figure
        """
        try:
            df = pd.DataFrame(achievements)
            
            fig = go.Figure(
                data=[go.Scatter(
                    x=df['date'],
                    y=df['score'],
                    mode='markers+text',
                    text=df['description'],
                    textposition='top center',
                    marker=dict(size=10)
                )]
            )
            fig.update_layout(
                title='Key Achievements',
                xaxis_title='Date',
                yaxis_title='Impact Score',
                showlegend=False
            )
            return fig
        except Exception as e:
            self.logger.error(f"Error creating achievement timeline: {str(e)}")
            raise
    
    def _create_risk_gauge(self, risk_score: float) -> go.Figure:
        """
        Create corruption risk gauge
        
        Args:
            risk_score: Risk score (0-1)
            
        Returns:
            go.Figure: Plotly figure
        """
        try:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=risk_score * 100,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Corruption Risk"},
                    gauge={'axis': {'range': [0, 100]},
                          'bar': {'color': "#FF4136" if risk_score > 0.5 else "#2ECC40"},
                          'steps': [
                              {'range': [0, 33], 'color': "#2ECC40"},
                              {'range': [33, 66], 'color': "#FFDC00"},
                              {'range': [66, 100], 'color': "#FF4136"}
                          ]}
                )
            )
            return fig
        except Exception as e:
            self.logger.error(f"Error creating risk gauge: {str(e)}")
            raise
    
    def render(self):
        """Render the analysis dashboard"""
        st.title("Analysis Dashboard")
        
        # Sector Analysis
        st.subheader("Sector Involvement")
        sector_data = {
            "Healthcare": 0.4,
            "Education": 0.3,
            "Economy": 0.2,
            "Others": 0.1
        }
        st.plotly_chart(self._create_sector_chart(sector_data), use_container_width=True)
        
        # Sentiment Analysis
        st.subheader("Sentiment Trend")
        sentiment_scores = [0.75, 0.80, 0.78, 0.82, 0.85, 0.83, 0.87]
        st.plotly_chart(self._create_sentiment_chart(sentiment_scores), use_container_width=True)
        
        # Achievement Timeline
        st.subheader("Key Achievements")
        achievements = [
            {'date': '2023-01-01', 'score': 0.9, 'description': 'Education Reform'},
            {'date': '2023-03-01', 'score': 0.85, 'description': 'Healthcare Bill'},
            {'date': '2023-06-01', 'score': 0.88, 'description': 'Economic Policy'}
        ]
        st.plotly_chart(self._create_achievement_timeline(achievements), use_container_width=True)
        
        # Corruption Risk
        st.subheader("Corruption Risk Assessment")
        risk_score = 0.15
        st.plotly_chart(self._create_risk_gauge(risk_score), use_container_width=True)
        
        # Voting Impact Analysis
        st.subheader("Voting Impact Analysis")
        st.markdown("""
        Based on analysis:
        - Strong impact on healthcare policy
        - Positive influence on education reform
        - Consistent economic policy stance
        - Low corruption risk
        """)
