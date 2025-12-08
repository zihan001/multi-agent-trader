"""
Unified Decision Models

These models provide a consistent interface for decision outputs
across different engine types (LLM, rule-based, hybrid, etc.).
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SignalData(BaseModel):
    """Individual signal or indicator value."""
    name: str
    value: float
    threshold: Optional[float] = None
    status: Optional[str] = None  # "bullish", "bearish", "neutral"


class TradingDecision(BaseModel):
    """The actual trading action recommended."""
    action: str = Field(..., description="BUY, SELL, or HOLD")
    quantity: float = Field(default=0.0, description="Amount to trade")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(default="", description="Human-readable explanation")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price level")
    take_profit: Optional[float] = Field(default=None, description="Take profit price level")
    position_size_pct: Optional[float] = Field(default=None, description="Position size as percentage of portfolio (0-1)")
    time_horizon: Optional[str] = Field(default=None, description="Expected holding period (e.g., '1h', '4h', '1d')")
    strategy: Optional[str] = Field(default=None, description="Strategy name for rule-based engines")


class DecisionMetadata(BaseModel):
    """Metadata about the decision-making process."""
    engine_type: str = Field(..., description="llm, rule, hybrid, etc.")
    strategy_name: Optional[str] = None
    execution_time_ms: float = Field(default=0.0, description="Time taken to generate decision")
    cost: float = Field(default=0.0, description="Cost in USD (0 for non-LLM engines)")
    tokens_used: int = Field(default=0, description="Total tokens (0 for non-LLM engines)")
    model_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentOutput(BaseModel):
    """Output from a single agent (for LLM mode)."""
    agent_name: str
    analysis: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionResult(BaseModel):
    """
    Unified decision result structure.
    
    Works for both LLM-based (with agent reasoning) and rule-based (with signals) engines.
    """
    # Core identification
    run_id: str
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Decision output
    decision: TradingDecision
    
    # Metadata about how the decision was made
    metadata: DecisionMetadata
    
    # Mode-specific data (optional)
    agents: Optional[Dict[str, AgentOutput]] = Field(
        default=None,
        description="Agent outputs for LLM mode"
    )
    signals: Optional[Dict[str, SignalData]] = Field(
        default=None,
        description="Technical signals for rule-based mode"
    )
    
    # Status and errors
    status: str = Field(default="completed", description="completed, failed, partial")
    errors: List[Dict[str, str]] = Field(default_factory=list)
    
    # Backwards compatibility properties for frontend
    @property
    def technical_analysis(self) -> Optional[Dict[str, Any]]:
        """Extract technical analysis from agents."""
        if self.agents and "technical" in self.agents:
            return self.agents["technical"].analysis
        return None
    
    @property
    def sentiment_analysis(self) -> Optional[Dict[str, Any]]:
        """Extract sentiment analysis from agents."""
        if self.agents and "sentiment" in self.agents:
            return self.agents["sentiment"].analysis
        return None
    
    @property
    def risk_analysis(self) -> Optional[Dict[str, Any]]:
        """Extract risk analysis from agents."""
        if self.agents and "risk" in self.agents:
            return self.agents["risk"].analysis
        return None
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_2024-01-01T12:00:00",
                "symbol": "BTCUSDT",
                "decision": {
                    "action": "BUY",
                    "quantity": 0.05,
                    "confidence": 0.75,
                    "reasoning": "RSI oversold + MACD bullish crossover",
                },
                "metadata": {
                    "engine_type": "rule",
                    "strategy_name": "rsi_macd",
                    "execution_time_ms": 45.2,
                    "cost": 0.0,
                    "tokens_used": 0,
                },
                "signals": {
                    "rsi": {"name": "RSI", "value": 28.5, "threshold": 30, "status": "oversold"},
                    "macd": {"name": "MACD", "value": 0.015, "status": "bullish"},
                }
            }
        }


class AnalysisRequest(BaseModel):
    """Request to run trading analysis."""
    symbol: str
    mode: str = Field(default="live", description="live or backtest_step")
    timestamp: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint."""
    result: DecisionResult
    portfolio_updated: bool = Field(default=False)
    recommendation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Stored recommendation (not auto-executed)"
    )
