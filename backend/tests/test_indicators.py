"""
Tests for technical indicators service.
"""
import pytest
from datetime import datetime, timedelta
from app.models.database import Candle
from app.services.indicators import (
    candles_to_dataframe,
    calculate_rsi,
    calculate_macd,
    calculate_ema,
    calculate_all_indicators,
    assess_trend,
    assess_momentum,
    get_overbought_oversold_status
)


@pytest.fixture
def sample_candles():
    """Create sample candle data for testing."""
    candles = []
    base_price = 50000.0
    base_time = datetime(2025, 1, 1)
    
    # Create 100 candles with realistic price movement
    for i in range(100):
        # Simple trending price pattern
        price = base_price + (i * 10) + ((-1) ** i * 50)
        
        candle = Candle(
            id=i,
            symbol="BTCUSDT",
            timestamp=base_time + timedelta(hours=i),
            timeframe="1h",
            open=price,
            high=price + 50,
            low=price - 50,
            close=price + ((-1) ** i * 20),
            volume=100.0 + i
        )
        candles.append(candle)
    
    return candles


def test_candles_to_dataframe(sample_candles):
    """Test converting candles to DataFrame."""
    df = candles_to_dataframe(sample_candles)
    
    assert len(df) == 100
    assert 'open' in df.columns
    assert 'high' in df.columns
    assert 'low' in df.columns
    assert 'close' in df.columns
    assert 'volume' in df.columns


def test_calculate_rsi(sample_candles):
    """Test RSI calculation."""
    df = candles_to_dataframe(sample_candles)
    rsi = calculate_rsi(df, window=14)
    
    assert len(rsi) == 100
    # RSI should be between 0 and 100
    assert rsi.iloc[-1] >= 0
    assert rsi.iloc[-1] <= 100


def test_calculate_macd(sample_candles):
    """Test MACD calculation."""
    df = candles_to_dataframe(sample_candles)
    macd_data = calculate_macd(df)
    
    assert 'macd' in macd_data
    assert 'macd_signal' in macd_data
    assert 'macd_diff' in macd_data
    assert len(macd_data['macd']) == 100


def test_calculate_ema(sample_candles):
    """Test EMA calculation."""
    df = candles_to_dataframe(sample_candles)
    ema = calculate_ema(df, window=21)
    
    assert len(ema) == 100
    # EMA should be close to price range
    assert ema.iloc[-1] > 40000
    assert ema.iloc[-1] < 60000


def test_calculate_all_indicators(sample_candles):
    """Test calculating all indicators at once."""
    indicators = calculate_all_indicators(sample_candles)
    
    # Check all expected keys exist
    assert 'current_price' in indicators
    assert 'ema_9' in indicators
    assert 'ema_21' in indicators
    assert 'ema_50' in indicators
    assert 'rsi_14' in indicators
    assert 'macd' in indicators
    assert 'macd_signal' in indicators
    assert 'macd_diff' in indicators
    assert 'atr_14' in indicators
    assert 'volatility_20' in indicators
    assert 'bb_upper' in indicators
    assert 'bb_middle' in indicators
    assert 'bb_lower' in indicators
    assert 'stoch_k' in indicators
    assert 'stoch_d' in indicators
    assert 'obv' in indicators
    assert 'trend' in indicators
    assert 'momentum' in indicators
    
    # Check values are reasonable
    assert indicators['current_price'] > 0
    assert 0 <= indicators['rsi_14'] <= 100
    assert indicators['trend'] in ['uptrend', 'downtrend', 'sideways']
    assert indicators['momentum'] in ['strong', 'moderate', 'weak']


def test_assess_trend(sample_candles):
    """Test trend assessment."""
    df = candles_to_dataframe(sample_candles)
    trend = assess_trend(df)
    
    assert trend in ['uptrend', 'downtrend', 'sideways']


def test_assess_momentum(sample_candles):
    """Test momentum assessment."""
    df = candles_to_dataframe(sample_candles)
    momentum = assess_momentum(df)
    
    assert momentum in ['strong', 'moderate', 'weak']


def test_overbought_oversold_status():
    """Test overbought/oversold detection."""
    # Overbought
    status = get_overbought_oversold_status(rsi=75, stoch_k=85)
    assert status == "overbought"
    
    # Oversold
    status = get_overbought_oversold_status(rsi=25, stoch_k=15)
    assert status == "oversold"
    
    # Neutral
    status = get_overbought_oversold_status(rsi=50, stoch_k=50)
    assert status == "neutral"


def test_indicators_with_minimal_data():
    """Test that indicators handle minimal data gracefully."""
    # Create only 30 candles (less than ideal for 50-period indicators)
    candles = []
    base_price = 50000.0
    base_time = datetime(2025, 1, 1)
    
    for i in range(30):
        candle = Candle(
            id=i,
            symbol="BTCUSDT",
            timestamp=base_time + timedelta(hours=i),
            timeframe="1h",
            open=base_price,
            high=base_price + 100,
            low=base_price - 100,
            close=base_price,
            volume=100.0
        )
        candles.append(candle)
    
    indicators = calculate_all_indicators(candles)
    
    # Should still return a result (some values may be None)
    assert 'current_price' in indicators
    assert indicators['current_price'] == base_price


def test_bollinger_bands_width(sample_candles):
    """Test that Bollinger Bands width is positive."""
    indicators = calculate_all_indicators(sample_candles)
    
    assert indicators['bb_upper'] > indicators['bb_middle']
    assert indicators['bb_middle'] > indicators['bb_lower']
    assert indicators['bb_width'] > 0
