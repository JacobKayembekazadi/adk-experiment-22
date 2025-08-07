"""
Integration tests for collaboration flow
These tests require Ollama to be running and can be skipped if not available
"""
import pytest
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import patch

from collaboration.system import LocalAgent2AgentSystem
from config.config_manager import ConfigManager
from utils.ollama_client import OllamaClient


# Skip integration tests if Ollama is not available
def pytest_configure(config):
    """Configure pytest with Ollama availability check"""
    config.addinivalue_line("markers", "integration: mark test as integration test requiring Ollama")
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture(scope="session")
async def ollama_available():
    """Check if Ollama is available for integration tests"""
    try:
        async with OllamaClient() as client:
            return await client.test_connection()
    except Exception:
        return False


@pytest.fixture
def integration_config_dir(temp_config_dir):
    """Create test configuration for integration tests"""
    # Create a minimal test configuration
    config_data = {
        'system': {
            'ollama_base_url': 'http://localhost:11434',
            'ollama_timeout': 60,  # Shorter timeout for tests
            'max_retries': 2,  # Fewer retries for tests
            'retry_delay': 0.5,
            'log_level': 'INFO',
            'session_save_dir': str(temp_config_dir / 'sessions'),
            'enable_metrics': True,
            'max_concurrent_requests': 2,
            'response_timeout': 30
        },
        'agents': [
            {
                'agent_id': 'TestAnalyst_Alpha',
                'role': 'Test Analyst',
                'model_name': 'llama3.2:3b',  # Use smaller model for faster tests
                'temperature': 0.3,
                'personality': 'analytical/methodical',
                'enabled': True,
                'max_tokens': 400,  # Shorter responses for faster tests
                'system_prompt': '''You are TestAnalyst_Alpha, a test analyst.
                Analyze problems systematically and provide structured responses.
                Always respond in valid JSON format with this structure:
                {
                  "agent_id": "TestAnalyst_Alpha",
                  "main_response": "your analysis (keep it concise for testing)",
                  "confidence_level": 0.0-1.0,
                  "key_insights": ["insight1", "insight2"],
                  "questions_for_others": ["question1?"],
                  "next_action": "suggested next step",
                  "reasoning": "your reasoning (brief for testing)"
                }'''
            },
            {
                'agent_id': 'TestReviewer_Beta',
                'role': 'Test Reviewer',
                'model_name': 'llama3.2:3b',
                'temperature': 0.5,
                'personality': 'critical/thorough',
                'enabled': True,
                'max_tokens': 400,
                'system_prompt': '''You are TestReviewer_Beta, a test reviewer.
                Review and critique analyses from other agents.
                Always respond in valid JSON format with this structure:
                {
                  "agent_id": "TestReviewer_Beta",
                  "main_response": "your review (concise for testing)",
                  "confidence_level": 0.0-1.0,
                  "key_insights": ["insight1", "insight2"],
                  "questions_for_others": ["question1?"],
                  "next_action": "suggested next step",
                  "reasoning": "your reasoning (brief for testing)"
                }'''
            }
        ]
    }
    
    # Save test configuration
    config_file = temp_config_dir / "test_integration.yaml"
    with open(config_file, 'w') as f:
        import yaml
        yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    return temp_config_dir, config_file


class TestCollaborationIntegration:
    """Integration tests for collaboration system"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_system_initialization_integration(self, integration_config_dir, ollama_available):
        """Test system initialization with real Ollama connection"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        config_dir, config_file = integration_config_dir
        
        system = LocalAgent2AgentSystem(config_file=str(config_file))
        
        try:
            success = await system.initialize_system()
            assert success is True
            assert len(system.agents) == 2
            
            # Check agent status
            for agent in system.agents.values():
                assert agent.is_initialized is True
                status = agent.get_status()
                assert status["initialized"] is True
                
        finally:
            await system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_single_phase_execution(self, integration_config_dir, ollama_available):
        """Test individual phase execution with real agents"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        config_dir, config_file = integration_config_dir
        system = LocalAgent2AgentSystem(config_file=str(config_file))
        
        try:
            await system.initialize_system()
            
            # Test simple problem
            problem = "What are the key factors to consider when testing software?"
            
            # Execute Phase 1 - Analysis
            analysis_results = await system._run_phase1_analysis(problem)
            
            assert len(analysis_results) == 2
            assert "TestAnalyst_Alpha" in analysis_results
            assert "TestReviewer_Beta" in analysis_results
            
            # Check response structure
            for agent_id, response in analysis_results.items():
                assert response["agent_id"] == agent_id
                assert isinstance(response["confidence_level"], (int, float))
                assert 0.0 <= response["confidence_level"] <= 1.0
                assert isinstance(response["main_response"], str)
                assert len(response["main_response"]) > 0
                assert isinstance(response["key_insights"], list)
                assert isinstance(response["questions_for_others"], list)
                
        finally:
            await system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_full_collaboration_flow_integration(self, integration_config_dir, ollama_available):
        """Test complete collaboration flow end-to-end with real agents"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        config_dir, config_file = integration_config_dir
        system = LocalAgent2AgentSystem(config_file=str(config_file))
        
        try:
            await system.initialize_system()
            
            # Run full collaboration on a simple problem
            problem = "How should we approach quality assurance for a new software feature?"
            
            result = await system.run_collaborative_problem_solving(problem)
            
            # Verify complete result structure
            assert result is not None
            assert "session_id" in result
            assert "results" in result
            assert "metrics" in result
            
            # Check all phases completed
            results = result["results"]
            assert "phase1_analysis" in results
            assert "phase2_critique" in results
            assert "phase3_synthesis" in results
            assert "phase4_consensus" in results
            
            # Verify each phase has expected agents
            assert len(results["phase1_analysis"]) == 2
            assert len(results["phase2_critique"]) == 2
            assert len(results["phase3_synthesis"]) == 2
            
            # Check consensus structure
            consensus = results["phase4_consensus"]
            assert "main_response" in consensus
            assert "confidence_level" in consensus
            assert "contributing_agents" in consensus
            assert isinstance(consensus["confidence_level"], (int, float))
            assert 0.0 <= consensus["confidence_level"] <= 1.0
            
            # Verify metrics
            metrics = result["metrics"]
            assert "total_duration" in metrics
            assert "success_rate" in metrics
            assert "phase_durations" in metrics
            assert metrics["success_rate"] > 0  # At least some success
            assert metrics["total_duration"] > 0
            
            # Check session was saved
            session_dir = Path(config_dir) / "sessions"
            assert session_dir.exists()
            session_files = list(session_dir.glob("session_*.json"))
            assert len(session_files) >= 1
            
        finally:
            await system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, integration_config_dir, ollama_available):
        """Test error handling with real system components"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        config_dir, config_file = integration_config_dir
        
        # Test with invalid model name
        invalid_config_data = {
            'system': {
                'ollama_base_url': 'http://localhost:11434',
                'ollama_timeout': 30,
                'max_retries': 1,
                'retry_delay': 0.1
            },
            'agents': [{
                'agent_id': 'InvalidAgent',
                'role': 'Invalid Agent',
                'model_name': 'nonexistent-model:latest',  # Invalid model
                'temperature': 0.5,
                'personality': 'test',
                'enabled': True,
                'max_tokens': 400,
                'system_prompt': 'Test agent with invalid model.'
            }]
        }
        
        # Save invalid configuration
        invalid_config_file = config_dir / "invalid_config.yaml"
        with open(invalid_config_file, 'w') as f:
            import yaml
            yaml.dump(invalid_config_data, f)
        
        system = LocalAgent2AgentSystem(config_file=str(invalid_config_file))
        
        try:
            # System should handle initialization gracefully
            success = await system.initialize_system()
            
            if success:
                # If initialization succeeded (maybe validation is disabled), 
                # test that agent failure is handled gracefully
                problem = "Test problem"
                analysis_results = await system._run_phase1_analysis(problem)
                
                # Should get fallback responses for failed agents
                for agent_response in analysis_results.values():
                    assert agent_response["confidence_level"] == 0.0  # Error response
            
        finally:
            await system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_configuration_presets_integration(self, temp_config_dir, ollama_available):
        """Test different configuration presets with real system"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        # Create light preset configuration
        light_config = {
            'system': {
                'ollama_base_url': 'http://localhost:11434',
                'ollama_timeout': 30,
                'max_retries': 1,
                'log_level': 'WARNING',
                'enable_metrics': False
            },
            'agents': [{
                'agent_id': 'LightAgent',
                'role': 'Light Agent',
                'model_name': 'llama3.2:3b',
                'temperature': 0.3,
                'personality': 'efficient',
                'enabled': True,
                'max_tokens': 200,
                'system_prompt': '''You are LightAgent, optimized for speed.
                Provide brief, structured responses in JSON format:
                {"agent_id": "LightAgent", "main_response": "brief response", 
                 "confidence_level": 0.7, "key_insights": ["insight"], 
                 "questions_for_others": [], "next_action": "action", "reasoning": "brief"}'''
            }]
        }
        
        # Create presets directory and file
        presets_dir = temp_config_dir / "presets"
        presets_dir.mkdir(exist_ok=True)
        
        with open(presets_dir / "light.yaml", 'w') as f:
            import yaml
            yaml.dump(light_config, f)
        
        system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir), preset="light")
        
        try:
            success = await system.initialize_system()
            assert success is True
            
            # Quick test with light configuration
            problem = "Brief test question?"
            analysis_results = await system._run_phase1_analysis(problem)
            
            assert len(analysis_results) == 1
            assert "LightAgent" in analysis_results
            
            # Response should be brief (light config)
            response = analysis_results["LightAgent"]
            assert len(response["main_response"]) > 0
            
        finally:
            await system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests_integration(self, integration_config_dir, ollama_available):
        """Test concurrent request handling"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        config_dir, config_file = integration_config_dir
        system = LocalAgent2AgentSystem(config_file=str(config_file))
        
        try:
            await system.initialize_system()
            
            # Test concurrent phase execution
            problems = [
                "How to test user interfaces?",
                "What makes good test data?",
                "How to measure test coverage?"
            ]
            
            # Run multiple problems concurrently (but use same system)
            tasks = []
            for problem in problems:
                task = asyncio.create_task(system._run_phase1_analysis(problem))
                tasks.append(task)
            
            # Wait for all tasks to complete
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that most requests succeeded
            successful_results = [r for r in results_list if not isinstance(r, Exception)]
            assert len(successful_results) >= len(problems) // 2  # At least half should succeed
            
            # Check structure of successful results
            for results in successful_results:
                if isinstance(results, dict):
                    assert len(results) == 2  # Should have responses from both agents
                    for response in results.values():
                        assert "agent_id" in response
                        assert "confidence_level" in response
            
        finally:
            await system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio 
    async def test_session_persistence_integration(self, integration_config_dir, ollama_available):
        """Test session persistence with real data"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        config_dir, config_file = integration_config_dir
        system = LocalAgent2AgentSystem(config_file=str(config_file))
        
        try:
            await system.initialize_system()
            
            problem = "What are effective testing strategies?"
            result = await system.run_collaborative_problem_solving(problem)
            
            # Verify session was saved
            session_id = result["session_id"]
            session_dir = Path(config_dir) / "sessions"
            session_file = session_dir / f"session_{session_id}.json"
            
            assert session_file.exists()
            
            # Load and verify session content
            with open(session_file, 'r') as f:
                saved_session = json.load(f)
            
            assert saved_session["session_id"] == session_id
            assert saved_session["problem"] == problem
            assert "results" in saved_session
            assert "metrics" in saved_session
            assert "timestamp" in saved_session
            
            # Verify all phases are saved
            assert "phase1_analysis" in saved_session["results"]
            assert "phase2_critique" in saved_session["results"]
            assert "phase3_synthesis" in saved_session["results"]
            assert "phase4_consensus" in saved_session["results"]
            
        finally:
            await system.cleanup()


class TestEnvironmentVariableIntegration:
    """Test environment variable integration with real system"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_env_var_overrides_integration(self, temp_config_dir, ollama_available):
        """Test environment variable overrides in real system"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        # Create base configuration
        base_config = {
            'system': {
                'ollama_base_url': 'http://localhost:11434',
                'log_level': 'INFO',
                'enable_metrics': True
            },
            'agents': [{
                'agent_id': 'EnvTestAgent',
                'role': 'Environment Test Agent',
                'model_name': 'llama3.2:3b',
                'temperature': 0.5,
                'personality': 'adaptable',
                'enabled': True,
                'max_tokens': 300,
                'system_prompt': 'Test agent for environment variable testing.'
            }]
        }
        
        config_file = temp_config_dir / "env_test.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(base_config, f)
        
        # Set environment variables to override configuration
        env_overrides = {
            'AGENT_SYSTEM_LOG_LEVEL': 'DEBUG',
            'AGENT_SYSTEM_ENABLE_METRICS': 'false',
            'AGENT_ENVTESTAGENT_TEMPERATURE': '0.8',
            'AGENT_ENVTESTAGENT_MAX_TOKENS': '500'
        }
        
        with patch.dict(os.environ, env_overrides):
            system = LocalAgent2AgentSystem(config_file=str(config_file))
            
            try:
                success = await system.initialize_system()
                assert success is True
                
                # Verify environment overrides were applied
                config_summary = system.config_manager.get_config_summary()
                
                # Check system config overrides
                assert config_summary['system_config']['log_level'] == 'DEBUG'
                
                # Check agent config overrides (through agent status)
                agent_status = system.agents['EnvTestAgent'].get_status()
                # Note: Some overrides might not be visible in status depending on implementation
                
            finally:
                await system.cleanup()


class TestModelCompatibilityIntegration:
    """Test compatibility with different models"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_different_models_integration(self, temp_config_dir, ollama_available):
        """Test system works with different available models"""
        if not ollama_available:
            pytest.skip("Ollama not available for integration test")
        
        # First, check what models are available
        async with OllamaClient() as client:
            available_models = await client.list_models()
        
        if not available_models:
            pytest.skip("No models available in Ollama")
        
        # Use first available model
        test_model = available_models[0]
        
        # Create configuration with available model
        model_config = {
            'system': {
                'ollama_base_url': 'http://localhost:11434',
                'ollama_timeout': 45,
                'max_retries': 2
            },
            'agents': [{
                'agent_id': 'ModelTestAgent',
                'role': 'Model Compatibility Agent',
                'model_name': test_model,
                'temperature': 0.4,
                'personality': 'adaptable',
                'enabled': True,
                'max_tokens': 300,
                'system_prompt': f'''You are ModelTestAgent using {test_model}.
                Respond in JSON format: {{"agent_id": "ModelTestAgent", 
                "main_response": "response", "confidence_level": 0.7, 
                "key_insights": ["insight"], "questions_for_others": [], 
                "next_action": "action", "reasoning": "reasoning"}}'''
            }]
        }
        
        config_file = temp_config_dir / "model_test.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(model_config, f)
        
        system = LocalAgent2AgentSystem(config_file=str(config_file))
        
        try:
            success = await system.initialize_system()
            assert success is True
            
            # Test basic functionality
            problem = "Simple test with available model"
            analysis_results = await system._run_phase1_analysis(problem)
            
            assert len(analysis_results) == 1
            assert "ModelTestAgent" in analysis_results
            
            response = analysis_results["ModelTestAgent"]
            assert response["agent_id"] == "ModelTestAgent"
            assert isinstance(response["confidence_level"], (int, float))
            
        finally:
            await system.cleanup()