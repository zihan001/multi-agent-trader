"""
Analysis API endpoints for running decision engines.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.engines.factory import DecisionEngineFactory
from app.models.decisions import AnalysisRequest, AnalysisResponse, DecisionResult
from app.models.database import AgentRecommendation
from app.services.binance import BinanceService, get_latest_candles
from app.services.indicators import IndicatorService
from app.services.portfolio import PortfolioManager
from app.services.paper_trading import PaperTradingService
from app.core.config import settings
import pandas as pd

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Run decision engine for market analysis and trading decision.
    
    This endpoint:
    1. Fetches latest market data for the symbol
    2. Calculates technical indicators
    3. Runs decision engine (LLM agents OR rule-based strategy)
    4. Executes approved trades (simulated)
    5. Updates portfolio
    6. Returns comprehensive analysis results
    
    The engine type is determined by settings.trading_mode:
    - "llm": Six-agent LLM system with natural language reasoning
    - "rule": Deterministic technical indicator strategies (zero cost)
    
    Args:
        request: Analysis request parameters
        db: Database session
        
    Returns:
        AnalysisResponse with unified decision result
    """
    try:
        # Validate symbol
        symbol = request.symbol.upper()
        timeframe = "1h"  # Default timeframe for analysis
        
        # Fetch latest market data
        binance_service = BinanceService()
        
        try:
            # Get recent candles (last 100 for indicators)
            candles = get_latest_candles(db, symbol, timeframe, limit=100)
            
            # If not enough candles in DB, fetch from Binance
            if len(candles) < 50:
                print(f"Fetching fresh data for {symbol} from Binance...")
                klines = await binance_service.fetch_klines(
                    symbol=symbol,
                    interval=timeframe,
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
            "timeframe": timeframe,
            "current_price": current_price,
            "price_change_24h": price_change_24h,
            "volume_24h": float(ticker_24h.get("volume", 0)),
            "candles": df.tail(50).to_dict(orient="records"),
            "indicators": indicators,
            "sentiment_data": {},  # Mock for now
            "token_data": {},  # Mock for now
        }
        
        # Get current portfolio state (always use simulation for portfolio tracking)
        portfolio_manager = PortfolioManager(db, use_paper_trading=False)
        portfolio_data = portfolio_manager.get_portfolio_summary()
        
        # Create decision engine using factory pattern
        engine = DecisionEngineFactory.create(db)
        
        # Generate run ID
        run_id = f"run_{datetime.utcnow().isoformat()}"
        
        # Run decision engine (works for both LLM and rule modes)
        result: DecisionResult = await engine.aanalyze(
            symbol=symbol,
            market_data=market_data,
            portfolio_data=portfolio_data,
            run_id=run_id,
        )
        
        # Store recommendation in database (not auto-executed)
        recommendation = None
        decision = result.decision
        
        if decision.action in ["BUY", "SELL", "HOLD"]:
            try:
                # Extract reasoning from agent outputs
                reasoning_parts = []
                if result.technical_analysis:
                    reasoning_parts.append(f"Technical: {result.technical_analysis.get('reasoning', '')}")
                if result.sentiment_analysis:
                    reasoning_parts.append(f"Sentiment: {result.sentiment_analysis.get('reasoning', '')}")
                if result.risk_analysis:
                    reasoning_parts.append(f"Risk: {result.risk_analysis.get('reasoning', '')}")
                
                reasoning = " | ".join(reasoning_parts) if reasoning_parts else decision.reasoning
                
                # Create recommendation record
                rec = AgentRecommendation(
                    run_id=run_id,
                    symbol=symbol,
                    action=decision.action,
                    quantity=decision.quantity if decision.action != "HOLD" else None,
                    price=current_price,
                    confidence=decision.confidence,
                    reasoning=reasoning,
                    status="pending",
                    decision_type=settings.trading_mode,  # "llm" or "rule"
                    strategy_name=decision.strategy if hasattr(decision, 'strategy') else None,
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                
                recommendation = {
                    "id": rec.id,
                    "symbol": rec.symbol,
                    "action": rec.action,
                    "quantity": rec.quantity,
                    "price": rec.price,
                    "confidence": rec.confidence,
                    "reasoning": rec.reasoning,
                    "status": rec.status,
                    "created_at": rec.created_at.isoformat(),
                }
                
                print(f"[{run_id}] Stored recommendation: {decision.action} {decision.quantity} {symbol} (ID: {rec.id})")
            except Exception as rec_error:
                print(f"[{run_id}] Error storing recommendation: {rec_error}")
                result.errors.append({
                    "type": "recommendation_storage_error",
                    "message": str(rec_error)
                })
        
        # Get portfolio (unchanged by this analysis)
        portfolio = portfolio_manager.get_portfolio_summary()
        
        return AnalysisResponse(
            result=result,
            portfolio_updated=False,  # No auto-execution
            recommendation=recommendation,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        from app.agents.llm_client import BudgetExceededError
        
        # Handle specific error types
        error_detail = str(e)
        status_code = 500
        
        if isinstance(e, BudgetExceededError):
            status_code = 429
            error_detail = f"Daily LLM token budget exceeded. {str(e)} Please try again tomorrow or contact admin to increase budget."
        elif "rate" in error_detail.lower() and "limit" in error_detail.lower():
            status_code = 429
            error_detail = f"Rate limit exceeded from LLM provider. Please wait a moment and try again. Details: {error_detail}"
        elif "timeout" in error_detail.lower():
            status_code = 504
            error_detail = f"Analysis timed out. The LLM provider may be experiencing high load. Please try again. Details: {error_detail}"
        elif "authentication" in error_detail.lower() or "api key" in error_detail.lower():
            status_code = 503
            error_detail = "LLM service authentication failed. Please contact administrator."
        
        raise HTTPException(
            status_code=status_code,
            detail=error_detail
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
