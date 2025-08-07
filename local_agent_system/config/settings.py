"""
Configuration settings for the local agent system - Legacy compatibility layer
"""
import logging
from typing import Dict, Optional

# Import the new configuration system
from .config_manager import ConfigManager
from .config_schema import AgentConfig, SystemConfig

logger = logging.getLogger(__name__)

# Legacy compatibility - maintain the same interface
class LegacyConfigManager(ConfigManager):
    """Legacy configuration manager for backward compatibility"""
    
    def __init__(self, config_dir: Optional[str] = None, preset: Optional[str] = None):
        """Initialize with backward compatibility"""
        super().__init__(config_dir, preset)
        # Load configuration on initialization for legacy compatibility
        self.load_config()
    
    def get_system_status(self) -> Dict:
        """Get system status - legacy method"""
        enabled_agents = self.get_enabled_agents()
        return {
            'agent_count': len(enabled_agents),
            'config': {
                'ollama_url': self.system_config.ollama_base_url,
                'timeout': self.system_config.ollama_timeout,
                'log_level': self.system_config.log_level
            },
            'agents': {
                agent_id: {
                    'model_name': agent.model_name,
                    'temperature': agent.temperature,
                    'enabled': agent.enabled
                }
                for agent_id, agent in enabled_agents.items()
            }
        }

# Create a global instance for legacy compatibility
_default_config_manager = None

def get_config_manager(config_dir: Optional[str] = None, preset: Optional[str] = None) -> ConfigManager:
    """Get the configuration manager instance"""
    global _default_config_manager
    
    if _default_config_manager is None or config_dir is not None or preset is not None:
        _default_config_manager = LegacyConfigManager(config_dir, preset)
    
    return _default_config_manager

def load_config(config_path: Optional[str] = None, preset: Optional[str] = None) -> Dict:
    """
    Load configuration from file - legacy function for backward compatibility.
    
    Args:
        config_path: Path to configuration file or preset name
        preset: Preset configuration name
        
    Returns:
        Configuration dictionary
    """
    try:
        if config_path and config_path.endswith('.yaml'):
            # Load from specific file
            config_manager = ConfigManager()
            config_manager.load_config_file(config_path)
        else:
            # Load from preset or default
            preset_name = preset or config_path or "balanced"
            config_manager = ConfigManager(preset=preset_name)
        
        # Return configuration in legacy format
        return {
            'system': {
                'ollama_base_url': config_manager.system_config.ollama_base_url,
                'ollama_timeout': config_manager.system_config.ollama_timeout,
                'max_retries': config_manager.system_config.max_retries,
                'retry_delay': config_manager.system_config.retry_delay,
                'log_level': config_manager.system_config.log_level,
                'session_save_dir': config_manager.system_config.session_save_dir,
                'enable_metrics': config_manager.system_config.enable_metrics,
                'max_concurrent_requests': config_manager.system_config.max_concurrent_requests,
                'response_timeout': config_manager.system_config.response_timeout
            },
            'agents': {
                agent_id: {
                    'role': agent.role,
                    'model_name': agent.model_name,
                    'temperature': agent.temperature,
                    'personality': agent.personality,
                    'enabled': agent.enabled,
                    'max_tokens': agent.max_tokens,
                    'system_prompt': agent.system_prompt
                }
                for agent_id, agent in config_manager.agents.items()
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        # Return minimal default configuration
        return {
            'system': {
                'ollama_base_url': 'http://localhost:11434',
                'ollama_timeout': 120,
                'max_retries': 3,
                'retry_delay': 1.0,
                'log_level': 'INFO',
                'session_save_dir': './sessions',
                'enable_metrics': True,
                'max_concurrent_requests': 3,
                'response_timeout': 60
            },
            'agents': {}
        }

# Export the classes for backward compatibility
__all__ = [
    'AgentConfig', 
    'SystemConfig', 
    'ConfigManager',
    'LegacyConfigManager',
    'get_config_manager',
    'load_config'
]
