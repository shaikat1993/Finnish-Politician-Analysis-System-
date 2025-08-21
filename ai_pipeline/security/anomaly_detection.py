"""
ML-based anomaly detection for security metrics
Uses scikit-learn for statistical analysis of security events
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetector:
    """
    Anomaly detection for security metrics using machine learning
    
    Uses Isolation Forest algorithm to detect anomalies in security event patterns
    """
    
    def __init__(self, contamination: float = 0.05, log_level: int = logging.INFO):
        """
        Initialize the anomaly detector
        
        Args:
            contamination: Expected proportion of anomalies (0.01-0.1)
            log_level: Logging level
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        self.contamination = contamination
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()
        
        self.logger.info("AnomalyDetector initialized with contamination=%s", contamination)
    
    def detect_anomalies(self, events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Detect anomalies in security events
        
        Args:
            events: List of security events
            
        Returns:
            Tuple of (anomalous events, anomaly stats)
        """
        if len(events) < 10:
            self.logger.warning("Not enough events for anomaly detection (minimum 10 required)")
            return [], {"status": "insufficient_data", "message": f"Not enough events ({len(events)}) for anomaly detection"}
        
        # Extract features for anomaly detection
        features = self._extract_features(events)
        
        if features.shape[0] < 10:
            self.logger.warning("Not enough feature vectors for anomaly detection")
            return [], {"status": "insufficient_data", "message": "Not enough feature vectors for anomaly detection"}
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Train model and predict anomalies
        self.model.fit(scaled_features)
        predictions = self.model.predict(scaled_features)
        
        # Isolation Forest returns -1 for anomalies and 1 for normal data
        anomaly_indices = np.where(predictions == -1)[0]
        
        # Get anomalous events
        anomalous_events = [events[i] for i in anomaly_indices]
        
        # Calculate anomaly stats
        anomaly_stats = {
            "total_events": len(events),
            "anomaly_count": len(anomalous_events),
            "anomaly_percentage": (len(anomalous_events) / len(events)) * 100,
            "contamination": self.contamination
        }
        
        self.logger.info("Detected %s anomalies out of %s events (%.2f%%)", 
                        len(anomalous_events), len(events), anomaly_stats["anomaly_percentage"])
        
        return anomalous_events, anomaly_stats
    
    def _extract_features(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract features from security events for anomaly detection
        
        Features include:
        - Events per hour
        - Events per component
        - Events per severity
        - Events per result (blocked, allowed, warning)
        
        Args:
            events: List of security events
            
        Returns:
            Numpy array of features
        """
        # Group events by hour
        events_by_hour = defaultdict(list)
        for event in events:
            if "timestamp" not in event:
                continue
                
            timestamp = event.get("timestamp", 0)
            if isinstance(timestamp, str):
                try:
                    timestamp = float(timestamp)
                except ValueError:
                    continue
                    
            event_time = datetime.fromtimestamp(timestamp)
            hour_key = event_time.strftime("%Y-%m-%d %H:00:00")
            events_by_hour[hour_key].append(event)
        
        # Create feature vectors for each hour
        feature_vectors = []
        
        for hour, hour_events in events_by_hour.items():
            if len(hour_events) < 2:  # Skip hours with too few events
                continue
                
            # Count events by component, severity, and result
            component_counts = defaultdict(int)
            severity_counts = defaultdict(int)
            result_counts = defaultdict(int)
            
            for event in hour_events:
                component = event.get("component", "unknown")
                severity = event.get("severity", "unknown")
                result = event.get("result", "unknown")
                
                component_counts[component] += 1
                severity_counts[severity] += 1
                result_counts[result] += 1
            
            # Create feature vector
            feature_vector = [
                len(hour_events),  # Total events in this hour
                component_counts.get("prompt_guard", 0),
                component_counts.get("output_sanitizer", 0),
                component_counts.get("verification_system", 0),
                severity_counts.get("low", 0),
                severity_counts.get("medium", 0),
                severity_counts.get("high", 0),
                severity_counts.get("critical", 0),
                result_counts.get("blocked", 0),
                result_counts.get("allowed", 0),
                result_counts.get("warning", 0)
            ]
            
            feature_vectors.append(feature_vector)
        
        return np.array(feature_vectors)
    
    def analyze_time_series(self, events: List[Dict[str, Any]], window_size: int = 24) -> Dict[str, Any]:
        """
        Analyze time series patterns in security events
        
        Args:
            events: List of security events
            window_size: Size of the sliding window in hours
            
        Returns:
            Time series analysis results
        """
        if len(events) < window_size:
            return {"status": "insufficient_data", "message": f"Not enough events for time series analysis"}
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        
        # Group events by hour
        events_by_hour = defaultdict(list)
        for event in sorted_events:
            timestamp = event.get("timestamp", 0)
            event_time = datetime.fromtimestamp(timestamp)
            hour_key = event_time.strftime("%Y-%m-%d %H:00:00")
            events_by_hour[hour_key].append(event)
        
        # Get hourly counts
        hours = sorted(events_by_hour.keys())
        counts = [len(events_by_hour[hour]) for hour in hours]
        
        # Calculate moving average
        moving_avg = []
        for i in range(len(counts) - window_size + 1):
            window = counts[i:i+window_size]
            moving_avg.append(sum(window) / window_size)
        
        # Calculate standard deviation
        if len(moving_avg) > 1:
            std_dev = np.std(moving_avg)
        else:
            std_dev = 0
        
        # Detect anomalies (hours with event counts > mean + 3*std_dev)
        mean = np.mean(counts) if counts else 0
        threshold = mean + 3 * std_dev
        
        anomalous_hours = []
        for i, hour in enumerate(hours):
            if counts[i] > threshold:
                anomalous_hours.append({
                    "hour": hour,
                    "count": counts[i],
                    "threshold": threshold,
                    "deviation": counts[i] - mean
                })
        
        return {
            "status": "success",
            "total_hours": len(hours),
            "mean_events_per_hour": mean,
            "std_dev": std_dev,
            "anomaly_threshold": threshold,
            "anomalous_hours": anomalous_hours
        }
