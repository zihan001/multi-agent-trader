"""
LLM Decision Engine

Wraps the existing multi-agent pipeline to implement the BaseDecisionEngine interface.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.engines.base import BaseDecisionEngine
from app.models.decisions import (
    DecisionResult, 
    TradingDecision, 
    DecisionMetadata, 
    AgentOutput
)
from app.agents.pipeline import AgentPipeline
from app.agents.llm_client import LLMClient
from app.core.config import settings


class LLMDecisionEngine(BaseDecisionEngine):
    """
    LLM-based decision engine using the multi-agent pipeline.
    
    This engine coordinates 6 specialized LLM agents:
    - Technical Analyst (cheap model)
    - Sentiment Analyst (cheap model) 
    - Tokenomics Analyst (cheap model)
    - Researcher (strong model)
    - Trader (strong model)
    - Risk Manager (strong model)
    """
    
    def __init__(self, db: Session, llm_client: Optional[LLMClient] = None):
        """
        Initialize the LLM decision engine.
        
        Args:
            db: Database session
            llm_client: Optional shared LLM client
        """
        super().__init__(db)
        self.llm_client = llm_client or LLMClient(db)
        self.pipeline = AgentPipeline(db, self.llm_client)
    
    def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: str,
    ) -> DecisionResult:
        """
        Analyze market conditions using LLM agents.
        
        Args:
            symbol: Trading pair symbol
            market_data: Market data context
            portfolio_data: Portfolio state
            run_id: Unique identifier for this analysis run
            
        Returns:
            DecisionResult with agent reasoning and trading decision
        """
        start_time = time.time()
        
        # Run the agent pipeline
        pipeline_result = self.pipeline.run(
            symbol=symbol,
            market_data=market_data,
            portfolio_data=portfolio_data,
            run_id=run_id,
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Convert pipeline result to unified DecisionResult format
        return self._convert_pipeline_result(
            pipeline_result, 
            symbol, 
            run_id,
            execution_time_ms
        )
    
    async def aanalyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: str,
    ) -> DecisionResult:
        """
        Asynchronous analysis using LLM agents.
        
        Args:
            symbol: Trading pair symbol
            market_data: Market data context
            portfolio_data: Portfolio state
            run_id: Unique identifier for this analysis run
            
        Returns:
            DecisionResult with agent reasoning and trading decision
        """
        start_time = time.time()
        
        # Run the agent pipeline asynchronously
        pipeline_result = await self.pipeline.arun(
            symbol=symbol,
            market_data=market_data,
            portfolio_data=portfolio_data,
            run_id=run_id,
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Convert pipeline result to unified DecisionResult format
        return self._convert_pipeline_result(
            pipeline_result,
            symbol,
            run_id,
            execution_time_ms
        )
    
    def _convert_pipeline_result(
        self,
        pipeline_result: Dict[str, Any],
        symbol: str,
        run_id: str,
        execution_time_ms: float
    ) -> DecisionResult:
        """
        Convert legacy pipeline result format to unified DecisionResult.
        
        Args:
            pipeline_result: Result from AgentPipeline
            symbol: Trading pair symbol
            run_id: Run identifier
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            DecisionResult in unified format
        """
        # Extract final decision from pipeline
        final_trade = pipeline_result.get("final_decision", {})
        if not final_trade:
            final_trade = {
                "action": "HOLD",
                "quantity": 0,
                "reasoning": "No decision made",
                "confidence": 0
            }
        
        # Create trading decision
        decision = TradingDecision(
            action=final_trade.get("action", "HOLD"),
            quantity=final_trade.get("quantity", 0.0),
            confidence=final_trade.get("confidence", 0.0),
            reasoning=final_trade.get("reasoning", ""),
            stop_loss=final_trade.get("stop_loss"),
            take_profit=final_trade.get("take_profit"),
        )
        
        # Create metadata
        metadata = DecisionMetadata(
            engine_type="llm",
            strategy_name="multi_agent_pipeline",
            execution_time_ms=execution_time_ms,
            cost=pipeline_result.get("total_cost", 0.0),
            tokens_used=pipeline_result.get("total_tokens", 0),
            model_name=f"cheap: {settings.cheap_model}, strong: {settings.strong_model}",
            timestamp=datetime.fromisoformat(pipeline_result.get("timestamp", datetime.utcnow().isoformat()))
        )
        
        # Convert agent outputs
        agents = {}
        for agent_name, agent_result in pipeline_result.get("agents", {}).items():
            agents[agent_name] = AgentOutput(
                agent_name=agent_name,
                analysis=agent_result.get("analysis", {}),
                metadata=agent_result.get("metadata", {})
            )
        
        # Create unified result
        return DecisionResult(
            run_id=run_id,
            symbol=symbol,
            timestamp=datetime.fromisoformat(pipeline_result.get("timestamp", datetime.utcnow().isoformat())),
            decision=decision,
            metadata=metadata,
            agents=agents,
            signals=None,  # LLM mode doesn't provide raw signals
            status=pipeline_result.get("status", "completed"),
            errors=pipeline_result.get("errors", [])
        )
    
    @property
    def engine_type(self) -> str:
        """Return engine type identifier."""
        return "llm"
    
    @property
    def engine_name(self) -> str:
        """Return human-readable engine name."""
        return "LLM Multi-Agent System"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return engine capabilities."""
        return {
            "engine_type": self.engine_type,
            "engine_name": self.engine_name,
            "supports_reasoning": True,
            "supports_signals": False,
            "cost_per_decision": 0.02,  # Approximate average cost
            "avg_latency_ms": 15000.0,  # ~15 seconds typical
            "agents": [
                "Technical Analyst",
                "Sentiment Analyst",
                "Tokenomics Analyst",
                "Researcher",
                "Trader",
                "Risk Manager"
            ],
            "models": {
                "cheap": settings.cheap_model,
                "strong": settings.strong_model
            }
        }
