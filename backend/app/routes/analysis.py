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
from app.services.sentiment import SentimentService
from app.services.tokenomics import TokenomicsService
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
    
    The engine type can be specified via engine_mode parameter:
    - \"llm\": Six-agent LLM system with natural language reasoning (requires LLM_API_KEY)
    - \"rule\": Deterministic technical indicator strategies (zero cost, always available)
    - If not specified, defaults to LLM if API key configured, otherwise rule-based
    
    Args:
        request: Analysis request parameters (symbol, mode, engine_mode)
        db: Database session
        
    Returns:
        AnalysisResponse with unified decision result
    """
    try:
        # Validate symbol and timeframe
        symbol = request.symbol.upper()
        timeframe = request.timeframe
        
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
        volume_24h = float(ticker_24h.get("volume", 0))
        
        # Calculate average volume (7-day)
        avg_volume = float(df.tail(7)["volume"].mean()) if len(df) >= 7 else volume_24h
        
        # Fetch real sentiment data
        sentiment_service = SentimentService(db)
        try:
            sentiment_data = await sentiment_service.get_comprehensive_sentiment(
                symbol=symbol,
                current_price=current_price,
                price_change_24h=price_change_24h,
                volume_24h=volume_24h,
                avg_volume=avg_volume,
                indicators=indicators
            )
        except Exception as e:
            print(f"Warning: Failed to fetch sentiment data: {e}")
            sentiment_data = {}  # Fallback to empty
        finally:
            await sentiment_service.close()
        
        # Fetch real tokenomics data
        tokenomics_service = TokenomicsService(db)
        try:
            # Calculate market cap from Binance data if available
            ticker_market_cap = float(ticker_24h.get("quoteVolume", 0)) * current_price if ticker_24h else 0
            
            token_data = await tokenomics_service.get_comprehensive_tokenomics(
                symbol=symbol,
                current_price=current_price,
                market_cap=ticker_market_cap,
                volume_24h=volume_24h
            )
        except Exception as e:
            print(f"Warning: Failed to fetch tokenomics data: {e}")
            token_data = {}  # Fallback to empty
        finally:
            await tokenomics_service.close()
        
        market_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": current_price,
            "price_change_24h": price_change_24h,
            "volume_24h": volume_24h,
            "candles": df.tail(50).to_dict(orient="records"),
            "indicators": indicators,
            "sentiment_data": sentiment_data,
            "token_data": token_data,
        }
        
        # Use run_id from request or default to "live" for production trading
        run_id = request.run_id if request.run_id else "live"
        
        # Get current portfolio state (always use simulation for portfolio tracking)
        portfolio_manager = PortfolioManager(db, run_id=run_id, use_paper_trading=False)
        portfolio_data = portfolio_manager.get_portfolio_summary()
        print(f"[{run_id}] Portfolio data: cash={portfolio_data['summary']['cash_balance']}, equity={portfolio_data['summary']['total_equity']}")
        
        # Validate engine mode if provided
        engine_mode = request.engine_mode
        if engine_mode:
            # Check if LLM mode is requested but not available
            llm_enabled = bool(settings.llm_api_key and settings.llm_api_key != "")
            if engine_mode == "llm" and not llm_enabled:
                raise HTTPException(
                    status_code=400,
                    detail="LLM mode is not available. Please configure LLM_API_KEY or use 'rule' mode."
                )
            if engine_mode not in ["llm", "rule"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid engine_mode '{engine_mode}'. Must be 'llm' or 'rule'."
                )
        
        # Create decision engine using factory pattern
        engine = DecisionEngineFactory.create(
            db, 
            trading_mode=engine_mode, 
            use_react=request.use_react,
            use_langchain=request.use_langchain
        )
        
        # Log which engine is being used
        agent_mode = " [LangChain Agents]" if request.use_langchain else (" [ReAct Mode]" if request.use_react else "")
        print(f"[{run_id}] Using engine: {engine.engine_type}{agent_mode} (requested mode: {engine_mode}, default: {settings.default_engine_mode})")
        
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
        
        # Normalize action to uppercase for consistency
        if decision.action:
            decision.action = decision.action.upper()
        
        if decision.action in ["BUY", "SELL", "HOLD"]:
            try:
                # Extract reasoning from all 6 agent outputs
                reasoning_parts = []
                
                print(f"[{run_id}] Extracting reasoning from agents...")
                print(f"[{run_id}] result.agents type: {type(result.agents)}")
                print(f"[{run_id}] result.agents keys: {list(result.agents.keys()) if result.agents else 'None'}")
                
                # Helper function to safely get reasoning from agent
                def get_agent_reasoning(agent_output, *keys):
                    """Extract reasoning from AgentOutput.analysis dict, trying multiple keys"""
                    if not agent_output:
                        return ''
                    analysis = getattr(agent_output, 'analysis', {})
                    for key in keys:
                        value = analysis.get(key, '')
                        if value:
                            return value
                    return ''
                
                # Technical Analyst
                tech_reasoning = get_agent_reasoning(result.agents.get('technical'), 'reasoning')
                print(f"[{run_id}] Technical reasoning length: {len(tech_reasoning)}")
                if tech_reasoning:
                    reasoning_parts.append(f"Technical: {tech_reasoning}")
                
                # Sentiment Analyst
                sent_reasoning = get_agent_reasoning(result.agents.get('sentiment'), 'reasoning')
                if sent_reasoning:
                    reasoning_parts.append(f"Sentiment: {sent_reasoning}")
                
                # Tokenomics Analyst
                token_reasoning = get_agent_reasoning(result.agents.get('tokenomics'), 'reasoning')
                if token_reasoning:
                    reasoning_parts.append(f"Tokenomics: {token_reasoning}")
                
                # Researcher
                research_reasoning = get_agent_reasoning(result.agents.get('researcher'), 'investment_thesis', 'primary_rationale')
                if research_reasoning:
                    reasoning_parts.append(f"Researcher: {research_reasoning}")
                
                # Trader
                trader_reasoning = get_agent_reasoning(result.agents.get('trader'), 'reasoning', 'market_conditions')
                if trader_reasoning:
                    reasoning_parts.append(f"Trader: {trader_reasoning}")
                
                # Risk Manager
                risk_reasoning = get_agent_reasoning(result.agents.get('risk_manager'), 'reasoning')
                if risk_reasoning:
                    reasoning_parts.append(f"Risk: {risk_reasoning}")
                
                reasoning = " | ".join(reasoning_parts) if reasoning_parts else decision.reasoning
                
                # Extract risk management fields from decision metadata
                stop_loss = None
                take_profit = None
                position_size_pct = None
                time_horizon = None
                
                # Try to extract from decision metadata (populated by engines)
                if hasattr(decision, 'stop_loss'):
                    stop_loss = decision.stop_loss
                if hasattr(decision, 'take_profit'):
                    take_profit = decision.take_profit
                if hasattr(decision, 'position_size_pct'):
                    position_size_pct = decision.position_size_pct
                if hasattr(decision, 'time_horizon'):
                    time_horizon = decision.time_horizon
                
                # Calculate defaults if not provided
                if decision.action == "BUY" and not stop_loss:
                    # Default SL: 5% below entry
                    stop_loss = current_price * 0.95
                elif decision.action == "SELL" and not stop_loss:
                    # Default SL: 5% above entry
                    stop_loss = current_price * 1.05
                
                if decision.action in ["BUY", "SELL"] and not take_profit:
                    # Default TP: 10% profit target
                    if decision.action == "BUY":
                        take_profit = current_price * 1.10
                    else:
                        take_profit = current_price * 0.90
                
                if not position_size_pct and decision.quantity:
                    # Calculate position size % from quantity
                    total_equity = portfolio_data.get("total_equity", 0)
                    if total_equity > 0:
                        position_value = decision.quantity * current_price
                        position_size_pct = position_value / total_equity
                
                # Default time horizon based on strategy/mode
                if not time_horizon:
                    time_horizon = "4h"  # Default to 4-hour horizon
                
                # Determine the actual engine type used (from metadata or request)
                actual_engine_type = result.metadata.engine_type if result.metadata else (engine_mode or settings.default_engine_mode)
                
                print(f"[{run_id}] Storing recommendation with decision_type: {actual_engine_type} (from metadata: {result.metadata.engine_type if result.metadata else 'N/A'})")
                
                # Create recommendation record
                rec = AgentRecommendation(
                    run_id=run_id,
                    symbol=symbol,
                    action=decision.action,
                    quantity=decision.quantity if decision.action != "HOLD" else None,
                    price=current_price,
                    confidence=decision.confidence,
                    reasoning=reasoning,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size_pct=position_size_pct,
                    time_horizon=time_horizon,
                    status="pending",
                    decision_type=actual_engine_type,  # Use actual engine type from metadata
                    strategy_name=decision.strategy if hasattr(decision, 'strategy') else None,
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                
                print(f"[{run_id}] Recommendation stored with ID: {rec.id}, decision_type: {rec.decision_type}")
                
                recommendation = {
                    "id": rec.id,
                    "symbol": rec.symbol,
                    "action": rec.action,
                    "quantity": rec.quantity,
                    "price": rec.price,
                    "confidence": rec.confidence,
                    "reasoning": rec.reasoning,
                    "stop_loss": rec.stop_loss,
                    "take_profit": rec.take_profit,
                    "position_size_pct": rec.position_size_pct,
                    "time_horizon": rec.time_horizon,
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
