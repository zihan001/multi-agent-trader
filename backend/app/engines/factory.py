"""
Decision Engine Factory

Factory pattern for creating decision engines based on configuration.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.engines.base import BaseDecisionEngine
from app.engines.llm_engine import LLMDecisionEngine
from app.engines.rule_engine import RuleEngine
from app.core.config import settings
from app.agents.llm_client import LLMClient


class DecisionEngineFactory:
    """
    Factory for creating decision engines.
    
    Instantiates the appropriate engine based on settings.trading_mode.
    """
    
    @staticmethod
    def create(
        db: Session,
        trading_mode: Optional[str] = None,
        llm_client: Optional[LLMClient] = None
    ) -> BaseDecisionEngine:
        """
        Create a decision engine based on configuration.
        
        Args:
            db: Database session
            trading_mode: Override trading mode (defaults to settings.trading_mode)
            llm_client: Optional LLM client for LLM mode
            
        Returns:
            BaseDecisionEngine instance
            
        Raises:
            ValueError: If trading_mode is invalid
        """
        mode = trading_mode or settings.trading_mode
        
        if mode == "llm":
            return LLMDecisionEngine(db=db, llm_client=llm_client)
        elif mode == "rule":
            return RuleEngine(db=db, strategy=settings.rule_strategy)
        else:
            raise ValueError(
                f"Invalid trading_mode '{mode}'. Must be 'llm' or 'rule'."
            )
    
    @staticmethod
    def get_available_engines() -> dict:
        """
        Get information about all available engines.
        
        Returns:
            Dictionary with engine information
        """
        return {
            "llm": {
                "name": "LLM Multi-Agent System",
                "description": "Six specialized LLM agents with natural language reasoning",
                "supports_reasoning": True,
                "supports_signals": False,
                "cost_per_decision": 0.02,
                "avg_latency_ms": 15000.0,
                "agents": [
                    "Technical Analyst",
                    "Sentiment Analyst",
                    "Tokenomics Analyst",
                    "Researcher",
                    "Trader",
                    "Risk Manager"
                ]
            },
            "rule": {
                "name": "Rule-Based Engine",
                "description": "Deterministic technical indicator strategies",
                "supports_reasoning": True,
                "supports_signals": True,
                "cost_per_decision": 0.0,
                "avg_latency_ms": 50.0,
                "strategies": {
                    "rsi_macd": "RSI + MACD Momentum Strategy",
                    "ema_crossover": "EMA Crossover Trend Strategy",
                    "bb_volume": "Bollinger Bands + Volume Strategy"
                }
            }
        }
    
    @staticmethod
    def get_current_engine_info() -> dict:
        """
        Get information about the currently configured engine.
        
        Returns:
            Dictionary with current engine information
        """
        all_engines = DecisionEngineFactory.get_available_engines()
        current_mode = settings.trading_mode
        
        if current_mode not in all_engines:
            return {
                "error": f"Invalid trading_mode: {current_mode}",
                "valid_modes": list(all_engines.keys())
            }
        
        engine_info = all_engines[current_mode].copy()
        engine_info["mode"] = current_mode
        
        if current_mode == "rule":
            engine_info["active_strategy"] = settings.rule_strategy
        elif current_mode == "llm":
            engine_info["models"] = {
                "cheap": settings.cheap_model,
                "strong": settings.strong_model
            }
            engine_info["daily_token_budget"] = settings.daily_token_budget
        
        return engine_info
