"""
Unit tests for configuration system
"""
import pytest
import os
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from config.config_manager import ConfigManager
from config.config_schema import (
    AgentConfig, SystemConfig, ConfigValidator, ValidationError, ConfigPreset
)
from config.settings import get_config_manager, LegacyConfigManager


class TestSystemConfig:
    """Test cases for SystemConfig dataclass"""
    
    def test_system_config_defaults(self):
        """Test default values for SystemConfig"""
        config = SystemConfig()
        
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.ollama_timeout == 120
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.log_level == "INFO"
        assert config.session_save_dir == "./sessions"
        assert config.enable_metrics is True
        assert config.max_concurrent_requests == 3
        assert config.response_timeout == 60
        assert config.enable_advanced_features is False
        assert config.detailed_reasoning is False
    
    def test_system_config_custom_values(self):
        """Test SystemConfig with custom values"""
        config = SystemConfig(
            ollama_base_url="http://custom-host:8080",
            ollama_timeout=180,
            max_retries=5,
            log_level="DEBUG"
        )
        
        assert config.ollama_base_url == "http://custom-host:8080"
        assert config.ollama_timeout == 180
        assert config.max_retries == 5
        assert config.log_level == "DEBUG"


class TestAgentConfig:
    """Test cases for AgentConfig dataclass"""
    
    def test_agent_config_required_fields(self):
        """Test AgentConfig with required fields"""
        config = AgentConfig(
            agent_id="TestAgent",
            role="Tester",
            model_name="test-model",
            temperature=0.5,
            personality="test-oriented",
            system_prompt="Test prompt"
        )
        
        assert config.agent_id == "TestAgent"
        assert config.role == "Tester"
        assert config.model_name == "test-model"
        assert config.temperature == 0.5
        assert config.personality == "test-oriented"
        assert config.system_prompt == "Test prompt"
        assert config.enabled is True  # Default value
        assert config.max_tokens == 800  # Default value
    
    def test_agent_config_with_defaults(self):
        """Test AgentConfig default values"""
        config = AgentConfig(
            agent_id="TestAgent",
            role="Tester",
            model_name="test-model",
            temperature=0.5,
            personality="test-oriented",
            system_prompt="Test prompt",
            enabled=False,
            max_tokens=1000
        )
        
        assert config.enabled is False
        assert config.max_tokens == 1000


class TestConfigValidator:
    """Test cases for ConfigValidator"""
    
    def test_validate_system_config_valid(self, sample_system_config):
        """Test validation of valid system configuration"""
        errors = ConfigValidator.validate_system_config(sample_system_config)
        assert len(errors) == 0
    
    def test_validate_system_config_invalid_url(self):
        """Test validation fails with invalid URL"""
        config = SystemConfig(ollama_base_url="not-a-valid-url")
        errors = ConfigValidator.validate_system_config(config)
        
        assert len(errors) > 0
        assert any("Invalid URL format" in error.message for error in errors)
    
    def test_validate_system_config_invalid_timeout(self):
        """Test validation fails with invalid timeout values"""
        # Test negative timeout
        config = SystemConfig(ollama_timeout=-10)
        errors = ConfigValidator.validate_system_config(config)
        assert any("between 1 and 3600 seconds" in error.message for error in errors)
        
        # Test excessive timeout
        config = SystemConfig(ollama_timeout=5000)
        errors = ConfigValidator.validate_system_config(config)
        assert any("between 1 and 3600 seconds" in error.message for error in errors)
    
    def test_validate_system_config_invalid_retries(self):
        """Test validation fails with invalid retry values"""
        config = SystemConfig(max_retries=-1)
        errors = ConfigValidator.validate_system_config(config)
        assert any("between 0 and 10" in error.message for error in errors)
        
        config = SystemConfig(max_retries=20)
        errors = ConfigValidator.validate_system_config(config)
        assert any("between 0 and 10" in error.message for error in errors)
    
    def test_validate_system_config_invalid_log_level(self):
        """Test validation fails with invalid log level"""
        config = SystemConfig(log_level="INVALID")
        errors = ConfigValidator.validate_system_config(config)
        assert any("Log level must be one of" in error.message for error in errors)
    
    def test_validate_agent_config_valid(self, sample_agent_config):
        """Test validation of valid agent configuration"""
        errors = ConfigValidator.validate_agent_config(sample_agent_config)
        assert len(errors) == 0
    
    def test_validate_agent_config_empty_fields(self):
        """Test validation fails with empty required fields"""
        config = AgentConfig(
            agent_id="",
            role="",
            model_name="",
            temperature=0.5,
            personality="test",
            system_prompt=""
        )
        errors = ConfigValidator.validate_agent_config(config)
        
        assert len(errors) >= 4  # Should have errors for empty fields
        error_messages = [error.message for error in errors]
        assert any("Agent ID cannot be empty" in msg for msg in error_messages)
        assert any("Role cannot be empty" in msg for msg in error_messages)
        assert any("Model name cannot be empty" in msg for msg in error_messages)
        assert any("System prompt cannot be empty" in msg for msg in error_messages)
    
    def test_validate_agent_config_invalid_agent_id(self):
        """Test validation fails with invalid agent ID format"""
        config = AgentConfig(
            agent_id="Invalid-Agent-ID!",
            role="Tester",
            model_name="test-model",
            temperature=0.5,
            personality="test",
            system_prompt="Test prompt"
        )
        errors = ConfigValidator.validate_agent_config(config)
        
        assert any("can only contain letters, numbers, and underscores" in error.message 
                  for error in errors)
    
    def test_validate_agent_config_invalid_temperature(self):
        """Test validation fails with invalid temperature"""
        config = AgentConfig(
            agent_id="TestAgent",
            role="Tester",
            model_name="test-model",
            temperature=3.0,  # Invalid: > 2.0
            personality="test",
            system_prompt="Test prompt"
        )
        errors = ConfigValidator.validate_agent_config(config)
        
        assert any("Temperature must be between 0 and 2" in error.message for error in errors)
    
    def test_validate_agent_config_invalid_max_tokens(self):
        """Test validation fails with invalid max_tokens"""
        config = AgentConfig(
            agent_id="TestAgent",
            role="Tester",
            model_name="test-model",
            temperature=0.5,
            personality="test",
            system_prompt="Test prompt",
            max_tokens=5000  # Invalid: > 4000
        )
        errors = ConfigValidator.validate_agent_config(config)
        
        assert any("between 1 and 4000" in error.message for error in errors)
    
    def test_validate_agents_collection_empty(self):
        """Test validation fails with empty agents collection"""
        errors = ConfigValidator.validate_agents_collection({})
        assert any("At least one agent must be configured" in error.message for error in errors)
    
    def test_validate_agents_collection_duplicate_ids(self, sample_agent_config):
        """Test validation fails with duplicate agent IDs"""
        agents = {
            "agent1": sample_agent_config,
            "agent2": sample_agent_config  # Same config = same agent_id
        }
        errors = ConfigValidator.validate_agents_collection(agents)
        
        assert any("Duplicate agent IDs found" in error.message for error in errors)
    
    def test_validate_agents_collection_no_enabled_agents(self):
        """Test validation fails when no agents are enabled"""
        disabled_agent = AgentConfig(
            agent_id="DisabledAgent",
            role="Tester",
            model_name="test-model",
            temperature=0.5,
            personality="test",
            system_prompt="Test prompt",
            enabled=False
        )
        agents = {"disabled": disabled_agent}
        errors = ConfigValidator.validate_agents_collection(agents)
        
        assert any("At least one agent must be enabled" in error.message for error in errors)


class TestConfigManager:
    """Test cases for ConfigManager"""
    
    def test_config_manager_initialization(self, temp_config_dir):
        """Test ConfigManager initialization"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        
        assert manager.config_dir == temp_config_dir
        assert manager.presets_dir == temp_config_dir / "presets"
        assert isinstance(manager.system_config, SystemConfig)
        assert isinstance(manager.agents, dict)
    
    def test_config_manager_default_preset(self, temp_config_dir):
        """Test ConfigManager with default preset"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        assert manager.preset == "balanced"
    
    def test_config_manager_custom_preset(self, temp_config_dir):
        """Test ConfigManager with custom preset"""
        manager = ConfigManager(config_dir=str(temp_config_dir), preset="light")
        assert manager.preset == "light"
    
    @patch.dict(os.environ, {'AGENT_SYSTEM_PRESET': 'premium'})
    def test_config_manager_env_preset(self, temp_config_dir):
        """Test ConfigManager respects environment variable preset"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        assert manager.preset == "premium"
    
    def test_load_config_from_preset_file(self, temp_config_dir):
        """Test loading configuration from preset file"""
        # Create preset directory and file
        presets_dir = temp_config_dir / "presets"
        presets_dir.mkdir()
        
        preset_config = {
            'system': {
                'ollama_base_url': 'http://test-host:11434',
                'log_level': 'DEBUG'
            },
            'agents': [{
                'agent_id': 'TestAgent',
                'role': 'Tester',
                'model_name': 'test-model',
                'temperature': 0.5,
                'personality': 'test-oriented',
                'system_prompt': 'Test prompt',
                'enabled': True,
                'max_tokens': 800
            }]
        }
        
        preset_file = presets_dir / "test.yaml"
        with open(preset_file, 'w') as f:
            yaml.dump(preset_config, f)
        
        manager = ConfigManager(config_dir=str(temp_config_dir), preset="test")
        success = manager.load_config()
        
        assert success is True
        assert manager.system_config.ollama_base_url == "http://test-host:11434"
        assert manager.system_config.log_level == "DEBUG"
        assert len(manager.agents) == 1
        assert "TestAgent" in manager.agents
    
    def test_load_config_nonexistent_preset(self, temp_config_dir):
        """Test loading configuration with nonexistent preset falls back to default"""
        manager = ConfigManager(config_dir=str(temp_config_dir), preset="nonexistent")
        success = manager.load_config()
        
        # Should fall back to default config
        assert success is True
        assert len(manager.agents) >= 1  # Should have at least one default agent
    
    def test_apply_env_overrides_system_config(self, temp_config_dir):
        """Test environment variable overrides for system configuration"""
        env_vars = {
            'AGENT_SYSTEM_OLLAMA_URL': 'http://env-host:11434',
            'AGENT_SYSTEM_OLLAMA_TIMEOUT': '180',
            'AGENT_SYSTEM_MAX_RETRIES': '5',
            'AGENT_SYSTEM_LOG_LEVEL': 'DEBUG',
            'AGENT_SYSTEM_ENABLE_METRICS': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigManager(config_dir=str(temp_config_dir))
            config_data = {'system': {}, 'agents': []}
            result = manager._apply_env_overrides(config_data)
            
            assert result['system']['ollama_base_url'] == 'http://env-host:11434'
            assert result['system']['ollama_timeout'] == 180
            assert result['system']['max_retries'] == 5
            assert result['system']['log_level'] == 'DEBUG'
            assert result['system']['enable_metrics'] is False
    
    def test_apply_env_overrides_agent_config(self, temp_config_dir):
        """Test environment variable overrides for agent configuration"""
        env_vars = {
            'AGENT_TESTAGENT_MODEL_NAME': 'env-model',
            'AGENT_TESTAGENT_TEMPERATURE': '0.7',
            'AGENT_TESTAGENT_ENABLED': 'false',
            'AGENT_TESTAGENT_MAX_TOKENS': '1000'
        }
        
        config_data = {
            'system': {},
            'agents': [{
                'agent_id': 'TestAgent',
                'role': 'Tester',
                'model_name': 'original-model',
                'temperature': 0.5,
                'personality': 'test',
                'system_prompt': 'Test',
                'enabled': True,
                'max_tokens': 800
            }]
        }
        
        with patch.dict(os.environ, env_vars):
            manager = ConfigManager(config_dir=str(temp_config_dir))
            result = manager._apply_env_overrides(config_data)
            
            agent = result['agents'][0]
            assert agent['model_name'] == 'env-model'
            assert agent['temperature'] == 0.7
            assert agent['enabled'] is False
            assert agent['max_tokens'] == 1000
    
    def test_convert_env_value_types(self, temp_config_dir):
        """Test environment value type conversion"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        
        # Boolean conversions
        assert manager._convert_env_value('true', 'enabled') is True
        assert manager._convert_env_value('false', 'enabled') is False
        assert manager._convert_env_value('1', 'enabled') is True
        assert manager._convert_env_value('0', 'enabled') is False
        
        # Integer conversions
        assert manager._convert_env_value('123', 'ollama_timeout') == 123
        assert manager._convert_env_value('invalid', 'ollama_timeout') is None
        
        # Float conversions
        assert manager._convert_env_value('0.75', 'temperature') == 0.75
        assert manager._convert_env_value('invalid', 'temperature') is None
        
        # String conversions
        assert manager._convert_env_value('test', 'log_level') == 'test'
    
    def test_get_enabled_agents_only(self, temp_config_dir):
        """Test getting only enabled agents"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        manager.agents = {
            'enabled_agent': AgentConfig(
                agent_id='enabled_agent',
                role='Tester',
                model_name='test',
                temperature=0.5,
                personality='test',
                system_prompt='Test',
                enabled=True
            ),
            'disabled_agent': AgentConfig(
                agent_id='disabled_agent',
                role='Tester',
                model_name='test',
                temperature=0.5,
                personality='test',
                system_prompt='Test',
                enabled=False
            )
        }
        
        enabled_agents = manager.get_enabled_agents()
        assert len(enabled_agents) == 1
        assert 'enabled_agent' in enabled_agents
        assert 'disabled_agent' not in enabled_agents
    
    def test_get_agent_config(self, temp_config_dir, sample_agent_config):
        """Test getting specific agent configuration"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        manager.agents = {'TestAgent': sample_agent_config}
        
        agent = manager.get_agent_config('TestAgent')
        assert agent == sample_agent_config
        
        agent = manager.get_agent_config('NonexistentAgent')
        assert agent is None
    
    def test_save_config(self, temp_config_dir, sample_system_config, sample_agent_config):
        """Test saving configuration to file"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        manager.system_config = sample_system_config
        manager.agents = {'TestAgent': sample_agent_config}
        
        success = manager.save_config()
        assert success is True
        
        # Verify file was created and contains expected data
        saved_file = temp_config_dir / "current_balanced.yaml"
        assert saved_file.exists()
        
        with open(saved_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert 'system' in saved_data
        assert 'agents' in saved_data
        assert saved_data['system']['ollama_base_url'] == sample_system_config.ollama_base_url
        assert len(saved_data['agents']) == 1
        assert saved_data['agents'][0]['agent_id'] == 'TestAgent_Alpha'
    
    def test_switch_preset(self, temp_config_dir):
        """Test switching between presets"""
        manager = ConfigManager(config_dir=str(temp_config_dir), preset="balanced")
        
        # Create a mock preset file
        presets_dir = temp_config_dir / "presets"
        presets_dir.mkdir()
        
        light_config = {
            'system': {'log_level': 'WARNING'},
            'agents': [{
                'agent_id': 'LightAgent',
                'role': 'Light',
                'model_name': 'light-model',
                'temperature': 0.3,
                'personality': 'light',
                'system_prompt': 'Light prompt',
                'enabled': True,
                'max_tokens': 500
            }]
        }
        
        with open(presets_dir / "light.yaml", 'w') as f:
            yaml.dump(light_config, f)
        
        success = manager.switch_preset("light")
        assert success is True
        assert manager.preset == "light"
        assert manager.system_config.log_level == "WARNING"
        assert "LightAgent" in manager.agents
    
    def test_list_available_presets(self, temp_config_dir):
        """Test listing available presets"""
        presets_dir = temp_config_dir / "presets"
        presets_dir.mkdir()
        
        # Create some preset files
        for preset_name in ["light", "balanced", "premium"]:
            preset_file = presets_dir / f"{preset_name}.yaml"
            preset_file.write_text("system: {}\nagents: []")
        
        presets = ConfigManager.list_available_presets(str(temp_config_dir))
        assert set(presets) == {"balanced", "light", "premium"}  # Should be sorted
    
    def test_get_config_summary(self, temp_config_dir, sample_system_config, sample_agents_dict):
        """Test getting configuration summary"""
        manager = ConfigManager(config_dir=str(temp_config_dir), preset="test")
        manager.system_config = sample_system_config
        manager.agents = sample_agents_dict
        
        summary = manager.get_config_summary()
        
        assert summary['preset'] == 'test'
        assert summary['system_config']['ollama_url'] == sample_system_config.ollama_base_url
        assert summary['agents']['total'] == 2
        assert summary['agents']['enabled'] == 2  # Both test agents are enabled
        assert len(summary['agents']['models']) >= 1


class TestLegacyConfigManager:
    """Test cases for LegacyConfigManager backward compatibility"""
    
    def test_legacy_config_manager_initialization(self, temp_config_dir):
        """Test LegacyConfigManager loads config on initialization"""
        with patch('config.settings.ConfigManager.load_config') as mock_load:
            mock_load.return_value = True
            manager = LegacyConfigManager(config_dir=str(temp_config_dir))
            mock_load.assert_called_once()
    
    def test_legacy_get_system_status(self, temp_config_dir, sample_system_config, sample_agents_dict):
        """Test legacy get_system_status method"""
        with patch('config.settings.ConfigManager.load_config') as mock_load:
            mock_load.return_value = True
            manager = LegacyConfigManager(config_dir=str(temp_config_dir))
            manager.system_config = sample_system_config
            manager.agents = sample_agents_dict
            
            status = manager.get_system_status()
            
            assert 'agent_count' in status
            assert 'config' in status
            assert 'agents' in status
            assert status['agent_count'] == 2
            assert status['config']['ollama_url'] == sample_system_config.ollama_base_url


class TestConfigManagerIntegration:
    """Integration tests for configuration manager"""
    
    def test_full_config_lifecycle(self, temp_config_dir):
        """Test complete configuration lifecycle"""
        # 1. Create manager and load default config
        manager = ConfigManager(config_dir=str(temp_config_dir))
        success = manager.load_config()
        assert success is True
        
        # 2. Validate configuration
        validation_success = manager.validate_config()
        assert validation_success is True
        
        # 3. Get configuration summary
        summary = manager.get_config_summary()
        assert isinstance(summary, dict)
        assert 'preset' in summary
        assert 'system_config' in summary
        assert 'agents' in summary
        
        # 4. Save configuration
        save_success = manager.save_config()
        assert save_success is True
    
    def test_configuration_with_validation_errors(self, temp_config_dir):
        """Test configuration handling with validation errors"""
        manager = ConfigManager(config_dir=str(temp_config_dir))
        
        # Set invalid configuration
        manager.system_config = SystemConfig(
            ollama_base_url="invalid-url",
            ollama_timeout=-1,
            log_level="INVALID"
        )
        manager.agents = {}  # Empty agents (invalid)
        
        # Validation should fail
        success = manager.validate_config()
        assert success is False
        assert len(manager.validation_errors) > 0
        
        # Summary should report validation errors
        summary = manager.get_config_summary()
        assert summary['validation_errors'] > 0