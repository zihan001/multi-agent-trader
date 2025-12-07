"""
VectorBT-based backtesting engine for fast, vectorized strategy testing.
"""
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Disable VectorBT plotting to avoid Plotly version conflicts
os.environ["VECTORBT_SUPPRESS_WARNINGS"] = "1"

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    print("Warning: vectorbt not installed. VectorBT backtesting unavailable.")

from app.backtesting.base import BaseBacktestEngine, BacktestResult, EquityPoint
from app.services.binance import get_candles_in_range, BinanceService
from app.services.indicators import IndicatorService
from app.core.config import settings


class VectorBTEngine(BaseBacktestEngine):
    """Fast vectorized backtesting using VectorBT."""
    
    def __init__(self, db, strategy: str = "rsi_macd"):
        super().__init__(db)
        if not VECTORBT_AVAILABLE:
            raise ImportError("vectorbt is not installed. Install with: pip install vectorbt")
        self.strategy = strategy
    
    @property
    def engine_type(self) -> str:
        return "vectorbt"
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "VectorBT Backtest Engine",
            "description": "Fast vectorized backtesting with professional metrics",
            "supports_parallel": True,
            "cost_per_decision": 0.0,
            "avg_decision_time_ms": 100.0,
            "strategies": {
                "rsi_macd": "RSI + MACD Momentum Strategy",
                "ema_crossover": "EMA Crossover Trend Strategy",
                "bb_volume": "Bollinger Bands + Volume Strategy"
            }
        }
    
    def run_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1h",
        initial_capital: float = 10000.0,
        **kwargs
    ) -> BacktestResult:
        """
        Run vectorized backtest with VectorBT.
        
        Args:
            symbol: Trading pair
            start_date: Backtest start
            end_date: Backtest end
            timeframe: Candle interval
            initial_capital: Starting capital
            
        Returns:
            BacktestResult with comprehensive metrics
        """
        start_time = time.time()
        run_id = f"vbt_backtest_{symbol}_{int(start_time)}"
        
        # Fetch historical data
        candles = get_candles_in_range(
            self.db, symbol, timeframe, start_date, end_date
        )
        
        if len(candles) < 50:
            # Fetch from Binance if not in DB
            binance = BinanceService()
            # Use get_historical_klines for proper pagination across long date ranges
            formatted_klines = binance.get_historical_klines(
                symbol=symbol,
                interval=timeframe,
                start_time=start_date,
                end_time=end_date
            )
            
            df = pd.DataFrame(formatted_klines)
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
        
        if df.empty or len(df) < 50:
            raise ValueError(f"Insufficient data for backtest (need >= 50 candles)")
        
        df.set_index("timestamp", inplace=True)
        
        # Calculate indicators - need full series for backtesting
        from app.services.indicators import (
            calculate_rsi, calculate_macd, calculate_ema, 
            calculate_bollinger_bands, calculate_sma
        )
        
        # RSI
        df["rsi"] = calculate_rsi(df, 14)
        
        # MACD
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
        
        # Volume moving average for BB+Volume strategy
        df["volume_ma"] = df["volume"].rolling(window=settings.bb_period).mean()
        
        # Generate signals based on strategy
        if self.strategy == "rsi_macd":
            entries, exits = self._rsi_macd_signals(df)
        elif self.strategy == "ema_crossover":
            entries, exits = self._ema_crossover_signals(df)
        elif self.strategy == "bb_volume":
            entries, exits = self._bb_volume_signals(df)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        # Run VectorBT portfolio simulation
        portfolio = vbt.Portfolio.from_signals(
            close=df["close"],
            entries=entries,
            exits=exits,
            init_cash=initial_capital,
            fees=0.001,  # 0.1% trading fees
            freq=timeframe
        )
        
        # Extract trades
        trades = []
        try:
            trade_records = portfolio.trades.records_readable
            if len(trade_records) > 0:
                for i in range(len(trade_records)):
                    trade = trade_records.iloc[i]
                    # Handle different column name formats
                    entry_idx = trade.get("Entry Index", trade.get("Entry Idx", None))
                    exit_idx = trade.get("Exit Index", trade.get("Exit Idx", None))
                    
                    # Get timestamp from index
                    if entry_idx is not None and entry_idx < len(df):
                        timestamp = df.index[int(entry_idx)]
                    else:
                        timestamp = df.index[0]
                    
                    trades.append({
                        "timestamp": timestamp,
                        "side": "BUY" if trade.get("Size", 0) > 0 else "SELL",
                        "quantity": abs(trade.get("Size", 0)),
                        "price": trade.get("Avg Entry Price", trade.get("Entry Price", df["close"].iloc[int(entry_idx)] if entry_idx is not None else 0)),
                        "pnl": trade.get("PnL", trade.get("Return", 0))
                    })
        except Exception as e:
            # If trade extraction fails, continue with empty trades list
            print(f"Warning: Could not extract trades: {e}")
        
        # Build equity curve
        equity_curve = []
        for ts, equity_val in zip(df.index, portfolio.value()):
            equity_curve.append(EquityPoint(
                timestamp=ts,
                equity=float(equity_val),
                cash=float(portfolio.cash()[df.index.get_loc(ts)]),
                positions_value=float(equity_val - portfolio.cash()[df.index.get_loc(ts)])
            ))
        
        # Calculate metrics using VectorBT stats
        stats = portfolio.stats()
        
        # Helper to safely convert stats values (handle NaN, inf)
        def safe_float(key, default=0.0):
            if key not in stats:
                return default
            val = float(stats[key])
            if np.isnan(val) or np.isinf(val):
                return default
            return val
        
        def safe_float_optional(key):
            if key not in stats:
                return None
            val = float(stats[key])
            if np.isnan(val) or np.isinf(val):
                return None
            return val
        
        from app.backtesting.base import BacktestMetrics
        metrics = BacktestMetrics(
            total_return=safe_float("Total Return"),
            total_return_pct=safe_float("Total Return [%]"),
            max_drawdown=safe_float("Max Drawdown"),
            max_drawdown_pct=safe_float("Max Drawdown [%]"),
            sharpe_ratio=safe_float_optional("Sharpe Ratio"),
            sortino_ratio=safe_float_optional("Sortino Ratio"),
            win_rate=safe_float("Win Rate [%]"),
            num_trades=int(stats.get("Total Trades", 0)),
            avg_trade_return=safe_float("Avg Winning Trade [%]"),
            best_trade=safe_float("Best Trade [%]"),
            worst_trade=safe_float("Worst Trade [%]"),
            profit_factor=safe_float_optional("Profit Factor")
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return BacktestResult(
            run_id=run_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            initial_capital=initial_capital,
            final_equity=equity_curve[-1].equity if equity_curve else initial_capital,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades,
            engine_type="vectorbt",
            strategy_name=self.strategy,
            execution_time_ms=execution_time_ms
        )
    
    def _rsi_macd_signals(self, df: pd.DataFrame) -> tuple:
        """
        Generate RSI + MACD entry/exit signals.
        
        Uses MACD crossover as primary signal with RSI as filter:
        - BUY on bullish MACD crossover when RSI < 50 (not overbought)
        - SELL on bearish MACD crossover when RSI > 50 (not oversold)
        """
        # Detect MACD crossovers
        macd_above_signal = df["macd"] > df["macd_signal"]
        macd_above_signal_prev = macd_above_signal.shift(1).fillna(False)
        
        # Bullish crossover: MACD crosses above signal
        macd_bullish_cross = (~macd_above_signal_prev) & macd_above_signal
        # Bearish crossover: MACD crosses below signal  
        macd_bearish_cross = macd_above_signal_prev & (~macd_above_signal)
        
        # Apply RSI filter (handle NaN in RSI)
        rsi_valid = df["rsi"].notna()
        entries = macd_bullish_cross & (df["rsi"] < 50) & rsi_valid
        exits = macd_bearish_cross & (df["rsi"] > 50) & rsi_valid
        
        return entries, exits
    
    def _ema_crossover_signals(self, df: pd.DataFrame) -> tuple:
        """Generate EMA crossover entry/exit signals."""
        fast_above_slow = df["ema_fast"] > df["ema_slow"]
        fast_above_slow_prev = fast_above_slow.shift(1).fillna(False)
        
        entries = (
            (~fast_above_slow_prev) & fast_above_slow &
            (df["close"] > df["ema_trend"])
        )
        exits = (
            fast_above_slow_prev & (~fast_above_slow)
        )
        return entries, exits
    
    def _bb_volume_signals(self, df: pd.DataFrame) -> tuple:
        """Generate Bollinger Bands + Volume signals."""
        volume_ma = df["volume"].rolling(window=settings.bb_period).mean()
        volume_ratio = (df["volume"] / volume_ma).fillna(0)
        
        # Handle NaN in BB values
        bb_valid = df["bb_lower"].notna() & df["bb_upper"].notna()
        
        entries = (
            (df["close"] <= df["bb_lower"]) &
            (volume_ratio >= settings.volume_surge_threshold) &
            bb_valid
        )
        exits = (
            (df["close"] >= df["bb_upper"]) &
            (volume_ratio >= settings.volume_surge_threshold) &
            bb_valid
        )
        return entries, exits
