"""
OWASP LLM01:2025 - Prompt Injection Prevention

Protects against prompt injection attacks in user queries to AI agents.
"""

from .prompt_guard import PromptGuard

__all__ = ['PromptGuard']
