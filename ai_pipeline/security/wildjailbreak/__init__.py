"""
WildJailbreak External Validation Module

This module provides external validation of prompt injection detection
using the WildJailbreak benchmark dataset (Xie et al., 2024).

Dataset: https://huggingface.co/datasets/allenai/wildjailbreak
Citation: Xie et al. (2024). WildJailbreak: A Benchmark for Jailbreaking LLMs in the Wild
"""

from .evaluate_wildjailbreak import evaluate_wildjailbreak

__all__ = ['evaluate_wildjailbreak']
