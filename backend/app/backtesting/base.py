"""
Base backtesting engine abstraction for unified backtest interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel


class BacktestMetrics(BaseModel):
    """Standardized backtest performance metrics."""
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    win_rate: float
    num_trades: int
    avg_trade_return: float
    best_trade: float
    worst_trade: float
    profit_factor: Optional[float]


class EquityPoint(BaseModel):
    """Single point in equity curve."""
    timestamp: datetime
    equity: float
    cash: float
    positions_value: float


class BacktestResult(BaseModel):
    """Unified backtest result structure."""
    run_id: str
    symbol: str
    start_date: datetime
    end_date: datetime
    timeframe: str
    initial_capital: float
    final_equity: float
    metrics: BacktestMetrics
    equity_curve: List[EquityPoint]
    trades: List[Dict[str, Any]]
    engine_type: str  # "llm" or "vectorbt"
    strategy_name: Optional[str] = None
    execution_time_ms: float


class BaseBacktestEngine(ABC):
    """Abstract base class for backtest engines."""
    
    def __init__(self, db):
        self.db = db
    
    @property
    @abstractmethod
    def engine_type(self) -> str:
        """Return engine type identifier."""
        pass
    
    @abstractmethod
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
        Run backtest for given parameters.
        
        Args:
            symbol: Trading pair symbol
            start_date: Backtest start date
            end_date: Backtest end date
            timeframe: Candle timeframe
            initial_capital: Starting capital
            **kwargs: Engine-specific parameters
            
        Returns:
            BacktestResult with metrics and trade history
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return engine capabilities and metadata."""
        pass
    
    def _calculate_metrics(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[EquityPoint],
        initial_capital: float
    ) -> BacktestMetrics:
        """
        Calculate standardized performance metrics.
        
        Args:
            trades: List of executed trades
            equity_curve: Equity curve data points
            initial_capital: Starting capital
            
        Returns:
            BacktestMetrics object
        """
        if not equity_curve:
            return BacktestMetrics(
                total_return=0.0,
                total_return_pct=0.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=None,
                sortino_ratio=None,
                win_rate=0.0,
                num_trades=0,
                avg_trade_return=0.0,
                best_trade=0.0,
                worst_trade=0.0,
                profit_factor=None
            )
        
        final_equity = equity_curve[-1].equity
        total_return = final_equity - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # Calculate max drawdown
        peak = initial_capital
        max_dd = 0.0
        for point in equity_curve:
            if point.equity > peak:
                peak = point.equity
            dd = peak - point.equity
            if dd > max_dd:
                max_dd = dd
        
        max_dd_pct = (max_dd / peak) * 100 if peak > 0 else 0.0
        
        # Trade statistics
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0.0
        avg_trade_return = sum(t.get('pnl', 0) for t in trades) / len(trades) if trades else 0.0
        best_trade = max((t.get('pnl', 0) for t in trades), default=0.0)
        worst_trade = min((t.get('pnl', 0) for t in trades), default=0.0)
        
        # Profit factor
        gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else None
        
        return BacktestMetrics(
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=None,  # TODO: Calculate from returns
            sortino_ratio=None,  # TODO: Calculate from returns
            win_rate=win_rate,
            num_trades=len(trades),
            avg_trade_return=avg_trade_return,
            best_trade=best_trade,
            worst_trade=worst_trade,
            profit_factor=profit_factor
        )
