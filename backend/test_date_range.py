"""
Debug script to test specific date ranges that fail.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from app.services.binance import BinanceService, get_candles_in_range
from app.services.indicators import calculate_rsi, calculate_macd, calculate_ema, calculate_bollinger_bands
from app.core.config import settings
from app.core.database import SessionLocal

def test_backtest_date_range(symbol: str, start_date: str, end_date: str, timeframe: str):
    """Test a specific date range that fails in backtest."""
    print(f"\n{'='*60}")
    print(f"Testing {symbol} {timeframe} from {start_date} to {end_date}")
    print(f"{'='*60}")
    
    db = SessionLocal()
    
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    # Fetch historical data (same way as VectorBT engine)
    candles = get_candles_in_range(db, symbol, timeframe, start_dt, end_dt)
    
    print(f"Candles from DB: {len(candles)}")
    
    if len(candles) < 50:
        # Fetch from Binance if not in DB
        print("Fetching from Binance...")
        binance = BinanceService()
        klines = binance.fetch_klines_sync(
            symbol=symbol,
            interval=timeframe,
            start_time=int(start_dt.timestamp() * 1000),
            end_time=int(end_dt.timestamp() * 1000)
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
    else:
        df = pd.DataFrame([
            {
                "timestamp": c.timestamp,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in candles
        ])
    
    if df.empty:
        print("ERROR: No data!")
        return
    
    df.set_index("timestamp", inplace=True)
    
    print(f"Total candles: {len(df)}")
    print(f"Actual date range: {df.index[0]} to {df.index[-1]}")
    
    # Calculate indicators
    df["rsi"] = calculate_rsi(df, 14)
    macd_data = calculate_macd(df)
    df["macd"] = macd_data["macd"]
    df["macd_signal"] = macd_data["macd_signal"]
    df["macd_hist"] = macd_data["macd_diff"]
    
    # Check for NaN values
    print(f"\nNaN counts:")
    print(f"RSI: {df['rsi'].isna().sum()}")
    print(f"MACD: {df['macd'].isna().sum()}")
    print(f"MACD Signal: {df['macd_signal'].isna().sum()}")
    print(f"MACD Hist: {df['macd_hist'].isna().sum()}")
    
    # Valid data points (after indicators are ready)
    valid_df = df[df["rsi"].notna() & df["macd"].notna()]
    print(f"Valid data points (non-NaN): {len(valid_df)}")
    
    if len(valid_df) == 0:
        print("ERROR: No valid data after calculating indicators!")
        return
    
    # Test RSI/MACD Strategy
    print(f"\n--- RSI/MACD Strategy ---")
    print(f"RSI range: {valid_df['rsi'].min():.2f} to {valid_df['rsi'].max():.2f}")
    print(f"RSI < 30: {(valid_df['rsi'] < 30).sum()} times")
    print(f"RSI > 70: {(valid_df['rsi'] > 70).sum()} times")
    print(f"RSI < 50: {(valid_df['rsi'] < 50).sum()} times")
    print(f"RSI > 50: {(valid_df['rsi'] > 50).sum()} times")
    
    # Detect MACD crossovers
    macd_above_signal = df["macd"] > df["macd_signal"]
    macd_above_signal_prev = macd_above_signal.shift(1).fillna(False)
    
    macd_bullish_cross = (~macd_above_signal_prev) & macd_above_signal
    macd_bearish_cross = macd_above_signal_prev & (~macd_above_signal)
    
    print(f"MACD bullish crossovers (total): {macd_bullish_cross.sum()}")
    print(f"MACD bearish crossovers (total): {macd_bearish_cross.sum()}")
    
    # Current strategy signals (what VectorBT uses)
    rsi_valid = df["rsi"].notna()
    entries = macd_bullish_cross & (df["rsi"] < 50) & rsi_valid
    exits = macd_bearish_cross & (df["rsi"] > 50) & rsi_valid
    
    print(f"BUY signals (MACD cross + RSI<50): {entries.sum()}")
    print(f"SELL signals (MACD cross + RSI>50): {exits.sum()}")
    
    if entries.sum() > 0:
        print(f"\nBUY signal dates:")
        buy_dates = df.index[entries].tolist()
        for date in buy_dates[:10]:  # Show first 10
            rsi_val = df.loc[date, "rsi"]
            macd_val = df.loc[date, "macd"]
            signal_val = df.loc[date, "macd_signal"]
            close_val = df.loc[date, "close"]
            print(f"  {date}: RSI={rsi_val:.1f}, MACD={macd_val:.2f}, Signal={signal_val:.2f}, Close=${close_val:.2f}")
    else:
        print("\n⚠️  NO BUY SIGNALS FOUND!")
        # Show some MACD crossovers without RSI filter
        bullish_crosses = df.index[macd_bullish_cross].tolist()
        if len(bullish_crosses) > 0:
            print(f"\nBullish MACD crossovers (without RSI filter):")
            for date in bullish_crosses[:5]:
                rsi_val = df.loc[date, "rsi"]
                macd_val = df.loc[date, "macd"]
                signal_val = df.loc[date, "macd_signal"]
                print(f"  {date}: RSI={rsi_val:.1f} (filter requires <50), MACD={macd_val:.2f}, Signal={signal_val:.2f}")
    
    db.close()

if __name__ == "__main__":
    # Test the failing case
    test_backtest_date_range("BTCUSDT", "2023-01-01", "2025-12-06", "1d")
    
    # Also test the working case
    test_backtest_date_range("BTCUSDT", "2022-01-01", "2025-12-06", "1d")
