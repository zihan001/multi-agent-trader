"""
Analysis API endpoints for running the agent pipeline.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.agents.pipeline import AgentPipeline
from app.services.binance import BinanceService, get_latest_candles
from app.services.indicators import IndicatorService
from app.services.portfolio import PortfolioManager
import pandas as pd

router = APIRouter(prefix="/analyze", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    """Request model for analysis endpoint."""
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    mode: str = Field(default="live", description="Analysis mode: 'live' or 'backtest_step'")
    timestamp: Optional[str] = Field(None, description="Optional timestamp for backtest mode (ISO format)")
    timeframe: str = Field(default="1h", description="Candle timeframe")


class AnalyzeResponse(BaseModel):
    """Response model for analysis endpoint."""
    run_id: str
    symbol: str
    timestamp: str
    status: str
    agents: Dict[str, Any]
    final_decision: Optional[Dict[str, Any]]
    total_cost: float
    total_tokens: int
    portfolio_snapshot: Dict[str, Any]
    errors: list


@router.post("", response_model=AnalyzeResponse)
async def run_analysis(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Run the full agent pipeline for market analysis and trading decision.
    
    This endpoint:
    1. Fetches latest market data for the symbol
    2. Calculates technical indicators
    3. Runs all agents (Technical, Sentiment, Tokenomics, Researcher, Trader, Risk)
    4. Executes approved trades (simulated)
    5. Updates portfolio
    6. Returns comprehensive analysis results
    
    Args:
        request: Analysis request parameters
        db: Database session
        
    Returns:
        Complete analysis results with agent outputs and final decision
    """
    try:
        # Validate symbol
        symbol = request.symbol.upper()
        
        # Fetch latest market data
        binance_service = BinanceService()
        
        try:
            # Get recent candles (last 100 for indicators)
            candles = get_latest_candles(db, symbol, request.timeframe, limit=100)
            
            # If not enough candles in DB, fetch from Binance
            if len(candles) < 50:
                print(f"Fetching fresh data for {symbol} from Binance...")
                klines = await binance_service.fetch_klines(
                    symbol=symbol,
                    interval=request.timeframe,
                    limit=100
                )
                
                # Convert to DataFrame for processing
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
                # Convert candles to DataFrame
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
            
            # Get latest ticker for 24h data
            ticker_24h = await binance_service.fetch_24h_ticker(symbol)
            
        finally:
            await binance_service.close()
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No market data found for {symbol}")
        
        # Calculate technical indicators
        indicator_service = IndicatorService()
        indicators = indicator_service.calculate_all_indicators(df)
        
        # Prepare market data context
        current_price = float(df.iloc[-1]["close"])
        price_change_24h = float(ticker_24h.get("priceChangePercent", 0))
        
        market_data = {
            "symbol": symbol,
            "timeframe": request.timeframe,
            "current_price": current_price,
            "price_change_24h": price_change_24h,
            "volume_24h": float(ticker_24h.get("volume", 0)),
            "candles": df.tail(50).to_dict(orient="records"),
            "indicators": indicators,
            "sentiment_data": {},  # Mock for now
            "token_data": {},  # Mock for now
        }
        
        # Get current portfolio state
        portfolio_manager = PortfolioManager(db)
        portfolio_data = portfolio_manager.get_portfolio_state()
        
        # Run agent pipeline
        pipeline = AgentPipeline(db)
        
        result = await pipeline.arun(
            symbol=symbol,
            market_data=market_data,
            portfolio_data=portfolio_data,
            run_id=None,  # Auto-generate
        )
        
        # Execute approved trade if action is not HOLD
        final_decision = result.get("final_decision")
        
        if final_decision and final_decision.get("action") != "HOLD":
            try:
                portfolio_manager.execute_trade(
                    symbol=symbol,
                    side=final_decision["action"],
                    quantity=final_decision.get("quantity", 0),
                    price=current_price,
                    run_id=result["run_id"],
                )
                print(f"Executed trade: {final_decision['action']} {symbol}")
            except Exception as trade_error:
                print(f"Error executing trade: {trade_error}")
                result["errors"].append({
                    "type": "trade_execution_error",
                    "message": str(trade_error)
                })
        
        # Get updated portfolio
        updated_portfolio = portfolio_manager.get_portfolio_state()
        
        return AnalyzeResponse(
            run_id=result["run_id"],
            symbol=result["symbol"],
            timestamp=result["timestamp"],
            status=result["status"],
            agents=result["agents"],
            final_decision=result["final_decision"],
            total_cost=result["total_cost"],
            total_tokens=result["total_tokens"],
            portfolio_snapshot=updated_portfolio,
            errors=result["errors"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/status/{run_id}")
async def get_analysis_status(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the status and results of a previous analysis run.
    
    Args:
        run_id: Run identifier
        db: Database session
        
    Returns:
        Analysis run status and results
    """
    # Query agent logs for this run
    from app.models.database import AgentLog
    
    logs = db.query(AgentLog).filter(AgentLog.run_id == run_id).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return {
        "run_id": run_id,
        "num_logs": len(logs),
        "agents": list(set(log.agent_name for log in logs)),
        "total_tokens": sum(log.tokens_used or 0 for log in logs),
        "total_cost": sum(float(log.cost or 0) for log in logs),
        "logs": [
            {
                "timestamp": log.timestamp.isoformat(),
                "agent_name": log.agent_name,
                "model": log.model,
                "tokens": log.tokens_used,
                "cost": float(log.cost or 0),
            }
            for log in logs
        ]
    }
