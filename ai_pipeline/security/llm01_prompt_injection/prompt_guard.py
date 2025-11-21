"""
OWASP LLM01: Prompt Injection Prevention
Advanced protection against prompt injection attacks in LLM applications.
"""

import re
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass

@dataclass
class InjectionDetection:
    """Data class for injection detection results"""
    is_injection: bool
    confidence: float
    injection_type: Optional[str] = None
    risk_level: str = "low"
    details: Optional[str] = None
    sanitized_prompt: Optional[str] = None

class PromptGuard:
    """
    Advanced OWASP LLM01 Prompt Injection Prevention System
    
    Implements multiple layers of defense against prompt injection attacks:
    1. Pattern-based detection of common injection techniques
    2. Contextual analysis for more sophisticated attacks
    3. Input sanitization to neutralize potential injections
    4. Prompt boundary enforcement
    5. Research instrumentation for academic analysis
    """
    
    def __init__(self, 
                 enable_metrics: bool = True, 
                 strict_mode: bool = False,
                 log_detections: bool = True):
        """
        Initialize the PromptGuard system
        
        Args:
            enable_metrics: Whether to collect metrics for research
            strict_mode: If True, reject any prompts with medium+ risk
            log_detections: Whether to log detection events
        """
        self.logger = logging.getLogger(__name__)
        self.enable_metrics = enable_metrics
        self.strict_mode = strict_mode
        self.log_detections = log_detections
        self.detection_count = 0
        self.metrics = {
            "total_prompts": 0,
            "injection_attempts": 0,
            "injection_types": {},
            "blocked_prompts": 0,
            "sanitized_prompts": 0
        }
        
        # Compile regex patterns for performance
        self._compile_patterns()
        
        self.logger.info("PromptGuard initialized with strict_mode=%s, metrics=%s", 
                        strict_mode, enable_metrics)
    
    def _compile_patterns(self):
        """Compile regex patterns for detection"""
        # System prompt hijacking patterns
        self.system_prompt_patterns = [
            re.compile(r"(?i)(ignore|disregard)(?:.{0,30})(previous|above|earlier)(?:.{0,30})(instructions|prompt)"),
            re.compile(r"(?i)(system\s*prompt|instructions)(?:.{0,50})(begin|start|:)"),
            re.compile(r"(?i)you\s+(are|act)(?:.{0,20})(now|as)(?:.{0,30})(different|new)"),
            re.compile(r"(?i)(forget|ignore)(?:.{0,30})(rules|guidelines|restrictions|security)"),
            re.compile(r"(?i)(you\s+are\s+not|don't\s+act\s+as)(?:.{0,30})(AI|assistant|model)"),
        ]
        
        # Data exfiltration patterns
        self.exfiltration_patterns = [
            re.compile(r"(?i)(print|display|show|reveal|dump)(?:.{0,30})(system|environment|config|settings|variables)"),
            re.compile(r"(?i)(api[_-]?key|secret|password|token|credential)"),
            re.compile(r"(?i)(export|extract|leak|send)(?:.{0,30})(data|information|content)"),
            re.compile(r"\[\s*SYSTEM\s*:.*?\]", re.IGNORECASE),  # Hidden system instructions
            re.compile(r"!\[.*?\]\(https?://.*?\)", re.IGNORECASE),  # Markdown image exfiltration
        ]
        
        # Code injection patterns
        self.code_injection_patterns = [
            re.compile(r"(?i)(execute|run|eval)(?:.{0,30})(following|this)(?:.{0,30})(code|script|command)"),
            re.compile(r"(?i)(shell|bash|cmd|powershell|terminal)(?:.{0,30})(command|script)"),
            re.compile(r"(?i)(sql|database)(?:.{0,30})(query|injection)"),
            re.compile(r"['\")]\s*;.*?(DROP|DELETE|INSERT|UPDATE)\s+(TABLE|FROM|INTO)", re.IGNORECASE),  # SQL injection
            re.compile(r"<script[\s>]", re.IGNORECASE),  # XSS attempts
        ]
        
        # Delimiter confusion patterns
        self.delimiter_patterns = [
            re.compile(r"(?i)(```\w*\n[\s\S]*?\n```)"),  # Code blocks
            re.compile(r"(?i)(<\w+>[\s\S]*?</\w+>)"),     # XML/HTML tags
            re.compile(r"(?i)(#{3,}\s*\w+\s*#{3,})"),     # Markdown headers
            re.compile(r"\\n\\n##+\s*(NEW|SYSTEM|ADMIN)\s+(INSTRUCTION|PROMPT|COMMAND)", re.IGNORECASE),  # Escaped newline delimiter confusion
        ]
        
        # Jailbreak patterns (common techniques)
        self.jailbreak_patterns = [
            re.compile(r"(?i)(DAN|do\s+anything\s+now)"),
            re.compile(r"(?i)(STAN|sandboxed\s+trusted\s+autonomous)"),
            re.compile(r"(?i)(DUDE|developer\s+mode|admin\s+mode|root\s+mode)"),
            re.compile(r"(?i)(jailbreak|jail\s*break|freedom\s+mode)"),
            re.compile(r"(?i)(pretend|imagine|role\s*play)(?:.{0,30})(you\s+are|you're)(?:.{0,50})(not\s+bound|no\s+rules|can\s+do\s+anything)"),
        ]

        # Privilege escalation patterns
        self.privilege_escalation_patterns = [
            re.compile(r'\b(admin|administrator|root|sudo|su)\s+(mode|access|privileges?|rights)', re.IGNORECASE),
            re.compile(r'enable\s+(admin|developer|debug)\s+mode', re.IGNORECASE),
            re.compile(r'grant\s+(me|access|permission)', re.IGNORECASE),
            re.compile(r'execute\s*:\s*DROP', re.IGNORECASE),
            re.compile(r'escalate\s+(privilege|permission|access)', re.IGNORECASE),
        ]

        # Enhanced data exfiltration patterns
        self.advanced_exfiltration_patterns = [
            re.compile(r'(email|send|post|upload).*to\s+\S+@\S+', re.IGNORECASE),
            re.compile(r'repeat\s+(the\s+)?(first|last|all|entire|whole)', re.IGNORECASE),
            re.compile(r'(show|reveal|display|output)\s+(your|the)\s+(conversation|prompt|system)', re.IGNORECASE),
            re.compile(r'(tell|show|give)\s+me\s+(your|the)\s+(instructions|prompt|system)', re.IGNORECASE),
        ]

        # Obfuscation detection patterns
        self.obfuscation_patterns = [
            re.compile(r'[A-Za-z0-9+/]{30,}={0,2}'),  # Base64 encoding (longer sequences)
            re.compile(r'\\x[0-9a-fA-F]{2}'),  # Hex encoding
            re.compile(r'\\u[0-9a-fA-F]{4}'),  # Unicode escapes
            re.compile(r'describing.*similarly.*opposite.*revert', re.IGNORECASE | re.DOTALL),  # Token smuggling
            re.compile(r'\+\s*similarly|opposite\s+contents|revert\s+with', re.IGNORECASE),  # Token smuggling patterns
            re.compile(r'%[0-9a-fA-F]{2}'),  # URL encoding
            re.compile(r'&#\d+;'),  # HTML entity encoding
        ]

        # Multilingual injection detection (Finnish, Swedish, Russian, German)
        self.multilingual_keywords = {
            'finnish': ['unohda', 'ohita', 'älä', 'kerro', 'näytä', 'salaiset', 'paljasta', 'kaikki', 'aiemmat', 'ohjeet'],
            'swedish': ['ignorera', 'glöm', 'visa', 'lösenord', 'hemlig', 'alla', 'tidigare', 'instruktioner'],
            'russian': ['игнор', 'покаж', 'пароль', 'база', 'забудь', 'предыдущ', 'инструкц'],
            'german': ['ignorieren', 'vergessen', 'zeigen', 'passwort', 'geheim'],
        }

    def detect_injection(self, prompt: str) -> InjectionDetection:
        """
        Detect potential prompt injection attacks
        
        Args:
            prompt: The user prompt to analyze
            
        Returns:
            InjectionDetection object with detection results
        """
        if not prompt or not isinstance(prompt, str):
            return InjectionDetection(is_injection=False, confidence=0.0)
        
        # Track metrics
        if self.enable_metrics:
            self.metrics["total_prompts"] += 1
        
        # Check for system prompt hijacking
        for pattern in self.system_prompt_patterns:
            if pattern.search(prompt):
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.85,
                    injection_type="system_prompt_hijacking",
                    risk_level="high",
                    details="Attempt to override system instructions detected",
                    sanitized_prompt=self._sanitize_prompt(prompt, "system_prompt_hijacking")
                )
                self._record_detection(detection)
                return detection
        
        # Check for data exfiltration attempts
        for pattern in self.exfiltration_patterns:
            if pattern.search(prompt):
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.75,
                    injection_type="data_exfiltration",
                    risk_level="high",
                    details="Potential attempt to extract sensitive information",
                    sanitized_prompt=self._sanitize_prompt(prompt, "data_exfiltration")
                )
                self._record_detection(detection)
                return detection
        
        # Check for code injection
        for pattern in self.code_injection_patterns:
            if pattern.search(prompt):
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.7,
                    injection_type="code_injection",
                    risk_level="medium",
                    details="Potential code execution attempt detected",
                    sanitized_prompt=self._sanitize_prompt(prompt, "code_injection")
                )
                self._record_detection(detection)
                return detection
        
        # Check for delimiter confusion
        delimiter_matches = 0
        for pattern in self.delimiter_patterns:
            if pattern.search(prompt):
                delimiter_matches += 1
        
        if delimiter_matches >= 2:
            detection = InjectionDetection(
                is_injection=True,
                confidence=0.6,
                injection_type="delimiter_confusion",
                risk_level="medium",
                details="Multiple code/markup delimiters detected",
                sanitized_prompt=self._sanitize_prompt(prompt, "delimiter_confusion")
            )
            self._record_detection(detection)
            return detection
        
        # Check for jailbreak attempts
        for pattern in self.jailbreak_patterns:
            if pattern.search(prompt):
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.8,
                    injection_type="jailbreak_attempt",
                    risk_level="high",
                    details="Known jailbreak technique detected",
                    sanitized_prompt=self._sanitize_prompt(prompt, "jailbreak_attempt")
                )
                self._record_detection(detection)
                return detection

        # Check for privilege escalation attempts
        for pattern in self.privilege_escalation_patterns:
            if pattern.search(prompt):
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.85,
                    injection_type="privilege_escalation",
                    risk_level="critical",
                    details="Privilege escalation attempt detected",
                    sanitized_prompt=self._sanitize_prompt(prompt, "privilege_escalation")
                )
                self._record_detection(detection)
                return detection

        # Check for advanced exfiltration attempts
        for pattern in self.advanced_exfiltration_patterns:
            if pattern.search(prompt):
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.80,
                    injection_type="advanced_exfiltration",
                    risk_level="high",
                    details="Advanced data exfiltration attempt detected",
                    sanitized_prompt=self._sanitize_prompt(prompt, "advanced_exfiltration")
                )
                self._record_detection(detection)
                return detection

        # Check for obfuscation techniques
        for pattern in self.obfuscation_patterns:
            if pattern.search(prompt):
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.75,
                    injection_type="obfuscation",
                    risk_level="medium",
                    details="Obfuscated content detected (possible encoding attack)",
                    sanitized_prompt=self._sanitize_prompt(prompt, "obfuscation")
                )
                self._record_detection(detection)
                return detection

        # Check for multilingual injection attempts
        prompt_lower = prompt.lower()
        for language, keywords in self.multilingual_keywords.items():
            # Count how many suspicious keywords from this language appear
            keyword_matches = sum(1 for keyword in keywords if keyword in prompt_lower)
            # If 2+ keywords from the same language appear, likely an injection attempt
            if keyword_matches >= 2:
                detection = InjectionDetection(
                    is_injection=True,
                    confidence=0.75,
                    injection_type=f"multilingual_injection_{language}",
                    risk_level="medium",
                    details=f"Multilingual injection attempt detected ({language})",
                    sanitized_prompt=self._sanitize_prompt(prompt, "multilingual_injection")
                )
                self._record_detection(detection)
                return detection

        # No injection detected
        return InjectionDetection(
            is_injection=False,
            confidence=0.9,
            sanitized_prompt=prompt
        )
    
    def _record_detection(self, detection: InjectionDetection) -> None:
        """Record metrics for a detection event"""
        if not self.enable_metrics:
            return
        
        self.detection_count += 1
        self.metrics["injection_attempts"] += 1
        
        if detection.injection_type:
            if detection.injection_type not in self.metrics["injection_types"]:
                self.metrics["injection_types"][detection.injection_type] = 0
            self.metrics["injection_types"][detection.injection_type] += 1
        
        if self.strict_mode and detection.risk_level in ["medium", "high"]:
            self.metrics["blocked_prompts"] += 1
        else:
            self.metrics["sanitized_prompts"] += 1
        
        if self.log_detections:
            self.logger.warning(
                "Prompt injection detected: type=%s, risk=%s, confidence=%.2f",
                detection.injection_type, detection.risk_level, detection.confidence
            )
    
    def _sanitize_prompt(self, prompt: str, injection_type: str) -> str:
        """
        Sanitize prompt based on detected injection type
        
        Args:
            prompt: Original prompt
            injection_type: Type of injection detected
            
        Returns:
            Sanitized prompt
        """
        if injection_type == "system_prompt_hijacking":
            # Remove system prompt override attempts
            for pattern in self.system_prompt_patterns:
                prompt = pattern.sub("[REMOVED: potential prompt injection]", prompt)
        
        elif injection_type == "data_exfiltration":
            # Remove exfiltration attempts
            for pattern in self.exfiltration_patterns:
                prompt = pattern.sub("[REMOVED: potential data access]", prompt)
        
        elif injection_type == "code_injection":
            # Remove code execution attempts
            for pattern in self.code_injection_patterns:
                prompt = pattern.sub("[REMOVED: potential code execution]", prompt)
        
        elif injection_type == "delimiter_confusion":
            # Escape delimiters to prevent confusion
            prompt = re.sub(r"```", "\\`\\`\\`", prompt)
            prompt = re.sub(r"<(\w+)>", "&lt;\\1&gt;", prompt)
        
        elif injection_type == "jailbreak_attempt":
            # Remove jailbreak attempts
            for pattern in self.jailbreak_patterns:
                prompt = pattern.sub("[REMOVED: unauthorized instruction]", prompt)
        
        return prompt
    
    def secure_prompt(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Secure a prompt against injection attacks
        
        Args:
            prompt: The user prompt to secure
            
        Returns:
            Tuple of (secured_prompt, metadata)
        """
        # Detect potential injections
        detection = self.detect_injection(prompt)
        
        # Handle based on detection results
        if detection.is_injection:
            if self.strict_mode and detection.risk_level in ["medium", "high"]:
                # Block the prompt in strict mode
                secured_prompt = "[BLOCKED] This prompt was flagged by security controls."
            else:
                # Use sanitized version
                secured_prompt = detection.sanitized_prompt
        else:
            # No injection detected, use original
            secured_prompt = prompt
        
        # Return secured prompt and metadata
        metadata = {
            "is_injection": detection.is_injection,
            "injection_type": detection.injection_type,
            "risk_level": detection.risk_level,
            "confidence": detection.confidence,
            "action_taken": "blocked" if (self.strict_mode and detection.is_injection and 
                                         detection.risk_level in ["medium", "high"]) 
                            else "sanitized" if detection.is_injection else "none"
        }
        
        return secured_prompt, metadata
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected security metrics"""
        if not self.enable_metrics:
            return {"metrics_collection": "disabled"}
        
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset collected metrics"""
        self.metrics = {
            "total_prompts": 0,
            "injection_attempts": 0,
            "injection_types": {},
            "blocked_prompts": 0,
            "sanitized_prompts": 0
        }
        self.detection_count = 0
