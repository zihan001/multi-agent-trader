"""
Debug script to test more relaxed signal generation.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.binance import BinanceService
from app.services.indicators import calculate_rsi, calculate_macd, calculate_ema, calculate_bollinger_bands
from app.core.config import settings

# Fetch some real data
binance = BinanceService()
end_time = int(datetime.now().timestamp() * 1000)
start_time = end_time - (60 * 24 * 60 * 60 * 1000)  # 60 days ago for better sample

klines = binance.fetch_klines_sync(
    symbol="BTCUSDT",
    interval="1h",
    start_time=start_time,
    end_time=end_time,
    limit=1000  # More data
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

print(f"Data shape: {df.shape}")
print(f"Date range: {df.index[0]} to {df.index[-1]}")

# Calculate indicators
df["rsi"] = calculate_rsi(df, 14)
macd_data = calculate_macd(df)
df["macd"] = macd_data["macd"]
df["macd_signal"] = macd_data["macd_signal"]
df["macd_hist"] = macd_data["macd_diff"]

print(f"\nRSI statistics:")
print(f"Min: {df['rsi'].min():.2f}")
print(f"Max: {df['rsi'].max():.2f}")
print(f"Mean: {df['rsi'].mean():.2f}")
print(f"< 30: {(df['rsi'] < 30).sum()}")
print(f"> 70: {(df['rsi'] > 70).sum()}")

# Test original strict strategy
strict_entries = (
    (df["rsi"] < 30) &
    (df["macd"] > df["macd_signal"])
)
strict_exits = (
    (df["rsi"] > 70) &
    (df["macd"] < df["macd_signal"])
)

print(f"\n=== STRICT STRATEGY (current) ===")
print(f"Entry signals (RSI<30 AND MACD>Signal): {strict_entries.sum()}")
print(f"Exit signals (RSI>70 AND MACD<Signal): {strict_exits.sum()}")

# Test more realistic strategies
print(f"\n=== RELAXED STRATEGY OPTIONS ===")

# Option 1: OR instead of AND
or_entries = (
    (df["rsi"] < 30) |
    ((df["macd"] > df["macd_signal"]) & (df["rsi"] < 40))
)
or_exits = (
    (df["rsi"] > 70) |
    ((df["macd"] < df["macd_signal"]) & (df["rsi"] > 60))
)
print(f"Option 1 (OR logic): Entries={or_entries.sum()}, Exits={or_exits.sum()}")

# Option 2: Relaxed thresholds
relaxed_entries = (
    (df["rsi"] < 35) &
    (df["macd"] > df["macd_signal"])
)
relaxed_exits = (
    (df["rsi"] > 65) &
    (df["macd"] < df["macd_signal"])
)
print(f"Option 2 (RSI 35/65): Entries={relaxed_entries.sum()}, Exits={relaxed_exits.sum()}")

# Option 3: MACD crossover with RSI confirmation
macd_bullish_cross = (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1))
macd_bearish_cross = (df["macd"] < df["macd_signal"]) & (df["macd"].shift(1) >= df["macd_signal"].shift(1))

cross_entries = macd_bullish_cross & (df["rsi"] < 50)
cross_exits = macd_bearish_cross & (df["rsi"] > 50)
print(f"Option 3 (MACD cross + RSI): Entries={cross_entries.sum()}, Exits={cross_exits.sum()}")

# Option 4: Just RSI
rsi_only_entries = df["rsi"] < 30
rsi_only_exits = df["rsi"] > 70
print(f"Option 4 (RSI only): Entries={rsi_only_entries.sum()}, Exits={rsi_only_exits.sum()}")

# Option 5: Just MACD crossover
macd_only_entries = macd_bullish_cross
macd_only_exits = macd_bearish_cross
print(f"Option 5 (MACD crossover only): Entries={macd_only_entries.sum()}, Exits={macd_only_exits.sum()}")
