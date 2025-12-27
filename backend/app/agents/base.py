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
    
    def get_response_model(self):
        """
        Get Pydantic model for structured outputs (optional).
        
        Override this method to enable Instructor-based structured outputs.
        If not overridden, falls back to parse_response() method.
        
        Returns:
            Pydantic model class or None
        """
        return None
    
    def analyze_structured(
        self, 
        context: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run agent analysis with structured outputs using Instructor.
        
        Requires get_response_model() to return a Pydantic model.
        
        Args:
            context: Context data for analysis
            temperature: LLM sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured analysis with metadata
        """
        response_model = self.get_response_model()
        if not response_model:
            raise NotImplementedError(
                f"Agent {self.name} must implement get_response_model() "
                "to use structured outputs"
            )
        
        # Build prompt
        messages = self.build_prompt(context)
        
        # Call LLM with structured output
        pydantic_response = self.llm_client.call_structured(
            messages=messages,
            response_model=response_model,
            model=self.model,
            agent_name=self.name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Convert Pydantic model to dict
        analysis = pydantic_response.model_dump()
        
        # Add metadata (note: structured calls don't return metadata directly)
        result = {
            "agent": self.name,
            "model": self.model,
            "analysis": analysis,
            "metadata": {
                "structured": True,
                "model_type": response_model.__name__,
            }
        }
        
        return result
    
    async def aanalyze_structured(
        self, 
        context: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run agent analysis asynchronously with structured outputs using Instructor.
        
        Requires get_response_model() to return a Pydantic model.
        
        Args:
            context: Context data for analysis
            temperature: LLM sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured analysis with metadata
        """
        response_model = self.get_response_model()
        if not response_model:
            raise NotImplementedError(
                f"Agent {self.name} must implement get_response_model() "
                "to use structured outputs"
            )
        
        # Build prompt
        messages = self.build_prompt(context)
        
        # Call LLM asynchronously with structured output
        pydantic_response = await self.llm_client.acall_structured(
            messages=messages,
            response_model=response_model,
            model=self.model,
            agent_name=self.name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Convert Pydantic model to dict
        analysis = pydantic_response.model_dump()
        
        # Add metadata
        result = {
            "agent": self.name,
            "model": self.model,
            "analysis": analysis,
            "metadata": {
                "structured": True,
                "model_type": response_model.__name__,
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
