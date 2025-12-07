"""
Debug script to test signal generation in backtesting.
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
start_time = end_time - (30 * 24 * 60 * 60 * 1000)  # 30 days ago

klines = binance.fetch_klines_sync(
    symbol="BTCUSDT",
    interval="1h",
    start_time=start_time,
    end_time=end_time
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

# Count NaN values
print(f"\nNaN counts:")
print(f"RSI: {df['rsi'].isna().sum()}")
print(f"MACD: {df['macd'].isna().sum()}")
print(f"MACD Signal: {df['macd_signal'].isna().sum()}")

# Check signal conditions for RSI + MACD strategy
print(f"\nSettings:")
print(f"RSI Oversold: {settings.rsi_oversold}")
print(f"RSI Overbought: {settings.rsi_overbought}")

# Generate signals
entries = (
    (df["rsi"] < settings.rsi_oversold) &
    (df["macd"] > df["macd_signal"])
)

exits = (
    (df["rsi"] > settings.rsi_overbought) &
    (df["macd"] < df["macd_signal"])
)

print(f"\nSignal counts:")
print(f"Entry signals: {entries.sum()}")
print(f"Exit signals: {exits.sum()}")

# Show RSI statistics
print(f"\nRSI statistics (excluding NaN):")
print(f"Min: {df['rsi'].min():.2f}")
print(f"Max: {df['rsi'].max():.2f}")
print(f"Mean: {df['rsi'].mean():.2f}")
print(f"< 30: {(df['rsi'] < 30).sum()}")
print(f"> 70: {(df['rsi'] > 70).sum()}")

# Show some samples where RSI is low
low_rsi = df[df['rsi'] < 35].copy()
if len(low_rsi) > 0:
    print(f"\nSample rows with RSI < 35:")
    low_rsi['macd_above_signal'] = low_rsi['macd'] > low_rsi['macd_signal']
    print(low_rsi[['close', 'rsi', 'macd', 'macd_signal', 'macd_above_signal']].head(10))
