"""
Performance benchmarks for the agent collaboration system
"""
import pytest
import asyncio
import time
import json
import statistics
import psutil
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock
from memory_profiler import profile
from typing import List, Dict, Any

from collaboration.system import LocalAgent2AgentSystem
from utils.response_parser import ResponseParser
from config.config_manager import ConfigManager


class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        
    def start(self):
        """Start monitoring"""
        self.start_time = time.perf_counter()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def end(self):
        """End monitoring"""
        self.end_time = time.perf_counter()
        self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.start_memory, self.end_memory)
        
    @property
    def duration(self) -> float:
        """Get duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def memory_usage(self) -> float:
        """Get memory usage in MB"""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return 0.0
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        return {
            'duration_seconds': self.duration,
            'memory_change_mb': self.memory_usage,
            'peak_memory_mb': self.peak_memory or 0.0,
            'start_memory_mb': self.start_memory or 0.0,
            'end_memory_mb': self.end_memory or 0.0
        }


class MockPerformanceAgent:
    """Mock agent optimized for performance testing"""
    
    def __init__(self, agent_id: str, response_delay: float = 0.1):
        self.agent_id = agent_id
        self.response_delay = response_delay
        self.is_initialized = True
        
    async def analyze_problem(self, problem: str) -> Dict[str, Any]:
        """Mock analysis with controlled delay"""
        await asyncio.sleep(self.response_delay)
        return {
            "agent_id": self.agent_id,
            "main_response": f"Mock analysis of: {problem[:50]}...",
            "confidence_level": 0.8,
            "key_insights": [f"Insight 1 from {self.agent_id}", f"Insight 2 from {self.agent_id}"],
            "questions_for_others": [f"Question from {self.agent_id}?"],
            "next_action": "Continue analysis",
            "reasoning": f"Mock reasoning from {self.agent_id}"
        }
    
    async def critique_analysis(self, problem: str, other_analyses: Dict) -> Dict[str, Any]:
        """Mock critique with controlled delay"""
        await asyncio.sleep(self.response_delay)
        return {
            "agent_id": self.agent_id,
            "main_response": f"Mock critique from {self.agent_id}",
            "confidence_level": 0.75,
            "key_insights": [f"Critique insight from {self.agent_id}"],
            "questions_for_others": [],
            "next_action": "Proceed to synthesis",
            "reasoning": f"Mock critique reasoning from {self.agent_id}"
        }
    
    async def synthesize_insights(self, problem: str, analyses: Dict, critiques: Dict) -> Dict[str, Any]:
        """Mock synthesis with controlled delay"""
        await asyncio.sleep(self.response_delay)
        return {
            "agent_id": self.agent_id,
            "main_response": f"Mock synthesis from {self.agent_id}",
            "confidence_level": 0.9,
            "key_insights": [f"Synthesis insight from {self.agent_id}"],
            "questions_for_others": [],
            "next_action": "Build consensus",
            "reasoning": f"Mock synthesis reasoning from {self.agent_id}"
        }
    
    async def build_consensus(self, problem: str, syntheses: Dict) -> Dict[str, Any]:
        """Mock consensus building"""
        await asyncio.sleep(self.response_delay * 0.5)  # Shorter for consensus
        return {
            "agent_id": self.agent_id,
            "main_response": f"Mock consensus from {self.agent_id}",
            "confidence_level": 0.85,
            "key_insights": [f"Consensus insight from {self.agent_id}"],
            "questions_for_others": [],
            "next_action": "Finalize solution",
            "reasoning": f"Mock consensus reasoning from {self.agent_id}"
        }
    
    async def initialize(self) -> bool:
        """Mock initialization"""
        await asyncio.sleep(0.01)  # Minimal delay
        return True
    
    async def cleanup(self):
        """Mock cleanup"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "initialized": True,
            "model_name": "mock-model"
        }


@pytest.mark.benchmark
class TestResponseParsingPerformance:
    """Benchmark response parsing performance"""
    
    def test_json_parsing_performance(self, benchmark_config):
        """Benchmark JSON response parsing speed"""
        # Create test responses of varying sizes
        small_response = {
            "agent_id": "TestAgent",
            "main_response": "Short response",
            "confidence_level": 0.8,
            "key_insights": ["Insight 1"],
            "questions_for_others": ["Question?"],
            "next_action": "Next",
            "reasoning": "Short reasoning"
        }
        
        large_response = {
            "agent_id": "TestAgent",
            "main_response": "This is a much longer response " * 50,  # ~1500 chars
            "confidence_level": 0.8,
            "key_insights": [f"Insight {i}" for i in range(20)],
            "questions_for_others": [f"Question {i}?" for i in range(10)],
            "next_action": "Complex next action with detailed steps",
            "reasoning": "Detailed reasoning " * 20
        }
        
        responses = [small_response, large_response]
        
        monitor = PerformanceMonitor()
        monitor.start()
        
        # Parse responses multiple times
        iterations = benchmark_config['iterations']
        parse_times = []
        
        for _ in range(iterations):
            for response_dict in responses:
                start_time = time.perf_counter()
                
                json_str = json.dumps(response_dict)
                parsed = ResponseParser.parse_agent_response(json_str, "TestAgent")
                
                end_time = time.perf_counter()
                parse_times.append(end_time - start_time)
                
                # Verify parsing worked
                assert parsed["agent_id"] == "TestAgent"
        
        monitor.end()
        
        # Calculate statistics
        avg_parse_time = statistics.mean(parse_times)
        max_parse_time = max(parse_times)
        min_parse_time = min(parse_times)
        
        print(f"\nJSON Parsing Performance:")
        print(f"  Iterations: {iterations}")
        print(f"  Average parse time: {avg_parse_time*1000:.3f}ms")
        print(f"  Min parse time: {min_parse_time*1000:.3f}ms")
        print(f"  Max parse time: {max_parse_time*1000:.3f}ms")
        print(f"  Total duration: {monitor.duration:.2f}s")
        print(f"  Memory usage: {monitor.memory_usage:.1f}MB")
        
        # Performance assertions
        assert avg_parse_time < benchmark_config['response_time_threshold_s']
        assert monitor.memory_usage < benchmark_config['memory_threshold_mb']
    
    def test_malformed_response_handling_performance(self, benchmark_config, sample_malformed_responses):
        """Benchmark malformed response handling"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        iterations = benchmark_config['iterations'] // 2  # Fewer iterations for error cases
        parse_times = []
        
        for _ in range(iterations):
            for malformed_response in sample_malformed_responses:
                start_time = time.perf_counter()
                
                # This should handle errors gracefully
                parsed = ResponseParser.parse_agent_response(malformed_response, "TestAgent")
                
                end_time = time.perf_counter()
                parse_times.append(end_time - start_time)
                
                # Should always return valid structure even for malformed input
                assert parsed["agent_id"] == "TestAgent"
                assert isinstance(parsed["confidence_level"], (int, float))
        
        monitor.end()
        
        avg_parse_time = statistics.mean(parse_times)
        
        print(f"\nMalformed Response Handling Performance:")
        print(f"  Iterations: {iterations}")
        print(f"  Average parse time: {avg_parse_time*1000:.3f}ms")
        print(f"  Total duration: {monitor.duration:.2f}s")
        print(f"  Memory usage: {monitor.memory_usage:.1f}MB")
        
        # Error handling should still be reasonably fast
        assert avg_parse_time < benchmark_config['response_time_threshold_s'] * 2  # Allow 2x for error cases


@pytest.mark.benchmark
class TestConfigurationPerformance:
    """Benchmark configuration system performance"""
    
    def test_config_loading_performance(self, temp_config_dir, benchmark_config):
        """Benchmark configuration loading speed"""
        # Create test configuration with many agents
        large_config = {
            'system': {
                'ollama_base_url': 'http://localhost:11434',
                'ollama_timeout': 120,
                'max_retries': 3,
                'retry_delay': 1.0,
                'log_level': 'INFO',
                'session_save_dir': './sessions',
                'enable_metrics': True
            },
            'agents': []
        }
        
        # Generate many agent configurations
        for i in range(50):  # Create 50 agents
            agent_config = {
                'agent_id': f'TestAgent_{i:03d}',
                'role': f'Test Agent {i}',
                'model_name': f'test-model-{i % 5}',  # Cycle through 5 models
                'temperature': 0.1 + (i % 10) * 0.1,  # Vary temperature
                'personality': f'personality-{i % 3}',
                'enabled': i % 4 != 0,  # Disable every 4th agent
                'max_tokens': 400 + (i % 10) * 100,
                'system_prompt': f'You are TestAgent_{i:03d}. ' + 'Test prompt content. ' * 20
            }
            large_config['agents'].append(agent_config)
        
        # Save large configuration
        config_file = temp_config_dir / "large_config.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(large_config, f, default_flow_style=False, indent=2)
        
        monitor = PerformanceMonitor()
        load_times = []
        
        iterations = benchmark_config['iterations'] // 5  # Fewer iterations for config loading
        
        for i in range(iterations):
            monitor.start()
            
            config_manager = ConfigManager(config_dir=str(temp_config_dir))
            success = config_manager.load_config(str(config_file))
            
            monitor.end()
            load_times.append(monitor.duration)
            
            assert success is True
            assert len(config_manager.agents) == 50
            enabled_agents = config_manager.get_enabled_agents()
            assert len(enabled_agents) > 0  # Some agents should be enabled
        
        avg_load_time = statistics.mean(load_times)
        
        print(f"\nConfiguration Loading Performance (50 agents):")
        print(f"  Iterations: {iterations}")
        print(f"  Average load time: {avg_load_time*1000:.3f}ms")
        print(f"  Peak memory: {monitor.peak_memory:.1f}MB")
        
        # Config loading should be fast even with many agents
        assert avg_load_time < 1.0  # Should load in under 1 second
    
    def test_config_validation_performance(self, temp_config_dir, benchmark_config):
        """Benchmark configuration validation speed"""
        # Create configuration with validation challenges
        config_manager = ConfigManager(config_dir=str(temp_config_dir))
        
        # Add many agents with various validation scenarios
        for i in range(20):
            agent_config = {
                'agent_id': f'ValidAgent_{i:02d}',
                'role': f'Valid Agent {i}',
                'model_name': 'valid-model',
                'temperature': 0.5,
                'personality': 'test',
                'enabled': True,
                'max_tokens': 800,
                'system_prompt': 'Valid prompt'
            }
            config_manager.agents[f'ValidAgent_{i:02d}'] = agent_config
        
        monitor = PerformanceMonitor()
        validation_times = []
        
        iterations = benchmark_config['iterations']
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            
            is_valid = config_manager.validate_config()
            
            end_time = time.perf_counter()
            validation_times.append(end_time - start_time)
            
            assert is_valid is True
        
        avg_validation_time = statistics.mean(validation_times)
        
        print(f"\nConfiguration Validation Performance:")
        print(f"  Iterations: {iterations}")
        print(f"  Average validation time: {avg_validation_time*1000:.3f}ms")
        
        # Validation should be fast
        assert avg_validation_time < 0.1  # Should validate in under 100ms


@pytest.mark.benchmark
class TestCollaborationPerformance:
    """Benchmark collaboration system performance"""
    
    @pytest.mark.asyncio
    async def test_mock_collaboration_performance(self, temp_config_dir, benchmark_config, performance_test_problems):
        """Benchmark collaboration system with mock agents"""
        # Create mock system with varying agent counts and response times
        agent_counts = [2, 5, 10]
        response_delays = [0.05, 0.1, 0.2]  # Different response speeds
        
        results = {}
        
        for agent_count in agent_counts:
            for delay in response_delays:
                test_key = f"{agent_count}_agents_{delay*1000:.0f}ms_delay"
                
                # Create mock agents
                mock_agents = {}
                for i in range(agent_count):
                    agent_id = f"MockAgent_{i:02d}"
                    mock_agents[agent_id] = MockPerformanceAgent(agent_id, delay)
                
                with patch('collaboration.system.get_config_manager') as mock_get_config:
                    mock_config_manager = MockPerformanceAgent("config", 0)
                    mock_config_manager.system_config = type('obj', (object,), {
                        'session_save_dir': str(temp_config_dir),
                        'enable_metrics': True
                    })
                    mock_get_config.return_value = mock_config_manager
                    
                    system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
                    system.agents = mock_agents
                    
                    monitor = PerformanceMonitor()
                    monitor.start()
                    
                    # Run collaboration on test problems
                    problem_times = []
                    
                    for problem in performance_test_problems[:3]:  # Test subset for performance
                        start_time = time.perf_counter()
                        
                        # Run individual phases for controlled testing
                        analysis = await system._run_phase1_analysis(problem)
                        critique = await system._run_phase2_critique(problem, analysis)
                        synthesis = await system._run_phase3_synthesis(problem, analysis, critique)
                        
                        end_time = time.perf_counter()
                        problem_times.append(end_time - start_time)
                    
                    monitor.end()
                    
                    avg_problem_time = statistics.mean(problem_times)
                    total_time = monitor.duration
                    
                    results[test_key] = {
                        'agent_count': agent_count,
                        'response_delay': delay,
                        'avg_problem_time': avg_problem_time,
                        'total_time': total_time,
                        'memory_usage': monitor.memory_usage,
                        'problems_per_second': len(performance_test_problems[:3]) / total_time if total_time > 0 else 0
                    }
        
        # Print performance results
        print(f"\nMock Collaboration Performance Results:")
        print(f"{'Config':<20} {'Avg Time':<10} {'Total':<8} {'Mem MB':<8} {'Prob/s':<8}")
        print("-" * 60)
        
        for test_key, result in results.items():
            print(f"{test_key:<20} "
                  f"{result['avg_problem_time']:.3f}s    "
                  f"{result['total_time']:.2f}s   "
                  f"{result['memory_usage']:.1f}MB   "
                  f"{result['problems_per_second']:.2f}")
        
        # Performance assertions
        # More agents should not exponentially increase time (good concurrency)
        two_agent_time = results['2_agents_100ms_delay']['avg_problem_time']
        ten_agent_time = results['10_agents_100ms_delay']['avg_problem_time']
        
        # 10 agents shouldn't take more than 3x the time of 2 agents (due to concurrency)
        assert ten_agent_time < two_agent_time * 3
        
        # Memory usage should be reasonable
        for result in results.values():
            assert result['memory_usage'] < benchmark_config['memory_threshold_mb']
    
    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self, temp_config_dir, benchmark_config):
        """Benchmark concurrent request handling"""
        # Create fast mock agents
        mock_agents = {}
        for i in range(5):
            agent_id = f"ConcurrentAgent_{i}"
            mock_agents[agent_id] = MockPerformanceAgent(agent_id, 0.05)  # Fast responses
        
        with patch('collaboration.system.get_config_manager') as mock_get_config:
            mock_config_manager = MockPerformanceAgent("config", 0)
            mock_config_manager.system_config = type('obj', (object,), {
                'session_save_dir': str(temp_config_dir),
                'enable_metrics': True,
                'max_concurrent_requests': 10
            })
            mock_get_config.return_value = mock_config_manager
            
            system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
            system.agents = mock_agents
            
            # Test concurrent requests
            concurrent_counts = [1, 5, 10, 20]
            
            print(f"\nConcurrent Request Performance:")
            print(f"{'Concurrent':<12} {'Time':<8} {'Rate':<12} {'Efficiency':<12}")
            print("-" * 48)
            
            baseline_time = None
            
            for concurrent_count in concurrent_counts:
                monitor = PerformanceMonitor()
                monitor.start()
                
                # Create concurrent tasks
                tasks = []
                problem = "Concurrent test problem"
                
                for _ in range(concurrent_count):
                    task = asyncio.create_task(system._run_phase1_analysis(problem))
                    tasks.append(task)
                
                # Execute all tasks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                monitor.end()
                
                # Calculate metrics
                successful_results = [r for r in results if not isinstance(r, Exception)]
                success_rate = len(successful_results) / len(results)
                requests_per_second = concurrent_count / monitor.duration if monitor.duration > 0 else 0
                
                if baseline_time is None:
                    baseline_time = monitor.duration
                    efficiency = 1.0
                else:
                    # Efficiency = how much faster we are vs sequential
                    expected_sequential_time = baseline_time * concurrent_count
                    efficiency = expected_sequential_time / monitor.duration if monitor.duration > 0 else 0
                
                print(f"{concurrent_count:<12} "
                      f"{monitor.duration:.3f}s   "
                      f"{requests_per_second:.2f}/s      "
                      f"{efficiency:.2f}x")
                
                # Performance assertions
                assert success_rate >= 0.8  # At least 80% success rate
                assert monitor.memory_usage < benchmark_config['memory_threshold_mb']
    
    def test_memory_usage_patterns(self, temp_config_dir, benchmark_config):
        """Test memory usage patterns and potential leaks"""
        import gc
        
        # Measure baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        memory_measurements = []
        
        # Run multiple iterations to check for memory leaks
        for iteration in range(10):
            # Create and destroy config managers
            config_manager = ConfigManager(config_dir=str(temp_config_dir))
            
            # Add agents
            for i in range(10):
                agent_config = {
                    'agent_id': f'MemTestAgent_{i}',
                    'role': f'Memory Test Agent {i}',
                    'model_name': 'test-model',
                    'temperature': 0.5,
                    'personality': 'test',
                    'enabled': True,
                    'max_tokens': 800,
                    'system_prompt': 'Test prompt ' * 100  # Larger prompt
                }
                config_manager.agents[f'MemTestAgent_{i}'] = agent_config
            
            # Validate configuration (creates more objects)
            config_manager.validate_config()
            
            # Force cleanup
            del config_manager
            gc.collect()
            
            # Measure memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_measurements.append(current_memory - baseline_memory)
        
        # Analyze memory usage
        avg_memory_growth = statistics.mean(memory_measurements)
        max_memory_growth = max(memory_measurements)
        final_memory_growth = memory_measurements[-1]
        
        print(f"\nMemory Usage Pattern Analysis:")
        print(f"  Baseline memory: {baseline_memory:.1f}MB")
        print(f"  Average growth: {avg_memory_growth:.1f}MB")
        print(f"  Max growth: {max_memory_growth:.1f}MB") 
        print(f"  Final growth: {final_memory_growth:.1f}MB")
        
        # Memory leak detection
        # Final memory should not be significantly higher than average (indicates leak)
        assert final_memory_growth < avg_memory_growth * 1.5
        assert max_memory_growth < benchmark_config['memory_threshold_mb']


@pytest.mark.benchmark
class TestScalabilityBenchmarks:
    """Test system scalability with varying loads"""
    
    @pytest.mark.asyncio
    async def test_agent_count_scalability(self, temp_config_dir):
        """Test how performance scales with agent count"""
        agent_counts = [1, 2, 5, 10, 20]
        results = {}
        
        for count in agent_counts:
            # Create mock agents
            mock_agents = {}
            for i in range(count):
                agent_id = f"ScaleAgent_{i:02d}"
                mock_agents[agent_id] = MockPerformanceAgent(agent_id, 0.1)
            
            with patch('collaboration.system.get_config_manager') as mock_get_config:
                mock_config_manager = MockPerformanceAgent("config", 0)
                mock_config_manager.system_config = type('obj', (object,), {
                    'session_save_dir': str(temp_config_dir),
                    'enable_metrics': True
                })
                mock_get_config.return_value = mock_config_manager
                
                system = LocalAgent2AgentSystem(config_dir=str(temp_config_dir))
                system.agents = mock_agents
                
                # Time a single analysis phase
                start_time = time.perf_counter()
                analysis_results = await system._run_phase1_analysis("Scale test problem")
                end_time = time.perf_counter()
                
                execution_time = end_time - start_time
                results[count] = {
                    'execution_time': execution_time,
                    'agents_processed': len(analysis_results),
                    'time_per_agent': execution_time / count if count > 0 else 0
                }
        
        print(f"\nAgent Count Scalability:")
        print(f"{'Agents':<8} {'Time':<8} {'Per Agent':<12} {'Efficiency':<12}")
        print("-" * 44)
        
        baseline_efficiency = None
        
        for count, result in results.items():
            if baseline_efficiency is None:
                baseline_efficiency = result['time_per_agent']
                efficiency_ratio = 1.0
            else:
                efficiency_ratio = baseline_efficiency / result['time_per_agent'] if result['time_per_agent'] > 0 else 0
            
            print(f"{count:<8} "
                  f"{result['execution_time']:.3f}s   "
                  f"{result['time_per_agent']:.4f}s     "
                  f"{efficiency_ratio:.2f}x")
        
        # Scalability assertions
        # Time per agent should not increase dramatically (indicates good concurrency)
        single_agent_time = results[1]['time_per_agent']
        twenty_agent_time = results[20]['time_per_agent']
        
        # 20 agents shouldn't take more than 2x time per agent vs 1 agent
        assert twenty_agent_time < single_agent_time * 2


if __name__ == "__main__":
    # Run benchmarks directly
    pytest.main([__file__, "-v", "-m", "benchmark", "--tb=short"])