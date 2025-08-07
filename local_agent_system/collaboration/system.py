"""
Complete multi-agent collaboration system implementation
"""
import asyncio
import time
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.local_agent import LocalAgent
from utils.ollama_client import OllamaClient, OllamaConfig
from config.settings import get_config_manager
from utils.response_parser import ResponseParser

logger = logging.getLogger(__name__)

class CollaborationMetrics:
    """Track metrics for collaboration sessions"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.start_time = None
        self.end_time = None
        self.total_duration = 0.0
        self.phase_durations = {}
        self.agent_response_times = {}
        self.total_tokens_used = 0
        self.successful_responses = 0
        self.failed_responses = 0
        self.phase_results = {}
    
    def start_session(self):
        self.start_time = time.time()
        logger.info("Collaboration session started")
    
    def end_session(self):
        if self.start_time:
            self.end_time = time.time()
            self.total_duration = self.end_time - self.start_time
            logger.info(f"Collaboration session completed in {self.total_duration:.2f}s")
    
    def record_phase_duration(self, phase: str, duration: float):
        self.phase_durations[phase] = duration
        logger.debug(f"Phase {phase} completed in {duration:.2f}s")
    
    def record_agent_response(self, agent_id: str, duration: float, success: bool):
        if agent_id not in self.agent_response_times:
            self.agent_response_times[agent_id] = []
        self.agent_response_times[agent_id].append(duration)
        
        if success:
            self.successful_responses += 1
        else:
            self.failed_responses += 1
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_duration": round(self.total_duration, 2),
            "phase_durations": {k: round(v, 2) for k, v in self.phase_durations.items()},
            "agent_avg_response_times": {
                agent: round(sum(times) / len(times), 2)
                for agent, times in self.agent_response_times.items()
            },
            "success_rate": (
                self.successful_responses / (self.successful_responses + self.failed_responses)
                if (self.successful_responses + self.failed_responses) > 0 else 0.0
            ),
            "total_responses": self.successful_responses + self.failed_responses
        }

class LocalAgent2AgentSystem:
    """
    Complete orchestration system implementing:
    - Agent registration and management
    - 4-phase collaboration workflow
    - Concurrent async processing
    - Metrics and reporting
    - Session persistence
    """
    
    def __init__(self, config_dir: str = None, preset: str = None, config_file: str = None):
        self.config_manager = get_config_manager(config_dir, preset)
        
        if config_file:
            self.config_manager.load_config(config_file)
        elif not hasattr(self.config_manager, 'system_config') or not self.config_manager.agents:
            self.config_manager.load_config()
        
        self.system_config = self.config_manager.system_config
        self.agents: Dict[str, LocalAgent] = {}
        self.ollama_client: Optional[OllamaClient] = None
        self.metrics = CollaborationMetrics()
        
        # Setup session persistence
        self.session_dir = Path(self.system_config.session_save_dir)
        self.session_dir.mkdir(exist_ok=True)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging based on system config"""
        log_level = getattr(logging, self.system_config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.session_dir / "collaboration.log")
            ]
        )
    
    async def initialize_system(self) -> bool:
        """Initialize the collaboration system and all agents"""
        logger.info("Initializing Local Agent2Agent System")
        
        try:
            # Initialize Ollama client
            ollama_config = OllamaConfig(
                base_url=self.system_config.ollama_base_url,
                timeout=self.system_config.ollama_timeout,
                max_retries=self.system_config.max_retries,
                retry_delay=self.system_config.retry_delay
            )
            
            self.ollama_client = OllamaClient(ollama_config)
            
            # Test Ollama connection
            async with self.ollama_client as client:
                if not await client.test_connection():
                    logger.error("Failed to connect to Ollama. Please ensure Ollama is running.")
                    return False
                
                # Initialize all agents
                await self._initialize_agents(client)
                
                # Test all agent connectivity
                connectivity_results = await self._test_agent_connectivity()
                
                if not all(connectivity_results.values()):
                    failed_agents = [agent_id for agent_id, result in connectivity_results.items() if not result]
                    logger.error(f"Failed to initialize agents: {failed_agents}")
                    return False
                
                logger.info(f"Successfully initialized {len(self.agents)} agents")
                return True
                
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    async def _initialize_agents(self, client: OllamaClient):
        """Initialize all agents with their configurations"""
        enabled_agents = self.config_manager.get_enabled_agents()
        for agent_config in enabled_agents.values():
            agent = LocalAgent(agent_config)
            success = await agent.initialize()
            if success:
                self.agents[agent_config.agent_id] = agent
                logger.debug(f"Initialized agent: {agent_config.agent_id}")
            else:
                logger.error(f"Failed to initialize agent: {agent_config.agent_id}")
    
    async def _test_agent_connectivity(self) -> Dict[str, bool]:
        """Test connectivity for all agents"""
        logger.info("Testing agent connectivity...")
        
        connectivity_tasks = [
            agent.test_connectivity() for agent in self.agents.values()
        ]
        
        results = await asyncio.gather(*connectivity_tasks, return_exceptions=True)
        
        connectivity_status = {}
        for agent_id, result in zip(self.agents.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Connectivity test failed for {agent_id}: {result}")
                connectivity_status[agent_id] = False
            else:
                connectivity_status[agent_id] = result
        
        return connectivity_status
    
    async def run_collaborative_problem_solving(self, problem: str) -> Dict[str, Any]:
        """
        Main collaboration orchestration implementing 4-phase workflow:
        Phase 1: Individual Analysis (concurrent)
        Phase 2: Cross-Agent Critique (round-robin)
        Phase 3: Solution Synthesis (concurrent)
        Phase 4: Consensus Building (algorithmic)
        """
        if not self.agents:
            raise RuntimeError("System not initialized. Call initialize_system() first.")
        
        logger.info(f"Starting collaborative problem solving for: {problem[:100]}...")
        self.metrics.reset()
        self.metrics.start_session()
        
        try:
            # Phase 1: Individual Analysis
            phase1_results = await self._phase1_individual_analysis(problem)
            
            # Phase 2: Cross-Agent Critique
            phase2_results = await self._phase2_cross_critique(phase1_results, problem)
            
            # Phase 3: Solution Synthesis
            phase3_results = await self._phase3_solution_synthesis(phase1_results, problem)
            
            # Phase 4: Consensus Building
            final_consensus = await self._phase4_consensus_building(
                phase1_results, phase2_results, phase3_results, problem
            )
            
            self.metrics.end_session()
            
            # Save session
            session_data = self._create_session_data(
                problem, phase1_results, phase2_results, phase3_results, final_consensus
            )
            
            if self.system_config.enable_metrics:
                await self._save_session(session_data)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Collaboration failed: {e}")
            self.metrics.end_session()
            raise
    
    async def _phase1_individual_analysis(self, problem: str) -> Dict[str, Any]:
        """Phase 1: All agents analyze the problem concurrently"""
        logger.info("Phase 1: Starting individual analysis")
        phase_start = time.time()
        
        # Create tasks for all agents
        analysis_tasks = [
            self._safe_agent_task(agent.analyze_problem(problem), agent.agent_id)
            for agent in self.agents.values()
        ]
        
        # Execute all analyses concurrently
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Process results
        phase1_results = {}
        for agent_id, result in zip(self.agents.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Phase 1 failed for {agent_id}: {result}")
                phase1_results[agent_id] = self._create_error_response(agent_id, str(result))
            else:
                phase1_results[agent_id] = result
        
        phase_duration = time.time() - phase_start
        self.metrics.record_phase_duration("phase1", phase_duration)
        
        logger.info(f"Phase 1 completed with {len(phase1_results)} analyses")
        return phase1_results
    
    async def _phase2_cross_critique(self, phase1_results: Dict[str, Any], problem: str) -> Dict[str, Any]:
        """Phase 2: Round-robin critique (each agent critiques the next agent's work)"""
        logger.info("Phase 2: Starting cross-agent critique")
        phase_start = time.time()
        
        agent_ids = list(self.agents.keys())
        critique_tasks = []
        critique_assignments = {}
        
        # Create round-robin critique assignments
        for i, agent_id in enumerate(agent_ids):
            target_agent_id = agent_ids[(i + 1) % len(agent_ids)]  # Next agent in circle
            target_analysis = phase1_results.get(target_agent_id, {})
            
            critique_assignments[agent_id] = target_agent_id
            agent = self.agents[agent_id]
            
            critique_task = self._safe_agent_task(
                agent.critique_analysis(problem, {target_agent_id: target_analysis}),
                agent_id
            )
            critique_tasks.append(critique_task)
        
        # Execute all critiques concurrently
        results = await asyncio.gather(*critique_tasks, return_exceptions=True)
        
        # Process results
        phase2_results = {}
        for agent_id, result in zip(agent_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Phase 2 failed for {agent_id}: {result}")
                phase2_results[agent_id] = self._create_error_response(agent_id, str(result))
            else:
                result['critique_target'] = critique_assignments[agent_id]
                phase2_results[agent_id] = result
        
        phase_duration = time.time() - phase_start
        self.metrics.record_phase_duration("phase2", phase_duration)
        
        logger.info(f"Phase 2 completed with {len(phase2_results)} critiques")
        return phase2_results
    
    async def _phase3_solution_synthesis(self, phase1_results: Dict[str, Any], problem: str) -> Dict[str, Any]:
        """Phase 3: All agents synthesize solutions concurrently"""
        logger.info("Phase 3: Starting solution synthesis")
        phase_start = time.time()
        
        # Prepare all analyses for synthesis
        all_analyses = list(phase1_results.values())
        
        # Create synthesis tasks for all agents
        synthesis_tasks = [
            self._safe_agent_task(agent.synthesize_insights(problem, phase1_results, {}), agent.agent_id)
            for agent in self.agents.values()
        ]
        
        # Execute all synthesis concurrently
        results = await asyncio.gather(*synthesis_tasks, return_exceptions=True)
        
        # Process results
        phase3_results = {}
        for agent_id, result in zip(self.agents.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Phase 3 failed for {agent_id}: {result}")
                phase3_results[agent_id] = self._create_error_response(agent_id, str(result))
            else:
                phase3_results[agent_id] = result
        
        phase_duration = time.time() - phase_start
        self.metrics.record_phase_duration("phase3", phase_duration)
        
        logger.info(f"Phase 3 completed with {len(phase3_results)} syntheses")
        return phase3_results
    
    async def _phase4_consensus_building(self, phase1_results: Dict[str, Any], 
                                       phase2_results: Dict[str, Any],
                                       phase3_results: Dict[str, Any], 
                                       problem: str) -> Dict[str, Any]:
        """Phase 4: Algorithmic consensus building with confidence weighting"""
        logger.info("Phase 4: Building consensus")
        phase_start = time.time()
        
        # Collect all insights and solutions
        all_insights = []
        all_solutions = []
        confidence_weights = {}
        
        for agent_id in self.agents.keys():
            # Phase 1 insights
            if agent_id in phase1_results:
                analysis = phase1_results[agent_id]
                confidence = analysis.get('confidence_level', 0.5)
                confidence_weights[f"{agent_id}_analysis"] = confidence
                
                insights = analysis.get('key_insights', [])
                for insight in insights:
                    all_insights.append({
                        'content': insight,
                        'source_agent': agent_id,
                        'source_phase': 'analysis',
                        'confidence': confidence
                    })
                
                all_solutions.append({
                    'content': analysis.get('main_response', ''),
                    'source_agent': agent_id,
                    'source_phase': 'analysis',
                    'confidence': confidence
                })
            
            # Phase 3 insights
            if agent_id in phase3_results:
                synthesis = phase3_results[agent_id]
                confidence = synthesis.get('confidence_level', 0.5)
                confidence_weights[f"{agent_id}_synthesis"] = confidence
                
                insights = synthesis.get('key_insights', [])
                for insight in insights:
                    all_insights.append({
                        'content': insight,
                        'source_agent': agent_id,
                        'source_phase': 'synthesis',
                        'confidence': confidence
                    })
                
                all_solutions.append({
                    'content': synthesis.get('main_response', ''),
                    'source_agent': agent_id,
                    'source_phase': 'synthesis',
                    'confidence': confidence
                })
        
        # Build consensus through confidence weighting
        consensus = self._build_weighted_consensus(all_insights, all_solutions, confidence_weights)
        
        phase_duration = time.time() - phase_start
        self.metrics.record_phase_duration("phase4", phase_duration)
        
        logger.info("Phase 4: Consensus building completed")
        return consensus
    
    def _build_weighted_consensus(self, all_insights: List[Dict], all_solutions: List[Dict], 
                                confidence_weights: Dict[str, float]) -> Dict[str, Any]:
        """Build consensus using confidence-weighted aggregation"""
        
        # Sort insights by confidence
        weighted_insights = sorted(all_insights, key=lambda x: x['confidence'], reverse=True)
        
        # Sort solutions by confidence
        weighted_solutions = sorted(all_solutions, key=lambda x: x['confidence'], reverse=True)
        
        # Calculate overall confidence
        total_confidence = sum(confidence_weights.values())
        avg_confidence = total_confidence / len(confidence_weights) if confidence_weights else 0.5
        
        # Extract top insights (confidence-weighted)
        top_insights = []
        seen_insights = set()
        for insight in weighted_insights:
            content = insight['content'].lower().strip()
            if content not in seen_insights and len(top_insights) < 5:
                top_insights.append(insight['content'])
                seen_insights.add(content)
        
        # Create consensus main response
        top_solution = weighted_solutions[0] if weighted_solutions else {}
        main_response = f"""
        COLLABORATIVE CONSENSUS SOLUTION:
        
        Based on multi-agent analysis with average confidence of {avg_confidence:.2f}, the recommended approach is:
        
        {top_solution.get('content', 'No clear solution identified')}
        
        This solution incorporates insights from {len(set(s['source_agent'] for s in weighted_solutions))} different perspectives
        and represents the weighted consensus of the agent collective.
        """
        
        # Identify critical next actions
        next_actions = []
        for solution in weighted_solutions:
            if 'next_action' in solution:
                next_actions.append(solution['next_action'])
        
        return {
            "consensus_type": "confidence_weighted",
            "agent_id": "SYSTEM_CONSENSUS",
            "main_response": main_response.strip(),
            "confidence_level": round(avg_confidence, 2),
            "key_insights": top_insights,
            "questions_for_others": [],
            "next_action": next_actions[0] if next_actions else "Proceed with implementation",
            "reasoning": f"Consensus built from {len(weighted_solutions)} agent perspectives with confidence weighting",
            "contributing_agents": list(set(s['source_agent'] for s in weighted_solutions)),
            "consensus_strength": len(weighted_solutions),
            "total_insights_considered": len(all_insights)
        }
    
    async def _safe_agent_task(self, task_coro, agent_id: str):
        """Execute agent task with error handling and timing"""
        start_time = time.time()
        try:
            result = await task_coro
            duration = time.time() - start_time
            self.metrics.record_agent_response(agent_id, duration, True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.metrics.record_agent_response(agent_id, duration, False)
            logger.error(f"Agent task failed for {agent_id}: {e}")
            raise
    
    def _create_error_response(self, agent_id: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "agent_id": agent_id,
            "main_response": f"Agent error: {error_message}",
            "confidence_level": 0.0,
            "key_insights": ["Agent encountered an error"],
            "questions_for_others": [],
            "next_action": "Investigate agent error",
            "reasoning": f"Error in agent {agent_id}: {error_message}",
            "error": True
        }
    
    def _create_session_data(self, problem: str, phase1: Dict, phase2: Dict, 
                           phase3: Dict, consensus: Dict) -> Dict[str, Any]:
        """Create complete session data for persistence"""
        return {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "problem": problem,
            "results": {
                "phase1_individual_analysis": phase1,
                "phase2_cross_critique": phase2,
                "phase3_solution_synthesis": phase3,
                "phase4_consensus": consensus
            },
            "metrics": self.metrics.get_summary(),
            "agent_status": {agent_id: agent.get_status() for agent_id, agent in self.agents.items()}
        }
    
    async def _save_session(self, session_data: Dict[str, Any]):
        """Save session data to file"""
        try:
            session_file = self.session_dir / f"session_{session_data['session_id']}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Session saved to {session_file}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "system_initialized": bool(self.agents),
            "agent_count": len(self.agents),
            "preset": getattr(self.config_manager, 'preset', 'unknown'),
            "agents": {agent_id: agent.get_status() for agent_id, agent in self.agents.items()},
            "metrics": self.metrics.get_summary(),
            "config": {
                "ollama_url": self.system_config.ollama_base_url,
                "timeout": self.system_config.ollama_timeout,
                "max_retries": self.system_config.max_retries
            }
        }
    
    async def _run_phase1_analysis(self, problem: str) -> Dict[str, Any]:
        """Run Phase 1 analysis - exposed for testing"""
        return await self._phase1_individual_analysis(problem)
    
    async def _run_phase2_critique(self, problem: str, phase1_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run Phase 2 critique - exposed for testing"""
        return await self._phase2_cross_critique(phase1_results, problem)
    
    async def _run_phase3_synthesis(self, problem: str, phase1_results: Dict[str, Any], phase2_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run Phase 3 synthesis - exposed for testing"""
        return await self._phase3_solution_synthesis(phase1_results, problem)
    
    def _build_algorithmic_consensus(self, problem: str, synthesis_results: Dict[str, Any], confidence_weights: Dict[str, float]) -> Dict[str, Any]:
        """Build algorithmic consensus - exposed for testing"""
        return self._build_weighted_consensus([], [], confidence_weights)
    
    async def cleanup(self):
        """Cleanup system resources"""
        # Cleanup all agents
        for agent in self.agents.values():
            await agent.cleanup()
        
        # Cleanup Ollama client
        if self.ollama_client:
            await self.ollama_client.close()
            
        self.agents.clear()
        logger.info("System cleanup completed")
