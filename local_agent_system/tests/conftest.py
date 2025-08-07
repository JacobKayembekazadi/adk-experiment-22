"""
Pytest configuration and shared fixtures
"""
import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager
from config.config_schema import AgentConfig, SystemConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for config tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_system_config():
    """Sample system configuration for testing"""
    return SystemConfig(
        ollama_base_url="http://localhost:11434",
        ollama_timeout=120,
        max_retries=3,
        retry_delay=1.0,
        log_level="INFO",
        session_save_dir="./test_sessions",
        enable_metrics=True,
        max_concurrent_requests=3,
        response_timeout=60
    )


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing"""
    return AgentConfig(
        agent_id="TestAgent_Alpha",
        role="Test Agent",
        model_name="llama3.2:3b",
        temperature=0.5,
        personality="test-oriented",
        enabled=True,
        max_tokens=800,
        system_prompt="You are a test agent. Always respond in valid JSON format."
    )


@pytest.fixture
def sample_agents_dict(sample_agent_config):
    """Sample agents dictionary for testing"""
    return {
        "TestAgent_Alpha": sample_agent_config,
        "TestAgent_Beta": AgentConfig(
            agent_id="TestAgent_Beta",
            role="Another Test Agent",
            model_name="llama3.2:3b",
            temperature=0.3,
            personality="analytical",
            enabled=True,
            max_tokens=600,
            system_prompt="You are another test agent."
        )
    }


@pytest.fixture
def sample_valid_json_response():
    """Valid JSON response that an agent might return"""
    return {
        "agent_id": "TestAgent_Alpha",
        "main_response": "This is a test response with analytical insights.",
        "confidence_level": 0.85,
        "key_insights": [
            "First key insight about the problem",
            "Second insight with data considerations",
            "Third insight about implementation"
        ],
        "questions_for_others": [
            "What are the technical constraints?",
            "How does this align with user needs?"
        ],
        "next_action": "Gather additional data and validate assumptions",
        "reasoning": "Based on the problem analysis, we need more data to proceed confidently."
    }


@pytest.fixture
def sample_malformed_responses():
    """Various malformed responses for testing parser robustness"""
    return [
        # Missing closing brace
        '{"agent_id": "TestAgent", "main_response": "incomplete',
        # Invalid JSON with extra comma
        '{"agent_id": "TestAgent", "main_response": "test",}',
        # Mixed content (JSON + text)
        'Some text before {"agent_id": "TestAgent", "main_response": "test"} and after',
        # Nested incomplete JSON
        '{"outer": {"agent_id": "TestAgent", "incomplete": ',
        # Valid JSON but wrong structure
        '{"wrong_field": "value", "not_agent_response": true}',
        # Empty response
        '',
        # Non-JSON response
        'This is just plain text without any JSON structure.',
        # Multiple JSON objects
        '{"first": "object"}{"second": "object"}'
    ]


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing without actual Ollama"""
    mock_client = AsyncMock()
    
    # Mock successful response
    mock_client.generate.return_value = {
        "response": json.dumps({
            "agent_id": "TestAgent_Alpha",
            "main_response": "Mock response from agent",
            "confidence_level": 0.8,
            "key_insights": ["Mock insight 1", "Mock insight 2"],
            "questions_for_others": ["Mock question?"],
            "next_action": "Mock next action",
            "reasoning": "Mock reasoning"
        }),
        "done": True,
        "total_duration": 1000000000,  # 1 second in nanoseconds
        "load_duration": 100000000,
        "prompt_eval_count": 50,
        "eval_count": 100
    }
    
    # Mock list models response
    mock_client.list.return_value = {
        "models": [
            {"name": "llama3.2:3b", "size": 2000000000},
            {"name": "llama3.1:8b", "size": 5000000000},
            {"name": "qwen2.5:7b", "size": 4000000000}
        ]
    }
    
    return mock_client


@pytest.fixture
def mock_collaboration_results():
    """Mock collaboration results for integration testing"""
    return {
        "session_id": "test_session_123",
        "results": {
            "phase1_analysis": {
                "TestAgent_Alpha": {
                    "agent_id": "TestAgent_Alpha",
                    "main_response": "Phase 1 analysis from Alpha",
                    "confidence_level": 0.8,
                    "key_insights": ["Insight 1", "Insight 2"],
                    "questions_for_others": ["Question 1?"],
                    "next_action": "Move to critique phase",
                    "reasoning": "Analysis complete"
                }
            },
            "phase2_critique": {
                "TestAgent_Alpha": {
                    "agent_id": "TestAgent_Alpha", 
                    "main_response": "Critique from Alpha",
                    "confidence_level": 0.7,
                    "key_insights": ["Critique insight"],
                    "questions_for_others": ["Critique question?"],
                    "next_action": "Synthesize findings",
                    "reasoning": "Critique reasoning"
                }
            },
            "phase3_synthesis": {
                "TestAgent_Alpha": {
                    "agent_id": "TestAgent_Alpha",
                    "main_response": "Synthesis from Alpha", 
                    "confidence_level": 0.9,
                    "key_insights": ["Synthesis insight"],
                    "questions_for_others": [],
                    "next_action": "Build consensus",
                    "reasoning": "Synthesis reasoning"
                }
            },
            "phase4_consensus": {
                "main_response": "Final consensus response",
                "confidence_level": 0.85,
                "key_insights": ["Final insight 1", "Final insight 2"],
                "next_action": "Implement solution",
                "contributing_agents": ["TestAgent_Alpha", "TestAgent_Beta"],
                "reasoning": "Consensus reached through collaboration"
            }
        },
        "metrics": {
            "total_duration": 45.2,
            "success_rate": 1.0,
            "phase_durations": {
                "phase1_analysis": 10.1,
                "phase2_critique": 12.3,
                "phase3_synthesis": 11.8,
                "phase4_consensus": 11.0
            },
            "agent_performance": {
                "TestAgent_Alpha": {"avg_response_time": 8.5, "success_rate": 1.0}
            }
        }
    }


@pytest.fixture
def performance_test_problems():
    """Set of problems for performance testing"""
    return [
        "How can we improve customer retention?",
        "What are the key technical challenges?", 
        "Design a marketing strategy for a new product",
        "Analyze the risks of this approach",
        "What are the scalability considerations?"
    ]


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    return {
        "AGENT_SYSTEM_OLLAMA_URL": "http://test-host:11434",
        "AGENT_SYSTEM_LOG_LEVEL": "DEBUG",
        "AGENT_SYSTEM_MAX_RETRIES": "5",
        "AGENT_TESTAGENT_ALPHA_MODEL_NAME": "custom-model",
        "AGENT_TESTAGENT_ALPHA_TEMPERATURE": "0.7"
    }


@pytest.fixture
def clean_env():
    """Clean environment variables before/after test"""
    original_env = os.environ.copy()
    # Remove any agent system env vars
    for key in list(os.environ.keys()):
        if key.startswith("AGENT_SYSTEM_") or key.startswith("AGENT_"):
            del os.environ[key]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Performance testing utilities
@pytest.fixture
def benchmark_config():
    """Configuration for benchmark tests"""
    return {
        "iterations": 10,
        "timeout": 30.0,
        "warmup_iterations": 2,
        "memory_threshold_mb": 500,
        "response_time_threshold_s": 2.0
    }