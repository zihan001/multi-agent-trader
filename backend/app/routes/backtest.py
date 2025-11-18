"""
Backtesting API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.database import get_db
from app.services.backtest import BacktestEngine
from app.models.database import BacktestRun

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    """Request model for backtest endpoint."""
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    start_date: str = Field(..., description="Start date in ISO format (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date in ISO format (YYYY-MM-DD)")
    timeframe: str = Field(default="1h", description="Candle timeframe (1h, 4h, 1d, etc.)")
    initial_cash: float = Field(default=10000.0, description="Starting cash balance")
    decision_frequency: int = Field(default=4, description="Run pipeline every N candles")
    max_decisions: Optional[int] = Field(None, description="Maximum number of decisions (cost control)")


class BacktestMetrics(BaseModel):
    """Backtest performance metrics."""
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate_pct: float
    num_trades: int
    avg_trade_pnl: float
    final_equity: float


class BacktestResponse(BaseModel):
    """Response model for backtest endpoint."""
    run_id: str
    symbol: str
    start_date: str
    end_date: str
    metrics: BacktestMetrics
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    final_portfolio: Dict[str, Any]


@router.post("", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db)
):
    """
    Run a historical backtest simulation.
    
    This endpoint:
    1. Loads historical market data from the database or fetches from Binance
    2. Simulates the agent pipeline over time at specified intervals
    3. Executes simulated trades at historical prices
    4. Calculates comprehensive performance metrics
    5. Returns equity curve and trade history
    
    Args:
        request: Backtest configuration parameters
        db: Database session
        
    Returns:
        Complete backtest results with metrics, equity curve, and trades
    """
    try:
        # Parse dates
        try:
            start_date = datetime.fromisoformat(request.start_date)
            end_date = datetime.fromisoformat(request.end_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
            )
        
        # Validate dates
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )
        
        # Validate symbol
        symbol = request.symbol.upper()
        
        # Estimate cost and warn user
        if request.max_decisions:
            estimated_cost = request.max_decisions * 0.05  # Rough estimate
            print(f"Estimated cost for {request.max_decisions} decisions: ~${estimated_cost:.2f}")
        
        # Initialize backtest engine
        engine = BacktestEngine(db)
        
        # Run backtest
        print(f"Starting backtest for {symbol} from {start_date} to {end_date}")
        
        result = engine.run_backtest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=request.timeframe,
            initial_cash=request.initial_cash,
            decision_frequency=request.decision_frequency,
            max_decisions=request.max_decisions,
        )
        
        print(f"Backtest completed: {result['metrics']}")
        
        return BacktestResponse(
            run_id=result["run_id"],
            symbol=result["symbol"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            metrics=BacktestMetrics(**result["metrics"]),
            equity_curve=result["equity_curve"],
            trades=result["trades"],
            final_portfolio=result["final_portfolio"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backtest failed: {str(e)}"
        )


@router.get("/runs", response_model=List[Dict[str, Any]])
async def list_backtest_runs(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List historical backtest runs.
    
    Args:
        symbol: Optional filter by symbol
        status: Optional filter by status (running, completed, failed)
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of backtest run summaries
    """
    query = db.query(BacktestRun)
    
    if symbol:
        query = query.filter(BacktestRun.symbol == symbol.upper())
    
    if status:
        query = query.filter(BacktestRun.status == status)
    
    runs = query.order_by(BacktestRun.created_at.desc()).limit(limit).all()
    
    return [
        {
            "run_id": run.run_id,
            "symbol": run.symbol,
            "start_date": run.start_date.isoformat(),
            "end_date": run.end_date.isoformat(),
            "timeframe": run.timeframe,
            "status": run.status,
            "total_return": float(run.total_return) if run.total_return else None,
            "max_drawdown": float(run.max_drawdown) if run.max_drawdown else None,
            "num_trades": run.num_trades,
            "num_decisions": run.num_decisions,
            "created_at": run.created_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }
        for run in runs
    ]


@router.get("/runs/{run_id}")
async def get_backtest_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific backtest run.
    
    Args:
        run_id: Backtest run identifier
        db: Database session
        
    Returns:
        Backtest run details
    """
    run = db.query(BacktestRun).filter(BacktestRun.run_id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail=f"Backtest run {run_id} not found")
    
    # Get trades from this run
    from app.models.database import Trade
    trades = db.query(Trade).filter(Trade.run_id == run_id).all()
    
    # Get agent logs from this run
    from app.models.database import AgentLog
    logs = db.query(AgentLog).filter(AgentLog.run_id == run_id).all()
    
    return {
        "run_id": run.run_id,
        "symbol": run.symbol,
        "start_date": run.start_date.isoformat(),
        "end_date": run.end_date.isoformat(),
        "timeframe": run.timeframe,
        "initial_cash": float(run.initial_cash),
        "decision_frequency": run.decision_frequency,
        "max_decisions": run.max_decisions,
        "status": run.status,
        "final_equity": float(run.final_equity) if run.final_equity else None,
        "total_return": float(run.total_return) if run.total_return else None,
        "max_drawdown": float(run.max_drawdown) if run.max_drawdown else None,
        "num_trades": run.num_trades,
        "num_decisions": run.num_decisions,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "trades": [
            {
                "symbol": t.symbol,
                "side": t.side,
                "quantity": float(t.quantity),
                "price": float(t.price),
                "pnl": float(t.pnl) if t.pnl else None,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in trades
        ],
        "agent_logs": {
            "num_calls": len(logs),
            "total_tokens": sum(log.tokens_used or 0 for log in logs),
            "total_cost": sum(float(log.cost or 0) for log in logs),
        }
    }


@router.delete("/runs/{run_id}")
async def delete_backtest_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a backtest run and its associated data.
    
    Args:
        run_id: Backtest run identifier
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    run = db.query(BacktestRun).filter(BacktestRun.run_id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail=f"Backtest run {run_id} not found")
    
    # Delete associated trades
    from app.models.database import Trade
    db.query(Trade).filter(Trade.run_id == run_id).delete()
    
    # Delete associated agent logs
    from app.models.database import AgentLog
    db.query(AgentLog).filter(AgentLog.run_id == run_id).delete()
    
    # Delete the run
    db.delete(run)
    db.commit()
    
    return {"message": f"Backtest run {run_id} deleted successfully"}
