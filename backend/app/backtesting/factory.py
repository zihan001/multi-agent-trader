"""
Factory for creating backtest engines.
"""
from typing import Optional, Dict, Any
from app.core.config import settings


class BacktestEngineFactory:
    """Factory for instantiating backtest engines."""
    
    @staticmethod
    def create(db, engine_type: Optional[str] = None, strategy: Optional[str] = None):
        """
        Create a backtest engine instance.
        
        Args:
            db: Database session
            engine_type: "llm" or "vectorbt" (defaults to settings.trading_mode)
            strategy: Strategy name for rule-based engines
            
        Returns:
            BaseBacktestEngine instance
        """
        from app.backtesting.llm_engine import LLMBacktestEngine
        from app.backtesting.vectorbt_engine import VectorBTEngine
        
        mode = engine_type or settings.trading_mode
        
        if mode == "llm":
            return LLMBacktestEngine(db)
        elif mode == "rule" or mode == "vectorbt":
            strat = strategy or settings.rule_strategy
            return VectorBTEngine(db, strategy=strat)
        else:
            raise ValueError(f"Unknown backtest engine type: {mode}")
    
    @staticmethod
    def get_available_engines() -> Dict[str, Any]:
        """
        Get information about all available backtest engines.
        
        Returns:
            Dict mapping engine names to capabilities
        """
        from app.backtesting.llm_engine import LLMBacktestEngine
        from app.backtesting.vectorbt_engine import VectorBTEngine, VECTORBT_AVAILABLE
        
        engines = {}
        
        # LLM engine (always available)
        temp_llm = LLMBacktestEngine(None)
        engines["llm"] = temp_llm.get_capabilities()
        
        # VectorBT engine (if installed)
        if VECTORBT_AVAILABLE:
            temp_vbt = VectorBTEngine(None, strategy="rsi_macd")
            engines["vectorbt"] = temp_vbt.get_capabilities()
        
        return engines
    
    @staticmethod
    def get_current_engine_info(db) -> Dict[str, Any]:
        """
        Get info about the currently configured backtest engine.
        
        Returns:
            Engine metadata dict
        """
        engine = BacktestEngineFactory.create(db)
        capabilities = engine.get_capabilities()
        
        return {
            "engine_type": engine.engine_type,
            "strategy": getattr(engine, 'strategy', None),
            "capabilities": capabilities
        }
