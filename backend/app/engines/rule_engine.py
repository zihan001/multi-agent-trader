"""
Rule-Based Decision Engine

Deterministic trading engine based on technical indicators.
Zero LLM costs, instant execution.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.engines.base import BaseDecisionEngine
from app.models.decisions import (
    DecisionResult,
    TradingDecision,
    DecisionMetadata,
    SignalData
)
from app.core.config import settings


class RuleEngine(BaseDecisionEngine):
    """
    Rule-based decision engine using technical indicators.
    
    Implements three strategies:
    1. RSI + MACD: Combined momentum strategy
    2. EMA Crossover: Trend-following strategy
    3. Bollinger Bands + Volume: Mean reversion with volume confirmation
    
    All strategies are deterministic with zero LLM costs.
    """
    
    def __init__(self, db: Session, strategy: str = None):
        """
        Initialize the rule engine.
        
        Args:
            db: Database session
            strategy: Strategy name (defaults to settings.rule_strategy)
        """
        super().__init__(db)
        self.strategy = strategy or settings.rule_strategy
        
        # Validate strategy
        valid_strategies = ["rsi_macd", "ema_crossover", "bb_volume"]
        if self.strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy '{self.strategy}'. Must be one of: {valid_strategies}")
    
    def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: str,
    ) -> DecisionResult:
        """
        Analyze market conditions using rule-based strategy.
        
        Args:
            symbol: Trading pair symbol
            market_data: Market data context
            portfolio_data: Portfolio state
            run_id: Unique identifier for this analysis run
            
        Returns:
            DecisionResult with technical signals and trading decision
        """
        start_time = time.time()
        
        # Get indicators from market data
        indicators = market_data.get("indicators", {})
        current_price = market_data.get("current_price", 0)
        
        # Execute strategy
        if self.strategy == "rsi_macd":
            decision, signals = self._rsi_macd_strategy(indicators, current_price, portfolio_data)
        elif self.strategy == "ema_crossover":
            decision, signals = self._ema_crossover_strategy(indicators, current_price, portfolio_data)
        elif self.strategy == "bb_volume":
            decision, signals = self._bb_volume_strategy(indicators, current_price, portfolio_data)
        else:
            # Fallback to HOLD
            decision = TradingDecision(
                action="HOLD",
                quantity=0.0,
                confidence=0.0,
                reasoning="Unknown strategy"
            )
            signals = {}
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Create metadata
        metadata = DecisionMetadata(
            engine_type="rule",
            strategy_name=self.strategy,
            execution_time_ms=execution_time_ms,
            cost=0.0,  # Zero cost for rule-based
            tokens_used=0,  # No LLM tokens
            model_name=None,
            timestamp=datetime.utcnow()
        )
        
        # Create unified result
        return DecisionResult(
            run_id=run_id,
            symbol=symbol,
            timestamp=datetime.utcnow(),
            decision=decision,
            metadata=metadata,
            agents=None,  # Rule mode doesn't use agents
            signals=signals,
            status="completed",
            errors=[]
        )
    
    async def aanalyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: str,
    ) -> DecisionResult:
        """
        Asynchronous analysis (same as sync for rule-based engine).
        
        Rule-based decisions are so fast that async doesn't provide benefit,
        but we implement it for interface consistency.
        """
        return self.analyze(symbol, market_data, portfolio_data, run_id)
    
    def _rsi_macd_strategy(
        self,
        indicators: Dict[str, Any],
        current_price: float,
        portfolio_data: Dict[str, Any]
    ) -> tuple[TradingDecision, Dict[str, SignalData]]:
        """
        RSI + MACD strategy.
        
        BUY when:
        - RSI < oversold threshold (default 30) AND
        - MACD > MACD Signal (bullish crossover)
        
        SELL when:
        - RSI > overbought threshold (default 70) AND
        - MACD < MACD Signal (bearish crossover)
        
        Returns:
            Tuple of (TradingDecision, signals dict)
        """
        rsi = indicators.get("rsi_14", 50)
        macd = indicators.get("macd", 0)
        macd_signal = indicators.get("macd_signal", 0)
        macd_hist = indicators.get("macd_histogram", 0)
        
        # Collect signals
        signals = {
            "rsi": SignalData(
                name="RSI",
                value=rsi,
                threshold=settings.rsi_oversold if rsi < 50 else settings.rsi_overbought,
                status="oversold" if rsi < settings.rsi_oversold else "overbought" if rsi > settings.rsi_overbought else "neutral"
            ),
            "macd": SignalData(
                name="MACD",
                value=macd,
                threshold=macd_signal,
                status="bullish" if macd > macd_signal else "bearish" if macd < macd_signal else "neutral"
            ),
            "macd_histogram": SignalData(
                name="MACD Histogram",
                value=macd_hist,
                threshold=0,
                status="positive" if macd_hist > 0 else "negative"
            )
        }
        
        # Determine action
        action = "HOLD"
        reasoning = ""
        confidence = 0.5
        
        if rsi < settings.rsi_oversold and macd > macd_signal:
            action = "BUY"
            reasoning = f"RSI oversold ({rsi:.1f} < {settings.rsi_oversold}) + MACD bullish crossover"
            confidence = 0.75 + (settings.rsi_oversold - rsi) / 100  # Higher confidence when more oversold
            confidence = min(confidence, 0.95)  # Cap at 95%
        elif rsi > settings.rsi_overbought and macd < macd_signal:
            action = "SELL"
            reasoning = f"RSI overbought ({rsi:.1f} > {settings.rsi_overbought}) + MACD bearish crossover"
            confidence = 0.75 + (rsi - settings.rsi_overbought) / 100
            confidence = min(confidence, 0.95)
        else:
            reasoning = f"No clear signal (RSI: {rsi:.1f}, MACD {'>' if macd > macd_signal else '<'} Signal)"
        
        # Calculate quantity
        quantity = self._calculate_quantity(action, current_price, portfolio_data, confidence)
        
        decision = TradingDecision(
            action=action,
            quantity=quantity,
            confidence=confidence,
            reasoning=reasoning
        )
        
        return decision, signals
    
    def _ema_crossover_strategy(
        self,
        indicators: Dict[str, Any],
        current_price: float,
        portfolio_data: Dict[str, Any]
    ) -> tuple[TradingDecision, Dict[str, SignalData]]:
        """
        EMA Crossover strategy.
        
        BUY when:
        - Fast EMA crosses above Slow EMA (golden cross) AND
        - Price is above Trend EMA (confirming uptrend)
        
        SELL when:
        - Fast EMA crosses below Slow EMA (death cross) AND
        - Price is below Trend EMA (confirming downtrend)
        
        Returns:
            Tuple of (TradingDecision, signals dict)
        """
        ema_fast = indicators.get(f"ema_{settings.ema_fast}", current_price)
        ema_slow = indicators.get(f"ema_{settings.ema_slow}", current_price)
        ema_trend = indicators.get(f"ema_{settings.ema_trend}", current_price)
        
        # Collect signals
        signals = {
            "ema_fast": SignalData(
                name=f"EMA {settings.ema_fast}",
                value=ema_fast,
                threshold=ema_slow,
                status="above" if ema_fast > ema_slow else "below"
            ),
            "ema_slow": SignalData(
                name=f"EMA {settings.ema_slow}",
                value=ema_slow,
                threshold=ema_trend,
                status="above" if ema_slow > ema_trend else "below"
            ),
            "price_vs_trend": SignalData(
                name="Price vs Trend EMA",
                value=current_price,
                threshold=ema_trend,
                status="bullish" if current_price > ema_trend else "bearish"
            )
        }
        
        # Determine action
        action = "HOLD"
        reasoning = ""
        confidence = 0.5
        
        if ema_fast > ema_slow and current_price > ema_trend:
            action = "BUY"
            crossover_strength = (ema_fast - ema_slow) / ema_slow * 100
            reasoning = f"Golden cross: EMA{settings.ema_fast} > EMA{settings.ema_slow} + price > trend EMA"
            confidence = 0.7 + min(abs(crossover_strength), 5) / 10  # Higher confidence with stronger crossover
        elif ema_fast < ema_slow and current_price < ema_trend:
            action = "SELL"
            crossover_strength = (ema_slow - ema_fast) / ema_fast * 100
            reasoning = f"Death cross: EMA{settings.ema_fast} < EMA{settings.ema_slow} + price < trend EMA"
            confidence = 0.7 + min(abs(crossover_strength), 5) / 10
        else:
            reasoning = f"No clear crossover signal (Fast EMA {'>' if ema_fast > ema_slow else '<'} Slow EMA)"
        
        # Calculate quantity
        quantity = self._calculate_quantity(action, current_price, portfolio_data, confidence)
        
        decision = TradingDecision(
            action=action,
            quantity=quantity,
            confidence=confidence,
            reasoning=reasoning
        )
        
        return decision, signals
    
    def _bb_volume_strategy(
        self,
        indicators: Dict[str, Any],
        current_price: float,
        portfolio_data: Dict[str, Any]
    ) -> tuple[TradingDecision, Dict[str, SignalData]]:
        """
        Bollinger Bands + Volume strategy.
        
        BUY when:
        - Price touches or breaks below lower Bollinger Band AND
        - Volume is above average (volume surge)
        
        SELL when:
        - Price touches or breaks above upper Bollinger Band AND
        - Volume is above average (volume surge)
        
        Returns:
            Tuple of (TradingDecision, signals dict)
        """
        bb_upper = indicators.get("bb_upper", current_price * 1.02)
        bb_lower = indicators.get("bb_lower", current_price * 0.98)
        bb_middle = indicators.get("bb_middle", current_price)
        current_volume = indicators.get("current_volume", 0)
        avg_volume = indicators.get("volume_ma", 1)
        
        # Avoid division by zero
        if avg_volume == 0:
            avg_volume = 1
        
        volume_ratio = current_volume / avg_volume
        
        # Collect signals
        signals = {
            "bb_position": SignalData(
                name="Bollinger Band Position",
                value=current_price,
                threshold=bb_middle,
                status="below_lower" if current_price <= bb_lower else "above_upper" if current_price >= bb_upper else "middle"
            ),
            "bb_upper": SignalData(
                name="BB Upper",
                value=bb_upper,
                threshold=current_price,
                status="resistance"
            ),
            "bb_lower": SignalData(
                name="BB Lower",
                value=bb_lower,
                threshold=current_price,
                status="support"
            ),
            "volume_ratio": SignalData(
                name="Volume Ratio",
                value=volume_ratio,
                threshold=settings.volume_surge_threshold,
                status="surge" if volume_ratio >= settings.volume_surge_threshold else "normal"
            )
        }
        
        # Determine action
        action = "HOLD"
        reasoning = ""
        confidence = 0.5
        
        if current_price <= bb_lower and volume_ratio >= settings.volume_surge_threshold:
            action = "BUY"
            distance_pct = (bb_lower - current_price) / bb_lower * 100
            reasoning = f"Price at lower BB ({distance_pct:.1f}% below) + volume surge ({volume_ratio:.1f}x)"
            confidence = 0.7 + min(distance_pct, 3) / 10  # Higher confidence with more oversold
        elif current_price >= bb_upper and volume_ratio >= settings.volume_surge_threshold:
            action = "SELL"
            distance_pct = (current_price - bb_upper) / bb_upper * 100
            reasoning = f"Price at upper BB ({distance_pct:.1f}% above) + volume surge ({volume_ratio:.1f}x)"
            confidence = 0.7 + min(distance_pct, 3) / 10
        else:
            reasoning = f"No BB breakout signal (Price: {((current_price - bb_middle) / bb_middle * 100):.1f}% from middle)"
        
        # Calculate quantity
        quantity = self._calculate_quantity(action, current_price, portfolio_data, confidence)
        
        decision = TradingDecision(
            action=action,
            quantity=quantity,
            confidence=confidence,
            reasoning=reasoning
        )
        
        return decision, signals
    
    def _calculate_quantity(
        self,
        action: str,
        current_price: float,
        portfolio_data: Dict[str, Any],
        confidence: float
    ) -> float:
        """
        Calculate trade quantity based on action, portfolio state, and confidence.
        
        Args:
            action: Trading action (BUY/SELL/HOLD)
            current_price: Current asset price
            portfolio_data: Portfolio state
            confidence: Strategy confidence (0-1)
            
        Returns:
            Quantity to trade
        """
        if action == "HOLD" or current_price == 0:
            return 0.0
        
        # Get portfolio info
        cash_balance = portfolio_data.get("cash_balance", 0)
        total_equity = portfolio_data.get("total_equity", cash_balance)
        positions = portfolio_data.get("positions", [])
        
        if action == "BUY":
            # Calculate position size based on confidence and max position size
            max_position_value = total_equity * settings.max_position_size_pct
            confidence_adjusted_value = max_position_value * confidence
            
            # Don't exceed available cash
            position_value = min(confidence_adjusted_value, cash_balance * 0.95)  # Keep 5% cash buffer
            
            if position_value > 0:
                quantity = position_value / current_price
                return round(quantity, 8)  # Round to 8 decimals for crypto
            return 0.0
        
        elif action == "SELL":
            # Find current position for this symbol
            # Note: In actual implementation, symbol should be passed or available
            # For now, we'll sell a percentage of the position based on confidence
            
            # Simplified: Assume selling entire position if confidence is high
            # In production, this should be more sophisticated
            if positions:
                # Get largest position (simplified)
                largest_position = max(positions, key=lambda x: x.get("quantity", 0))
                position_quantity = largest_position.get("quantity", 0)
                
                # Sell proportion based on confidence
                quantity = position_quantity * confidence
                return round(quantity, 8)
            return 0.0
        
        return 0.0
    
    @property
    def engine_type(self) -> str:
        """Return engine type identifier."""
        return "rule"
    
    @property
    def engine_name(self) -> str:
        """Return human-readable engine name."""
        strategy_names = {
            "rsi_macd": "RSI + MACD Momentum Strategy",
            "ema_crossover": "EMA Crossover Trend Strategy",
            "bb_volume": "Bollinger Bands + Volume Strategy"
        }
        return strategy_names.get(self.strategy, f"Rule-Based Strategy: {self.strategy}")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return engine capabilities."""
        return {
            "engine_type": self.engine_type,
            "engine_name": self.engine_name,
            "supports_reasoning": True,  # Provides reasoning, just not LLM-style
            "supports_signals": True,
            "cost_per_decision": 0.0,
            "avg_latency_ms": 50.0,  # ~50ms typical
            "strategy": self.strategy,
            "available_strategies": ["rsi_macd", "ema_crossover", "bb_volume"],
            "parameters": self._get_strategy_parameters()
        }
    
    def _get_strategy_parameters(self) -> Dict[str, Any]:
        """Return current strategy parameters."""
        if self.strategy == "rsi_macd":
            return {
                "rsi_period": settings.rsi_period,
                "rsi_oversold": settings.rsi_oversold,
                "rsi_overbought": settings.rsi_overbought,
                "macd_fast": settings.macd_fast,
                "macd_slow": settings.macd_slow,
                "macd_signal": settings.macd_signal,
            }
        elif self.strategy == "ema_crossover":
            return {
                "ema_fast": settings.ema_fast,
                "ema_slow": settings.ema_slow,
                "ema_trend": settings.ema_trend,
            }
        elif self.strategy == "bb_volume":
            return {
                "bb_period": settings.bb_period,
                "bb_std": settings.bb_std,
                "volume_ma_period": settings.volume_ma_period,
                "volume_surge_threshold": settings.volume_surge_threshold,
            }
        return {}
