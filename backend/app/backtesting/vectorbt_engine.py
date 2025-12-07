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
        
        # Extract trades - create entries and exits as separate trade records
        trades = []
        try:
            trade_records = portfolio.trades.records_readable
            if len(trade_records) > 0:
                for i in range(len(trade_records)):
                    trade_row = trade_records.iloc[i]
                    
                    # Get timestamps
                    entry_ts = trade_row.get("Entry Timestamp")
                    exit_ts = trade_row.get("Exit Timestamp")
                    
                    # Entry trade (BUY)
                    trades.append({
                        "timestamp": entry_ts,
                        "side": "BUY",
                        "quantity": abs(trade_row.get("Size", 0)),
                        "price": trade_row.get("Avg Entry Price", 0),
                        "pnl": None  # No PnL on entry
                    })
                    
                    # Exit trade (SELL) - only if trade is closed
                    if trade_row.get("Status") == "Closed" and exit_ts is not None:
                        trades.append({
                            "timestamp": exit_ts,
                            "side": "SELL",
                            "quantity": abs(trade_row.get("Size", 0)),
                            "price": trade_row.get("Avg Exit Price", 0),
                            "pnl": trade_row.get("PnL", 0)
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
        
        Uses MACD HISTOGRAM crossover as primary signal with RSI as filter:
        - BUY on bullish MACD histogram crossover (negative->positive) when RSI < 50
        - SELL on bearish MACD histogram crossover (positive->negative) when RSI > 50
        
        Tracks position state to prevent duplicate entries.
        """
        # Calculate previous MACD histogram for crossover detection
        macd_hist_prev = df["macd_hist"].shift(1)
        
        # Detect MACD histogram crossovers
        # Bullish crossover: histogram crosses from negative to positive
        macd_bullish_cross = (df["macd_hist"] > 0) & (macd_hist_prev <= 0)
        # Bearish crossover: histogram crosses from positive to negative
        macd_bearish_cross = (df["macd_hist"] < 0) & (macd_hist_prev >= 0)
        
        # Apply RSI filter (handle NaN in RSI)
        rsi_valid = df["rsi"].notna()
        raw_entries = macd_bullish_cross & (df["rsi"] < 50) & rsi_valid
        raw_exits = macd_bearish_cross & (df["rsi"] > 50) & rsi_valid
        
        # Track position state: only allow entry when not in position
        entries, exits = self._enforce_position_state(raw_entries, raw_exits)
        
        return entries, exits
    
    def _ema_crossover_signals(self, df: pd.DataFrame) -> tuple:
        """
        Generate EMA crossover entry/exit signals.
        
        Tracks position state to prevent duplicate entries.
        """
        fast_above_slow = df["ema_fast"] > df["ema_slow"]
        fast_above_slow_prev = fast_above_slow.shift(1).fillna(False)
        
        raw_entries = (
            (~fast_above_slow_prev) & fast_above_slow &
            (df["close"] > df["ema_trend"])
        )
        raw_exits = (
            fast_above_slow_prev & (~fast_above_slow) &
            (df["close"] < df["ema_trend"])  # Also check price below trend for exit
        )
        
        # Track position state: only allow entry when not in position
        entries, exits = self._enforce_position_state(raw_entries, raw_exits)
        
        return entries, exits
    
    def _bb_volume_signals(self, df: pd.DataFrame) -> tuple:
        """
        Generate Bollinger Bands + Volume signals.
        
        Tracks position state to prevent duplicate entries.
        """
        volume_ma = df["volume"].rolling(window=settings.bb_period).mean()
        volume_ratio = (df["volume"] / volume_ma).fillna(0)
        
        # Handle NaN in BB values
        bb_valid = df["bb_lower"].notna() & df["bb_upper"].notna()
        
        raw_entries = (
            (df["close"] <= df["bb_lower"]) &
            (volume_ratio >= settings.volume_surge_threshold) &
            bb_valid
        )
        raw_exits = (
            (df["close"] >= df["bb_upper"]) &
            (volume_ratio >= settings.volume_surge_threshold) &
            bb_valid
        )
        
        # Track position state: only allow entry when not in position
        entries, exits = self._enforce_position_state(raw_entries, raw_exits)
        
        return entries, exits
    
    def _enforce_position_state(self, raw_entries: pd.Series, raw_exits: pd.Series) -> tuple:
        """
        Enforce position state tracking to prevent duplicate entries.
        
        Only allow entry signals when not in a position.
        Only allow exit signals when in a position.
        
        Args:
            raw_entries: Boolean series of raw entry signals
            raw_exits: Boolean series of raw exit signals
            
        Returns:
            Tuple of (entries, exits) with position state enforced
        """
        entries = pd.Series(False, index=raw_entries.index)
        exits = pd.Series(False, index=raw_exits.index)
        
        in_position = False
        
        for i in range(len(raw_entries)):
            if not in_position and raw_entries.iloc[i]:
                # Not in position and entry signal -> ENTER
                entries.iloc[i] = True
                in_position = True
            elif in_position and raw_exits.iloc[i]:
                # In position and exit signal -> EXIT
                exits.iloc[i] = True
                in_position = False
        
        return entries, exits
