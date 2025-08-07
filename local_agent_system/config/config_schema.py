"""
Configuration schema definitions and validation
"""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import re

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ConfigPreset(Enum):
    LIGHT = "light"
    BALANCED = "balanced"
    PREMIUM = "premium"

@dataclass
class ValidationError:
    field: str
    message: str
    value: Any = None

@dataclass
class AgentConfig:
    agent_id: str
    role: str
    model_name: str
    temperature: float
    personality: str
    system_prompt: str
    enabled: bool = True
    max_tokens: int = 800
    data_requirements: List[str] = field(default_factory=list)
    metrics_suggestions: List[str] = field(default_factory=list)
    stakeholder_impact: List[str] = field(default_factory=list)
    market_considerations: List[str] = field(default_factory=list)
    architecture_patterns: List[str] = field(default_factory=list)
    scalability_concerns: List[str] = field(default_factory=list)
    security_considerations: List[str] = field(default_factory=list)
    alternative_approaches: List[str] = field(default_factory=list)
    disruptive_opportunities: List[str] = field(default_factory=list)
    risk_categories: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    contingency_plans: List[str] = field(default_factory=list)
    quality_metrics: List[str] = field(default_factory=list)
    testing_strategies: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)

@dataclass
class SystemConfig:
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"
    session_save_dir: str = "./sessions"
    enable_metrics: bool = True
    max_concurrent_requests: int = 3
    response_timeout: int = 60
    enable_advanced_features: bool = False
    detailed_reasoning: bool = False

class ConfigValidator:
    """Configuration validator with comprehensive validation rules"""
    
    @staticmethod
    def validate_system_config(config: SystemConfig) -> List[ValidationError]:
        """Validate system configuration"""
        errors = []
        
        # URL validation
        url_pattern = re.compile(r'^https?://[\w\-.]+(:\d+)?(/.*)?$')
        if not url_pattern.match(config.ollama_base_url):
            errors.append(ValidationError(
                "ollama_base_url", 
                "Invalid URL format", 
                config.ollama_base_url
            ))
        
        # Timeout validation
        if config.ollama_timeout <= 0 or config.ollama_timeout > 3600:
            errors.append(ValidationError(
                "ollama_timeout", 
                "Timeout must be between 1 and 3600 seconds", 
                config.ollama_timeout
            ))
        
        # Retry validation
        if config.max_retries < 0 or config.max_retries > 10:
            errors.append(ValidationError(
                "max_retries", 
                "Max retries must be between 0 and 10", 
                config.max_retries
            ))
        
        # Retry delay validation
        if config.retry_delay < 0 or config.retry_delay > 60:
            errors.append(ValidationError(
                "retry_delay", 
                "Retry delay must be between 0 and 60 seconds", 
                config.retry_delay
            ))
        
        # Log level validation
        valid_log_levels = [level.value for level in LogLevel]
        if config.log_level not in valid_log_levels:
            errors.append(ValidationError(
                "log_level", 
                f"Log level must be one of: {', '.join(valid_log_levels)}", 
                config.log_level
            ))
        
        # Concurrent requests validation
        if config.max_concurrent_requests <= 0 or config.max_concurrent_requests > 10:
            errors.append(ValidationError(
                "max_concurrent_requests", 
                "Max concurrent requests must be between 1 and 10", 
                config.max_concurrent_requests
            ))
        
        # Response timeout validation
        if config.response_timeout <= 0 or config.response_timeout > 600:
            errors.append(ValidationError(
                "response_timeout", 
                "Response timeout must be between 1 and 600 seconds", 
                config.response_timeout
            ))
        
        return errors
    
    @staticmethod
    def validate_agent_config(config: AgentConfig) -> List[ValidationError]:
        """Validate agent configuration"""
        errors = []
        
        # Agent ID validation
        if not config.agent_id or not config.agent_id.strip():
            errors.append(ValidationError(
                "agent_id", 
                "Agent ID cannot be empty", 
                config.agent_id
            ))
        
        agent_id_pattern = re.compile(r'^[a-zA-Z0-9_]+$')
        if config.agent_id and not agent_id_pattern.match(config.agent_id):
            errors.append(ValidationError(
                "agent_id", 
                "Agent ID can only contain letters, numbers, and underscores", 
                config.agent_id
            ))
        
        # Role validation
        if not config.role or not config.role.strip():
            errors.append(ValidationError(
                "role", 
                "Role cannot be empty", 
                config.role
            ))
        
        # Model name validation
        if not config.model_name or not config.model_name.strip():
            errors.append(ValidationError(
                "model_name", 
                "Model name cannot be empty", 
                config.model_name
            ))
        
        # Temperature validation
        if config.temperature < 0 or config.temperature > 2:
            errors.append(ValidationError(
                "temperature", 
                "Temperature must be between 0 and 2", 
                config.temperature
            ))
        
        # Max tokens validation
        if config.max_tokens <= 0 or config.max_tokens > 4000:
            errors.append(ValidationError(
                "max_tokens", 
                "Max tokens must be between 1 and 4000", 
                config.max_tokens
            ))
        
        # System prompt validation
        if not config.system_prompt or not config.system_prompt.strip():
            errors.append(ValidationError(
                "system_prompt", 
                "System prompt cannot be empty", 
                config.system_prompt
            ))
        
        return errors
    
    @staticmethod
    def validate_agents_collection(agents: Dict[str, AgentConfig]) -> List[ValidationError]:
        """Validate collection of agents"""
        errors = []
        
        if not agents:
            errors.append(ValidationError(
                "agents", 
                "At least one agent must be configured", 
                len(agents)
            ))
        
        # Check for duplicate agent IDs
        agent_ids = [agent.agent_id for agent in agents.values()]
        duplicates = set([x for x in agent_ids if agent_ids.count(x) > 1])
        if duplicates:
            errors.append(ValidationError(
                "agents", 
                f"Duplicate agent IDs found: {', '.join(duplicates)}", 
                duplicates
            ))
        
        # Ensure at least one enabled agent
        enabled_agents = [agent for agent in agents.values() if agent.enabled]
        if not enabled_agents:
            errors.append(ValidationError(
                "agents", 
                "At least one agent must be enabled", 
                len(enabled_agents)
            ))
        
        return errors