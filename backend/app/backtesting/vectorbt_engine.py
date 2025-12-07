"""
VectorBT-based backtesting engine for fast, vectorized strategy testing.
"""
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

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
            klines = binance.fetch_klines_sync(
                symbol=symbol,
                interval=timeframe,
                start_time=int(start_date.timestamp() * 1000),
                end_time=int(end_date.timestamp() * 1000)
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
        
        if df.empty or len(df) < 50:
            raise ValueError(f"Insufficient data for backtest (need >= 50 candles)")
        
        df.set_index("timestamp", inplace=True)
        
        # Calculate indicators
        indicator_service = IndicatorService()
        indicators = indicator_service.calculate_all_indicators(df)
        
        # Add indicators to dataframe
        df["rsi"] = indicators["rsi"]
        df["macd"] = indicators["macd"]
        df["macd_signal"] = indicators["macd_signal"]
        df["ema_fast"] = indicators["ema_12"]
        df["ema_slow"] = indicators["ema_26"]
        df["ema_trend"] = indicators.get("ema_50", indicators["ema_26"])
        df["bb_upper"] = indicators["bb_upper"]
        df["bb_lower"] = indicators["bb_lower"]
        
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
        for trade_record in portfolio.trades.records:
            trades.append({
                "timestamp": df.index[trade_record["entry_idx"]],
                "side": "BUY" if trade_record["size"] > 0 else "SELL",
                "quantity": abs(trade_record["size"]),
                "price": trade_record["entry_price"],
                "pnl": trade_record["pnl"]
            })
        
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
        
        from app.backtesting.base import BacktestMetrics
        metrics = BacktestMetrics(
            total_return=float(stats["Total Return"]) if "Total Return" in stats else 0.0,
            total_return_pct=float(stats["Total Return [%]"]) if "Total Return [%]" in stats else 0.0,
            max_drawdown=float(stats["Max Drawdown"]) if "Max Drawdown" in stats else 0.0,
            max_drawdown_pct=float(stats["Max Drawdown [%]"]) if "Max Drawdown [%]" in stats else 0.0,
            sharpe_ratio=float(stats["Sharpe Ratio"]) if "Sharpe Ratio" in stats else None,
            sortino_ratio=float(stats["Sortino Ratio"]) if "Sortino Ratio" in stats else None,
            win_rate=float(stats["Win Rate [%]"]) if "Win Rate [%]" in stats else 0.0,
            num_trades=int(stats["Total Trades"]) if "Total Trades" in stats else 0,
            avg_trade_return=float(stats["Avg Winning Trade [%]"]) if "Avg Winning Trade [%]" in stats else 0.0,
            best_trade=float(stats["Best Trade [%]"]) if "Best Trade [%]" in stats else 0.0,
            worst_trade=float(stats["Worst Trade [%]"]) if "Worst Trade [%]" in stats else 0.0,
            profit_factor=float(stats["Profit Factor"]) if "Profit Factor" in stats else None
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
        """Generate RSI + MACD entry/exit signals."""
        entries = (
            (df["rsi"] < settings.rsi_oversold) &
            (df["macd"] > df["macd_signal"])
        )
        exits = (
            (df["rsi"] > settings.rsi_overbought) &
            (df["macd"] < df["macd_signal"])
        )
        return entries, exits
    
    def _ema_crossover_signals(self, df: pd.DataFrame) -> tuple:
        """Generate EMA crossover entry/exit signals."""
        fast_above_slow = df["ema_fast"] > df["ema_slow"]
        fast_above_slow_prev = fast_above_slow.shift(1)
        
        entries = (
            ~fast_above_slow_prev & fast_above_slow &
            (df["close"] > df["ema_trend"])
        )
        exits = (
            fast_above_slow_prev & ~fast_above_slow
        )
        return entries, exits
    
    def _bb_volume_signals(self, df: pd.DataFrame) -> tuple:
        """Generate Bollinger Bands + Volume signals."""
        volume_ma = df["volume"].rolling(window=settings.bb_period).mean()
        volume_ratio = df["volume"] / volume_ma
        
        entries = (
            (df["close"] <= df["bb_lower"]) &
            (volume_ratio >= settings.min_volume_ratio)
        )
        exits = (
            (df["close"] >= df["bb_upper"]) &
            (volume_ratio >= settings.min_volume_ratio)
        )
        return entries, exits
