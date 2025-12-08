"""
LLM-based backtesting engine using the agent pipeline.
"""
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

from app.backtesting.base import BaseBacktestEngine, BacktestResult, EquityPoint
from app.engines.factory import DecisionEngineFactory
from app.services.binance import BinanceService, get_candles_in_range
from app.services.indicators import IndicatorService
from app.services.portfolio import PortfolioManager
from app.core.config import settings


class LLMBacktestEngine(BaseBacktestEngine):
    """Backtest using LLM decision engine with sequential execution."""
    
    @property
    def engine_type(self) -> str:
        return "llm"
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": "LLM Agent Backtest",
            "description": "Sequential backtest using 6-agent LLM pipeline",
            "supports_parallel": False,
            "cost_per_decision": 0.02,
            "avg_decision_time_ms": 15000.0,
            "max_decisions_recommended": 100
        }
    
    def run_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1h",
        initial_capital: float = 10000.0,
        max_decisions: Optional[int] = None,
        **kwargs
    ) -> BacktestResult:
        """
        Run LLM-based backtest.
        
        Note: LLM backtests are SLOW and EXPENSIVE. Use sparingly!
        Recommended: max_decisions <= 50 for testing
        
        Args:
            symbol: Trading pair
            start_date: Backtest start
            end_date: Backtest end
            timeframe: Candle interval
            initial_capital: Starting cash
            max_decisions: Limit number of decisions (cost control)
            
        Returns:
            BacktestResult with comprehensive metrics
        """
        start_time = time.time()
        run_id = f"llm_backtest_{symbol}_{int(start_time)}"
        
        # Fetch historical candles
        candles = get_candles_in_range(
            self.db, symbol, timeframe, start_date, end_date
        )
        
        if len(candles) < 50:
            # Not enough data in DB, fetch from Binance
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
        
        if df.empty:
            raise ValueError(f"No historical data found for {symbol}")
        
        # Initialize portfolio manager with separate backtest run
        from app.models.database import PortfolioSnapshot
        snapshot = PortfolioSnapshot(
            timestamp=datetime.utcnow(),
            total_equity=initial_capital,
            cash_balance=initial_capital,
            run_id=run_id
        )
        self.db.add(snapshot)
        self.db.commit()
        
        # Never use paper trading for backtests (historical data only)
        portfolio_manager = PortfolioManager(self.db, run_id, use_paper_trading=False)
        
        # Create decision engine
        engine = DecisionEngineFactory.create(self.db)
        indicator_service = IndicatorService()
        
        trades: List[Dict[str, Any]] = []
        equity_curve: List[EquityPoint] = []
        
        # Apply max_decisions limit
        decision_points = df.iloc[50:]  # Need 50 candles for indicators
        if max_decisions:
            decision_points = decision_points.head(max_decisions)
        
        print(f"[LLMBacktest] Running {len(decision_points)} decisions for {symbol}")
        
        for idx, row in decision_points.iterrows():
            # Get historical data up to this point
            hist_df = df.loc[:idx]
            
            # Calculate indicators
            indicators = indicator_service.calculate_all_indicators(hist_df)
            
            # Prepare market context
            market_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": float(row["close"]),
                "price_change_24h": 0.0,  # Not available in backtest
                "volume_24h": float(row["volume"]),
                "candles": hist_df.tail(50).to_dict(orient="records"),
                "indicators": indicators,
                "sentiment_data": {},
                "token_data": {}
            }
            
            # Get current portfolio
            portfolio_data = portfolio_manager.get_portfolio_summary()
            
            # Run decision engine
            try:
                result = engine.analyze(
                    symbol=symbol,
                    market_data=market_data,
                    portfolio_data=portfolio_data,
                    run_id=run_id
                )
                
                decision = result.decision
                
                # Execute trade if approved
                if decision.action in ["BUY", "SELL"] and decision.approved:
                    trade = portfolio_manager.execute_trade(
                        symbol=symbol,
                        side=decision.action,
                        quantity=decision.quantity or 0.0,
                        price=decision.price or float(row["close"]),
                        run_id=run_id
                    )
                    
                    if trade:
                        trades.append({
                            "timestamp": row["timestamp"],
                            "side": decision.action,
                            "quantity": decision.quantity,
                            "price": decision.price,
                            "pnl": trade.pnl or 0.0
                        })
                
            except Exception as e:
                print(f"[LLMBacktest] Decision error at {row['timestamp']}: {e}")
                continue
            
            # Record equity
            portfolio_summary = portfolio_manager.get_portfolio_summary()
            equity_curve.append(EquityPoint(
                timestamp=row["timestamp"],
                equity=portfolio_summary["total_equity"],
                cash=portfolio_summary["cash_balance"],
                positions_value=portfolio_summary["total_equity"] - portfolio_summary["cash_balance"]
            ))
        
        # Calculate metrics
        metrics = self._calculate_metrics(trades, equity_curve, initial_capital)
        
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
            engine_type="llm",
            strategy_name=None,
            execution_time_ms=execution_time_ms
        )
