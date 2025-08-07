"""
Mock tests that don't require Ollama - agent functionality tests
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from unittest.mock import call

from agents.local_agent import LocalAgent
from utils.ollama_client import OllamaClient, GenerationResponse
from utils.response_parser import ResponseParser


class TestMockAgents:
    """Test agent functionality without requiring Ollama"""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create mock Ollama client"""
        mock_client = AsyncMock(spec=OllamaClient)
        
        # Mock successful response
        mock_response = GenerationResponse(
            response=json.dumps({
                "agent_id": "TestAgent_Alpha",
                "main_response": "This is a mock response from the agent",
                "confidence_level": 0.8,
                "key_insights": ["Mock insight 1", "Mock insight 2"],
                "questions_for_others": ["Mock question 1?", "Mock question 2?"],
                "next_action": "Continue with mock analysis",
                "reasoning": "This is mock reasoning"
            }),
            model="llama3.2:3b",
            done=True,
            total_duration=1500000000,  # 1.5 seconds in nanoseconds
            eval_count=150,
            prompt_eval_count=50
        )
        
        mock_client.generate_with_retry.return_value = mock_response
        mock_client.test_connection.return_value = True
        mock_client.list_models.return_value = ["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b"]
        
        return mock_client
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, sample_agent_config):
        """Test agent initialization with mock client"""
        with patch('agents.local_agent.OllamaClient') as mock_client_class:
            mock_client_class.return_value = AsyncMock()
            
            agent = LocalAgent(sample_agent_config)
            
            assert agent.config == sample_agent_config
            assert agent.agent_id == sample_agent_config.agent_id
            assert agent.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_agent_initialize_success(self, sample_agent_config, mock_ollama_client):
        """Test successful agent initialization"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            
            success = await agent.initialize()
            
            assert success is True
            assert agent.is_initialized is True
            mock_ollama_client.test_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_initialize_failure(self, sample_agent_config):
        """Test agent initialization failure"""
        mock_client = AsyncMock()
        mock_client.test_connection.return_value = False
        
        with patch('agents.local_agent.OllamaClient', return_value=mock_client):
            agent = LocalAgent(sample_agent_config)
            
            success = await agent.initialize()
            
            assert success is False
            assert agent.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_agent_analyze_problem(self, sample_agent_config, mock_ollama_client):
        """Test agent problem analysis"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            result = await agent.analyze_problem("Test problem for analysis")
            
            assert result is not None
            assert result["agent_id"] == sample_agent_config.agent_id
            assert result["main_response"] == "This is a mock response from the agent"
            assert result["confidence_level"] == 0.8
            assert len(result["key_insights"]) == 2
            assert len(result["questions_for_others"]) == 2
    
    @pytest.mark.asyncio
    async def test_agent_analyze_problem_not_initialized(self, sample_agent_config):
        """Test agent analysis fails when not initialized"""
        agent = LocalAgent(sample_agent_config)
        
        result = await agent.analyze_problem("Test problem")
        
        assert result is not None
        assert result["agent_id"] == sample_agent_config.agent_id
        assert "not properly initialized" in result["main_response"]
        assert result["confidence_level"] == 0.0
    
    @pytest.mark.asyncio
    async def test_agent_critique_analysis(self, sample_agent_config, mock_ollama_client):
        """Test agent critique functionality"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            # Mock different response for critique
            mock_ollama_client.generate_with_retry.return_value = GenerationResponse(
                response=json.dumps({
                    "agent_id": "TestAgent_Alpha",
                    "main_response": "This is a critique of the analysis",
                    "confidence_level": 0.7,
                    "key_insights": ["Critique insight 1", "Critique insight 2"],
                    "questions_for_others": ["Critique question?"],
                    "next_action": "Refine analysis",
                    "reasoning": "Critique reasoning"
                }),
                model="llama3.2:3b",
                done=True
            )
            
            other_analyses = {
                "OtherAgent": {
                    "main_response": "Other agent's analysis",
                    "confidence_level": 0.9
                }
            }
            
            result = await agent.critique_analysis("Test problem", other_analyses)
            
            assert result is not None
            assert result["agent_id"] == sample_agent_config.agent_id
            assert result["main_response"] == "This is a critique of the analysis"
            assert result["confidence_level"] == 0.7
    
    @pytest.mark.asyncio
    async def test_agent_synthesize_insights(self, sample_agent_config, mock_ollama_client):
        """Test agent synthesis functionality"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            # Mock synthesis response
            mock_ollama_client.generate_with_retry.return_value = GenerationResponse(
                response=json.dumps({
                    "agent_id": "TestAgent_Alpha",
                    "main_response": "Synthesized insights from all analyses",
                    "confidence_level": 0.9,
                    "key_insights": ["Final insight 1", "Final insight 2"],
                    "questions_for_others": [],
                    "next_action": "Build consensus",
                    "reasoning": "Synthesis complete"
                }),
                model="llama3.2:3b",
                done=True
            )
            
            all_analyses = {
                "Agent1": {"main_response": "Analysis 1", "key_insights": ["Insight A"]},
                "Agent2": {"main_response": "Analysis 2", "key_insights": ["Insight B"]}
            }
            
            all_critiques = {
                "Agent1": {"main_response": "Critique 1", "key_insights": ["Critique A"]},
                "Agent2": {"main_response": "Critique 2", "key_insights": ["Critique B"]}
            }
            
            result = await agent.synthesize_insights("Test problem", all_analyses, all_critiques)
            
            assert result is not None
            assert result["agent_id"] == sample_agent_config.agent_id
            assert "Synthesized insights" in result["main_response"]
            assert result["confidence_level"] == 0.9
    
    @pytest.mark.asyncio
    async def test_agent_build_consensus(self, sample_agent_config, mock_ollama_client):
        """Test agent consensus building functionality"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            # Mock consensus response
            mock_ollama_client.generate_with_retry.return_value = GenerationResponse(
                response=json.dumps({
                    "agent_id": "TestAgent_Alpha",
                    "main_response": "Final consensus recommendation",
                    "confidence_level": 0.95,
                    "key_insights": ["Consensus insight 1", "Consensus insight 2"],
                    "questions_for_others": [],
                    "next_action": "Implement solution",
                    "reasoning": "Consensus reached"
                }),
                model="llama3.2:3b",
                done=True
            )
            
            all_syntheses = {
                "Agent1": {"main_response": "Synthesis 1", "confidence_level": 0.8},
                "Agent2": {"main_response": "Synthesis 2", "confidence_level": 0.9}
            }
            
            result = await agent.build_consensus("Test problem", all_syntheses)
            
            assert result is not None
            assert result["agent_id"] == sample_agent_config.agent_id
            assert "consensus recommendation" in result["main_response"]
            assert result["confidence_level"] == 0.95
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, sample_agent_config):
        """Test agent handles Ollama client errors gracefully"""
        mock_client = AsyncMock()
        mock_client.test_connection.return_value = True
        mock_client.generate_with_retry.side_effect = Exception("Mock Ollama error")
        
        with patch('agents.local_agent.OllamaClient', return_value=mock_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            result = await agent.analyze_problem("Test problem")
            
            # Should return fallback response
            assert result is not None
            assert result["agent_id"] == sample_agent_config.agent_id
            assert result["confidence_level"] == 0.0
            assert "error occurred" in result["main_response"].lower()
    
    @pytest.mark.asyncio
    async def test_agent_malformed_response_handling(self, sample_agent_config):
        """Test agent handles malformed responses from Ollama"""
        mock_client = AsyncMock()
        mock_client.test_connection.return_value = True
        
        # Mock malformed JSON response
        mock_client.generate_with_retry.return_value = GenerationResponse(
            response='{"agent_id": "TestAgent", "incomplete": ',  # Malformed JSON
            model="llama3.2:3b",
            done=True
        )
        
        with patch('agents.local_agent.OllamaClient', return_value=mock_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            result = await agent.analyze_problem("Test problem")
            
            # Parser should handle malformed response
            assert result is not None
            assert result["agent_id"] == sample_agent_config.agent_id
            assert isinstance(result["confidence_level"], (int, float))
            assert 0.0 <= result["confidence_level"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_agent_context_building(self, sample_agent_config, mock_ollama_client):
        """Test agent builds context properly for different phases"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            # Test different phases use appropriate prompts
            await agent.analyze_problem("Test problem")
            await agent.critique_analysis("Test problem", {"Other": {"main_response": "test"}})
            await agent.synthesize_insights("Test problem", {}, {})
            await agent.build_consensus("Test problem", {})
            
            # Should have called generate_with_retry 4 times
            assert mock_ollama_client.generate_with_retry.call_count == 4
            
            # Each call should have different context
            calls = mock_ollama_client.generate_with_retry.call_args_list
            assert len(calls) == 4
            
            # Check that each phase has different prompts
            phase_prompts = [call.kwargs.get('prompt', '') for call in calls]
            assert len(set(phase_prompts)) == 4  # All prompts should be different
    
    @pytest.mark.asyncio
    async def test_agent_cleanup(self, sample_agent_config, mock_ollama_client):
        """Test agent cleanup functionality"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            await agent.cleanup()
            
            mock_ollama_client.close.assert_called_once()
            assert agent.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_agent_get_status(self, sample_agent_config, mock_ollama_client):
        """Test agent status reporting"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            
            # Test before initialization
            status = agent.get_status()
            assert status["initialized"] is False
            assert status["agent_id"] == sample_agent_config.agent_id
            
            # Test after initialization
            await agent.initialize()
            status = agent.get_status()
            assert status["initialized"] is True
            assert status["model_name"] == sample_agent_config.model_name
    
    @pytest.mark.asyncio
    async def test_agent_response_validation(self, sample_agent_config, mock_ollama_client):
        """Test that agent responses are properly validated"""
        with patch('agents.local_agent.OllamaClient', return_value=mock_ollama_client):
            agent = LocalAgent(sample_agent_config)
            await agent.initialize()
            
            with patch('utils.response_parser.ResponseParser.validate_and_log_response') as mock_validate:
                mock_validate.return_value = True
                
                result = await agent.analyze_problem("Test problem")
                
                # Validation should have been called
                mock_validate.assert_called_once()
                assert result is not None


class TestMockOllamaClient:
    """Test Ollama client functionality with mocks"""
    
    @pytest.mark.asyncio
    async def test_mock_client_generation(self, mock_ollama_client):
        """Test mock client generates responses"""
        response = await mock_ollama_client.generate_with_retry(
            model="llama3.2:3b",
            prompt="Test prompt",
            temperature=0.7
        )
        
        assert isinstance(response, GenerationResponse)
        assert response.model == "llama3.2:3b"
        assert response.done is True
        
        # Parse the JSON response
        response_data = json.loads(response.response)
        assert response_data["agent_id"] == "TestAgent_Alpha"
        assert response_data["confidence_level"] == 0.8
    
    @pytest.mark.asyncio
    async def test_mock_client_connection_test(self, mock_ollama_client):
        """Test mock client connection testing"""
        result = await mock_ollama_client.test_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_mock_client_list_models(self, mock_ollama_client):
        """Test mock client model listing"""
        models = await mock_ollama_client.list_models()
        assert isinstance(models, list)
        assert len(models) == 3
        assert "llama3.2:3b" in models
        assert "llama3.1:8b" in models
        assert "qwen2.5:7b" in models
    
    def test_create_custom_mock_responses(self):
        """Test creating custom mock responses for different scenarios"""
        mock_client = AsyncMock()
        
        # Mock error response
        mock_client.generate_with_retry.side_effect = Exception("Connection failed")
        
        # Mock successful responses with different content
        success_responses = [
            GenerationResponse(
                response=json.dumps({
                    "agent_id": "Agent1",
                    "main_response": "Response 1",
                    "confidence_level": 0.7
                }),
                model="test-model",
                done=True
            ),
            GenerationResponse(
                response=json.dumps({
                    "agent_id": "Agent2", 
                    "main_response": "Response 2",
                    "confidence_level": 0.9
                }),
                model="test-model",
                done=True
            )
        ]
        
        # Test different behaviors
        mock_client.generate_with_retry.side_effect = success_responses
        
        assert len(success_responses) == 2
        assert json.loads(success_responses[0].response)["confidence_level"] == 0.7
        assert json.loads(success_responses[1].response)["confidence_level"] == 0.9


class TestMockResponseParser:
    """Test response parser with mock data"""
    
    def test_parse_mock_responses(self, sample_valid_json_response, sample_malformed_responses):
        """Test parser handles various mock response formats"""
        # Test valid response
        result = ResponseParser.parse_agent_response(
            json.dumps(sample_valid_json_response), "TestAgent"
        )
        assert result["agent_id"] == "TestAgent"
        assert result["confidence_level"] == 0.85
        
        # Test malformed responses
        for malformed_response in sample_malformed_responses:
            result = ResponseParser.parse_agent_response(malformed_response, "TestAgent")
            
            # Should always return valid structure
            assert result["agent_id"] == "TestAgent"
            assert isinstance(result["confidence_level"], (int, float))
            assert 0.0 <= result["confidence_level"] <= 1.0
            assert isinstance(result["key_insights"], list)
            assert isinstance(result["questions_for_others"], list)
    
    def test_mock_structured_text_parsing(self):
        """Test parsing structured text responses"""
        mock_structured_responses = [
            """
            main_response: This is a structured mock response
            confidence_level: 0.8
            key_insights: [Mock insight 1, Mock insight 2]
            questions_for_others: [Mock question?]
            """,
            """
            analysis: Different field name for main response
            confidence: 0.6
            insights: [Different field name for insights]
            """,
            """
            response: Minimal structured response
            """
        ]
        
        for response in mock_structured_responses:
            result = ResponseParser.parse_agent_response(response, "MockAgent")
            
            assert result["agent_id"] == "MockAgent"
            assert isinstance(result["main_response"], str)
            assert len(result["main_response"]) > 0
            assert isinstance(result["confidence_level"], (int, float))
    
    def test_mock_fallback_responses(self):
        """Test fallback response creation with mock data"""
        mock_free_text_responses = [
            "This is completely unstructured text that should trigger fallback parsing.",
            "A longer response with multiple sentences. Each sentence could be an insight. The system should handle this gracefully. Even without any JSON structure whatsoever.",
            "",  # Empty response
            "Short response",
            "A" * 2000  # Very long response that should be truncated
        ]
        
        for response in mock_free_text_responses:
            result = ResponseParser.parse_agent_response(response, "FallbackAgent")
            
            assert result["agent_id"] == "FallbackAgent"
            assert result["confidence_level"] == 0.3  # Low confidence for fallback
            assert result["reasoning"] == "Response created from fallback parsing"
            assert len(result["main_response"]) <= 1000  # Should be truncated if too long