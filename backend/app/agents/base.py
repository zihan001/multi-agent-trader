"""
Base agent class for all AI trading agents.

Provides common interface and utilities for agent implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.agents.llm_client import LLMClient
from app.core.config import settings


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    
    All agents must implement the analyze() method which takes
    context data and returns structured analysis.
    """
    
    def __init__(
        self, 
        db: Session, 
        llm_client: Optional[LLMClient] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the agent.
        
        Args:
            db: Database session
            llm_client: Optional LLM client (creates new if not provided)
            model: Optional model override (defaults to agent's default)
        """
        self.db = db
        self.llm_client = llm_client or LLMClient(db)
        self.model = model or self.get_default_model()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging."""
        pass
    
    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role description."""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get default model for this agent."""
        pass
    
    @abstractmethod
    def build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build the prompt messages for the LLM.
        
        Args:
            context: Context data for analysis
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured output.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured analysis dict
        """
        pass
    
    def analyze(
        self, 
        context: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run agent analysis on provided context.
        
        Args:
            context: Context data for analysis
            temperature: LLM sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured analysis with metadata
        """
        # Build prompt
        messages = self.build_prompt(context)
        
        # Call LLM
        llm_response = self.llm_client.call(
            messages=messages,
            model=self.model,
            agent_name=self.name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Parse response
        analysis = self.parse_response(llm_response["content"])
        
        # Add metadata
        result = {
            "agent": self.name,
            "model": llm_response["model"],
            "analysis": analysis,
            "metadata": {
                "tokens": llm_response["total_tokens"],
                "cost": llm_response["cost"],
                "latency": llm_response["latency"],
                "finish_reason": llm_response["finish_reason"],
            }
        }
        
        return result
    
    async def aanalyze(
        self, 
        context: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run agent analysis asynchronously.
        
        Args:
            context: Context data for analysis
            temperature: LLM sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured analysis with metadata
        """
        # Build prompt
        messages = self.build_prompt(context)
        
        # Call LLM asynchronously
        llm_response = await self.llm_client.acall(
            messages=messages,
            model=self.model,
            agent_name=self.name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Parse response
        analysis = self.parse_response(llm_response["content"])
        
        # Add metadata
        result = {
            "agent": self.name,
            "model": llm_response["model"],
            "analysis": analysis,
            "metadata": {
                "tokens": llm_response["total_tokens"],
                "cost": llm_response["cost"],
                "latency": llm_response["latency"],
                "finish_reason": llm_response["finish_reason"],
            }
        }
        
        return result


class AnalystAgent(BaseAgent):
    """
    Base class for analyst agents (Technical, Sentiment, Tokenomics).
    
    Uses cheap model by default.
    """
    
    def get_default_model(self) -> str:
        """Analysts use the cheap model."""
        return settings.cheap_model


class DecisionAgent(BaseAgent):
    """
    Base class for decision agents (Researcher, Trader, Risk Manager).
    
    Uses strong model by default.
    """
    
    def get_default_model(self) -> str:
        """Decision makers use the strong model."""
        return settings.strong_model
