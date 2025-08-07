# Configuration System

This flexible configuration system supports YAML config files, environment variable overrides, runtime validation, and multiple preset configurations.

## Quick Start

### Using Presets
```bash
# Light configuration (minimal resources)
python main.py --preset light --problem "Your problem"

# Balanced configuration (default)
python main.py --preset balanced --problem "Your problem"

# Premium configuration (maximum capability)
python main.py --preset premium --problem "Your problem"
```

### Using Custom Configuration
```bash
# Use custom config file
python main.py --config my_config.yaml --problem "Your problem"

# List available presets
python main.py --list-presets

# Show current configuration info
python main.py --config-info --preset premium
```

## Environment Variable Overrides

Override any configuration setting using environment variables:

### System Settings
```bash
export AGENT_SYSTEM_OLLAMA_URL="http://custom-host:11434"
export AGENT_SYSTEM_OLLAMA_TIMEOUT="180"
export AGENT_SYSTEM_MAX_RETRIES="5"
export AGENT_SYSTEM_LOG_LEVEL="DEBUG"
export AGENT_SYSTEM_ENABLE_METRICS="true"
export AGENT_SYSTEM_MAX_CONCURRENT="5"
export AGENT_SYSTEM_RESPONSE_TIMEOUT="120"
```

### Agent-Specific Settings
```bash
export AGENT_DATASCIENTIST_ALPHA_MODEL_NAME="llama3.1:8b"
export AGENT_DATASCIENTIST_ALPHA_TEMPERATURE="0.2"
export AGENT_DATASCIENTIST_ALPHA_ENABLED="true"
export AGENT_DATASCIENTIST_ALPHA_MAX_TOKENS="1000"
```

## Configuration Presets

### Light Configuration
- **Purpose**: Minimal resource usage, fast responses
- **Agents**: 2-3 enabled agents
- **Models**: Smaller models (3b parameters)
- **Features**: Basic metrics, shorter timeouts
- **Use Case**: Development, testing, resource-constrained environments

### Balanced Configuration  
- **Purpose**: Good balance of performance and resources
- **Agents**: 5 enabled agents
- **Models**: Mixed sizes (3b-8b parameters)
- **Features**: Full metrics, standard timeouts
- **Use Case**: Production use, general problem-solving

### Premium Configuration
- **Purpose**: Maximum capability and comprehensive analysis
- **Agents**: 6 enabled agents (including QualityAssurance_Zeta)
- **Models**: Larger models with specialized roles
- **Features**: Advanced features, extended prompts, detailed reasoning
- **Use Case**: Complex problems, research, comprehensive analysis

## Configuration File Structure

```yaml
system:
  ollama_base_url: "http://localhost:11434"
  ollama_timeout: 120
  max_retries: 3
  retry_delay: 1.0
  log_level: "INFO"
  session_save_dir: "./sessions"
  enable_metrics: true
  max_concurrent_requests: 3
  response_timeout: 60
  enable_advanced_features: false
  detailed_reasoning: false

agents:
  - agent_id: "DataScientist_Alpha"
    role: "Data Scientist"
    model_name: "llama3.1:8b"
    temperature: 0.3
    personality: "analytical/methodical"
    enabled: true
    max_tokens: 800
    system_prompt: |
      You are DataScientist_Alpha...
```

## Runtime Validation

The configuration system includes comprehensive validation:

- **URL Format**: Validates Ollama URL format
- **Range Validation**: Ensures timeouts, retries, temperatures are within valid ranges
- **Required Fields**: Validates all required agent and system fields
- **Agent Collection**: Ensures at least one enabled agent
- **Duplicate Prevention**: Prevents duplicate agent IDs

### Validation Errors
```bash
# Check for validation errors
python main.py --config-info --preset light

# Output includes validation error count:
# ⚠️ Validation Errors: 2
```

## Programmatic Usage

```python
from config import ConfigManager, get_config_manager

# Load with preset
config_manager = ConfigManager(preset="premium")
config_manager.load_config()

# Get enabled agents only
enabled_agents = config_manager.get_enabled_agents()

# Switch presets at runtime
config_manager.switch_preset("light")

# Get configuration summary
summary = config_manager.get_config_summary()
print(f"Using {summary['agents']['enabled']} of {summary['agents']['total']} agents")

# Validate configuration
if config_manager.validate_config():
    print("Configuration is valid")
else:
    for error in config_manager.validation_errors:
        print(f"Error in {error.field}: {error.message}")
```

## Creating Custom Configurations

1. **Copy an existing preset**:
   ```bash
   cp config/presets/balanced.yaml config/my_custom.yaml
   ```

2. **Modify settings** as needed

3. **Use custom configuration**:
   ```bash
   python main.py --config config/my_custom.yaml --problem "Test problem"
   ```

## Advanced Features

### Configuration Inheritance
Environment variables override YAML settings, allowing you to:
- Use a base preset configuration
- Override specific settings via environment variables
- Maintain different configurations for different environments

### Preset Switching
Switch between presets at runtime:
```python
config_manager = ConfigManager(preset="balanced")
config_manager.switch_preset("premium")  # Switches to premium configuration
```

### Agent Enabling/Disabling
Control which agents participate in collaboration:
```yaml
agents:
  - agent_id: "DataScientist_Alpha"
    enabled: true    # Participates in collaboration
  - agent_id: "TechArchitect_Gamma"  
    enabled: false   # Skipped during collaboration
```

### Model Flexibility
Each preset can use different models optimized for different scenarios:
- **Light**: Fast, smaller models
- **Balanced**: Mixed model sizes
- **Premium**: Larger, more capable models

This system provides maximum flexibility while maintaining simplicity for common use cases.