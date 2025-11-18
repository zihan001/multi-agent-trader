"""
Backtesting Engine

Runs historical backtests by simulating the agent pipeline over historical data.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
import pandas as pd

from app.agents.pipeline import AgentPipeline
from app.services.binance import BinanceService
from app.services.indicators import IndicatorService
from app.services.portfolio import PortfolioManager
from app.models.database import Candle, Trade, BacktestRun


class BacktestEngine:
    """
    Engine for running historical backtests.
    
    Simulates trading by:
    - Loading historical market data
    - Running agent pipeline at intervals
    - Executing simulated trades
    - Calculating performance metrics
    """
    
    def __init__(self, db: Session):
        """
        Initialize backtest engine.
        
        Args:
            db: Database session
        """
        self.db = db
        self.binance_service = BinanceService()
        self.indicator_service = IndicatorService()
    
    def run_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1h",
        initial_cash: float = 10000.0,
        decision_frequency: int = 4,  # Run pipeline every N candles
        max_decisions: Optional[int] = None,  # Cap total decisions for cost control
    ) -> Dict[str, Any]:
        """
        Run a complete backtest.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            start_date: Backtest start date
            end_date: Backtest end date
            timeframe: Candle timeframe (1h, 4h, 1d, etc.)
            initial_cash: Starting cash balance
            decision_frequency: Run pipeline every N candles
            max_decisions: Maximum number of decisions to make (cost control)
            
        Returns:
            Backtest results with metrics, equity curve, and trades
        """
        print(f"Starting backtest for {symbol}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Timeframe: {timeframe}, Decision Frequency: every {decision_frequency} candles")
        
        # Create backtest run record
        run_id = f"backtest_{symbol}_{start_date.date()}_{end_date.date()}_{datetime.utcnow().timestamp()}"
        
        backtest_run = BacktestRun(
            run_id=run_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            initial_cash=Decimal(str(initial_cash)),
            decision_frequency=decision_frequency,
            max_decisions=max_decisions,
            status="running",
            created_at=datetime.utcnow(),
        )
        self.db.add(backtest_run)
        self.db.commit()
        
        try:
            # Load historical candles
            candles = self._load_candles(symbol, start_date, end_date, timeframe)
            
            if not candles:
                raise ValueError(f"No candles found for {symbol} in the specified period")
            
            print(f"Loaded {len(candles)} candles")
            
            # Initialize backtest portfolio
            portfolio_state = {
                "cash_balance": initial_cash,
                "positions": {},
                "total_equity": initial_cash,
                "trades": [],
            }
            
            equity_curve = [{"timestamp": start_date.isoformat(), "equity": initial_cash}]
            
            # Initialize agent pipeline
            pipeline = AgentPipeline(self.db)
            
            # Run backtest loop
            decisions_made = 0
            
            for i, candle in enumerate(candles):
                # Update portfolio mark-to-market
                current_price = float(candle.close)
                portfolio_state = self._update_portfolio_mtm(portfolio_state, symbol, current_price)
                
                # Record equity
                equity_curve.append({
                    "timestamp": candle.timestamp.isoformat(),
                    "equity": portfolio_state["total_equity"]
                })
                
                # Check if we should make a decision
                if i % decision_frequency == 0:
                    if max_decisions and decisions_made >= max_decisions:
                        print(f"Reached max decisions limit: {max_decisions}")
                        break
                    
                    print(f"Making decision at candle {i}/{len(candles)} - {candle.timestamp}")
                    
                    # Prepare market data context
                    market_data = self._prepare_market_data(candles[:i+1], timeframe)
                    
                    # Prepare portfolio data
                    portfolio_data = {
                        "cash_balance": portfolio_state["cash_balance"],
                        "total_equity": portfolio_state["total_equity"],
                        "positions": [
                            {
                                "symbol": sym,
                                "quantity": pos["quantity"],
                                "avg_entry_price": pos["avg_entry_price"],
                                "current_price": current_price if sym == symbol else pos["avg_entry_price"],
                                "unrealized_pnl": pos.get("unrealized_pnl", 0),
                            }
                            for sym, pos in portfolio_state["positions"].items()
                        ],
                    }
                    
                    # Run agent pipeline
                    try:
                        result = pipeline.run(
                            symbol=symbol,
                            market_data=market_data,
                            portfolio_data=portfolio_data,
                            run_id=run_id,
                        )
                        
                        # Extract final decision
                        final_decision = result.get("final_decision")
                        
                        if final_decision and final_decision.get("action") != "HOLD":
                            # Execute trade at next candle's open (simulate slippage)
                            if i + 1 < len(candles):
                                execution_price = float(candles[i + 1].open)
                                
                                portfolio_state = self._execute_backtest_trade(
                                    portfolio_state=portfolio_state,
                                    symbol=symbol,
                                    decision=final_decision,
                                    execution_price=execution_price,
                                    timestamp=candles[i + 1].timestamp,
                                    run_id=run_id,
                                )
                        
                        decisions_made += 1
                        
                    except Exception as e:
                        print(f"Error running pipeline at candle {i}: {e}")
                        continue
            
            # Calculate final metrics
            metrics = self._calculate_metrics(
                equity_curve=equity_curve,
                trades=portfolio_state["trades"],
                initial_cash=initial_cash,
            )
            
            # Update backtest run
            backtest_run.status = "completed"
            backtest_run.final_equity = Decimal(str(portfolio_state["total_equity"]))
            backtest_run.total_return = Decimal(str(metrics["total_return_pct"]))
            backtest_run.max_drawdown = Decimal(str(metrics["max_drawdown_pct"]))
            backtest_run.num_trades = len(portfolio_state["trades"])
            backtest_run.num_decisions = decisions_made
            backtest_run.completed_at = datetime.utcnow()
            self.db.commit()
            
            print(f"Backtest completed: {metrics}")
            
            return {
                "run_id": run_id,
                "symbol": symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "metrics": metrics,
                "equity_curve": equity_curve,
                "trades": portfolio_state["trades"],
                "final_portfolio": {
                    "cash": portfolio_state["cash_balance"],
                    "positions": portfolio_state["positions"],
                    "equity": portfolio_state["total_equity"],
                },
            }
            
        except Exception as e:
            backtest_run.status = "failed"
            backtest_run.error_message = str(e)
            self.db.commit()
            raise
    
    def _load_candles(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
    ) -> List[Candle]:
        """
        Load historical candles from database or fetch from Binance.
        
        Args:
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date
            timeframe: Candle timeframe
            
        Returns:
            List of candles sorted by timestamp
        """
        # Query database first
        candles = (
            self.db.query(Candle)
            .filter(
                Candle.symbol == symbol,
                Candle.timeframe == timeframe,
                Candle.timestamp >= start_date,
                Candle.timestamp <= end_date,
            )
            .order_by(Candle.timestamp)
            .all()
        )
        
        # If we have enough candles, return them
        if candles:
            print(f"Found {len(candles)} candles in database")
            return candles
        
        # Otherwise, fetch from Binance
        print(f"Fetching historical data from Binance...")
        
        klines = self.binance_service.get_historical_klines(
            symbol=symbol,
            interval=timeframe,
            start_time=start_date,
            end_time=end_date,
        )
        
        # Store in database
        candle_objects = []
        for kline in klines:
            candle = Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=kline["timestamp"],
                open=kline["open"],
                high=kline["high"],
                low=kline["low"],
                close=kline["close"],
                volume=kline["volume"],
            )
            candle_objects.append(candle)
        
        self.db.bulk_save_objects(candle_objects)
        self.db.commit()
        
        print(f"Fetched and stored {len(candle_objects)} candles")
        
        return candle_objects
    
    def _prepare_market_data(self, candles: List[Candle], timeframe: str) -> Dict[str, Any]:
        """
        Prepare market data context for agent pipeline.
        
        Args:
            candles: List of historical candles up to current point
            timeframe: Candle timeframe
            
        Returns:
            Market data dict with OHLCV and indicators
        """
        if not candles:
            return {}
        
        current_candle = candles[-1]
        
        # Convert to DataFrame for indicator calculation
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
        
        # Calculate indicators
        indicators = self.indicator_service.calculate_all_indicators(df)
        
        # Get last N candles for context
        recent_candles = candles[-50:] if len(candles) > 50 else candles
        
        return {
            "symbol": current_candle.symbol,
            "timeframe": timeframe,
            "current_price": float(current_candle.close),
            "price_change_24h": self._calculate_price_change_24h(candles),
            "candles": [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "open": float(c.open),
                    "high": float(c.high),
                    "low": float(c.low),
                    "close": float(c.close),
                    "volume": float(c.volume),
                }
                for c in recent_candles
            ],
            "indicators": indicators,
            "sentiment_data": {},  # Mock for now
            "token_data": {},  # Mock for now
        }
    
    def _calculate_price_change_24h(self, candles: List[Candle]) -> float:
        """Calculate 24h price change percentage."""
        if len(candles) < 24:
            return 0.0
        
        current_price = float(candles[-1].close)
        price_24h_ago = float(candles[-24].close)
        
        return ((current_price - price_24h_ago) / price_24h_ago) * 100
    
    def _update_portfolio_mtm(
        self,
        portfolio_state: Dict[str, Any],
        symbol: str,
        current_price: float,
    ) -> Dict[str, Any]:
        """
        Update portfolio mark-to-market values.
        
        Args:
            portfolio_state: Current portfolio state
            symbol: Symbol to update
            current_price: Current market price
            
        Returns:
            Updated portfolio state
        """
        if symbol in portfolio_state["positions"]:
            position = portfolio_state["positions"][symbol]
            position["unrealized_pnl"] = (
                (current_price - position["avg_entry_price"]) * position["quantity"]
            )
        
        # Calculate total equity
        total_equity = portfolio_state["cash_balance"]
        for pos_symbol, pos in portfolio_state["positions"].items():
            if pos_symbol == symbol:
                total_equity += pos["quantity"] * current_price
            else:
                total_equity += pos["quantity"] * pos["avg_entry_price"]
        
        portfolio_state["total_equity"] = total_equity
        
        return portfolio_state
    
    def _execute_backtest_trade(
        self,
        portfolio_state: Dict[str, Any],
        symbol: str,
        decision: Dict[str, Any],
        execution_price: float,
        timestamp: datetime,
        run_id: str,
    ) -> Dict[str, Any]:
        """
        Execute a simulated trade in the backtest.
        
        Args:
            portfolio_state: Current portfolio state
            symbol: Trading pair symbol
            decision: Trade decision from agents
            execution_price: Price to execute at
            timestamp: Trade timestamp
            run_id: Backtest run ID
            
        Returns:
            Updated portfolio state
        """
        action = decision.get("action")
        size_pct = decision.get("size_pct", 0.05)
        
        if action == "BUY":
            # Calculate quantity to buy based on available cash (not total equity)
            # This prevents trying to buy with money tied up in positions
            allocation = portfolio_state["cash_balance"] * size_pct
            quantity = allocation / execution_price
            cost = quantity * execution_price
            
            # Ensure we don't exceed available cash (with small buffer for rounding)
            if cost > portfolio_state["cash_balance"] * 1.0001:
                print(f"Insufficient cash for BUY: need ${cost:.2f}, have ${portfolio_state['cash_balance']:.2f}")
                return portfolio_state
            
            # Update cash
            portfolio_state["cash_balance"] -= cost
            
            # Update position
            if symbol not in portfolio_state["positions"]:
                portfolio_state["positions"][symbol] = {
                    "quantity": quantity,
                    "avg_entry_price": execution_price,
                    "unrealized_pnl": 0,
                }
            else:
                # Average in
                pos = portfolio_state["positions"][symbol]
                total_quantity = pos["quantity"] + quantity
                pos["avg_entry_price"] = (
                    (pos["quantity"] * pos["avg_entry_price"] + cost) / total_quantity
                )
                pos["quantity"] = total_quantity
            
            # Record trade
            trade = Trade(
                symbol=symbol,
                side="BUY",
                quantity=Decimal(str(quantity)),
                price=Decimal(str(execution_price)),
                timestamp=timestamp,
                run_id=run_id,
            )
            self.db.add(trade)
            self.db.commit()
            
            portfolio_state["trades"].append({
                "symbol": symbol,
                "side": "BUY",
                "quantity": quantity,
                "price": execution_price,
                "timestamp": timestamp.isoformat(),
            })
            
            print(f"BUY {quantity:.6f} {symbol} @ ${execution_price:.2f}")
            
        elif action == "SELL":
            if symbol not in portfolio_state["positions"]:
                print(f"No position to SELL for {symbol}")
                return portfolio_state
            
            pos = portfolio_state["positions"][symbol]
            sell_quantity = pos["quantity"] * size_pct  # Sell a portion
            
            if sell_quantity <= 0:
                return portfolio_state
            
            # Calculate PnL
            proceeds = sell_quantity * execution_price
            cost_basis = sell_quantity * pos["avg_entry_price"]
            realized_pnl = proceeds - cost_basis
            
            # Update cash
            portfolio_state["cash_balance"] += proceeds
            
            # Update position
            pos["quantity"] -= sell_quantity
            
            if pos["quantity"] < 0.0001:  # Close position if negligible
                del portfolio_state["positions"][symbol]
            
            # Record trade
            trade = Trade(
                symbol=symbol,
                side="SELL",
                quantity=Decimal(str(sell_quantity)),
                price=Decimal(str(execution_price)),
                timestamp=timestamp,
                pnl=Decimal(str(realized_pnl)),
                run_id=run_id,
            )
            self.db.add(trade)
            self.db.commit()
            
            portfolio_state["trades"].append({
                "symbol": symbol,
                "side": "SELL",
                "quantity": sell_quantity,
                "price": execution_price,
                "pnl": realized_pnl,
                "timestamp": timestamp.isoformat(),
            })
            
            print(f"SELL {sell_quantity:.6f} {symbol} @ ${execution_price:.2f} (PnL: ${realized_pnl:.2f})")
        
        return portfolio_state
    
    def _calculate_metrics(
        self,
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        initial_cash: float,
    ) -> Dict[str, Any]:
        """
        Calculate backtest performance metrics.
        
        Args:
            equity_curve: List of equity snapshots over time
            trades: List of executed trades
            initial_cash: Starting cash amount
            
        Returns:
            Dict with performance metrics
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                "total_return_pct": 0,
                "max_drawdown_pct": 0,
                "sharpe_ratio": 0,
                "win_rate_pct": 0,
                "num_trades": 0,
                "avg_trade_pnl": 0,
            }
        
        final_equity = equity_curve[-1]["equity"]
        
        # Total return
        total_return_pct = ((final_equity - initial_cash) / initial_cash) * 100
        
        # Max drawdown
        max_equity = initial_cash
        max_drawdown = 0
        
        for point in equity_curve:
            equity = point["equity"]
            if equity > max_equity:
                max_equity = equity
            drawdown = (max_equity - equity) / max_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_pct = max_drawdown * 100
        
        # Trade statistics
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        win_rate_pct = (len(winning_trades) / len(trades) * 100) if trades else 0
        
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        avg_trade_pnl = total_pnl / len(trades) if trades else 0
        
        # Sharpe ratio (simplified daily returns)
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i]["equity"] - equity_curve[i-1]["equity"]) / equity_curve[i-1]["equity"]
            returns.append(ret)
        
        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "win_rate_pct": round(win_rate_pct, 2),
            "num_trades": len(trades),
            "avg_trade_pnl": round(avg_trade_pnl, 2),
            "final_equity": round(final_equity, 2),
        }
