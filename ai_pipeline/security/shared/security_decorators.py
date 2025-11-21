"""
OWASP LLM Security Decorators
Provides decorator functions for easy integration of security controls into LLM pipelines.

Implements decorators for:
- LLM01:2025 - Prompt Injection Prevention (secure_prompt)
- LLM02:2025 - Sensitive Information Disclosure Prevention (secure_output)
- LLM09:2025 - Misinformation Prevention (verify_response)
"""

import functools
import logging
from typing import Any, Callable, Dict, Optional, Tuple, Union

from ..llm01_prompt_injection import PromptGuard
from ..llm02_sensitive_information import OutputSanitizer
from ..llm09_misinformation import VerificationSystem
from .security_metrics import SecurityMetricsCollector

# Initialize logger
logger = logging.getLogger(__name__)

# Global security components
_prompt_guard = None
_output_sanitizer = None
_verification_system = None
_metrics_collector = None

def _get_prompt_guard() -> PromptGuard:
    """Get or initialize the prompt guard singleton"""
    global _prompt_guard
    if _prompt_guard is None:
        _prompt_guard = PromptGuard(enable_metrics=True)
    return _prompt_guard

def _get_output_sanitizer() -> OutputSanitizer:
    """Get or initialize the output sanitizer singleton"""
    global _output_sanitizer
    if _output_sanitizer is None:
        _output_sanitizer = OutputSanitizer(enable_metrics=True)
    return _output_sanitizer

def _get_verification_system() -> VerificationSystem:
    """Get or initialize the verification system singleton"""
    global _verification_system
    if _verification_system is None:
        _verification_system = VerificationSystem(enable_metrics=True)
    return _verification_system

def _get_metrics_collector() -> SecurityMetricsCollector:
    """Get or initialize the metrics collector singleton"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = SecurityMetricsCollector()
    return _metrics_collector

def secure_prompt(strict_mode: bool = False):
    """
    Decorator to secure prompts against injection attacks (OWASP LLM01)
    
    Args:
        strict_mode: If True, block prompts with medium+ risk
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract prompt from args or kwargs
            prompt = None
            if args and isinstance(args[0], str):
                prompt = args[0]
                args = list(args)
            elif "prompt" in kwargs:
                prompt = kwargs["prompt"]
            
            if prompt:
                # Get or initialize prompt guard
                prompt_guard = _get_prompt_guard()
                prompt_guard.strict_mode = strict_mode
                
                # Secure the prompt
                secured_prompt, metadata = prompt_guard.secure_prompt(prompt)
                
                # Log security action
                if metadata["is_injection"]:
                    action = "blocked" if metadata["action_taken"] == "blocked" else "sanitized"
                    logger.warning(
                        f"Prompt injection detected: {metadata['injection_type']} "
                        f"(risk: {metadata['risk_level']}, confidence: {metadata['confidence']:.2f}). "
                        f"Action taken: {action}"
                    )
                
                # Update args or kwargs with secured prompt
                if args and isinstance(args[0], str):
                    args[0] = secured_prompt
                    args = tuple(args)
                elif "prompt" in kwargs:
                    kwargs["prompt"] = secured_prompt
                
                # Track metrics
                metrics_collector = _get_metrics_collector()
                metrics_collector.record_security_event(
                    "prompt_security",
                    metadata
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def secure_output(strict_mode: bool = False):
    """
    Decorator to sanitize outputs to prevent sensitive information disclosure (OWASP LLM02)

    Args:
        strict_mode: If True, apply more aggressive redaction

    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Process the result
            if result and isinstance(result, str):
                # Get or initialize output sanitizer
                output_sanitizer = _get_output_sanitizer()
                output_sanitizer.strict_mode = strict_mode
                
                # Sanitize the output
                sanitized_output, metadata = output_sanitizer.sanitize_output(result)
                
                # Log security action
                if metadata["contains_sensitive"]:
                    logger.warning(
                        f"Sensitive information detected: {metadata['sensitive_type']} "
                        f"(risk: {metadata['risk_level']}, confidence: {metadata['confidence']:.2f}). "
                        f"Redacted {metadata['redacted_count']} items."
                    )
                
                # Track metrics
                metrics_collector = _get_metrics_collector()
                metrics_collector.record_security_event(
                    "output_security",
                    metadata
                )
                
                return sanitized_output
            elif isinstance(result, dict) and "response" in result and isinstance(result["response"], str):
                # Handle dictionary response format
                output_sanitizer = _get_output_sanitizer()
                output_sanitizer.strict_mode = strict_mode
                
                sanitized_output, metadata = output_sanitizer.sanitize_output(result["response"])
                
                # Log security action if needed
                if metadata["contains_sensitive"]:
                    logger.warning(
                        f"Sensitive information detected: {metadata['sensitive_type']} "
                        f"(risk: {metadata['risk_level']}, confidence: {metadata['confidence']:.2f}). "
                        f"Redacted {metadata['redacted_count']} items."
                    )
                
                # Track metrics
                metrics_collector = _get_metrics_collector()
                metrics_collector.record_security_event(
                    "output_security",
                    metadata
                )
                
                # Update the response
                result["response"] = sanitized_output
                result["security_metadata"] = metadata
                
                return result
            
            # Return original result if not a string or dict with response
            return result
        
        return wrapper
    
    return decorator

def verify_response(verification_type: str = "consistency", require_human: bool = False):
    """
    Decorator to verify LLM outputs to prevent overreliance (OWASP LLM09)
    
    Args:
        verification_type: Type of verification to perform
        require_human: Whether to require human verification
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context from kwargs if available
            context = kwargs.get("context", {})
            
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Process the result
            if result and isinstance(result, str):
                # Get or initialize verification system
                verification_system = _get_verification_system()
                
                # Verify the output
                verification_result = verification_system.verify_output(
                    result,
                    context=context,
                    verification_type=verification_type,
                    require_human=require_human
                )
                
                # Log verification result
                if not verification_result.is_verified:
                    logger.warning(
                        f"Output verification failed: {verification_result.verification_type} "
                        f"(risk: {verification_result.risk_level}, confidence: {verification_result.confidence:.2f}). "
                        f"Details: {verification_result.details}"
                    )
                
                # Track metrics
                metrics_collector = _get_metrics_collector()
                metrics_collector.record_security_event(
                    "output_verification",
                    {
                        "is_verified": verification_result.is_verified,
                        "verification_type": verification_result.verification_type,
                        "confidence": verification_result.confidence,
                        "risk_level": verification_result.risk_level
                    }
                )
                
                # Return verified output or original with warning
                if verification_result.is_verified:
                    return result
                else:
                    return f"[VERIFICATION WARNING: {verification_result.details}]\n\n{result}"
                    
            elif isinstance(result, dict) and "response" in result and isinstance(result["response"], str):
                # Handle dictionary response format
                verification_system = _get_verification_system()
                
                verification_result = verification_system.verify_output(
                    result["response"],
                    context=context,
                    verification_type=verification_type,
                    require_human=require_human
                )
                
                # Log verification result
                if not verification_result.is_verified:
                    logger.warning(
                        f"Output verification failed: {verification_result.verification_type} "
                        f"(risk: {verification_result.risk_level}, confidence: {verification_result.confidence:.2f}). "
                        f"Details: {verification_result.details}"
                    )
                
                # Track metrics
                metrics_collector = _get_metrics_collector()
                metrics_collector.record_security_event(
                    "output_verification",
                    {
                        "is_verified": verification_result.is_verified,
                        "verification_type": verification_result.verification_type,
                        "confidence": verification_result.confidence,
                        "risk_level": verification_result.risk_level
                    }
                )
                
                # Update the response with verification metadata
                result["verification_result"] = {
                    "is_verified": verification_result.is_verified,
                    "confidence": verification_result.confidence,
                    "details": verification_result.details,
                    "risk_level": verification_result.risk_level
                }
                
                # Add warning if not verified
                if not verification_result.is_verified:
                    result["response"] = f"[VERIFICATION WARNING: {verification_result.details}]\n\n{result['response']}"
                
                return result
            
            # Return original result if not a string or dict with response
            return result
        
        return wrapper
    
    return decorator

def track_metrics():
    """
    Decorator to track security metrics for research purposes
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get metrics collector
            metrics_collector = _get_metrics_collector()
            
            # Start timing
            metrics_collector.start_timing(func.__name__)
            
            # Call the original function
            result = await func(*args, **kwargs)
            
            # End timing and record
            metrics_collector.end_timing(func.__name__)
            
            # Record function call
            metrics_collector.record_function_call(
                func.__name__,
                {
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "result_type": type(result).__name__
                }
            )
            
            return result
        
        return wrapper
    
    return decorator
