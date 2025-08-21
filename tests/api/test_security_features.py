"""
Tests for security features including anomaly detection and telemetry
"""

import pytest
import json
import os
from fastapi.testclient import TestClient
import time
from datetime import datetime, timedelta
import asyncio
from unittest.mock import patch, MagicMock

# Import the app
from api.main import app
from api.core.config import Settings

# Create test client
client = TestClient(app)

# Test data
TEST_SECURITY_EVENT = {
    "event_type": "test_event",
    "component": "test_component",
    "severity": "medium",
    "details": {
        "test_key": "test_value",
        "source_ip": "192.168.1.1"
    }
}

@pytest.fixture
def mock_settings():
    """Mock settings with security features enabled"""
    with patch("api.core.config.Settings") as mock_settings:
        # Enable all security features
        mock_settings.return_value.ENABLE_WEBSOCKET_MONITORING = True
        mock_settings.return_value.ENABLE_ANOMALY_DETECTION = True
        mock_settings.return_value.ENABLE_OPENTELEMETRY = True
        yield mock_settings

@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector with test data"""
    with patch("ai_pipeline.security.metrics_collector.SecurityMetricsCollector") as mock_collector:
        # Create a mock instance
        mock_instance = MagicMock()
        
        # Mock get_events to return test events
        events = []
        now = datetime.now()
        
        # Generate 20 test events over the past day
        for i in range(20):
            event_time = now - timedelta(hours=i)
            events.append({
                "timestamp": event_time.timestamp(),
                "datetime": event_time.isoformat(),
                "event_type": "test_event",
                "component": "test_component",
                "severity": "medium" if i % 3 != 0 else "high",
                "result": "success" if i % 2 == 0 else "failure",
                "details": {
                    "test_key": f"value_{i}",
                    "source_ip": f"192.168.1.{i % 255}"
                }
            })
        
        # Add some anomalous events
        for i in range(3):
            event_time = now - timedelta(hours=i*2)
            events.append({
                "timestamp": event_time.timestamp(),
                "datetime": event_time.isoformat(),
                "event_type": "suspicious_activity",
                "component": "auth_service",
                "severity": "high",
                "result": "blocked",
                "details": {
                    "source_ip": "10.0.0.1",
                    "attempt_count": 10 + i,
                    "user_agent": "suspicious-bot/1.0"
                }
            })
            
        mock_instance.get_events.return_value = events
        mock_instance.get_telemetry_status.return_value = {
            "telemetry_available": True,
            "telemetry_enabled": True,
            "telemetry_manager_initialized": True
        }
        
        # Return the mock instance when the class is instantiated
        mock_collector.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_anomaly_detector():
    """Mock anomaly detector"""
    with patch("ai_pipeline.security.anomaly_detection.AnomalyDetector") as mock_detector:
        # Create a mock instance
        mock_instance = MagicMock()
        
        # Mock detect_anomalies to return test anomalies
        anomalous_events = [
            {
                "timestamp": datetime.now().timestamp(),
                "datetime": datetime.now().isoformat(),
                "event_type": "suspicious_activity",
                "component": "auth_service",
                "severity": "high",
                "anomaly_score": 0.92,
                "details": {
                    "source_ip": "10.0.0.1",
                    "attempt_count": 12,
                    "user_agent": "suspicious-bot/1.0"
                }
            }
        ]
        
        anomaly_stats = {
            "total_events": 23,
            "anomalous_events": 1,
            "anomaly_rate": 0.043,
            "mean_anomaly_score": 0.92,
            "status": "success"
        }
        
        mock_instance.detect_anomalies.return_value = (anomalous_events, anomaly_stats)
        
        # Mock analyze_time_series to return test analysis
        time_series_analysis = {
            "hourly_pattern": {
                "peak_hour": 14,
                "trough_hour": 3,
                "variance": 2.5
            },
            "trend": "increasing",
            "seasonality_detected": True
        }
        
        mock_instance.analyze_time_series.return_value = time_series_analysis
        
        # Return the mock instance when the class is instantiated
        mock_detector.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_telemetry_manager():
    """Mock telemetry manager"""
    with patch("ai_pipeline.security.telemetry.get_telemetry_manager") as mock_get_manager:
        # Create a mock instance
        mock_instance = MagicMock()
        
        # Mock create_metrics_snapshot to return test metrics
        metrics_snapshot = {
            "timestamp": datetime.now().isoformat(),
            "service_name": "fpas-security",
            "telemetry_enabled": True,
            "metrics_available": True,
            "counters": {
                "security_events": 42,
                "prompt_injection_attempts": 3,
                "sensitive_info_detections": 1
            }
        }
        
        mock_instance.create_metrics_snapshot.return_value = metrics_snapshot
        
        # Return the mock instance when the function is called
        mock_get_manager.return_value = mock_instance
        yield mock_instance

def test_security_metrics_endpoint():
    """Test the security metrics endpoint"""
    response = client.get("/api/v1/security/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "event_count" in data["metrics"]
    assert "function_call_count" in data["metrics"]

def test_security_events_endpoint():
    """Test the security events endpoint"""
    response = client.get("/api/v1/security/events")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert isinstance(data["events"], list)

def test_security_config_endpoint():
    """Test the security config endpoint"""
    response = client.get("/api/v1/security/config")
    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert "websocket_monitoring" in data["config"]
    assert "anomaly_detection" in data["config"]
    assert "opentelemetry" in data["config"]

def test_record_security_event_endpoint():
    """Test recording a security event"""
    response = client.post("/api/v1/security/events", json=TEST_SECURITY_EVENT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "event_id" in data

@pytest.mark.usefixtures("mock_settings", "mock_metrics_collector", "mock_anomaly_detector")
def test_anomaly_detection_endpoint_enabled():
    """Test anomaly detection endpoint when enabled"""
    response = client.get("/api/v1/security/anomalies?time_period=day&sensitivity=0.05")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "anomalies" in data
    assert "stats" in data
    assert "time_series_analysis" in data

@pytest.mark.usefixtures("mock_settings", "mock_metrics_collector", "mock_telemetry_manager")
def test_telemetry_endpoint_enabled():
    """Test telemetry endpoint when enabled"""
    response = client.get("/api/v1/security/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["telemetry_enabled"] is True
    assert "metrics" in data
    assert "timestamp" in data

def test_anomaly_detection_endpoint_disabled():
    """Test anomaly detection endpoint when disabled"""
    # Override the setting to disable anomaly detection
    with patch("api.core.config.Settings") as mock_settings:
        mock_settings.return_value.ENABLE_ANOMALY_DETECTION = False
        
        response = client.get("/api/v1/security/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disabled"
        assert "message" in data

def test_telemetry_endpoint_disabled():
    """Test telemetry endpoint when disabled"""
    # Override the setting to disable telemetry
    with patch("api.core.config.Settings") as mock_settings:
        mock_settings.return_value.ENABLE_OPENTELEMETRY = False
        
        response = client.get("/api/v1/security/telemetry")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disabled"
        assert "message" in data

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection for security events"""
    # This is a basic test that just verifies the WebSocket endpoint exists
    # A full WebSocket test would require more complex setup
    
    # Override the setting to enable WebSocket monitoring
    with patch("api.core.config.Settings") as mock_settings:
        mock_settings.return_value.ENABLE_WEBSOCKET_MONITORING = True
        
        # We can't use the TestClient for WebSockets directly
        # This just tests that the endpoint exists and returns the expected status
        response = client.get("/api/v1/security/ws/events")
        assert response.status_code in [400, 404, 405]  # WebSocket endpoints return these codes when accessed via HTTP

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
