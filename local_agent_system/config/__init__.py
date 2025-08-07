"""
Configuration module for the local agent system
"""
from .config_manager import ConfigManager
from .config_schema import AgentConfig, SystemConfig, ConfigValidator, ConfigPreset
from .settings import get_config_manager, LegacyConfigManager

__all__ = [
    'ConfigManager',
    'AgentConfig', 
    'SystemConfig',
    'ConfigValidator',
    'ConfigPreset',
    'get_config_manager',
    'LegacyConfigManager'
]
