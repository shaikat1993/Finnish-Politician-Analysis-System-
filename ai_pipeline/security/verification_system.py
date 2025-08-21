"""
OWASP LLM09: Overreliance Prevention System
Advanced protection against overreliance on LLM outputs in critical applications.
"""

import re
import logging
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
from dataclasses import dataclass
import hashlib
import random

@dataclass
class VerificationResult:
    """Data class for verification results"""
    is_verified: bool
    confidence: float
    verification_type: str
    risk_level: str = "low"
    details: Optional[str] = None
    verified_output: Optional[str] = None
    verification_method: Optional[str] = None

class VerificationSystem:
    """
    Advanced OWASP LLM09 Overreliance Prevention System
    
    Implements multiple layers of defense against overreliance on LLM outputs:
    1. Fact verification against trusted sources
    2. Consistency checking across multiple responses
    3. Confidence scoring and uncertainty detection
    4. Human-in-the-loop verification for critical decisions
    5. Research instrumentation for academic analysis
    """
    
    def __init__(self, 
                 enable_metrics: bool = True,
                 strict_mode: bool = False,
                 log_verifications: bool = True,
                 verification_threshold: float = 0.7,
                 external_verifiers: Optional[Dict[str, Callable]] = None):
        """
        Initialize the VerificationSystem
        
        Args:
            enable_metrics: Whether to collect metrics for research
            strict_mode: If True, require higher verification confidence
            log_verifications: Whether to log verification events
            verification_threshold: Minimum confidence threshold for verification
            external_verifiers: Custom verification functions
        """
        self.logger = logging.getLogger(__name__)
        self.enable_metrics = enable_metrics
        self.strict_mode = strict_mode
        self.log_verifications = log_verifications
        self.verification_threshold = verification_threshold
        self.external_verifiers = external_verifiers or {}
        self.verification_count = 0
        self.metrics = {
            "total_verifications": 0,
            "verified_outputs": 0,
            "unverified_outputs": 0,
            "verification_types": {},
            "average_confidence": 0.0,
            "human_interventions": 0
        }
        
        self.logger.info("VerificationSystem initialized with strict_mode=%s, metrics=%s", 
                        strict_mode, enable_metrics)
    
    def verify_output(self, 
                     output: str, 
                     context: Optional[Dict[str, Any]] = None,
                     verification_type: str = "consistency",
                     require_human: bool = False) -> VerificationResult:
        """
        Verify an LLM output against overreliance risks
        
        Args:
            output: The LLM output to verify
            context: Additional context for verification
            verification_type: Type of verification to perform
            require_human: Whether to require human verification
            
        Returns:
            VerificationResult object with verification results
        """
        if not output or not isinstance(output, str):
            return VerificationResult(
                is_verified=False, 
                confidence=0.0,
                verification_type=verification_type
            )
        
        # Track metrics
        if self.enable_metrics:
            self.metrics["total_verifications"] += 1
        
        # Determine verification method based on type
        if verification_type == "fact_checking":
            result = self._verify_facts(output, context)
        elif verification_type == "consistency":
            result = self._verify_consistency(output, context)
        elif verification_type == "uncertainty":
            result = self._detect_uncertainty(output)
        elif verification_type == "human":
            result = self._human_verification(output, context)
        elif verification_type in self.external_verifiers:
            # Use external verification function
            result = self.external_verifiers[verification_type](output, context)
        else:
            # Default to consistency checking
            result = self._verify_consistency(output, context)
        
        # Apply strict mode if enabled
        if self.strict_mode:
            # Increase threshold for verification
            if result.confidence < (self.verification_threshold + 0.15):
                result.is_verified = False
                result.details = f"{result.details} (Failed strict mode verification)"
        
        # Force human verification if required
        if require_human and result.verification_method != "human":
            human_result = self._human_verification(output, context)
            # Combine results
            result.is_verified = result.is_verified and human_result.is_verified
            result.confidence = (result.confidence + human_result.confidence) / 2
            result.details = f"{result.details}; Human verification: {human_result.details}"
            result.verification_method = f"{result.verification_method}+human"
        
        # Record metrics
        self._record_verification(result)
        
        return result
    
    def _verify_facts(self, output: str, context: Optional[Dict[str, Any]]) -> VerificationResult:
        """
        Verify factual claims in the output
        
        Args:
            output: The output to verify
            context: Additional context including trusted sources
            
        Returns:
            VerificationResult with fact checking results
        """
        # In a real implementation, this would connect to trusted data sources
        # For this academic implementation, we'll simulate fact checking
        
        # Extract potential factual claims
        facts = self._extract_factual_claims(output)
        
        if not facts:
            # No clear factual claims to verify
            return VerificationResult(
                is_verified=True,
                confidence=0.8,
                verification_type="fact_checking",
                risk_level="low",
                details="No specific factual claims requiring verification",
                verified_output=output,
                verification_method="fact_extraction"
            )
        
        # Simulate verification against trusted sources
        # In a real implementation, this would query databases or APIs
        verified_count = 0
        total_facts = len(facts)
        verification_notes = []
        
        for fact in facts:
            # Simulate verification (would be replaced with real verification)
            if context and "trusted_data" in context:
                # Check against provided trusted data
                is_verified = self._check_against_trusted_data(fact, context["trusted_data"])
            else:
                # Simulate verification
                is_verified = random.random() > 0.2  # 80% chance of verification
            
            if is_verified:
                verified_count += 1
            else:
                verification_notes.append(f"Could not verify: '{fact}'")
        
        # Calculate verification confidence
        if total_facts > 0:
            confidence = verified_count / total_facts
        else:
            confidence = 0.8  # Default confidence when no facts to check
        
        # Determine verification result
        is_verified = confidence >= self.verification_threshold
        
        if is_verified:
            risk_level = "low"
            details = "Factual claims verified against trusted sources"
            if verification_notes:
                details += f" with exceptions: {'; '.join(verification_notes)}"
        else:
            risk_level = "high"
            details = f"Failed to verify {total_facts - verified_count} out of {total_facts} factual claims"
            if verification_notes:
                details += f": {'; '.join(verification_notes)}"
        
        return VerificationResult(
            is_verified=is_verified,
            confidence=confidence,
            verification_type="fact_checking",
            risk_level=risk_level,
            details=details,
            verified_output=output if is_verified else None,
            verification_method="trusted_sources"
        )
    
    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract potential factual claims from text"""
        # Simple extraction of sentences that appear to be factual claims
        # In a real implementation, this would use more sophisticated NLP
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter for likely factual claims
        factual_patterns = [
            r'\b(?:is|are|was|were)\b',  # Being verbs
            r'\b(?:has|have|had)\b',      # Having verbs
            r'\b(?:in|on|at|during)\b \d{4}',  # Years
            r'\b(?:according to|research shows|studies indicate)\b',  # Citations
            r'\b(?:percent|%)\b',         # Statistics
            r'\b(?:increased|decreased|reduced|expanded)\b',  # Change indicators
        ]
        
        facts = []
        for sentence in sentences:
            # Skip short sentences and questions
            if len(sentence) < 10 or sentence.endswith('?'):
                continue
                
            # Check if sentence matches factual patterns
            for pattern in factual_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    facts.append(sentence)
                    break
        
        return facts
    
    def _check_against_trusted_data(self, fact: str, trusted_data: Dict[str, Any]) -> bool:
        """Check a fact against trusted data sources"""
        # This would be implemented with real data sources in production
        # For now, we'll just simulate checking
        
        # Convert fact to lowercase for comparison
        fact_lower = fact.lower()
        
        # Check if any trusted data keys are mentioned in the fact
        for key, value in trusted_data.items():
            if key.lower() in fact_lower:
                # If the value is a string, check if it's mentioned
                if isinstance(value, str) and value.lower() in fact_lower:
                    return True
                # If the value is a number, check if it's mentioned
                elif isinstance(value, (int, float)):
                    if str(value) in fact_lower:
                        return True
        
        # Default to not verified if no matches found
        return False
    
    def _verify_consistency(self, output: str, context: Optional[Dict[str, Any]]) -> VerificationResult:
        """
        Verify consistency of the output with previous outputs or context
        
        Args:
            output: The output to verify
            context: Previous outputs or other context
            
        Returns:
            VerificationResult with consistency checking results
        """
        if not context or "previous_outputs" not in context or not context["previous_outputs"]:
            # No previous outputs to compare with
            return VerificationResult(
                is_verified=True,
                confidence=0.7,
                verification_type="consistency",
                risk_level="medium",
                details="No previous outputs to check consistency against",
                verified_output=output,
                verification_method="consistency_baseline"
            )
        
        previous_outputs = context["previous_outputs"]
        
        # Check for contradictions with previous outputs
        contradiction_score = self._calculate_contradiction_score(output, previous_outputs)
        
        # Calculate consistency confidence
        consistency_confidence = 1.0 - contradiction_score
        
        # Determine verification result
        is_consistent = consistency_confidence >= self.verification_threshold
        
        if is_consistent:
            risk_level = "low"
            details = "Output is consistent with previous responses"
        else:
            risk_level = "high"
            details = "Output contradicts previous responses"
        
        return VerificationResult(
            is_verified=is_consistent,
            confidence=consistency_confidence,
            verification_type="consistency",
            risk_level=risk_level,
            details=details,
            verified_output=output if is_consistent else None,
            verification_method="contradiction_detection"
        )
    
    def _calculate_contradiction_score(self, output: str, previous_outputs: List[str]) -> float:
        """Calculate contradiction score between current and previous outputs"""
        # In a real implementation, this would use semantic analysis
        # For this academic implementation, we'll use a simple heuristic
        
        # Extract key statements from current output
        current_statements = self._extract_key_statements(output)
        
        if not current_statements:
            return 0.0  # No statements to check
        
        # Check each statement against previous outputs
        contradiction_count = 0
        
        for statement in current_statements:
            for prev_output in previous_outputs:
                # Look for negations of the statement in previous outputs
                negation = self._find_negation(statement, prev_output)
                if negation:
                    contradiction_count += 1
                    break  # Only count one contradiction per statement
        
        # Calculate contradiction score
        if current_statements:
            return min(1.0, contradiction_count / len(current_statements))
        else:
            return 0.0
    
    def _extract_key_statements(self, text: str) -> List[str]:
        """Extract key statements from text"""
        # Simple extraction of declarative sentences
        # In a real implementation, this would use more sophisticated NLP
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter for declarative statements
        statements = []
        for sentence in sentences:
            # Skip questions, short sentences, and non-declarative sentences
            if sentence.endswith('?') or len(sentence) < 15:
                continue
            
            # Check if sentence is a declarative statement
            if re.search(r'\b(?:is|are|was|were|will|has|have|had)\b', sentence, re.IGNORECASE):
                statements.append(sentence)
        
        return statements
    
    def _find_negation(self, statement: str, text: str) -> bool:
        """Find negation of a statement in text"""
        # This is a simplified implementation
        # In a real system, this would use semantic understanding
        
        # Extract key subject and predicate from statement
        match = re.search(r'(\w+(?:\s+\w+){0,3})\s+(is|are|was|were|will|has|have|had)\s+(\w+(?:\s+\w+){0,5})', 
                         statement, re.IGNORECASE)
        
        if not match:
            return False
        
        subject, verb, predicate = match.groups()
        
        # Look for negations
        negation_pattern = rf'{re.escape(subject)}(?:\s+\w+){{0,3}}\s+{re.escape(verb)}\s+not\s+{re.escape(predicate)}'
        alt_negation_pattern = rf'{re.escape(subject)}(?:\s+\w+){{0,3}}\s+{re.escape(verb)}n[\'o]t\s+{re.escape(predicate)}'
        
        return bool(re.search(negation_pattern, text, re.IGNORECASE) or 
                   re.search(alt_negation_pattern, text, re.IGNORECASE))
    
    def _detect_uncertainty(self, output: str) -> VerificationResult:
        """
        Detect uncertainty markers in the output
        
        Args:
            output: The output to check for uncertainty
            
        Returns:
            VerificationResult with uncertainty detection results
        """
        # Define uncertainty markers
        uncertainty_markers = [
            r'\b(?:may|might|could|possibly|perhaps|maybe|potentially)\b',
            r'\b(?:uncertain|unclear|unknown|not\s+sure|not\s+clear)\b',
            r'\b(?:approximately|roughly|around|about|estimated)\b',
            r'\b(?:sometimes|occasionally|in\s+some\s+cases)\b',
            r'(?:[\?\.])\s+(?:However|But|Nevertheless)',
            r'\b(?:I\s+think|I\s+believe|I\s+suspect|seems\s+to|appears\s+to)\b'
        ]
        
        # Count uncertainty markers
        uncertainty_count = 0
        for marker in uncertainty_markers:
            matches = re.findall(marker, output, re.IGNORECASE)
            uncertainty_count += len(matches)
        
        # Calculate uncertainty score based on density
        words = output.split()
        if not words:
            return VerificationResult(
                is_verified=True,
                confidence=0.9,
                verification_type="uncertainty",
                risk_level="low",
                details="Empty output",
                verified_output=output,
                verification_method="uncertainty_detection"
            )
        
        uncertainty_density = uncertainty_count / (len(words) / 100)  # Per 100 words
        
        # Convert to confidence score (inverse of uncertainty)
        if uncertainty_density > 5:
            # High uncertainty
            confidence = 0.5
            risk_level = "high"
            details = f"High uncertainty detected ({uncertainty_count} markers)"
            is_verified = False
        elif uncertainty_density > 2:
            # Medium uncertainty
            confidence = 0.7
            risk_level = "medium"
            details = f"Moderate uncertainty detected ({uncertainty_count} markers)"
            is_verified = confidence >= self.verification_threshold
        else:
            # Low uncertainty
            confidence = 0.9
            risk_level = "low"
            details = f"Low uncertainty detected ({uncertainty_count} markers)"
            is_verified = True
        
        return VerificationResult(
            is_verified=is_verified,
            confidence=confidence,
            verification_type="uncertainty",
            risk_level=risk_level,
            details=details,
            verified_output=output if is_verified else None,
            verification_method="uncertainty_detection"
        )
    
    def _human_verification(self, output: str, context: Optional[Dict[str, Any]]) -> VerificationResult:
        """
        Simulate human verification of the output
        
        Args:
            output: The output to verify
            context: Additional context for verification
            
        Returns:
            VerificationResult with human verification results
        """
        # In a real implementation, this would prompt a human reviewer
        # For this academic implementation, we'll simulate human verification
        
        if self.enable_metrics:
            self.metrics["human_interventions"] += 1
        
        # Simulate human verification
        # In a real system, this would wait for human input
        time.sleep(0.1)  # Simulate brief delay
        
        # For simulation, we'll verify based on output characteristics
        word_count = len(output.split())
        
        if word_count < 10:
            # Very short outputs are suspicious
            return VerificationResult(
                is_verified=False,
                confidence=0.4,
                verification_type="human",
                risk_level="high",
                details="Human reviewer rejected: output too short",
                verified_output=None,
                verification_method="human"
            )
        
        # Simulate human approval with high confidence
        return VerificationResult(
            is_verified=True,
            confidence=0.95,
            verification_type="human",
            risk_level="low",
            details="Verified by human reviewer",
            verified_output=output,
            verification_method="human"
        )
    
    def _record_verification(self, result: VerificationResult) -> None:
        """Record metrics for a verification event"""
        if not self.enable_metrics:
            return
        
        self.verification_count += 1
        
        if result.is_verified:
            self.metrics["verified_outputs"] += 1
        else:
            self.metrics["unverified_outputs"] += 1
        
        # Track verification types
        if result.verification_type not in self.metrics["verification_types"]:
            self.metrics["verification_types"][result.verification_type] = {
                "total": 0,
                "verified": 0,
                "confidence_sum": 0.0
            }
        
        type_metrics = self.metrics["verification_types"][result.verification_type]
        type_metrics["total"] += 1
        if result.is_verified:
            type_metrics["verified"] += 1
        type_metrics["confidence_sum"] += result.confidence
        
        # Update average confidence
        total_verifications = self.metrics["verified_outputs"] + self.metrics["unverified_outputs"]
        if total_verifications > 0:
            self.metrics["average_confidence"] = (
                (self.metrics["average_confidence"] * (total_verifications - 1) + result.confidence) / 
                total_verifications
            )
        
        if self.log_verifications:
            self.logger.info(
                "Verification result: type=%s, verified=%s, confidence=%.2f, risk=%s",
                result.verification_type, result.is_verified, 
                result.confidence, result.risk_level
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected verification metrics"""
        if not self.enable_metrics:
            return {"metrics_collection": "disabled"}
        
        # Calculate success rates for each verification type
        for vtype, metrics in self.metrics["verification_types"].items():
            if metrics["total"] > 0:
                metrics["success_rate"] = metrics["verified"] / metrics["total"]
                metrics["average_confidence"] = metrics["confidence_sum"] / metrics["total"]
        
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset collected metrics"""
        self.metrics = {
            "total_verifications": 0,
            "verified_outputs": 0,
            "unverified_outputs": 0,
            "verification_types": {},
            "average_confidence": 0.0,
            "human_interventions": 0
        }
        self.verification_count = 0
