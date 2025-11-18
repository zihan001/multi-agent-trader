"""
Portfolio management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.database import get_db
from app.services.portfolio import PortfolioManager, initialize_portfolio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TradeRequest(BaseModel):
    """Request model for executing a trade."""
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: float


@router.get("")
async def get_portfolio(
    run_id: str = Query(default="live"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current portfolio state including positions, cash, and equity.
    """
    try:
        pm = PortfolioManager(db, run_id)
        summary = pm.get_portfolio_summary()
        return summary
    
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving portfolio: {str(e)}"
        )


@router.post("/initialize")
async def init_portfolio(
    run_id: str = Query(default="live"),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Initialize a new portfolio with starting cash.
    """
    try:
        initialize_portfolio(db, run_id)
        return {
            "message": f"Portfolio {run_id} initialized successfully",
            "run_id": run_id
        }
    
    except Exception as e:
        logger.error(f"Error initializing portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing portfolio: {str(e)}"
        )


@router.get("/positions")
async def get_positions(
    run_id: str = Query(default="live"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all open positions."""
    try:
        pm = PortfolioManager(db, run_id)
        portfolio = pm.get_portfolio_summary()
        return portfolio['positions']
    
    except Exception as e:
        logger.error(f"Error getting positions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving positions: {str(e)}"
        )


@router.get("/trades")
async def get_trades(
    run_id: str = Query(default="live"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get trade history."""
    try:
        pm = PortfolioManager(db, run_id)
        trades = pm.get_trade_history(limit)
        return {
            "trades": trades,
            "total": len(trades)
        }
    
    except Exception as e:
        logger.error(f"Error getting trades: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trades: {str(e)}"
        )


@router.post("/trade")
async def execute_trade(
    trade: TradeRequest,
    run_id: str = Query(default="live"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute a simulated trade.
    
    This is mainly for testing. In production, trades come from agent decisions.
    """
    try:
        pm = PortfolioManager(db, run_id)
        
        # Validate inputs
        if trade.side not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")
        
        if trade.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        if trade.price <= 0:
            raise HTTPException(status_code=400, detail="Price must be positive")
        
        # Check risk limits for BUY orders
        if trade.side == 'BUY':
            trade_value = trade.quantity * trade.price
            is_valid, reason = pm.check_risk_limits(trade.symbol, trade.side, trade_value)
            
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Trade rejected: {reason}"
                )
        
        # Execute trade
        executed_trade = pm.execute_trade(
            symbol=trade.symbol.upper(),
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price
        )
        
        # Get updated portfolio
        portfolio = pm.get_portfolio_summary()
        
        return {
            "trade": {
                "id": executed_trade.id,
                "symbol": executed_trade.symbol,
                "side": executed_trade.side,
                "quantity": executed_trade.quantity,
                "price": executed_trade.price,
                "value": executed_trade.quantity * executed_trade.price,
                "pnl": executed_trade.pnl,
                "timestamp": executed_trade.timestamp.isoformat()
            },
            "portfolio": portfolio
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing trade: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing trade: {str(e)}"
        )
