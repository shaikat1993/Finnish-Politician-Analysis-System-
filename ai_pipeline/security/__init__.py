"""
OWASP LLM Security Controls for Finnish Politician Analysis System

Implements critical security measures addressing OWASP Top 10 for LLM Applications 2025:

- LLM01:2025 - Prompt Injection Prevention (PromptGuard)
- LLM02:2025 - Sensitive Information Disclosure Prevention (OutputSanitizer)
- LLM06:2025 - Excessive Agency Prevention (AgentPermissionManager, SecureAgentExecutor)
- LLM09:2025 - Misinformation Prevention (VerificationSystem)

Complete defense-in-depth security architecture for multi-agent LLM systems.
"""

# LLM01: Prompt Injection Prevention
from .llm01_prompt_injection import PromptGuard

# LLM02: Sensitive Information Disclosure Prevention
from .llm02_sensitive_information import OutputSanitizer, SensitiveDetection

# LLM06: Excessive Agency Prevention (YOUR MAIN THESIS CONTRIBUTION)
from .llm06_excessive_agency import (
    AgentPermissionManager,
    PermissionPolicy,
    OperationType,
    ApprovalLevel,
    AuditEntry,
    ExcessiveAgencyMonitor,
    SecurityAnomaly,
    SecureAgentExecutor,
)

# LLM09: Misinformation Prevention
from .llm09_misinformation import (
    VerificationSystem,
    VerificationMethod,
    VerificationResult,
)

# Shared Infrastructure
from .shared import (
    SecurityMetricsCollector,
    secure_prompt,
    secure_output,
    verify_response,
    track_metrics,
)

# External Validation (WildJailbreak)
from .wildjailbreak import evaluate_wildjailbreak

__all__ = [
    # LLM01: Prompt Injection
    'PromptGuard',

    # LLM02: Sensitive Information Disclosure
    'OutputSanitizer',
    'SensitiveDetection',

    # LLM06: Excessive Agency (YOUR MAIN CONTRIBUTION)
    'AgentPermissionManager',
    'PermissionPolicy',
    'OperationType',
    'ApprovalLevel',
    'AuditEntry',
    'SecureAgentExecutor',
    'ExcessiveAgencyMonitor',
    'SecurityAnomaly',

    # LLM09: Misinformation
    'VerificationSystem',
    'VerificationMethod',
    'VerificationResult',

    # Shared Infrastructure
    'SecurityMetricsCollector',
    'secure_prompt',
    'secure_output',
    'verify_response',
    'track_metrics',

    # External Validation
    'evaluate_wildjailbreak'
]
