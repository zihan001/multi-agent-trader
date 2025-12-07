"""
Debug script to test signal generation for LONG timeframes (4h, 1d).
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.binance import BinanceService
from app.services.indicators import calculate_rsi, calculate_macd, calculate_ema, calculate_bollinger_bands
from app.core.config import settings

def test_timeframe(interval: str, days_back: int = 365):
    """Test signal generation for a specific timeframe."""
    print(f"\n{'='*60}")
    print(f"Testing {interval} timeframe")
    print(f"{'='*60}")
    
    # Fetch data
    binance = BinanceService()
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (days_back * 24 * 60 * 60 * 1000)
    
    klines = binance.fetch_klines_sync(
        symbol="BTCUSDT",
        interval=interval,
        start_time=start_time,
        end_time=end_time,
        limit=1000
    )
    
    df = pd.DataFrame([
        {
            "timestamp": datetime.fromtimestamp(k[0] / 1000),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        }
        for k in klines
    ])
    
    df.set_index("timestamp", inplace=True)
    
    print(f"Data points: {len(df)}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    # Calculate indicators
    df["rsi"] = calculate_rsi(df, 14)
    macd_data = calculate_macd(df)
    df["macd"] = macd_data["macd"]
    df["macd_signal"] = macd_data["macd_signal"]
    df["macd_hist"] = macd_data["macd_diff"]
    
    # EMAs
    df["ema_fast"] = calculate_ema(df, settings.ema_fast)
    df["ema_slow"] = calculate_ema(df, settings.ema_slow)
    df["ema_trend"] = calculate_ema(df, settings.ema_trend)
    
    # Bollinger Bands
    bb_data = calculate_bollinger_bands(df)
    df["bb_upper"] = bb_data["bb_high"]
    df["bb_middle"] = bb_data["bb_mid"]
    df["bb_lower"] = bb_data["bb_low"]
    df["volume_ma"] = df["volume"].rolling(window=settings.bb_period).mean()
    
    # Test RSI/MACD Strategy
    print(f"\n--- RSI/MACD Strategy ---")
    print(f"RSI range: {df['rsi'].min():.2f} to {df['rsi'].max():.2f}")
    print(f"RSI < 30: {(df['rsi'] < 30).sum()} times")
    print(f"RSI > 70: {(df['rsi'] > 70).sum()} times")
    print(f"RSI < 50: {(df['rsi'] < 50).sum()} times")
    print(f"RSI > 50: {(df['rsi'] > 50).sum()} times")
    
    # Detect MACD crossovers
    macd_above_signal = df["macd"] > df["macd_signal"]
    macd_above_signal_prev = macd_above_signal.shift(1).fillna(False)
    
    macd_bullish_cross = (~macd_above_signal_prev) & macd_above_signal
    macd_bearish_cross = macd_above_signal_prev & (~macd_above_signal)
    
    print(f"MACD bullish crossovers: {macd_bullish_cross.sum()}")
    print(f"MACD bearish crossovers: {macd_bearish_cross.sum()}")
    
    # Current strategy signals
    rsi_valid = df["rsi"].notna()
    entries = macd_bullish_cross & (df["rsi"] < 50) & rsi_valid
    exits = macd_bearish_cross & (df["rsi"] > 50) & rsi_valid
    
    print(f"BUY signals (MACD cross + RSI<50): {entries.sum()}")
    print(f"SELL signals (MACD cross + RSI>50): {exits.sum()}")
    
    if entries.sum() > 0:
        print(f"Example BUY signals:")
        buy_dates = df.index[entries].tolist()[:5]
        for date in buy_dates:
            rsi_val = df.loc[date, "rsi"]
            macd_val = df.loc[date, "macd"]
            signal_val = df.loc[date, "macd_signal"]
            print(f"  {date}: RSI={rsi_val:.1f}, MACD={macd_val:.2f}, Signal={signal_val:.2f}")
    
    # Test EMA Crossover Strategy
    print(f"\n--- EMA Crossover Strategy ---")
    fast_above_slow = df["ema_fast"] > df["ema_slow"]
    fast_above_slow_prev = fast_above_slow.shift(1).fillna(False)
    
    ema_entries = (
        (~fast_above_slow_prev) & fast_above_slow &
        (df["close"] > df["ema_trend"])
    )
    ema_exits = fast_above_slow_prev & (~fast_above_slow)
    
    print(f"BUY signals (EMA golden cross + price>trend): {ema_entries.sum()}")
    print(f"SELL signals (EMA death cross): {ema_exits.sum()}")
    
    # Test BB + Volume Strategy
    print(f"\n--- Bollinger Bands + Volume Strategy ---")
    volume_ratio = (df["volume"] / df["volume_ma"]).fillna(0)
    bb_valid = df["bb_lower"].notna() & df["bb_upper"].notna()
    
    print(f"Volume > 1.5x MA: {(volume_ratio >= 1.5).sum()} times")
    print(f"Price at lower BB: {(df['close'] <= df['bb_lower']).sum()} times")
    print(f"Price at upper BB: {(df['close'] >= df['bb_upper']).sum()} times")
    
    bb_entries = (
        (df["close"] <= df["bb_lower"]) &
        (volume_ratio >= settings.volume_surge_threshold) &
        bb_valid
    )
    bb_exits = (
        (df["close"] >= df["bb_upper"]) &
        (volume_ratio >= settings.volume_surge_threshold) &
        bb_valid
    )
    
    print(f"BUY signals (price≤lower BB + volume surge): {bb_entries.sum()}")
    print(f"SELL signals (price≥upper BB + volume surge): {bb_exits.sum()}")

if __name__ == "__main__":
    # Test different timeframes
    test_timeframe("1h", days_back=90)
    test_timeframe("4h", days_back=365)
    test_timeframe("1d", days_back=1095)  # 3 years
