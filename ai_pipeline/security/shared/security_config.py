"""
Security Configuration for Finnish Politician Analysis System
Centralizes all security settings for the AI pipeline components.
"""

from typing import Dict, Any, List, Optional
import os
from pathlib import Path
import json

class SecurityConfig:
    """
    Centralized security configuration for the AI pipeline.
    
    This class manages all security settings for:
    - Prompt guarding
    - Output sanitization
    - Response verification
    - Security metrics collection
    
    It supports loading from environment variables or a config file,
    and provides default values for all settings.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "prompt_guard": {
            "enabled": True,
            "strict_mode": True,
            "block_suspicious": True,
            "log_all_prompts": True,
            "max_prompt_length": 8192,
            "detection_patterns": {
                "system_prompt_hijacking": True,
                "data_exfiltration": True,
                "code_injection": True,
                "delimiter_confusion": True,
                "jailbreak_attempts": True
            }
        },
        "output_sanitizer": {
            "enabled": True,
            "strict_mode": False,
            "redact_pii": True,
            "redact_credentials": True,
            "redact_system_info": True,
            "log_all_outputs": True,
            "detection_patterns": {
                "personal_identifiers": True,
                "contact_information": True,
                "financial_information": True,
                "credentials": True,
                "system_paths": True
            }
        },
        "verification_system": {
            "enabled": True,
            "verification_types": {
                "factuality": {
                    "enabled": True,
                    "threshold": 0.8,
                    "require_sources": True
                },
                "consistency": {
                    "enabled": True,
                    "threshold": 0.7
                },
                "uncertainty": {
                    "enabled": True,
                    "threshold": 0.6
                },
                "human_feedback": {
                    "enabled": False,
                    "threshold": 0.5
                }
            }
        },
        "metrics_collector": {
            "enabled": True,
            "persistence": {
                "enabled": True,
                "storage_path": "security_metrics",
                "max_file_size_mb": 10,
                "rotation_count": 5
            },
            "visualization": {
                "enabled": True,
                "generate_charts": True
            },
            "alert_thresholds": {
                "prompt_injection_attempts": 5,
                "pii_detection_rate": 0.1,
                "verification_failure_rate": 0.2
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize security configuration with default values,
        then override with values from config file or environment variables.
        
        Args:
            config_path: Optional path to a JSON configuration file
        """
        # Start with default configuration
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Override with config file if provided
        if config_path:
            self._load_from_file(config_path)
            
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_file(self, config_path: str) -> None:
        """
        Load configuration from a JSON file
        
        Args:
            config_path: Path to the JSON configuration file
        """
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    self._update_config_recursive(self.config, file_config)
        except Exception as e:
            print(f"Error loading security config from file: {str(e)}")
    
    def _load_from_env(self) -> None:
        """
        Load configuration from environment variables
        
        Environment variables should be in the format:
        FPAS_SECURITY_{SECTION}_{SETTING}
        
        For example:
        FPAS_SECURITY_PROMPT_GUARD_ENABLED=true
        """
        for key in os.environ:
            if key.startswith("FPAS_SECURITY_"):
                try:
                    # Parse the environment variable name
                    parts = key[14:].lower().split('_')
                    if len(parts) < 2:
                        continue
                    
                    # Get the value and convert to appropriate type
                    value = os.environ[key]
                    if value.lower() in ('true', 'yes', '1'):
                        value = True
                    elif value.lower() in ('false', 'no', '0'):
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                    
                    # Update the configuration
                    self._set_config_value(parts, value)
                except Exception as e:
                    print(f"Error processing environment variable {key}: {str(e)}")
    
    def _update_config_recursive(self, target: Dict, source: Dict) -> None:
        """
        Recursively update a nested dictionary with values from another dictionary
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(value, dict) and isinstance(target[key], dict):
                self._update_config_recursive(target[key], value)
            else:
                target[key] = value
    
    def _set_config_value(self, path: List[str], value: Any) -> None:
        """
        Set a configuration value at the specified path
        
        Args:
            path: List of keys forming the path to the setting
            value: Value to set
        """
        config = self.config
        for part in path[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        config[path[-1]] = value
    
    def get_prompt_guard_config(self) -> Dict[str, Any]:
        """Get prompt guard configuration"""
        return self.config["prompt_guard"]
    
    def get_output_sanitizer_config(self) -> Dict[str, Any]:
        """Get output sanitizer configuration"""
        return self.config["output_sanitizer"]
    
    def get_verification_system_config(self) -> Dict[str, Any]:
        """Get verification system configuration"""
        return self.config["verification_system"]
    
    def get_metrics_collector_config(self) -> Dict[str, Any]:
        """Get metrics collector configuration"""
        return self.config["metrics_collector"]
    
    def save_to_file(self, config_path: str) -> None:
        """
        Save the current configuration to a JSON file
        
        Args:
            config_path: Path to save the configuration file
        """
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving security config to file: {str(e)}")

# Global instance
_security_config = None

def get_security_config(config_path: Optional[str] = None) -> SecurityConfig:
    """
    Get the global security configuration instance
    
    Args:
        config_path: Optional path to a JSON configuration file
        
    Returns:
        SecurityConfig instance
    """
    global _security_config
    if _security_config is None:
        _security_config = SecurityConfig(config_path)
    return _security_config
