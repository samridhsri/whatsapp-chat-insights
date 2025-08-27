"""
Configuration management for WhatsApp Chat Analyzer.

This module handles environment variables, configuration settings,
and provides defaults for various application parameters.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values
DEFAULT_CONFIG = {
    "logging_level": "INFO",
    "log_file": None,
    "max_file_size_mb": 100,
    "supported_encodings": ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"],
    "default_platform": "auto",
    "conversation_threshold_hours": 1,
    "max_messages_preview": 200,
    "export_formats": ["csv", "excel", "json"],
    "debug_mode": False,
    "anonymize_default": False,
    "include_media_default": False,
}

# Environment variable mappings
ENV_MAPPINGS = {
    "WHATSAPP_LOG_LEVEL": "logging_level",
    "WHATSAPP_LOG_FILE": "log_file",
    "WHATSAPP_MAX_FILE_SIZE": "max_file_size_mb",
    "WHATSAPP_DEFAULT_PLATFORM": "default_platform",
    "WHATSAPP_CONVERSATION_THRESHOLD": "conversation_threshold_hours",
    "WHATSAPP_DEBUG": "debug_mode",
    "WHATSAPP_ANONYMIZE": "anonymize_default",
    "WHATSAPP_INCLUDE_MEDIA": "include_media_default",
}


class Config:
    """Configuration manager for WhatsApp Chat Analyzer."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Optional path to configuration file
        """
        self._config = DEFAULT_CONFIG.copy()
        self._load_environment_variables()
        
        if config_file:
            self._load_config_file(config_file)
    
    def _load_environment_variables(self):
        """Load configuration from environment variables."""
        for env_var, config_key in ENV_MAPPINGS.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key == "debug_mode":
                    self._config[config_key] = value.lower() in ("true", "1", "yes", "on")
                elif config_key == "anonymize_default":
                    self._config[config_key] = value.lower() in ("true", "1", "yes", "on")
                elif config_key == "include_media_default":
                    self._config[config_key] = value.lower() in ("true", "1", "yes", "on")
                elif config_key in ["max_file_size_mb", "conversation_threshold_hours", "max_messages_preview"]:
                    try:
                        self._config[config_key] = int(value)
                    except ValueError:
                        pass  # Keep default if conversion fails
                else:
                    self._config[config_key] = value
    
    def _load_config_file(self, config_file: str):
        """Load configuration from file (future enhancement)."""
        # TODO: Implement configuration file loading
        # This could support YAML, JSON, or INI files
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()
    
    def update(self, updates: Dict[str, Any]):
        """
        Update multiple configuration values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self._config.update(updates)
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if configuration is valid
        """
        # Validate file size limit
        if self.get("max_file_size_mb", 0) <= 0:
            return False
        
        # Validate conversation threshold
        if self.get("conversation_threshold_hours", 0) <= 0:
            return False
        
        # Validate logging level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.get("logging_level", "").upper() not in valid_log_levels:
            return False
        
        return True


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def get_setting(key: str, default: Any = None) -> Any:
    """Get a configuration setting."""
    return config.get(key, default)


def set_setting(key: str, value: Any):
    """Set a configuration setting."""
    config.set(key, value)


def update_settings(updates: Dict[str, Any]):
    """Update multiple configuration settings."""
    config.update(updates)


def validate_settings() -> bool:
    """Validate all configuration settings."""
    return config.validate()


# Convenience functions for common settings
def get_log_level() -> str:
    """Get logging level."""
    return get_setting("logging_level", "INFO")


def get_max_file_size() -> int:
    """Get maximum file size in MB."""
    return get_setting("max_file_size_mb", 100)


def get_default_platform() -> str:
    """Get default platform setting."""
    return get_setting("default_platform", "auto")


def get_conversation_threshold() -> int:
    """Get conversation threshold in hours."""
    return get_setting("conversation_threshold_hours", 1)


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return get_setting("debug_mode", False)


def should_anonymize() -> bool:
    """Check if anonymization is enabled by default."""
    return get_setting("anonymize_default", False)


def should_include_media() -> bool:
    """Check if media messages should be included by default."""
    return get_setting("include_media_default", False) 