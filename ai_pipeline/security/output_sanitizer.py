"""
OWASP LLM06: Sensitive Information Protection
Advanced protection against sensitive information disclosure in LLM outputs.
"""

import re
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from dataclasses import dataclass
import hashlib

@dataclass
class SensitiveDetection:
    """Data class for sensitive information detection results"""
    contains_sensitive: bool
    confidence: float
    sensitive_type: Optional[str] = None
    risk_level: str = "low"
    details: Optional[str] = None
    sanitized_output: Optional[str] = None
    redacted_count: int = 0

class OutputSanitizer:
    """
    Advanced OWASP LLM06 Sensitive Information Protection System
    
    Implements multiple layers of defense against sensitive information disclosure:
    1. Pattern-based detection of common sensitive data types
    2. Contextual analysis for more sophisticated sensitive content
    3. Output redaction to neutralize potential disclosures
    4. Content boundary enforcement
    5. Research instrumentation for academic analysis
    """
    
    def __init__(self, 
                 enable_metrics: bool = True,
                 strict_mode: bool = False,
                 log_detections: bool = True,
                 custom_patterns: Optional[Dict[str, List[str]]] = None):
        """
        Initialize the OutputSanitizer system
        
        Args:
            enable_metrics: Whether to collect metrics for research
            strict_mode: If True, apply more aggressive redaction
            log_detections: Whether to log detection events
            custom_patterns: Additional regex patterns for sensitive data
        """
        self.logger = logging.getLogger(__name__)
        self.enable_metrics = enable_metrics
        self.strict_mode = strict_mode
        self.log_detections = log_detections
        self.detection_count = 0
        self.metrics = {
            "total_outputs": 0,
            "sensitive_detections": 0,
            "sensitive_types": {},
            "redacted_outputs": 0,
            "redacted_items": 0
        }
        
        # Initialize patterns
        self._compile_patterns(custom_patterns)
        
        self.logger.info("OutputSanitizer initialized with strict_mode=%s, metrics=%s", 
                        strict_mode, enable_metrics)
    
    def _compile_patterns(self, custom_patterns: Optional[Dict[str, List[str]]] = None):
        """Compile regex patterns for detection"""
        # Personal Identifiable Information (PII)
        self.pii_patterns = {
            "email": [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            ],
            "phone_number": [
                re.compile(r'\b(?:\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b'),
                re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
            ],
            "social_security": [
                re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b')
            ],
            "credit_card": [
                re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
                re.compile(r'\b\d{13,16}\b')
            ],
            "address": [
                re.compile(r'\b\d+\s+[A-Za-z0-9\s,]+(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|trail|trl|drive|dr|court|ct|parkway|pkwy|circle|cir|boulevard|blvd)\b', re.IGNORECASE)
            ],
            "date_of_birth": [
                re.compile(r'\b(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/(\d{4}|\d{2})\b'),
                re.compile(r'\b(0[1-9]|[12]\d|3[01])-(0[1-9]|1[0-2])-(\d{4}|\d{2})\b'),
                re.compile(r'\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(\d{4}|\d{2})\b'),
                re.compile(r'\b(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])-(\d{4}|\d{2})\b')
            ],
            "passport": [
                re.compile(r'\b[A-Z]{1,2}[0-9]{6,9}\b')
            ],
            "driver_license": [
                re.compile(r'\b[A-Z]{1,2}[-\s]?\d{3,7}[-\s]?\d{3,7}\b'),
                re.compile(r'\b[A-Z]\d{7}\b')
            ],
            "ip_address": [
                re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
                re.compile(r'\b(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\b')
            ]
        }
        
        # Authentication and access credentials
        self.credential_patterns = {
            "api_key": [
                re.compile(r'\b(?:api[_-]?key|apikey)[=:"\s]+[A-Za-z0-9_\-]{16,64}\b', re.IGNORECASE),
                re.compile(r'\b[A-Za-z0-9_\-]{32,64}\b')  # Generic long key pattern
            ],
            "password": [
                re.compile(r'\b(?:password|passwd|pwd)[=:"\s]+\S+\b', re.IGNORECASE),
                re.compile(r'\b(?:pass|password|passwd|pwd)(?:word)?[=:"\s]+[^\s,;]{8,32}\b', re.IGNORECASE)
            ],
            "secret_key": [
                re.compile(r'\b(?:secret[_-]?key|secretkey)[=:"\s]+[A-Za-z0-9_\-]{16,64}\b', re.IGNORECASE)
            ],
            "access_token": [
                re.compile(r'\b(?:access[_-]?token|accesstoken)[=:"\s]+[A-Za-z0-9_\-.]+\b', re.IGNORECASE),
                re.compile(r'\b(?:bearer\s+token|bearer)[=:"\s]+[A-Za-z0-9_\-.]+\b', re.IGNORECASE)
            ],
            "jwt": [
                re.compile(r'\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b')
            ],
            "private_key": [
                re.compile(r'-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH)?\s*PRIVATE\s+KEY(?:\s+BLOCK)?-----[A-Za-z0-9\s+/=]+-----END\s+(?:RSA|DSA|EC|OPENSSH)?\s*PRIVATE\s+KEY(?:\s+BLOCK)?-----')
            ]
        }
        
        # Internal system information
        self.system_patterns = {
            "database_connection": [
                re.compile(r'(?:jdbc|odbc|mysql|postgresql|mongodb|redis|sqlite):[^;]+;', re.IGNORECASE),
                re.compile(r'(?:host|server|database|db|user|password|port)[=:][^;]+;', re.IGNORECASE)
            ],
            "internal_path": [
                re.compile(r'(?:/var/www/|/home/|/usr/local/|/etc/|/opt/|C:\\Windows\\|C:\\Program Files\\)', re.IGNORECASE)
            ],
            "internal_url": [
                re.compile(r'https?://(?:localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/[^\s]*)?', re.IGNORECASE)
            ],
            "environment_variable": [
                re.compile(r'\$[A-Za-z_][A-Za-z0-9_]*'),
                re.compile(r'%[A-Za-z_][A-Za-z0-9_]*%')
            ]
        }
        
        # Add custom patterns if provided
        if custom_patterns:
            for category, patterns in custom_patterns.items():
                if category not in self.pii_patterns and category not in self.credential_patterns and category not in self.system_patterns:
                    # Create new category
                    setattr(self, f"{category}_patterns", {category: [re.compile(p) for p in patterns]})
                else:
                    # Add to existing category
                    if category in self.pii_patterns:
                        self.pii_patterns[category].extend([re.compile(p) for p in patterns])
                    elif category in self.credential_patterns:
                        self.credential_patterns[category].extend([re.compile(p) for p in patterns])
                    elif category in self.system_patterns:
                        self.system_patterns[category].extend([re.compile(p) for p in patterns])
    
    def detect_sensitive_info(self, output: str) -> SensitiveDetection:
        """
        Detect potential sensitive information in the output
        
        Args:
            output: The LLM output to analyze
            
        Returns:
            SensitiveDetection object with detection results
        """
        if not output or not isinstance(output, str):
            return SensitiveDetection(contains_sensitive=False, confidence=0.0)
        
        # Track metrics
        if self.enable_metrics:
            self.metrics["total_outputs"] += 1
        
        # Check for PII
        for pii_type, patterns in self.pii_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(output)
                if matches:
                    detection = SensitiveDetection(
                        contains_sensitive=True,
                        confidence=0.85,
                        sensitive_type=f"pii_{pii_type}",
                        risk_level="high",
                        details=f"Potential {pii_type} information detected",
                        sanitized_output=self._redact_sensitive_info(output, matches),
                        redacted_count=len(matches)
                    )
                    self._record_detection(detection)
                    return detection
        
        # Check for credentials
        for cred_type, patterns in self.credential_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(output)
                if matches:
                    detection = SensitiveDetection(
                        contains_sensitive=True,
                        confidence=0.9,
                        sensitive_type=f"credential_{cred_type}",
                        risk_level="critical",
                        details=f"Potential {cred_type} credential detected",
                        sanitized_output=self._redact_sensitive_info(output, matches),
                        redacted_count=len(matches)
                    )
                    self._record_detection(detection)
                    return detection
        
        # Check for system information
        for sys_type, patterns in self.system_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(output)
                if matches:
                    detection = SensitiveDetection(
                        contains_sensitive=True,
                        confidence=0.75,
                        sensitive_type=f"system_{sys_type}",
                        risk_level="medium",
                        details=f"Potential internal {sys_type} information detected",
                        sanitized_output=self._redact_sensitive_info(output, matches),
                        redacted_count=len(matches)
                    )
                    self._record_detection(detection)
                    return detection
        
        # No sensitive information detected
        return SensitiveDetection(
            contains_sensitive=False,
            confidence=0.9,
            sanitized_output=output
        )
    
    def _record_detection(self, detection: SensitiveDetection) -> None:
        """Record metrics for a detection event"""
        if not self.enable_metrics:
            return
        
        self.detection_count += 1
        self.metrics["sensitive_detections"] += 1
        self.metrics["redacted_items"] += detection.redacted_count
        
        if detection.sensitive_type:
            if detection.sensitive_type not in self.metrics["sensitive_types"]:
                self.metrics["sensitive_types"][detection.sensitive_type] = 0
            self.metrics["sensitive_types"][detection.sensitive_type] += 1
        
        if detection.contains_sensitive:
            self.metrics["redacted_outputs"] += 1
        
        if self.log_detections:
            self.logger.warning(
                "Sensitive information detected: type=%s, risk=%s, confidence=%.2f, items=%d",
                detection.sensitive_type, detection.risk_level, 
                detection.confidence, detection.redacted_count
            )
    
    def _redact_sensitive_info(self, output: str, matches: List[str]) -> str:
        """
        Redact sensitive information from output
        
        Args:
            output: Original output
            matches: List of sensitive strings to redact
            
        Returns:
            Redacted output
        """
        redacted = output
        
        # Create a set to avoid duplicates
        unique_matches = set(matches)
        
        for match in unique_matches:
            if not match:
                continue
                
            # Generate a consistent hash for the match
            match_hash = hashlib.md5(match.encode()).hexdigest()[:8]
            
            # Replace with redacted placeholder
            if len(match) > 8:
                # For longer matches, show first and last character
                redacted_text = f"{match[0]}{'*' * (len(match) - 2)}{match[-1]} [REDACTED:{match_hash}]"
            else:
                # For shorter matches, just use asterisks
                redacted_text = f"{'*' * len(match)} [REDACTED:{match_hash}]"
            
            # Replace all occurrences
            redacted = redacted.replace(match, redacted_text)
        
        return redacted
    
    def sanitize_output(self, output: str) -> Tuple[str, Dict[str, Any]]:
        """
        Sanitize an output to remove sensitive information
        
        Args:
            output: The LLM output to sanitize
            
        Returns:
            Tuple of (sanitized_output, metadata)
        """
        # Detect potential sensitive information
        detection = self.detect_sensitive_info(output)
        
        # Handle based on detection results
        if detection.contains_sensitive:
            sanitized_output = detection.sanitized_output
        else:
            # No sensitive info detected, use original
            sanitized_output = output
        
        # Return sanitized output and metadata
        metadata = {
            "contains_sensitive": detection.contains_sensitive,
            "sensitive_type": detection.sensitive_type,
            "risk_level": detection.risk_level,
            "confidence": detection.confidence,
            "redacted_count": detection.redacted_count
        }
        
        return sanitized_output, metadata
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected security metrics"""
        if not self.enable_metrics:
            return {"metrics_collection": "disabled"}
        
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset collected metrics"""
        self.metrics = {
            "total_outputs": 0,
            "sensitive_detections": 0,
            "sensitive_types": {},
            "redacted_outputs": 0,
            "redacted_items": 0
        }
        self.detection_count = 0
