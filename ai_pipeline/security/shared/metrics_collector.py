"""
OWASP LLM Security Metrics Collector
Advanced metrics collection for academic research on LLM security controls.
"""

import json
import time
import logging
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import threading
import uuid
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict, Counter

# Import telemetry conditionally
try:
    from ai_pipeline.security.shared.telemetry import get_telemetry_manager
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

@dataclass
class SecurityEvent:
    """Data class for security events"""
    event_id: str
    timestamp: float
    event_type: str
    component: str
    severity: str
    result: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class SecurityMetrics:
    """Data class for security metrics"""
    total_events: int = 0
    blocked_events: int = 0
    allowed_events: int = 0
    warning_events: int = 0
    components: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(Counter))
    severity_counts: Dict[str, int] = field(default_factory=Counter)
    response_times: List[float] = field(default_factory=list)
    hourly_events: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "total_events": self.total_events,
            "blocked_events": self.blocked_events,
            "allowed_events": self.allowed_events,
            "warning_events": self.warning_events,
            "components": {k: dict(v) for k, v in self.components.items()},
            "severity_counts": dict(self.severity_counts),
            "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "hourly_events": dict(self.hourly_events)
        }
        return result

class SecurityMetricsCollector:
    """
    Advanced OWASP LLM Security Metrics Collector
    
    Collects, analyzes, and visualizes security metrics for academic research:
    1. Tracks security events across all OWASP controls
    2. Provides visualization capabilities for dashboards
    3. Supports academic research with detailed metrics
    4. Enables A/B testing of different security approaches
    """
    
    def __init__(self, 
                 metrics_dir: str = "security_metrics",
                 enable_persistence: bool = True,
                 enable_visualization: bool = True,
                 enable_telemetry: bool = False,
                 log_level: int = logging.INFO):
        """
        Initialize the SecurityMetricsCollector
        
        Args:
            metrics_dir: Directory to store metrics data
            enable_persistence: Whether to persist metrics to disk
            enable_visualization: Whether to generate visualizations
            enable_telemetry: Whether to enable OpenTelemetry integration
            log_level: Logging level
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        self.metrics_dir = metrics_dir
        self.enable_persistence = enable_persistence
        self.enable_visualization = enable_visualization
        self.enable_telemetry = enable_telemetry and TELEMETRY_AVAILABLE
        
        # Create metrics directory if it doesn't exist
        if self.enable_persistence:
            os.makedirs(self.metrics_dir, exist_ok=True)
            
        # Initialize metrics
        self.metrics = SecurityMetrics()
        self.events: List[SecurityEvent] = []
        
        # Session tracking
        self.current_session_id = str(uuid.uuid4())
        
        # Component-specific metrics
        self.component_metrics = {
            "prompt_guard": {},
            "output_sanitizer": {},
            "verification_system": {}
        }
        
        # Thread lock for thread safety
        self._lock = threading.Lock()
        
        # Initialize telemetry if available and enabled
        self.telemetry_manager = None
        
        if self.enable_telemetry and TELEMETRY_AVAILABLE:
            try:
                self.telemetry_manager = get_telemetry_manager(enable_telemetry=True)
                self.logger.info("Telemetry integration enabled for security metrics")
            except Exception as e:
                self.logger.error(f"Failed to initialize telemetry: {str(e)}")
                self.telemetry_manager = None
        
        self.logger.info("SecurityMetricsCollector initialized with persistence=%s, visualization=%s, telemetry=%s", 
                        enable_persistence, enable_visualization, enable_telemetry)
    
    def record_event(self, 
                    event_type: str,
                    component: str,
                    severity: str,
                    result: str,
                    details: Optional[Dict[str, Any]] = None,
                    user_id: Optional[str] = None,
                    response_time: Optional[float] = None) -> str:
        """
        Record a security event
        
        Args:
            event_type: Type of security event
            component: Security component that generated the event
            severity: Severity level (low, medium, high, critical)
            result: Result of the event (blocked, allowed, warning)
            details: Additional details about the event
            user_id: ID of the user associated with the event
            response_time: Time taken to process the security check
            
        Returns:
            ID of the recorded event
        """
        with self._lock:
            # Create event
            event_id = str(uuid.uuid4())
            timestamp = time.time()
            
            event = SecurityEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                component=component,
                severity=severity,
                result=result,
                details=details,
                user_id=user_id,
                session_id=self.current_session_id
            )
            
            # Add to events list
            self.events.append(event)
            
            # Update metrics
            self.metrics.total_events += 1
            
            if result == "blocked":
                self.metrics.blocked_events += 1
            elif result == "allowed":
                self.metrics.allowed_events += 1
            elif result == "warning":
                self.metrics.warning_events += 1
            
            # Update component metrics
            if component not in self.metrics.components:
                self.metrics.components[component] = Counter()
            self.metrics.components[component][result] += 1
            
            # Update severity counts
            self.metrics.severity_counts[severity] += 1
            
            # Update response time metrics
            if response_time is not None:
                self.metrics.response_times.append(response_time)
            
            # Update hourly metrics
            hour = datetime.fromtimestamp(timestamp).hour
            self.metrics.hourly_events[hour] += 1
            
            # Record to telemetry if enabled
            if self.enable_telemetry and self.telemetry_manager:
                try:
                    # Extract response time if available
                    response_time = response_time
                    
                    # Record to OpenTelemetry
                    self.telemetry_manager.record_security_event(
                        event_type=event_type,
                        component=component,
                        severity=severity,
                        result=result,
                        response_time=response_time,
                        attributes=details
                    )
                except Exception as e:
                    self.logger.error(f"Failed to record event to telemetry: {str(e)}")
            
            # Persist event if enabled
            if self.enable_persistence:
                self._persist_event(event)
            
            self.logger.debug("Recorded security event: %s, %s, %s", component, event_type, result)
            
            return event_id
    
    def record_prompt_injection_attempt(self, 
                                       severity: str,
                                       result: str,
                                       prompt: str,
                                       detection_method: str,
                                       confidence: float,
                                       user_id: Optional[str] = None,
                                       response_time: Optional[float] = None) -> str:
        """
        Record a prompt injection attempt
        
        Args:
            severity: Severity level of the attempt
            result: Result of the detection (blocked, allowed, warning)
            prompt: The prompt that was analyzed
            detection_method: Method used to detect the injection
            confidence: Confidence score of the detection
            user_id: ID of the user associated with the event
            response_time: Time taken to process the security check
            
        Returns:
            ID of the recorded event
        """
        details = {
            "prompt_length": len(prompt),
            "detection_method": detection_method,
            "confidence": confidence,
            "prompt_excerpt": prompt[:100] + "..." if len(prompt) > 100 else prompt
        }
        
        return self.record_event(
            event_type="prompt_injection_attempt",
            component="prompt_guard",
            severity=severity,
            result=result,
            details=details,
            user_id=user_id,
            response_time=response_time
        )
    
    def record_sensitive_information_detection(self,
                                             severity: str,
                                             result: str,
                                             content_type: str,
                                             detection_method: str,
                                             info_types: List[str],
                                             user_id: Optional[str] = None,
                                             response_time: Optional[float] = None) -> str:
        """
        Record a sensitive information detection event
        
        Args:
            severity: Severity level of the detection
            result: Result of the detection (blocked, allowed, warning)
            content_type: Type of content (prompt, response, etc.)
            detection_method: Method used to detect sensitive information
            info_types: Types of sensitive information detected
            user_id: ID of the user associated with the event
            response_time: Time taken to process the security check
            
        Returns:
            ID of the recorded event
        """
        details = {
            "content_type": content_type,
            "detection_method": detection_method,
            "info_types": info_types,
            "info_count": len(info_types)
        }
        
        return self.record_event(
            event_type="sensitive_information_detection",
            component="output_sanitizer",
            severity=severity,
            result=result,
            details=details,
            user_id=user_id,
            response_time=response_time
        )
    
    def record_verification_result(self,
                                 verification_type: str,
                                 is_verified: bool,
                                 confidence: float,
                                 risk_level: str,
                                 verification_method: str,
                                 user_id: Optional[str] = None,
                                 response_time: Optional[float] = None) -> str:
        """
        Record a verification result
        
        Args:
            verification_type: Type of verification performed
            is_verified: Whether the verification passed
            confidence: Confidence score of the verification
            risk_level: Risk level assessed
            verification_method: Method used for verification
            user_id: ID of the user associated with the event
            response_time: Time taken to process the verification
            
        Returns:
            ID of the recorded event
        """
        result = "allowed" if is_verified else "blocked"
        
        details = {
            "verification_type": verification_type,
            "confidence": confidence,
            "verification_method": verification_method
        }
        
        return self.record_event(
            event_type="verification_result",
            component="verification_system",
            severity=risk_level,
            result=result,
            details=details,
            user_id=user_id,
            response_time=response_time
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self._lock:
            return self.metrics.to_dict()
    
    def get_component_metrics(self, component: str) -> Dict[str, Any]:
        """Get metrics for a specific component"""
        with self._lock:
            if component not in self.metrics.components:
                return {}
            
            # Filter events for this component
            component_events = [e for e in self.events if e.component == component]
            
            # Calculate component-specific metrics
            result = {
                "total_events": len(component_events),
                "results": dict(self.metrics.components[component]),
                "severity_distribution": Counter(e.severity for e in component_events),
                "event_types": Counter(e.event_type for e in component_events)
            }
            
            # Calculate average response time if available
            response_times = [e.details.get("response_time", 0) for e in component_events 
                             if e.details and "response_time" in e.details]
            if response_times:
                result["avg_response_time"] = sum(response_times) / len(response_times)
            
            return result
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self.metrics = SecurityMetrics()
            self.events = []
            self.current_session_id = str(uuid.uuid4())
    
    def generate_visualizations(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Generate visualizations of security metrics
        
        Args:
            output_dir: Directory to save visualizations
            
        Returns:
            Dictionary mapping visualization names to file paths
        """
        if not self.enable_visualization:
            return {}
        
        if output_dir is None:
            output_dir = os.path.join(self.metrics_dir, "visualizations")
        
        os.makedirs(output_dir, exist_ok=True)
        
        visualization_paths = {}
        
        with self._lock:
            # Convert events to DataFrame for easier analysis
            events_data = [e.to_dict() for e in self.events]
            if not events_data:
                return {}
            
            df = pd.DataFrame(events_data)
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            
            # 1. Security Events by Result
            fig, ax = plt.subplots(figsize=(10, 6))
            result_counts = Counter(e.result for e in self.events)
            ax.bar(result_counts.keys(), result_counts.values(), color=["red", "green", "orange"])
            ax.set_title("Security Events by Result")
            ax.set_xlabel("Result")
            ax.set_ylabel("Count")
            
            result_path = os.path.join(output_dir, "events_by_result.png")
            fig.savefig(result_path)
            visualization_paths["events_by_result"] = result_path
            plt.close(fig)
            
            # 2. Events by Component
            fig, ax = plt.subplots(figsize=(10, 6))
            component_counts = Counter(e.component for e in self.events)
            ax.bar(component_counts.keys(), component_counts.values())
            ax.set_title("Events by Security Component")
            ax.set_xlabel("Component")
            ax.set_ylabel("Count")
            
            component_path = os.path.join(output_dir, "events_by_component.png")
            fig.savefig(component_path)
            visualization_paths["events_by_component"] = component_path
            plt.close(fig)
            
            # 3. Events by Severity
            fig, ax = plt.subplots(figsize=(10, 6))
            severity_order = ["low", "medium", "high", "critical"]
            severity_counts = {s: self.metrics.severity_counts.get(s, 0) for s in severity_order}
            colors = ["green", "yellow", "orange", "red"]
            ax.bar(severity_counts.keys(), severity_counts.values(), color=colors)
            ax.set_title("Events by Severity")
            ax.set_xlabel("Severity")
            ax.set_ylabel("Count")
            
            severity_path = os.path.join(output_dir, "events_by_severity.png")
            fig.savefig(severity_path)
            visualization_paths["events_by_severity"] = severity_path
            plt.close(fig)
            
            # 4. Events Over Time
            if len(df) > 1:  # Need at least 2 points for a line chart
                fig, ax = plt.subplots(figsize=(12, 6))
                df.set_index("datetime").resample("1H").size().plot(ax=ax)
                ax.set_title("Security Events Over Time")
                ax.set_xlabel("Time")
                ax.set_ylabel("Number of Events")
                
                time_path = os.path.join(output_dir, "events_over_time.png")
                fig.savefig(time_path)
                visualization_paths["events_over_time"] = time_path
                plt.close(fig)
            
            # 5. Component Performance Comparison
            if self.metrics.response_times:
                component_response_times = defaultdict(list)
                for e in self.events:
                    if e.details and "response_time" in e.details:
                        component_response_times[e.component].append(e.details["response_time"])
                
                if len(component_response_times) > 1:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    data = []
                    labels = []
                    for component, times in component_response_times.items():
                        if times:
                            data.append(times)
                            labels.append(component)
                    
                    if data:
                        ax.boxplot(data, labels=labels)
                        ax.set_title("Component Response Time Comparison")
                        ax.set_xlabel("Component")
                        ax.set_ylabel("Response Time (s)")
                        
                        perf_path = os.path.join(output_dir, "component_performance.png")
                        fig.savefig(perf_path)
                        visualization_paths["component_performance"] = perf_path
                        plt.close(fig)
        
        return visualization_paths
    
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics to a file
        
        Args:
            format: Export format (json or csv)
            
        Returns:
            Path to the exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            export_path = os.path.join(self.metrics_dir, f"security_metrics_{timestamp}.json")
            
            with open(export_path, "w") as f:
                json.dump({
                    "metrics": self.metrics.to_dict(),
                    "events": [e.to_dict() for e in self.events]
                }, f, indent=2)
                
        elif format.lower() == "csv":
            export_path = os.path.join(self.metrics_dir, f"security_metrics_{timestamp}.csv")
            
            # Convert events to DataFrame
            events_data = [e.to_dict() for e in self.events]
            if events_data:
                df = pd.DataFrame(events_data)
                # Flatten details column
                for i, row in df.iterrows():
                    if row["details"]:
                        for k, v in row["details"].items():
                            df.loc[i, f"details_{k}"] = v
                df.drop("details", axis=1, inplace=True)
                df.to_csv(export_path, index=False)
            else:
                # Create empty CSV with headers
                with open(export_path, "w") as f:
                    f.write("event_id,timestamp,event_type,component,severity,result,user_id,session_id\n")
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return export_path
    
    def _persist_event(self, event: SecurityEvent) -> None:
        """Persist an event to disk"""
        if not self.enable_persistence:
            return
        
        # Create events directory if it doesn't exist
        events_dir = os.path.join(self.metrics_dir, "events")
        os.makedirs(events_dir, exist_ok=True)
        
        # Save event to JSON file
        event_path = os.path.join(events_dir, f"{event.event_id}.json")
        with open(event_path, "w") as f:
            json.dump(event.to_dict(), f)
        
        # Update metrics summary
        metrics_path = os.path.join(self.metrics_dir, "metrics_summary.json")
        with open(metrics_path, "w") as f:
            json.dump(self.metrics.to_dict(), f)
    
    def load_persisted_metrics(self) -> None:
        """Load persisted metrics from disk"""
        if not self.enable_persistence:
            return
        
        # Check if metrics directory exists
        if not os.path.exists(self.metrics_dir):
            return
        
        # Load events
        events_dir = os.path.join(self.metrics_dir, "events")
        if os.path.exists(events_dir):
            event_files = [f for f in os.listdir(events_dir) if f.endswith(".json")]
            
            events = []
            for event_file in event_files:
                try:
                    with open(os.path.join(events_dir, event_file), "r") as f:
                        event_data = json.load(f)
                        event = SecurityEvent(**event_data)
                        events.append(event)
                except Exception as e:
                    self.logger.error("Error loading event %s: %s", event_file, e)
            
            # Sort events by timestamp
            events.sort(key=lambda e: e.timestamp)
            
            # Rebuild metrics from events
            self.events = events
            self._rebuild_metrics_from_events()
    
    def _rebuild_metrics_from_events(self) -> None:
        """Rebuild metrics from events"""
        metrics = SecurityMetrics()
        
        for event in self.events:
            metrics.total_events += 1
            
            if event.result == "blocked":
                metrics.blocked_events += 1
            elif event.result == "allowed":
                metrics.allowed_events += 1
            elif event.result == "warning":
                metrics.warning_events += 1
            
            # Update component metrics
            if event.component not in metrics.components:
                metrics.components[event.component] = Counter()
            metrics.components[event.component][event.result] += 1
            
            # Update severity counts
            metrics.severity_counts[event.severity] += 1
            
            # Update response time metrics
            if event.details and "response_time" in event.details:
                metrics.response_times.append(event.details["response_time"])
            
            # Update hourly metrics
            hour = datetime.fromtimestamp(event.timestamp).hour
            metrics.hourly_events[hour] += 1
        
        self.metrics = metrics
    
    def get_telemetry_status(self) -> Dict[str, Any]:
        """
        Get the status of telemetry integration
        
        Returns:
            Dictionary with telemetry status
        """
        status = {
            "telemetry_available": TELEMETRY_AVAILABLE,
            "telemetry_enabled": self.enable_telemetry,
            "telemetry_manager_initialized": self.telemetry_manager is not None
        }
        
        # Add metrics snapshot if telemetry is enabled
        if self.enable_telemetry and self.telemetry_manager:
            try:
                status["metrics_snapshot"] = self.telemetry_manager.create_metrics_snapshot()
            except Exception as e:
                status["metrics_error"] = str(e)
                
        return status
