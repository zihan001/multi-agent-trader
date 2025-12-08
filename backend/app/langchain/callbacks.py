"""
Custom LangChain callbacks for observability.

Replaces LangSmith with custom logging to our database.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from sqlalchemy.orm import Session

from app.models.database import AgentLog


class DatabaseCallbackHandler(BaseCallbackHandler):
    """
    Custom callback handler that logs LangChain operations to our database.
    
    This replaces LangSmith for observability while keeping everything open-source.
    """
    
    def __init__(self, db: Session, agent_name: str = "langchain"):
        """
        Initialize callback handler.
        
        Args:
            db: Database session for logging
            agent_name: Name of the agent making calls
        """
        self.db = db
        self.agent_name = agent_name
        self.run_data = {}  # Track data for each run
        
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts running."""
        self.run_data[str(run_id)] = {
            "start_time": datetime.utcnow(),
            "prompts": prompts,
            "model": serialized.get("name", "unknown"),
            "metadata": metadata or {},
        }
        
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM ends running."""
        run_id_str = str(run_id)
        if run_id_str not in self.run_data:
            return
            
        run_info = self.run_data[run_id_str]
        
        # Extract token usage
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)
        total_tokens = token_usage.get("total_tokens", input_tokens + output_tokens)
        
        # Calculate cost (simplified - can be enhanced)
        model = run_info["model"]
        cost = self._estimate_cost(model, input_tokens, output_tokens)
        
        # Calculate latency
        latency = (datetime.utcnow() - run_info["start_time"]).total_seconds()
        
        # Get output
        output_text = ""
        if response.generations:
            output_text = response.generations[0][0].text
        
        # Log to database
        log_entry = AgentLog(
            agent_name=self.agent_name,
            model=model,
            input_data=str(run_info["prompts"]),
            output_data=output_text,
            tokens_used=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            latency_seconds=latency,
            timestamp=datetime.utcnow(),
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        # Clean up
        del self.run_data[run_id_str]
        
    def on_llm_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM errors."""
        run_id_str = str(run_id)
        if run_id_str in self.run_data:
            run_info = self.run_data[run_id_str]
            
            # Log error to database
            log_entry = AgentLog(
                agent_name=self.agent_name,
                model=run_info["model"],
                input_data=str(run_info["prompts"]),
                output_data=f"ERROR: {str(error)}",
                tokens_used=0,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                latency_seconds=(datetime.utcnow() - run_info["start_time"]).total_seconds(),
                timestamp=datetime.utcnow(),
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
            # Clean up
            del self.run_data[run_id_str]
    
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost based on model and token usage.
        
        Args:
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Estimated cost in USD
        """
        # Cost per 1M tokens (simplified, can be enhanced)
        costs = {
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        }
        
        # Match model name (flexible matching)
        model_lower = model.lower()
        for key, rates in costs.items():
            if key in model_lower:
                input_cost = (input_tokens / 1_000_000) * rates["input"]
                output_cost = (output_tokens / 1_000_000) * rates["output"]
                return input_cost + output_cost
        
        # Default fallback
        return (input_tokens + output_tokens) / 1_000_000 * 2.0


class ConsoleCallbackHandler(BaseCallbackHandler):
    """
    Simple callback handler that prints to console for debugging.
    """
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts running."""
        print(f"[LangChain] Starting LLM call with {serialized.get('name', 'unknown')}")
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends running."""
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        print(f"[LangChain] LLM call completed. Tokens: {token_usage.get('total_tokens', 0)}")
        
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        print(f"[LangChain] LLM error: {str(error)}")
