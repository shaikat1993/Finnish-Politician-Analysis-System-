"""
OpenTelemetry integration for security metrics
Provides observability for security events and metrics
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import json
from pathlib import Path

class TelemetryManager:
    """
    OpenTelemetry integration for security metrics
    
    Provides a feature-flagged implementation that gracefully degrades
    when OpenTelemetry is not available or disabled
    """
    
    def __init__(self, 
                 service_name: str = "fpas-security",
                 enable_telemetry: bool = False,
                 log_level: int = logging.INFO):
        """
        Initialize the telemetry manager
        
        Args:
            service_name: Name of the service for telemetry
            enable_telemetry: Whether to enable OpenTelemetry integration
            log_level: Logging level
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        self.service_name = service_name
        self.enable_telemetry = enable_telemetry
        self.tracer = None
        self.meter = None
        self.metrics_exporter = None
        self.trace_exporter = None
        
        # Initialize OpenTelemetry if enabled
        if self.enable_telemetry:
            self._setup_telemetry()
        else:
            self.logger.info("OpenTelemetry integration is disabled")
    
    def _setup_telemetry(self):
        """Set up OpenTelemetry integration if available"""
        try:
            # Import OpenTelemetry modules
            from opentelemetry import trace, metrics
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            
            # Set up trace provider
            trace_provider = TracerProvider()
            trace.set_tracer_provider(trace_provider)
            
            # Set up metrics provider
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter()
            )
            metrics_provider = MeterProvider(metric_readers=[metric_reader])
            metrics.set_meter_provider(metrics_provider)
            
            # Create exporters
            self.trace_exporter = OTLPSpanExporter()
            trace_provider.add_span_processor(BatchSpanProcessor(self.trace_exporter))
            
            # Get tracer and meter
            self.tracer = trace.get_tracer(self.service_name)
            self.meter = metrics.get_meter(self.service_name)
            
            # Create counters
            self._setup_metrics()
            
            self.logger.info("OpenTelemetry integration initialized successfully")
            return True
        except ImportError:
            self.logger.warning("OpenTelemetry packages not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
            return False
        except Exception as e:
            self.logger.error("Failed to initialize OpenTelemetry: %s", str(e))
            return False
    
    def _setup_metrics(self):
        """Set up metrics counters and gauges"""
        if not self.meter:
            return
            
        try:
            # Create counters for security events
            self.security_event_counter = self.meter.create_counter(
                name="security_events",
                description="Count of security events",
                unit="1"
            )
            
            # Create counters for specific event types
            self.prompt_injection_counter = self.meter.create_counter(
                name="prompt_injection_attempts",
                description="Count of prompt injection attempts",
                unit="1"
            )
            
            self.sensitive_info_counter = self.meter.create_counter(
                name="sensitive_info_detections",
                description="Count of sensitive information detections",
                unit="1"
            )
            
            # Create histogram for response times
            self.response_time_histogram = self.meter.create_histogram(
                name="security_response_times",
                description="Response times for security checks",
                unit="ms"
            )
            
            self.logger.debug("OpenTelemetry metrics initialized")
        except Exception as e:
            self.logger.error("Failed to initialize OpenTelemetry metrics: %s", str(e))
    
    def record_security_event(self, 
                             event_type: str,
                             component: str,
                             severity: str,
                             result: str,
                             response_time: Optional[float] = None,
                             attributes: Optional[Dict[str, str]] = None) -> None:
        """
        Record a security event to OpenTelemetry
        
        Args:
            event_type: Type of security event
            component: Security component that generated the event
            severity: Severity level
            result: Result of the event
            response_time: Time taken to process the security check
            attributes: Additional attributes for the event
        """
        if not self.enable_telemetry or not self.tracer:
            return
            
        try:
            # Create attributes dictionary
            event_attributes = {
                "event_type": event_type,
                "component": component,
                "severity": severity,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add additional attributes if provided
            if attributes:
                event_attributes.update(attributes)
                
            # Record counter
            if self.security_event_counter:
                self.security_event_counter.add(1, event_attributes)
                
            # Record specific event counters
            if event_type == "prompt_injection_attempt" and self.prompt_injection_counter:
                self.prompt_injection_counter.add(1, event_attributes)
                
            if event_type == "sensitive_information_detection" and self.sensitive_info_counter:
                self.sensitive_info_counter.add(1, event_attributes)
                
            # Record response time
            if response_time is not None and self.response_time_histogram:
                self.response_time_histogram.record(response_time, event_attributes)
                
            self.logger.debug("Recorded security event to OpenTelemetry: %s", event_type)
        except Exception as e:
            self.logger.error("Failed to record security event to OpenTelemetry: %s", str(e))
    
    def start_span(self, name: str, attributes: Optional[Dict[str, str]] = None) -> Any:
        """
        Start a new span for tracing
        
        Args:
            name: Name of the span
            attributes: Attributes for the span
            
        Returns:
            Span object or None if telemetry is disabled
        """
        if not self.enable_telemetry or not self.tracer:
            return None
            
        try:
            return self.tracer.start_span(name, attributes=attributes)
        except Exception as e:
            self.logger.error("Failed to start span: %s", str(e))
            return None
    
    def end_span(self, span: Any) -> None:
        """
        End a span
        
        Args:
            span: Span object to end
        """
        if not span:
            return
            
        try:
            span.end()
        except Exception as e:
            self.logger.error("Failed to end span: %s", str(e))
    
    def create_metrics_snapshot(self) -> Dict[str, Any]:
        """
        Create a snapshot of current metrics
        
        Returns:
            Dictionary with metrics snapshot
        """
        # This is a placeholder that would normally use OpenTelemetry's metrics API
        # to get current metric values, but we'll just return a basic structure
        return {
            "timestamp": datetime.now().isoformat(),
            "service_name": self.service_name,
            "telemetry_enabled": self.enable_telemetry,
            "metrics_available": self.meter is not None
        }
    
    def shutdown(self) -> None:
        """Shutdown telemetry components"""
        if not self.enable_telemetry:
            return
            
        try:
            # Import OpenTelemetry modules
            from opentelemetry import trace, metrics
            
            # Shutdown trace provider
            trace.get_tracer_provider().shutdown()
            
            # Shutdown metrics provider
            metrics.get_meter_provider().shutdown()
            
            self.logger.info("OpenTelemetry shutdown complete")
        except ImportError:
            pass
        except Exception as e:
            self.logger.error("Error during OpenTelemetry shutdown: %s", str(e))


# Singleton instance
_telemetry_manager = None

def get_telemetry_manager(enable_telemetry: bool = False) -> TelemetryManager:
    """
    Get the singleton telemetry manager instance
    
    Args:
        enable_telemetry: Whether to enable OpenTelemetry integration
        
    Returns:
        TelemetryManager instance
    """
    global _telemetry_manager
    
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager(enable_telemetry=enable_telemetry)
        
    return _telemetry_manager
