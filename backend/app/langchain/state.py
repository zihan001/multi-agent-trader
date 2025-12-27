"""
LangGraph state definitions for trading workflow.

Defines the state schema that flows through the agent graph.
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class AnalystResult(BaseModel):
    """Result from an analyst agent."""
    agent_name: str
    analysis: Dict[str, Any]
    confidence: int
    recommendation: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TradingState(BaseModel):
    """
    State that flows through the LangGraph workflow.
    
    This represents all data available at each step of the decision process.
    """
    # Input data
    symbol: str
    timeframe: str = "1h"
    run_id: str
    mode: str = "live"
    
    # Market data
    market_data: Dict[str, Any] = Field(default_factory=dict)
    current_price: float = 0.0
    
    # Analyst results
    technical_analysis: Optional[AnalystResult] = None
    sentiment_analysis: Optional[AnalystResult] = None
    tokenomics_analysis: Optional[AnalystResult] = None
    
    # Research synthesis
    research_synthesis: Optional[Dict[str, Any]] = None
    average_confidence: float = 0.0
    
    # RAG context (historical similar situations)
    similar_analyses: List[Dict[str, Any]] = Field(default_factory=list)
    similar_trades: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Trade proposal
    trade_proposal: Optional[Dict[str, Any]] = None
    
    # Risk validation
    risk_validation: Optional[Dict[str, Any]] = None
    
    # Final decision
    final_decision: Optional[Dict[str, Any]] = None
    
    # Execution result
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None
    
    # Human approval (for high-risk trades)
    requires_human_approval: bool = False
    human_approved: Optional[bool] = None
    human_feedback: Optional[str] = None
    
    # Workflow metadata
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    step_times: Dict[str, float] = Field(default_factory=dict)
    total_cost: float = 0.0
    total_tokens: int = 0
    
    # Conditional routing decisions
    confidence_gate_passed: bool = False
    skip_low_confidence: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class GraphConfig(BaseModel):
    """Configuration for the trading graph."""
    
    # Confidence thresholds
    min_confidence_to_trade: int = 60
    min_confidence_for_execution: int = 70
    
    # RAG settings
    enable_rag: bool = True
    rag_retrieval_k: int = 5
    
    # Human approval thresholds
    require_approval_above_risk: int = 8
    require_approval_above_position_pct: float = 0.15
    
    # Parallel execution
    run_analysts_parallel: bool = True
    
    # Retry settings
    max_retries_per_agent: int = 2
    
    # Routing logic
    skip_tokenomics_for_btc: bool = True  # BTC fundamentals are well-known
    skip_sentiment_low_volume: bool = True
    
    class Config:
        arbitrary_types_allowed = True


def create_initial_state(
    symbol: str,
    timeframe: str = "1h",
    mode: str = "live",
    run_id: Optional[str] = None,
) -> TradingState:
    """
    Create initial state for the workflow.
    
    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        mode: Trading mode
        run_id: Run ID for tracking
        
    Returns:
        Initial TradingState
    """
    if run_id is None:
        run_id = f"run_{datetime.utcnow().isoformat()}"
    
    return TradingState(
        symbol=symbol,
        timeframe=timeframe,
        run_id=run_id,
        mode=mode,
    )
