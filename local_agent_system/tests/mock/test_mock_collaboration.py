"""
Mock tests for collaboration system without requiring Ollama
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from collaboration.system import LocalAgent2AgentSystem
from agents.local_agent import LocalAgent
from utils.ollama_client import GenerationResponse


class TestMockCollaborationSystem:
    """Test collaboration system with mocked components"""
    
    @pytest.fixture
    def mock_agent_responses(self):
        """Mock responses for different collaboration phases"""
        return {
            "phase1_analysis": {
                "DataScientist_Alpha": {
                    "agent_id": "DataScientist_Alpha",
                    "main_response": "From a data perspective, this problem requires quantitative analysis of customer behavior patterns and retention metrics.",
                    "confidence_level": 0.85,
                    "key_insights": [
                        "Historical data shows 40% churn rate in first 3 months",
                        "Customer engagement correlates with feature usage depth",
                        "Segmentation reveals distinct user personas with different needs"
                    ],
                    "questions_for_others": [
                        "What technical constraints affect our tracking capabilities?",
                        "How do user experience factors impact retention?"
                    ],
                    "next_action": "Collect more granular usage data",
                    "reasoning": "Data-driven approach identifies key retention factors"
                },
                "ProductManager_Beta": {
                    "agent_id": "ProductManager_Beta",
                    "main_response": "Customer retention requires balancing user value delivery with business objectives through strategic product improvements.",
                    "confidence_level": 0.9,
                    "key_insights": [
                        "User onboarding experience is critical for early retention",
                        "Feature adoption drives long-term engagement",
                        "Customer feedback reveals pain points in current workflow"
                    ],
                    "questions_for_others": [
                        "What data supports our retention hypotheses?",
                        "Are there technical limitations to proposed solutions?"
                    ],
                    "next_action": "Prioritize retention initiatives based on impact",
                    "reasoning": "User-centered approach focuses on value delivery"
                }
            },
            "phase2_critique": {
                "DataScientist_Alpha": {
                    "agent_id": "DataScientist_Alpha",
                    "main_response": "The product approach is sound but needs stronger quantitative validation of proposed initiatives.",
                    "confidence_level": 0.75,
                    "key_insights": [
                        "Onboarding improvements should be A/B tested",
                        "Feature adoption metrics need clearer definitions",
                        "Customer feedback analysis requires statistical significance"
                    ],
                    "questions_for_others": [
                        "How will we measure onboarding success quantitatively?"
                    ],
                    "next_action": "Design measurement framework for retention initiatives",
                    "reasoning": "Critique focuses on measurability and validation"
                },
                "ProductManager_Beta": {
                    "agent_id": "ProductManager_Beta",
                    "main_response": "Data insights are valuable but must be translated into actionable product improvements that users will actually adopt.",
                    "confidence_level": 0.8,
                    "key_insights": [
                        "Data collection shouldn't compromise user experience",
                        "Segmentation insights need product feature implications",
                        "Retention metrics should align with business outcomes"
                    ],
                    "questions_for_others": [
                        "Can we implement tracking without adding friction?"
                    ],
                    "next_action": "Create user-friendly data collection strategy",
                    "reasoning": "Critique emphasizes user experience in data strategy"
                }
            },
            "phase3_synthesis": {
                "DataScientist_Alpha": {
                    "agent_id": "DataScientist_Alpha", 
                    "main_response": "Synthesis reveals need for integrated approach combining rigorous measurement with user-centric product improvements.",
                    "confidence_level": 0.9,
                    "key_insights": [
                        "Balanced approach uses data to inform user experience improvements",
                        "Phased implementation allows learning and iteration",
                        "Success requires both quantitative metrics and qualitative feedback"
                    ],
                    "questions_for_others": [],
                    "next_action": "Develop comprehensive retention strategy framework",
                    "reasoning": "Synthesis integrates analytical and product perspectives"
                },
                "ProductManager_Beta": {
                    "agent_id": "ProductManager_Beta",
                    "main_response": "Combined insights point to data-driven product strategy that prioritizes user value while maintaining measurement discipline.",
                    "confidence_level": 0.95,
                    "key_insights": [
                        "User experience and data collection can be mutually reinforcing",
                        "Retention strategy needs both immediate and long-term initiatives",
                        "Cross-functional collaboration is essential for success"
                    ],
                    "questions_for_others": [],
                    "next_action": "Build integrated retention improvement roadmap",
                    "reasoning": "Synthesis creates unified approach to retention challenge"
                }
            }
        }
    
    @pytest.fixture
    def mock_consensus_response(self):
        """Mock consensus response"""
        return {
            "main_response": "Comprehensive customer retention strategy combining data-driven insights with user-centric product improvements, implemented through phased approach with continuous measurement and iteration.",
            "confidence_level": 0.92,
            "key_insights": [
                "Integrate quantitative analysis with qualitative user feedback",
                "Implement phased retention initiatives with A/B testing",
                "Focus on onboarding experience and feature adoption",
                "Establish clear metrics for measuring retention success"
            ],
            "next_action": "Develop detailed implementation roadmap with success metrics",
            "contributing_agents": ["DataScientist_Alpha", "ProductManager_Beta"],
            "reasoning": "Consensus reached through synthesis of analytical and product perspectives"
        }
    
    def create_mock_agent(self, agent_id, responses_dict):
        """Create a mock agent with predefined responses"""
        mock_agent = AsyncMock(spec=LocalAgent)
        mock_agent.agent_id = agent_id
        mock_agent.is_initialized = True
        mock_agent.config.enabled = True
        
        # Mock different methods to return appropriate responses
        mock_agent.analyze_problem.return_value = responses_dict["phase1_analysis"][agent_id]
        mock_agent.critique_analysis.return_value = responses_dict["phase2_critique"][agent_id]
        mock_agent.synthesize_insights.return_value = responses_dict["phase3_synthesis"][agent_id]
        mock_agent.build_consensus.return_value = responses_dict["phase3_synthesis"][agent_id]
        
        mock_agent.initialize.return_value = True
        mock_agent.cleanup.return_value = None
        mock_agent.get_status.return_value = {
            "agent_id": agent_id,
            "initialized": True,
            "model_name": "mock-model"
        }
        
        return mock_agent
    
    @pytest.mark.asyncio
    async def test_mock_system_initialization(self, temp_config_dir):
        """Test collaboration system initialization with mocks"""
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.load_config.return_value = True
            mock_config_manager.validate_config.return_value = True
            mock_config_manager.get_enabled_agents.return_value = {
                "TestAgent1": Mock(agent_id="TestAgent1"),
                "TestAgent2": Mock(agent_id="TestAgent2")
            }
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            
            with patch('collaboration.system.LocalAgent') as mock_agent_class:
                mock_agent_class.return_value = AsyncMock()
                
                success = await system.initialize_system()
                
                assert success is True
                assert len(system.agents) == 2
    
    @pytest.mark.asyncio
    async def test_mock_full_collaboration_flow(self, mock_agent_responses, mock_consensus_response, temp_config_dir):
        """Test complete collaboration flow with mocked agents"""
        # Create mock agents
        mock_agents = {
            "DataScientist_Alpha": self.create_mock_agent("DataScientist_Alpha", mock_agent_responses),
            "ProductManager_Beta": self.create_mock_agent("ProductManager_Beta", mock_agent_responses)
        }
        
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.load_config.return_value = True
            mock_config_manager.validate_config.return_value = True
            mock_config_manager.system_config.session_save_dir = str(temp_config_dir)
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            system.agents = mock_agents
            
            # Mock the consensus building algorithm
            with patch.object(system, '_build_algorithmic_consensus') as mock_consensus:
                mock_consensus.return_value = mock_consensus_response
                
                problem = "How can we improve customer retention for our SaaS product?"
                result = await system.run_collaborative_problem_solving(problem)
                
                # Verify the collaboration flow
                assert result is not None
                assert "session_id" in result
                assert "results" in result
                assert "metrics" in result
                
                # Check that all phases were executed
                results = result["results"]
                assert "phase1_analysis" in results
                assert "phase2_critique" in results  
                assert "phase3_synthesis" in results
                assert "phase4_consensus" in results
                
                # Verify agent method calls
                for agent in mock_agents.values():
                    agent.analyze_problem.assert_called_once_with(problem)
                    agent.critique_analysis.assert_called_once()
                    agent.synthesize_insights.assert_called_once()
                
                # Check consensus result
                consensus = results["phase4_consensus"]
                assert consensus["confidence_level"] == 0.92
                assert len(consensus["contributing_agents"]) == 2
    
    @pytest.mark.asyncio
    async def test_mock_phase_execution(self, mock_agent_responses, temp_config_dir):
        """Test individual phase execution with mocks"""
        mock_agents = {
            "DataScientist_Alpha": self.create_mock_agent("DataScientist_Alpha", mock_agent_responses)
        }
        
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.system_config.session_save_dir = str(temp_config_dir)
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            system.agents = mock_agents
            
            problem = "Test problem"
            
            # Test Phase 1 - Analysis
            analysis_results = await system._run_phase1_analysis(problem)
            assert len(analysis_results) == 1
            assert "DataScientist_Alpha" in analysis_results
            assert analysis_results["DataScientist_Alpha"]["confidence_level"] == 0.85
            
            # Test Phase 2 - Critique
            critique_results = await system._run_phase2_critique(problem, analysis_results)
            assert len(critique_results) == 1
            assert "DataScientist_Alpha" in critique_results
            assert critique_results["DataScientist_Alpha"]["confidence_level"] == 0.75
            
            # Test Phase 3 - Synthesis
            synthesis_results = await system._run_phase3_synthesis(problem, analysis_results, critique_results)
            assert len(synthesis_results) == 1
            assert "DataScientist_Alpha" in synthesis_results
            assert synthesis_results["DataScientist_Alpha"]["confidence_level"] == 0.9
    
    @pytest.mark.asyncio
    async def test_mock_error_handling(self, temp_config_dir):
        """Test error handling with mocked failures"""
        # Create mock agent that fails
        failing_agent = AsyncMock(spec=LocalAgent)
        failing_agent.agent_id = "FailingAgent"
        failing_agent.is_initialized = True
        failing_agent.config.enabled = True
        failing_agent.analyze_problem.side_effect = Exception("Mock agent failure")
        
        mock_agents = {"FailingAgent": failing_agent}
        
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.system_config.session_save_dir = str(temp_config_dir)
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            system.agents = mock_agents
            
            problem = "Test problem"
            
            # Phase should handle the failure gracefully
            analysis_results = await system._run_phase1_analysis(problem)
            
            # Should get fallback response for failing agent
            assert "FailingAgent" in analysis_results
            assert analysis_results["FailingAgent"]["confidence_level"] == 0.0
    
    @pytest.mark.asyncio
    async def test_mock_consensus_algorithm(self, mock_agent_responses, temp_config_dir):
        """Test consensus building algorithm with mock data"""
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.system_config.session_save_dir = str(temp_config_dir)
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            
            # Use synthesis results for consensus building
            synthesis_results = mock_agent_responses["phase3_synthesis"]
            
            consensus = system._build_algorithmic_consensus(
                "Test problem", 
                synthesis_results,
                {"DataScientist_Alpha": 0.9, "ProductManager_Beta": 0.95}
            )
            
            assert consensus is not None
            assert "main_response" in consensus
            assert "confidence_level" in consensus
            assert "contributing_agents" in consensus
            
            # Confidence should be weighted average
            expected_confidence = (0.9 * 0.9 + 0.95 * 0.95) / (0.9 + 0.95)
            assert abs(consensus["confidence_level"] - expected_confidence) < 0.01
    
    @pytest.mark.asyncio
    async def test_mock_session_persistence(self, mock_collaboration_results, temp_config_dir):
        """Test session saving with mock results"""
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.system_config.session_save_dir = str(temp_config_dir)
            mock_config_manager.system_config.enable_metrics = True
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            
            session_id = await system._save_session_results(
                "Test problem", 
                mock_collaboration_results["results"],
                mock_collaboration_results["metrics"]
            )
            
            assert session_id is not None
            
            # Check that session file was created
            session_file = Path(temp_config_dir) / f"session_{session_id}.json"
            assert session_file.exists()
            
            # Verify session content
            with open(session_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["problem"] == "Test problem"
            assert "results" in saved_data
            assert "metrics" in saved_data
            assert saved_data["session_id"] == session_id
    
    @pytest.mark.asyncio
    async def test_mock_metrics_collection(self, temp_config_dir):
        """Test metrics collection with mock timing data"""
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.system_config.session_save_dir = str(temp_config_dir)
            mock_config_manager.system_config.enable_metrics = True
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            
            # Mock successful execution times
            phase_results = {
                "phase1_analysis": {"Agent1": {"confidence_level": 0.8}},
                "phase2_critique": {"Agent1": {"confidence_level": 0.7}},
                "phase3_synthesis": {"Agent1": {"confidence_level": 0.9}},
                "phase4_consensus": {"confidence_level": 0.85}
            }
            
            with patch('time.time') as mock_time:
                # Mock timing sequence
                mock_time.side_effect = [0, 10.5, 23.2, 35.8, 47.1]  # Start, phase1, phase2, phase3, end
                
                metrics = system._calculate_collaboration_metrics(
                    phase_results, 
                    start_time=0,
                    end_time=47.1
                )
                
                assert metrics["total_duration"] == 47.1
                assert metrics["success_rate"] == 1.0  # All phases succeeded
                assert "phase_durations" in metrics
                assert metrics["phase_durations"]["phase1_analysis"] == 10.5
                assert metrics["phase_durations"]["phase2_critique"] == 12.7  # 23.2 - 10.5
    
    def test_mock_system_status(self, temp_config_dir):
        """Test system status with mock agents"""
        mock_agents = {
            "Agent1": Mock(agent_id="Agent1", get_status=Mock(return_value={
                "agent_id": "Agent1", 
                "initialized": True,
                "model_name": "mock-model-1"
            })),
            "Agent2": Mock(agent_id="Agent2", get_status=Mock(return_value={
                "agent_id": "Agent2",
                "initialized": True, 
                "model_name": "mock-model-2"
            }))
        }
        
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = Mock()
            mock_config_manager.get_config_summary.return_value = {
                "preset": "test",
                "system_config": {"ollama_url": "http://localhost:11434"}
            }
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            system.agents = mock_agents
            
            status = system.get_system_status()
            
            assert status["agent_count"] == 2
            assert "config" in status
            assert "agents" in status
            assert len(status["agents"]) == 2
            assert "Agent1" in status["agents"]
            assert "Agent2" in status["agents"]