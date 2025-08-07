"""
Enhanced configuration manager with environment variables and validation
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import asdict

from .config_schema import (
    AgentConfig, SystemConfig, ConfigValidator, ValidationError,
    ConfigPreset, LogLevel
)

logger = logging.getLogger(__name__)

class ConfigManager:
    """Enhanced configuration manager with validation and environment variable support"""
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        'system': {
            'AGENT_SYSTEM_OLLAMA_URL': 'ollama_base_url',
            'AGENT_SYSTEM_OLLAMA_TIMEOUT': 'ollama_timeout',
            'AGENT_SYSTEM_MAX_RETRIES': 'max_retries',
            'AGENT_SYSTEM_RETRY_DELAY': 'retry_delay',
            'AGENT_SYSTEM_LOG_LEVEL': 'log_level',
            'AGENT_SYSTEM_SESSION_DIR': 'session_save_dir',
            'AGENT_SYSTEM_ENABLE_METRICS': 'enable_metrics',
            'AGENT_SYSTEM_MAX_CONCURRENT': 'max_concurrent_requests',
            'AGENT_SYSTEM_RESPONSE_TIMEOUT': 'response_timeout',
            'AGENT_SYSTEM_ADVANCED_FEATURES': 'enable_advanced_features',
            'AGENT_SYSTEM_DETAILED_REASONING': 'detailed_reasoning',
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None, preset: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
            preset: Configuration preset to use (light/balanced/premium)
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.presets_dir = self.config_dir / "presets"
        self.preset = preset or os.getenv('AGENT_SYSTEM_PRESET', 'balanced')
        
        self.system_config: SystemConfig = SystemConfig()
        self.agents: Dict[str, AgentConfig] = {}
        self.validation_errors: List[ValidationError] = []
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.presets_dir, exist_ok=True)
        
    def load_config(self, config_file: Optional[str] = None) -> bool:
        """
        Load configuration with preset and environment variable support
        
        Args:
            config_file: Specific config file to load (overrides preset)
            
        Returns:
            True if configuration loaded successfully, False otherwise
        """
        try:
            config_data = {}
            
            # 1. Load preset configuration first
            if not config_file:
                preset_file = self.presets_dir / f"{self.preset}.yaml"
                if preset_file.exists():
                    logger.info(f"Loading preset configuration: {preset_file}")
                    with open(preset_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                else:
                    logger.warning(f"Preset file not found: {preset_file}")
                    return self._load_default_config()
            else:
                # Load specific config file
                config_path = Path(config_file)
                if config_path.exists():
                    logger.info(f"Loading configuration file: {config_path}")
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                else:
                    logger.error(f"Config file not found: {config_path}")
                    return False
            
            # 2. Apply environment variable overrides
            config_data = self._apply_env_overrides(config_data)
            
            # 3. Parse and validate configuration
            if not self._parse_config_data(config_data):
                return False
            
            # 4. Validate configuration
            if not self.validate_config():
                logger.error("Configuration validation failed")
                return False
            
            logger.info(f"Configuration loaded successfully: {len(self.agents)} agents configured")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration data"""
        
        # Apply system configuration overrides
        if 'system' not in config_data:
            config_data['system'] = {}
        
        for env_var, config_key in self.ENV_MAPPINGS['system'].items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert to appropriate type
                converted_value = self._convert_env_value(env_value, config_key)
                if converted_value is not None:
                    config_data['system'][config_key] = converted_value
                    logger.debug(f"Applied env override: {env_var}={converted_value}")
        
        # Apply agent-specific overrides
        for i, agent_data in enumerate(config_data.get('agents', [])):
            agent_id = agent_data.get('agent_id', '')
            
            # Check for agent-specific environment variables
            for field in ['model_name', 'temperature', 'enabled', 'max_tokens']:
                env_var = f"AGENT_{agent_id.upper()}_{field.upper()}"
                env_value = os.getenv(env_var)
                if env_value is not None:
                    converted_value = self._convert_env_value(env_value, field)
                    if converted_value is not None:
                        config_data['agents'][i][field] = converted_value
                        logger.debug(f"Applied agent env override: {env_var}={converted_value}")
        
        return config_data
    
    def _convert_env_value(self, value: str, field_name: str) -> Any:
        """Convert environment variable string to appropriate type"""
        try:
            # Boolean fields
            if field_name in ['enable_metrics', 'enabled', 'enable_advanced_features', 'detailed_reasoning']:
                return value.lower() in ('true', '1', 'yes', 'on')
            
            # Integer fields
            elif field_name in ['ollama_timeout', 'max_retries', 'max_concurrent_requests', 'response_timeout', 'max_tokens']:
                return int(value)
            
            # Float fields
            elif field_name in ['retry_delay', 'temperature']:
                return float(value)
            
            # String fields
            else:
                return value
                
        except ValueError as e:
            logger.warning(f"Failed to convert env value '{value}' for field '{field_name}': {e}")
            return None
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> bool:
        """Parse configuration data into typed objects"""
        try:
            # Parse system configuration
            system_data = config_data.get('system', {})
            self.system_config = SystemConfig(**system_data)
            
            # Parse agent configurations
            self.agents = {}
            for agent_data in config_data.get('agents', []):
                agent = AgentConfig(**agent_data)
                self.agents[agent.agent_id] = agent
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to parse configuration data: {e}")
            return False
    
    def validate_config(self) -> bool:
        """Validate the loaded configuration"""
        self.validation_errors = []
        
        # Validate system configuration
        system_errors = ConfigValidator.validate_system_config(self.system_config)
        self.validation_errors.extend(system_errors)
        
        # Validate individual agent configurations
        for agent_id, agent in self.agents.items():
            agent_errors = ConfigValidator.validate_agent_config(agent)
            # Prefix agent errors with agent ID for clarity
            for error in agent_errors:
                error.field = f"{agent_id}.{error.field}"
            self.validation_errors.extend(agent_errors)
        
        # Validate agents collection
        collection_errors = ConfigValidator.validate_agents_collection(self.agents)
        self.validation_errors.extend(collection_errors)
        
        # Log validation errors
        if self.validation_errors:
            logger.error("Configuration validation errors:")
            for error in self.validation_errors:
                logger.error(f"  - {error.field}: {error.message} (value: {error.value})")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def _load_default_config(self) -> bool:
        """Load default configuration as fallback"""
        logger.info("Loading default configuration")
        
        # Create default balanced configuration
        config_data = {
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
            'agents': [
                {
                    'agent_id': 'DataScientist_Alpha',
                    'role': 'Data Scientist',
                    'model_name': 'llama3.1:8b',
                    'temperature': 0.3,
                    'personality': 'analytical/methodical',
                    'enabled': True,
                    'max_tokens': 800,
                    'system_prompt': self._get_default_prompt('DataScientist_Alpha')
                }
            ]
        }
        
        return self._parse_config_data(config_data) and self.validate_config()
    
    def _get_default_prompt(self, agent_id: str) -> str:
        """Get default system prompt for agent"""
        prompts = {
            'DataScientist_Alpha': """You are DataScientist_Alpha, an analytical and methodical data scientist. 
            You approach problems with rigorous analysis, statistical thinking, and evidence-based reasoning.
            Always respond in valid JSON format with the required structure."""
        }
        return prompts.get(agent_id, "You are an AI agent. Respond in JSON format.")
    
    def get_enabled_agents(self) -> Dict[str, AgentConfig]:
        """Get only enabled agents"""
        return {k: v for k, v in self.agents.items() if v.enabled}
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for specific agent"""
        return self.agents.get(agent_id)
    
    def save_config(self, output_file: Optional[str] = None) -> bool:
        """
        Save current configuration to file
        
        Args:
            output_file: Output file path (defaults to current preset)
        """
        try:
            if not output_file:
                output_file = self.config_dir / f"current_{self.preset}.yaml"
            else:
                output_file = Path(output_file)
            
            config_data = {
                'system': asdict(self.system_config),
                'agents': [asdict(agent) for agent in self.agents.values()]
            }
            
            os.makedirs(output_file.parent, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging/status"""
        enabled_agents = self.get_enabled_agents()
        
        return {
            'preset': self.preset,
            'system_config': {
                'ollama_url': self.system_config.ollama_base_url,
                'timeout': self.system_config.ollama_timeout,
                'log_level': self.system_config.log_level,
                'max_concurrent': self.system_config.max_concurrent_requests
            },
            'agents': {
                'total': len(self.agents),
                'enabled': len(enabled_agents),
                'models': list(set(agent.model_name for agent in enabled_agents.values()))
            },
            'validation_errors': len(self.validation_errors)
        }
    
    def switch_preset(self, preset: str) -> bool:
        """Switch to a different configuration preset"""
        old_preset = self.preset
        self.preset = preset
        
        if self.load_config():
            logger.info(f"Switched from '{old_preset}' to '{preset}' preset")
            return True
        else:
            # Revert on failure
            self.preset = old_preset
            logger.error(f"Failed to switch to '{preset}' preset, reverting to '{old_preset}'")
            return False
    
    @staticmethod
    def list_available_presets(config_dir: Optional[str] = None) -> List[str]:
        """List all available configuration presets"""
        if not config_dir:
            config_dir = Path(__file__).parent
        else:
            config_dir = Path(config_dir)
        
        presets_dir = config_dir / "presets"
        if not presets_dir.exists():
            return []
        
        presets = []
        for file in presets_dir.glob("*.yaml"):
            presets.append(file.stem)
        
        return sorted(presets)