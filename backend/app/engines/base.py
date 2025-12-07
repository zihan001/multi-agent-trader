"""
Base Decision Engine

Abstract base class defining the contract for all decision engines.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.decisions import DecisionResult


class BaseDecisionEngine(ABC):
    """
    Abstract base class for all trading decision engines.
    
    All engines (LLM-based, rule-based, hybrid, ML-based) must implement this interface.
    This ensures consistent behavior and allows transparent mode-switching.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the decision engine.
        
        Args:
            db: Database session for logging and data access
        """
        self.db = db
    
    @abstractmethod
    def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: str,
    ) -> DecisionResult:
        """
        Analyze market conditions and generate a trading decision.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            market_data: Market data context containing:
                - current_price: Current asset price
                - candles: Historical OHLCV data
                - indicators: Calculated technical indicators
                - timeframe: Data timeframe (e.g., "1h")
                - sentiment_data: Optional sentiment information
                - token_data: Optional tokenomics data
            portfolio_data: Portfolio state containing:
                - cash_balance: Available cash
                - total_equity: Total portfolio value
                - positions: List of open positions
                - trades: Historical trades
            run_id: Unique identifier for this analysis run
            
        Returns:
            DecisionResult with trading decision and supporting data
        """
        pass
    
    @abstractmethod
    async def aanalyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: str,
    ) -> DecisionResult:
        """
        Asynchronous version of analyze().
        
        Args:
            Same as analyze()
            
        Returns:
            DecisionResult with trading decision and supporting data
        """
        pass
    
    @property
    @abstractmethod
    def engine_type(self) -> str:
        """
        Return the engine type identifier.
        
        Returns:
            Engine type string (e.g., "llm", "rule", "hybrid", "ml")
        """
        pass
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """
        Return a human-readable engine name.
        
        Returns:
            Engine name string (e.g., "LLM Multi-Agent System", "RSI+MACD Rule Engine")
        """
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return engine capabilities and configuration.
        
        Returns:
            Dictionary with engine information:
                - engine_type: Type identifier
                - engine_name: Human-readable name
                - supports_reasoning: Whether engine provides human-readable reasoning
                - supports_signals: Whether engine provides technical signals
                - cost_per_decision: Approximate cost per decision (USD)
                - avg_latency_ms: Average decision latency
                - strategies: Available strategies (for rule-based engines)
        """
        return {
            "engine_type": self.engine_type,
            "engine_name": self.engine_name,
            "supports_reasoning": False,
            "supports_signals": False,
            "cost_per_decision": 0.0,
            "avg_latency_ms": 0.0,
        }
