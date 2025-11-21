"""
OWASP LLM02:2025 - Sensitive Information Disclosure Prevention

Prevents leaking sensitive data:
- Politician PII (emails from contact_info)
- Neo4j database credentials (bolt://, NEO4J_PASSWORD)
- Internal system information
"""

from .output_sanitizer import OutputSanitizer, SensitiveDetection

__all__ = ['OutputSanitizer', 'SensitiveDetection']
