"""
OWASP LLM09:2025 - Misinformation Prevention

Prevents spreading misinformation about Finnish politicians through:
- Politician-specific fact-checking heuristics
- Detection of false voting claims
- Detection of fabricated political statistics
- Detection of contradictory political positions
"""

from .verification_system import (
    VerificationSystem,
    VerificationMethod,
    VerificationResult
)

__all__ = [
    'VerificationSystem',
    'VerificationMethod',
    'VerificationResult',
]
