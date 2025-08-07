"""
Base agent class defining the interface for all agents
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """Metrics for agent performance tracking"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    total_tokens_processed: int = 0
    last_request_time: Optional[float] = None

class BaseAgent(ABC):
    """Abstract base class for all agents in the system"""
    
    def __init__(self, agent_id: str, role: str, personality: str):
        self.agent_id = agent_id
        self.role = role
        self.personality = personality
        self.metrics = AgentMetrics()
        self._logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    @abstractmethod
    async def generate_response_async(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """Generate structured JSON response"""
        pass
    
    @abstractmethod
    async def analyze_task(self, task: str) -> Dict[str, Any]:
        """Phase 1: Individual analysis"""
        pass
    
    @abstractmethod
    async def critique_analysis(self, other_analysis: Dict[str, Any], task: str) -> Dict[str, Any]:
        """Phase 2: Critique other agent's work"""
        pass
    
    @abstractmethod
    async def synthesize_solutions(self, all_analyses: list, task: str) -> Dict[str, Any]:
        """Phase 3: Synthesize all perspectives"""
        pass
    
    def _update_metrics(self, success: bool, response_time: float, tokens: int = 0):
        """Update agent performance metrics"""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        self.metrics.total_response_time += response_time
        self.metrics.average_response_time = (
            self.metrics.total_response_time / self.metrics.total_requests
        )
        self.metrics.total_tokens_processed += tokens
        self.metrics.last_request_time = time.time()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current agent metrics"""
        success_rate = (
            self.metrics.successful_requests / self.metrics.total_requests
            if self.metrics.total_requests > 0 else 0.0
        )
        
        return {
            "agent_id": self.agent_id,
            "total_requests": self.metrics.total_requests,
            "success_rate": success_rate,
            "average_response_time": round(self.metrics.average_response_time, 2),
            "total_tokens_processed": self.metrics.total_tokens_processed,
            "last_request_time": self.metrics.last_request_time
        }
    
    def reset_metrics(self):
        """Reset agent metrics"""
        self.metrics = AgentMetrics()
        self._logger.info(f"Metrics reset for agent {self.agent_id}")
    
    def __str__(self) -> str:
        return f"{self.agent_id} ({self.role}) - {self.personality}"
    
    def __repr__(self) -> str:
        return f"BaseAgent(id={self.agent_id}, role={self.role})"
