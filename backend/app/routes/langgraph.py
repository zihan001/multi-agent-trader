"""
LangGraph workflow API endpoint.

This provides a new /analyze-v2 endpoint that uses the LangGraph orchestration
instead of the original pipeline.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.langchain.graph import TradingWorkflow, GraphConfig


router = APIRouter(prefix="/analyze-v2", tags=["langgraph"])


class AnalyzeRequestV2(BaseModel):
    """Request for LangGraph-based analysis."""
    symbol: str
    timeframe: str = "1h"
    mode: str = "live"
    
    # Graph configuration overrides
    min_confidence_to_trade: Optional[int] = None
    enable_rag: Optional[bool] = True
    run_analysts_parallel: Optional[bool] = True
    require_approval_above_risk: Optional[int] = None


@router.post("")
async def run_langgraph_analysis(
    request: AnalyzeRequestV2,
    db: Session = Depends(get_db),
):
    """
    Run LangGraph-based multi-agent analysis.
    
    This endpoint uses the advanced LangGraph workflow with:
    - Conditional routing based on confidence
    - Parallel analyst execution
    - RAG-enhanced context from historical data
    - Human-in-the-loop for high-risk trades
    - State management and checkpointing
    
    **Advantages over /analyze:**
    - More intelligent routing (skips unnecessary steps)
    - Learns from past trades via RAG
    - Production-ready approval flows
    - Better error handling and retry logic
    - Transparent state inspection
    
    Args:
        request: Analysis request
        db: Database session
        
    Returns:
        Complete workflow state with all decisions
    """
    try:
        # Build config from request
        config = GraphConfig()
        if request.min_confidence_to_trade is not None:
            config.min_confidence_to_trade = request.min_confidence_to_trade
        if request.enable_rag is not None:
            config.enable_rag = request.enable_rag
        if request.run_analysts_parallel is not None:
            config.run_analysts_parallel = request.run_analysts_parallel
        if request.require_approval_above_risk is not None:
            config.require_approval_above_risk = request.require_approval_above_risk
        
        # Create workflow
        workflow = TradingWorkflow(
            db=db,
            config=config,
            enable_rag=request.enable_rag,
        )
        
        # Run workflow
        result = await workflow.run(
            symbol=request.symbol,
            timeframe=request.timeframe,
            mode=request.mode,
        )
        
        return {
            "status": "success",
            "workflow": "langgraph_v2",
            "result": result,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
def get_default_config():
    """Get default graph configuration."""
    config = GraphConfig()
    return config.model_dump()
