"""
Tests for Rule-Based Decision Engine
"""
import pytest
from unittest.mock import Mock
from datetime import datetime

from app.engines.rule_engine import RuleEngine
from app.models.decisions import DecisionResult


class TestRuleEngine:
    """Test suite for RuleEngine."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data with indicators."""
        return {
            "current_price": 50000.0,
            "timeframe": "1h",
            "indicators": {
                "rsi_14": 28.5,  # Oversold
                "macd": 150.0,
                "macd_signal": 100.0,  # Bullish crossover
                "macd_histogram": 50.0,
                "ema_9": 49500.0,
                "ema_21": 49000.0,
                "ema_50": 48000.0,
                "bb_upper": 51000.0,
                "bb_lower": 49000.0,
                "bb_middle": 50000.0,
                "current_volume": 3000.0,
                "volume_ma": 2000.0,  # Volume surge: 1.5x
            }
        }
    
    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data."""
        return {
            "cash_balance": 10000.0,
            "total_equity": 15000.0,
            "positions": [
                {"symbol": "BTCUSDT", "quantity": 0.1, "avg_entry_price": 50000.0}
            ]
        }
    
    def test_engine_initialization_rsi_macd(self, db_session):
        """Test RSI+MACD engine initialization."""
        engine = RuleEngine(db_session, strategy="rsi_macd")
        assert engine.engine_type == "rule"
        assert engine.strategy == "rsi_macd"
        assert "RSI + MACD" in engine.engine_name
    
    def test_engine_initialization_ema_crossover(self, db_session):
        """Test EMA Crossover engine initialization."""
        engine = RuleEngine(db_session, strategy="ema_crossover")
        assert engine.strategy == "ema_crossover"
        assert "EMA Crossover" in engine.engine_name
    
    def test_engine_initialization_bb_volume(self, db_session):
        """Test BB+Volume engine initialization."""
        engine = RuleEngine(db_session, strategy="bb_volume")
        assert engine.strategy == "bb_volume"
        assert "Bollinger Bands" in engine.engine_name
    
    def test_engine_initialization_invalid_strategy(self, db_session):
        """Test that invalid strategy raises error."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            RuleEngine(db_session, strategy="invalid_strategy")
    
    def test_rsi_macd_buy_signal(self, db_session, sample_market_data, sample_portfolio_data):
        """Test RSI+MACD strategy generates BUY signal."""
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_1"
        )
        
        assert isinstance(result, DecisionResult)
        assert result.decision.action == "BUY"
        assert result.decision.quantity > 0
        assert result.decision.confidence > 0.7
        assert "oversold" in result.decision.reasoning.lower()
        assert result.metadata.engine_type == "rule"
        assert result.metadata.strategy_name == "rsi_macd"
        assert result.metadata.cost == 0.0
        assert result.metadata.tokens_used == 0
        assert result.signals is not None
        assert "rsi" in result.signals
        assert "macd" in result.signals
    
    def test_rsi_macd_sell_signal(self, db_session, sample_market_data, sample_portfolio_data):
        """Test RSI+MACD strategy generates SELL signal."""
        # Modify indicators for SELL signal
        sample_market_data["indicators"]["rsi_14"] = 75.0  # Overbought
        sample_market_data["indicators"]["macd"] = 100.0
        sample_market_data["indicators"]["macd_signal"] = 150.0  # Bearish crossover
        
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_2"
        )
        
        assert result.decision.action == "SELL"
        assert result.decision.quantity > 0
        assert "overbought" in result.decision.reasoning.lower()
    
    def test_rsi_macd_hold_signal(self, db_session, sample_market_data, sample_portfolio_data):
        """Test RSI+MACD strategy generates HOLD signal."""
        # Modify indicators for no clear signal
        sample_market_data["indicators"]["rsi_14"] = 50.0  # Neutral
        sample_market_data["indicators"]["macd"] = 100.0
        sample_market_data["indicators"]["macd_signal"] = 100.0  # No crossover
        
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_3"
        )
        
        assert result.decision.action == "HOLD"
        assert result.decision.quantity == 0
    
    def test_ema_crossover_buy_signal(self, db_session, sample_market_data, sample_portfolio_data):
        """Test EMA Crossover strategy generates BUY signal."""
        # Set up golden cross: fast > slow, price > trend
        sample_market_data["current_price"] = 50000.0
        sample_market_data["indicators"]["ema_9"] = 49800.0
        sample_market_data["indicators"]["ema_21"] = 49500.0
        sample_market_data["indicators"]["ema_50"] = 48000.0
        
        engine = RuleEngine(db_session, strategy="ema_crossover")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_4"
        )
        
        assert result.decision.action == "BUY"
        assert "Golden cross" in result.decision.reasoning or "cross" in result.decision.reasoning.lower()
        assert result.signals is not None
        assert "ema_fast" in result.signals
    
    def test_ema_crossover_sell_signal(self, db_session, sample_market_data, sample_portfolio_data):
        """Test EMA Crossover strategy generates SELL signal."""
        # Set up death cross: fast < slow, price < trend
        sample_market_data["current_price"] = 48000.0
        sample_market_data["indicators"]["ema_9"] = 48500.0
        sample_market_data["indicators"]["ema_21"] = 49000.0
        sample_market_data["indicators"]["ema_50"] = 50000.0
        
        engine = RuleEngine(db_session, strategy="ema_crossover")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_5"
        )
        
        assert result.decision.action == "SELL"
        assert "Death cross" in result.decision.reasoning or "cross" in result.decision.reasoning.lower()
    
    def test_bb_volume_buy_signal(self, db_session, sample_market_data, sample_portfolio_data):
        """Test BB+Volume strategy generates BUY signal."""
        # Price at lower band with volume surge
        sample_market_data["current_price"] = 49000.0
        sample_market_data["indicators"]["bb_lower"] = 49000.0
        sample_market_data["indicators"]["bb_upper"] = 51000.0
        sample_market_data["indicators"]["bb_middle"] = 50000.0
        sample_market_data["indicators"]["current_volume"] = 3000.0
        sample_market_data["indicators"]["volume_ma"] = 2000.0  # 1.5x surge
        
        engine = RuleEngine(db_session, strategy="bb_volume")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_6"
        )
        
        assert result.decision.action == "BUY"
        assert "lower BB" in result.decision.reasoning or "volume surge" in result.decision.reasoning
        assert result.signals is not None
        assert "bb_position" in result.signals
        assert "volume_ratio" in result.signals
    
    def test_bb_volume_sell_signal(self, db_session, sample_market_data, sample_portfolio_data):
        """Test BB+Volume strategy generates SELL signal."""
        # Price at upper band with volume surge
        sample_market_data["current_price"] = 51000.0
        sample_market_data["indicators"]["bb_upper"] = 51000.0
        sample_market_data["indicators"]["bb_lower"] = 49000.0
        sample_market_data["indicators"]["bb_middle"] = 50000.0
        sample_market_data["indicators"]["current_volume"] = 3000.0
        sample_market_data["indicators"]["volume_ma"] = 2000.0
        
        engine = RuleEngine(db_session, strategy="bb_volume")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_7"
        )
        
        assert result.decision.action == "SELL"
        assert "upper BB" in result.decision.reasoning or "volume surge" in result.decision.reasoning
    
    @pytest.mark.asyncio
    async def test_async_analyze(self, db_session, sample_market_data, sample_portfolio_data):
        """Test asynchronous analysis works."""
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = await engine.aanalyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_run_async"
        )
        
        assert isinstance(result, DecisionResult)
        assert result.decision.action in ["BUY", "SELL", "HOLD"]
    
    def test_get_capabilities(self, db_session):
        """Test engine capabilities reporting."""
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        capabilities = engine.get_capabilities()
        
        assert capabilities["engine_type"] == "rule"
        assert capabilities["supports_signals"] is True
        assert capabilities["cost_per_decision"] == 0.0
        assert capabilities["avg_latency_ms"] < 100  # Should be very fast
        assert "rsi_macd" in capabilities["available_strategies"]
        assert "parameters" in capabilities
    
    def test_execution_speed(self, db_session, sample_market_data, sample_portfolio_data):
        """Test that rule engine executes quickly."""
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_speed"
        )
        
        # Should complete in under 100ms
        assert result.metadata.execution_time_ms < 100
    
    def test_quantity_calculation_respects_max_position(self, db_session, sample_market_data, sample_portfolio_data):
        """Test that quantity calculation respects max position size."""
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_quantity"
        )
        
        if result.decision.action == "BUY":
            # Calculate max allowed position value
            max_position_value = sample_portfolio_data["total_equity"] * 0.10  # 10% max
            actual_position_value = result.decision.quantity * sample_market_data["current_price"]
            
            # Should not exceed max position size
            assert actual_position_value <= max_position_value * 1.01  # Allow 1% tolerance
    
    def test_zero_price_handling(self, db_session, sample_market_data, sample_portfolio_data):
        """Test that engine handles zero price gracefully."""
        sample_market_data["current_price"] = 0.0
        
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_zero_price"
        )
        
        # Should return HOLD with zero quantity, not crash
        assert result.decision.quantity == 0
    
    def test_missing_indicators_handling(self, db_session, sample_portfolio_data):
        """Test engine handles missing indicators gracefully."""
        # Market data with missing indicators
        incomplete_market_data = {
            "current_price": 50000.0,
            "indicators": {}  # Empty indicators
        }
        
        engine = RuleEngine(db_session, strategy="rsi_macd")
        
        result = engine.analyze(
            symbol="BTCUSDT",
            market_data=incomplete_market_data,
            portfolio_data=sample_portfolio_data,
            run_id="test_missing_indicators"
        )
        
        # Should not crash, defaults to HOLD
        assert isinstance(result, DecisionResult)
        assert result.status == "completed"
