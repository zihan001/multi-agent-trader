"""
Technical indicators calculation using pandas and ta library.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
from app.models.database import Candle
import logging

logger = logging.getLogger(__name__)


def candles_to_dataframe(candles: List[Candle]) -> pd.DataFrame:
    """
    Convert list of Candle objects to pandas DataFrame.
    
    Args:
        candles: List of Candle model objects
    
    Returns:
        DataFrame with OHLCV data
    """
    data = {
        'timestamp': [c.timestamp for c in candles],
        'open': [c.open for c in candles],
        'high': [c.high for c in candles],
        'low': [c.low for c in candles],
        'close': [c.close for c in candles],
        'volume': [c.volume for c in candles],
    }
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    rsi = RSIIndicator(close=df['close'], window=window)
    return rsi.rsi()


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """Calculate MACD indicator."""
    macd = MACD(close=df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
    return {
        'macd': macd.macd(),
        'macd_signal': macd.macd_signal(),
        'macd_diff': macd.macd_diff()
    }


def calculate_ema(df: pd.DataFrame, window: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    ema = EMAIndicator(close=df['close'], window=window)
    return ema.ema_indicator()


def calculate_sma(df: pd.DataFrame, window: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    sma = SMAIndicator(close=df['close'], window=window)
    return sma.sma_indicator()


def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, window_dev: int = 2) -> Dict[str, pd.Series]:
    """Calculate Bollinger Bands."""
    bb = BollingerBands(close=df['close'], window=window, window_dev=window_dev)
    return {
        'bb_high': bb.bollinger_hband(),
        'bb_mid': bb.bollinger_mavg(),
        'bb_low': bb.bollinger_lband(),
        'bb_width': bb.bollinger_wband(),
    }


def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculate Average True Range (volatility indicator)."""
    atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=window)
    return atr.average_true_range()


def calculate_stochastic(df: pd.DataFrame, window: int = 14, smooth_window: int = 3) -> Dict[str, pd.Series]:
    """Calculate Stochastic Oscillator."""
    stoch = StochasticOscillator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=window,
        smooth_window=smooth_window
    )
    return {
        'stoch_k': stoch.stoch(),
        'stoch_d': stoch.stoch_signal()
    }


def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """Calculate On-Balance Volume."""
    obv = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume'])
    return obv.on_balance_volume()


def calculate_volatility(df: pd.DataFrame, window: int = 20) -> float:
    """Calculate price volatility (standard deviation of returns)."""
    returns = df['close'].pct_change()
    volatility = returns.rolling(window=window).std().iloc[-1]
    return float(volatility) if not pd.isna(volatility) else 0.0


def calculate_all_indicators(candles: List[Candle]) -> Dict[str, Any]:
    """
    Calculate all technical indicators for a list of candles.
    
    Args:
        candles: List of Candle objects (should be in chronological order)
    
    Returns:
        Dictionary with all calculated indicators
    """
    if len(candles) < 50:
        logger.warning(f"Only {len(candles)} candles available. Some indicators may be unreliable.")
    
    df = candles_to_dataframe(candles)
    
    # Calculate all indicators
    macd_data = calculate_macd(df)
    bb_data = calculate_bollinger_bands(df)
    stoch_data = calculate_stochastic(df)
    
    # Get latest values
    latest_idx = -1
    
    result = {
        # Price data
        'current_price': float(df['close'].iloc[latest_idx]),
        'open': float(df['open'].iloc[latest_idx]),
        'high': float(df['high'].iloc[latest_idx]),
        'low': float(df['low'].iloc[latest_idx]),
        'volume': float(df['volume'].iloc[latest_idx]),
        
        # Moving averages
        'ema_9': float(calculate_ema(df, 9).iloc[latest_idx]),
        'ema_21': float(calculate_ema(df, 21).iloc[latest_idx]),
        'ema_50': float(calculate_ema(df, 50).iloc[latest_idx]),
        'sma_20': float(calculate_sma(df, 20).iloc[latest_idx]),
        'sma_50': float(calculate_sma(df, 50).iloc[latest_idx]),
        
        # Momentum indicators
        'rsi_14': float(calculate_rsi(df, 14).iloc[latest_idx]),
        'macd': float(macd_data['macd'].iloc[latest_idx]),
        'macd_signal': float(macd_data['macd_signal'].iloc[latest_idx]),
        'macd_diff': float(macd_data['macd_diff'].iloc[latest_idx]),
        
        # Volatility
        'atr_14': float(calculate_atr(df, 14).iloc[latest_idx]),
        'volatility_20': calculate_volatility(df, 20),
        'bb_upper': float(bb_data['bb_high'].iloc[latest_idx]),
        'bb_middle': float(bb_data['bb_mid'].iloc[latest_idx]),
        'bb_lower': float(bb_data['bb_low'].iloc[latest_idx]),
        'bb_width': float(bb_data['bb_width'].iloc[latest_idx]),
        
        # Stochastic
        'stoch_k': float(stoch_data['stoch_k'].iloc[latest_idx]),
        'stoch_d': float(stoch_data['stoch_d'].iloc[latest_idx]),
        
        # Volume
        'obv': float(calculate_obv(df).iloc[latest_idx]),
        
        # Trend assessment
        'trend': assess_trend(df),
        'momentum': assess_momentum(df),
    }
    
    # Replace NaN values with None
    for key, value in result.items():
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            result[key] = None
    
    return result


def assess_trend(df: pd.DataFrame) -> str:
    """
    Assess overall trend based on moving averages.
    
    Returns:
        'uptrend', 'downtrend', or 'sideways'
    """
    try:
        ema_9 = calculate_ema(df, 9).iloc[-1]
        ema_21 = calculate_ema(df, 21).iloc[-1]
        ema_50 = calculate_ema(df, 50).iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Strong uptrend: price above all EMAs, EMAs in order
        if current_price > ema_9 > ema_21 > ema_50:
            return "uptrend"
        # Strong downtrend: price below all EMAs, EMAs in reverse order
        elif current_price < ema_9 < ema_21 < ema_50:
            return "downtrend"
        else:
            return "sideways"
    except Exception as e:
        logger.error(f"Error assessing trend: {e}")
        return "sideways"


def assess_momentum(df: pd.DataFrame) -> str:
    """
    Assess momentum strength based on RSI and MACD.
    
    Returns:
        'strong', 'moderate', or 'weak'
    """
    try:
        rsi = calculate_rsi(df, 14).iloc[-1]
        macd_data = calculate_macd(df)
        macd_diff = macd_data['macd_diff'].iloc[-1]
        
        # Strong momentum: RSI extreme and MACD confirming
        if (rsi > 70 or rsi < 30) and abs(macd_diff) > 0:
            return "strong"
        # Moderate: some indication but not extreme
        elif (60 < rsi < 70 or 30 < rsi < 40) or abs(macd_diff) > 0:
            return "moderate"
        else:
            return "weak"
    except Exception as e:
        logger.error(f"Error assessing momentum: {e}")
        return "weak"


def get_overbought_oversold_status(rsi: float, stoch_k: float) -> str:
    """
    Determine if asset is overbought or oversold.
    
    Args:
        rsi: RSI value
        stoch_k: Stochastic K value
    
    Returns:
        'overbought', 'oversold', or 'neutral'
    """
    if rsi > 70 and stoch_k > 80:
        return "overbought"
    elif rsi < 30 and stoch_k < 20:
        return "oversold"
    else:
        return "neutral"
