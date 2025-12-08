"""
Agent Recommendations API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.database import AgentRecommendation, PaperOrder
from app.services.paper_trading import PaperTradingService
from app.core.config import settings

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationResponse(BaseModel):
    id: int
    run_id: str
    symbol: str
    action: str
    quantity: Optional[float]
    price: float
    confidence: Optional[float]
    reasoning: Optional[str]
    status: str
    decision_type: str
    strategy_name: Optional[str]
    executed_order_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ExecuteRecommendationRequest(BaseModel):
    order_type: str = "MARKET"  # MARKET, LIMIT
    limit_price: Optional[float] = None
    time_in_force: str = "GTC"


@router.get("", response_model=List[RecommendationResponse])
async def get_recommendations(
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get agent recommendations.
    
    Args:
        status: Filter by status (pending, executed, rejected, expired)
        symbol: Filter by symbol
        limit: Maximum number to return
    """
    query = db.query(AgentRecommendation)
    
    if status:
        query = query.filter(AgentRecommendation.status == status)
    if symbol:
        query = query.filter(AgentRecommendation.symbol == symbol.upper())
    
    recommendations = query.order_by(desc(AgentRecommendation.created_at)).limit(limit).all()
    
    return recommendations


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific recommendation by ID."""
    rec = db.query(AgentRecommendation).filter(AgentRecommendation.id == recommendation_id).first()
    
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return rec


@router.post("/{recommendation_id}/execute")
async def execute_recommendation(
    recommendation_id: int,
    request: ExecuteRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a pending recommendation by creating a paper trading order.
    """
    # Get recommendation
    rec = db.query(AgentRecommendation).filter(AgentRecommendation.id == recommendation_id).first()
    
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation already {rec.status}")
    
    if rec.action == "HOLD":
        raise HTTPException(status_code=400, detail="Cannot execute HOLD recommendation")
    
    # Check if paper trading is enabled
    if not settings.paper_trading_enabled or settings.paper_trading_mode != "testnet":
        raise HTTPException(status_code=503, detail="Paper trading not enabled")
    
    try:
        # Create paper trading service
        paper_service = PaperTradingService(db)
        
        # Execute order on testnet
        order = await paper_service.create_order(
            symbol=rec.symbol,
            side=rec.action,
            order_type=request.order_type,
            quantity=rec.quantity,
            price=request.limit_price if request.order_type == "LIMIT" else None,
            time_in_force=request.time_in_force,
            run_id=rec.run_id,
        )
        
        # Update recommendation status
        rec.status = "executed"
        rec.executed_order_id = order.id
        rec.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Recommendation executed successfully",
            "recommendation_id": rec.id,
            "order_id": order.id,
            "binance_order_id": order.binance_order_id,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute recommendation: {str(e)}")


@router.post("/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """
    Reject a pending recommendation.
    """
    rec = db.query(AgentRecommendation).filter(AgentRecommendation.id == recommendation_id).first()
    
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation already {rec.status}")
    
    rec.status = "rejected"
    rec.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Recommendation rejected",
        "recommendation_id": rec.id,
    }
