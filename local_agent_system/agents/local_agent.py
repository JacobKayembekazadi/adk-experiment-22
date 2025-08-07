"""
Local Ollama agent implementation with complete functionality
"""
import time
import logging
import sys
from typing import Dict, Any, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from utils.ollama_client import OllamaClient, OllamaConfig
from utils.response_parser import ResponseParser
from config.config_schema import AgentConfig

logger = logging.getLogger(__name__)

class LocalAgent(BaseAgent):
    """
    Complete implementation of LocalAgent with:
    - Async Ollama API integration
    - JSON response parsing with fallbacks
    - Role-specific system prompts
    - Error handling and recovery
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config.agent_id, config.role, config.personality)
        self.config = config
        self.ollama_client: OllamaClient = None
        self.system_prompt = config.system_prompt
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the agent with Ollama client"""
        try:
            # Create Ollama client with configuration
            from config.settings import get_config_manager
            config_manager = get_config_manager()
            
            ollama_config = OllamaConfig(
                base_url=config_manager.system_config.ollama_base_url,
                timeout=config_manager.system_config.ollama_timeout,
                max_retries=config_manager.system_config.max_retries,
                retry_delay=config_manager.system_config.retry_delay
            )
            
            self.ollama_client = OllamaClient(ollama_config)
            
            # Test connection
            async with self.ollama_client as client:
                if await client.test_connection():
                    self.is_initialized = True
                    self._logger.info(f"Agent {self.agent_id} initialized successfully")
                    return True
                else:
                    self._logger.error(f"Failed to initialize agent {self.agent_id}")
                    return False
                    
        except Exception as e:
            self._logger.error(f"Error initializing agent {self.agent_id}: {e}")
            return False
        
    async def generate_response_async(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """Generate structured JSON response via Ollama API"""
        if not self.is_initialized:
            return self._create_error_response("Agent not properly initialized")
            
        start_time = time.time()
        
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context)
            
            self._logger.debug(f"Generating response for prompt: {prompt[:100]}...")
            
            # Generate response using Ollama
            async with self.ollama_client as client:
                raw_response = await client.generate_with_retry(
                    model=self.config.model_name,
                    prompt=full_prompt,
                    system=self.system_prompt,
                    temperature=self.config.temperature,
                    format="json"
                )
            
            # Parse the response
            response_text = raw_response.response if hasattr(raw_response, 'response') else str(raw_response)
            parsed_response = ResponseParser.parse_agent_response(response_text, self.agent_id)
            
            # Update metrics
            response_time = time.time() - start_time
            tokens = (
                (raw_response.eval_count + raw_response.prompt_eval_count) 
                if hasattr(raw_response, 'eval_count') and hasattr(raw_response, 'prompt_eval_count')
                else 0
            )
            self._update_metrics(True, response_time, tokens)
            
            self._logger.info(f"Successfully generated response in {response_time:.2f}s")
            return parsed_response
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(False, response_time)
            self._logger.error(f"Failed to generate response: {e}")
            
            # Return fallback response
            return self._create_error_response(str(e))
    
    async def analyze_problem(self, problem: str) -> Dict[str, Any]:
        """Phase 1: Individual analysis of the given problem"""
        self._logger.info(f"Starting individual problem analysis")
        
        analysis_prompt = f"""
        Analyze the following problem from your perspective as a {self.role}:
        
        PROBLEM: {problem}
        
        Provide a comprehensive analysis that includes:
        1. Your initial assessment of the problem
        2. Key considerations from your role's perspective
        3. Potential approaches or solutions
        4. Critical factors that need attention
        5. Your confidence in your analysis
        
        Focus on what you bring uniquely as a {self.role} with {self.personality} characteristics.
        """
        
        return await self.generate_response_async(analysis_prompt)
        
    # Alias for compatibility
    async def analyze_task(self, task: str) -> Dict[str, Any]:
        """Phase 1: Individual analysis (alias for analyze_problem)"""
        return await self.analyze_problem(task)
    
    async def critique_analysis(self, problem: str, other_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Critique other agents' analyses"""
        self._logger.info(f"Starting critique of other analyses")
        
        # Format other analyses for the prompt
        analyses_text = []
        for agent_id, analysis in other_analyses.items():
            if agent_id != self.agent_id:  # Don't critique self
                analyses_text.append(f"""
                Agent: {agent_id}
                Response: {analysis.get('main_response', '')[:300]}...
                Key Insights: {', '.join(analysis.get('key_insights', [])[:3])}
                Confidence: {analysis.get('confidence_level', 0)}
                """)
        
        critique_prompt = f"""
        Review and critique the following analyses from other agents:
        
        ORIGINAL PROBLEM: {problem}
        
        OTHER AGENTS' ANALYSES:
        {chr(10).join(analyses_text)}
        
        As a {self.role}, provide a constructive critique that includes:
        1. Strengths you see in their analyses
        2. Gaps or weaknesses you identify
        3. Alternative perspectives from your expertise
        4. Questions that need to be addressed
        5. Suggestions for improvement
        
        Be constructive but honest in your assessment.
        """
        
        return await self.generate_response_async(critique_prompt)
    
    async def synthesize_insights(self, problem: str, all_analyses: Dict[str, Any], all_critiques: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Synthesize all perspectives into unified solutions"""
        self._logger.info(f"Synthesizing insights from analyses and critiques")
        
        # Prepare summary of all analyses
        analyses_summary = []
        for agent_id, analysis in all_analyses.items():
            main_response = analysis.get('main_response', '')
            insights = analysis.get('key_insights', [])
            confidence = analysis.get('confidence_level', 0)
            
            summary = f"""
            Agent: {agent_id}
            Analysis: {main_response[:200]}...
            Key Insights: {', '.join(insights[:2])}
            Confidence: {confidence}
            """
            analyses_summary.append(summary)
        
        synthesis_prompt = f"""
        Synthesize insights from all agent analyses and critiques to create a comprehensive solution:
        
        ORIGINAL PROBLEM: {problem}
        
        ALL AGENT ANALYSES:
        {chr(10).join(analyses_summary)}
        
        As a {self.role}, synthesize these perspectives into:
        1. A unified understanding of the problem
        2. Integration of the best insights from all analyses
        3. A comprehensive solution approach
        4. Implementation recommendations
        5. Potential risks and mitigation strategies
        
        Focus on creating a coherent, actionable synthesis that leverages the collective intelligence.
        """
        
        return await self.generate_response_async(synthesis_prompt)
        
    # Alias for compatibility
    async def synthesize_solutions(self, all_analyses: List[Dict[str, Any]], task: str) -> Dict[str, Any]:
        """Phase 3: Synthesize solutions (alias for synthesize_insights)"""
        # Convert list to dict format
        analyses_dict = {f"Agent_{i}": analysis for i, analysis in enumerate(all_analyses)}
        return await self.synthesize_insights(task, analyses_dict, {})
    
    async def build_consensus(self, problem: str, all_syntheses: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Build consensus from syntheses"""
        self._logger.info(f"Building consensus from syntheses")
        
        # Format syntheses for the prompt
        syntheses_summary = []
        for agent_id, synthesis in all_syntheses.items():
            main_response = synthesis.get('main_response', '')
            insights = synthesis.get('key_insights', [])
            confidence = synthesis.get('confidence_level', 0)
            
            summary = f"""
            Agent: {agent_id}
            Synthesis: {main_response[:200]}...
            Key Insights: {', '.join(insights[:2])}
            Confidence: {confidence}
            """
            syntheses_summary.append(summary)
        
        consensus_prompt = f"""
        Build consensus from the following agent syntheses:
        
        ORIGINAL PROBLEM: {problem}
        
        AGENT SYNTHESES:
        {chr(10).join(syntheses_summary)}
        
        As a {self.role}, help build consensus by:
        1. Identifying common themes across syntheses
        2. Highlighting areas of agreement
        3. Addressing any disagreements constructively
        4. Proposing a unified path forward
        5. Assessing overall confidence in the solution
        
        Focus on creating consensus while preserving the best insights from all perspectives.
        """
        
        return await self.generate_response_async(consensus_prompt)
    
    def _prepare_prompt(self, prompt: str, context: str = "") -> str:
        """Prepare the full prompt with context"""
        if context:
            return f"""
            CONTEXT: {context}
            
            PROMPT: {prompt}
            
            Please respond in valid JSON format according to the specified schema.
            """
        return prompt
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a valid response structure for error cases"""
        return {
            "agent_id": self.agent_id,
            "main_response": f"Error occurred during response generation: {error_message}",
            "confidence_level": 0.0,
            "key_insights": ["Error in processing", "Requires retry or manual intervention"],
            "questions_for_others": ["Can other agents help with this analysis?"],
            "next_action": "Retry with different approach or escalate",
            "reasoning": f"Agent {self.agent_id} encountered an error: {error_message}"
        }
    
    async def test_connectivity(self) -> bool:
        """Test if the agent can connect to its assigned model"""
        if not self.ollama_client:
            return False
            
        try:
            self._logger.info(f"Testing connectivity for model {self.config.model_name}")
            
            async with self.ollama_client as client:
                test_response = await client.generate_with_retry(
                    model=self.config.model_name,
                    prompt="Test connectivity. Respond with valid JSON: {\"status\": \"connected\", \"agent_id\": \"" + self.agent_id + "\"}",
                    system="You are testing connectivity. Respond only with the requested JSON.",
                    temperature=0.1,
                    format="json"
                )
                
                if hasattr(test_response, 'response') and test_response.response:
                    self._logger.info(f"Connectivity test successful for {self.agent_id}")
                    return True
                else:
                    self._logger.error(f"Connectivity test failed for {self.agent_id}")
                    return False
                    
        except Exception as e:
            self._logger.error(f"Connectivity test error for {self.agent_id}: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup agent resources"""
        if self.ollama_client:
            await self.ollama_client.close()
        self.is_initialized = False
        
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and configuration"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "personality": self.personality,
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "initialized": self.is_initialized,
            "enabled": getattr(self.config, 'enabled', True),
            "metrics": self.get_metrics(),
            "system_prompt_length": len(self.system_prompt)
        }