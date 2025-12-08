"""
Paper trading API routes for order management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.services.paper_trading import (
    PaperTradingService,
    OrderType,
    OrderSide,
    OrderStatus
)
from app.models.database import PaperOrder

router = APIRouter(prefix="/paper-trading", tags=["paper-trading"])


# Pydantic models for requests/responses

class CreateOrderRequest(BaseModel):
    """Request model for creating an order."""
    symbol: str = Field(..., description="Trading pair (e.g., 'BTCUSDT')")
    side: str = Field(..., description="Order side: 'BUY' or 'SELL'")
    order_type: str = Field(..., description="Order type: 'MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT'")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Limit price (required for LIMIT orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (required for STOP_LOSS/TAKE_PROFIT)")
    time_in_force: str = Field("GTC", description="Time in force: 'GTC', 'IOC', 'FOK'")


class OrderResponse(BaseModel):
    """Response model for order."""
    id: int
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    filled_quantity: float
    avg_fill_price: Optional[float]
    status: str
    time_in_force: str
    run_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    binance_order_id: Optional[int]
    
    class Config:
        from_attributes = True


class AccountInfoResponse(BaseModel):
    """Response model for account information."""
    mode: str
    testnet_connected: bool
    balances: Optional[List[dict]] = None
    can_trade: bool
    account_type: Optional[str] = None


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new paper trading order.
    
    **Testnet Mode**: Places order on Binance Testnet (requires API credentials)
    **Simulation Mode**: Creates simulated order in local database
    
    Configure mode in .env with `PAPER_TRADING_MODE=testnet` or `simulation`
    """
    service = PaperTradingService(db)
    
    try:
        # Validate and convert enums
        side = OrderSide(request.side.upper())
        order_type = OrderType(request.order_type.upper())
        
        order = await service.create_order(
            symbol=request.symbol,
            side=side,
            order_type=order_type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force
        )
        
        return order
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")
    finally:
        await service.close()


@router.delete("/orders/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a pending order.
    
    Only pending or partially filled orders can be cancelled.
    """
    service = PaperTradingService(db)
    
    try:
        order = await service.cancel_order(order_id)
        return order
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")
    finally:
        await service.close()


@router.get("/orders/open", response_model=List[OrderResponse])
async def get_open_orders(
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all open (pending or partially filled) orders.
    
    Args:
        symbol: Optional filter by trading pair
    """
    service = PaperTradingService(db)
    
    try:
        orders = await service.get_open_orders(symbol)
        return orders
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")
    finally:
        await service.close()


@router.get("/orders/history", response_model=List[OrderResponse])
async def get_order_history(
    symbol: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get order history (all orders).
    
    Args:
        symbol: Optional filter by trading pair
        limit: Maximum number of orders to return
    """
    service = PaperTradingService(db)
    
    try:
        orders = await service.get_order_history(symbol, limit)
        return orders
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order history: {str(e)}")
    finally:
        await service.close()


@router.post("/orders/sync")
async def sync_orders(
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Sync order status from Binance Testnet.
    
    Updates database with latest order status from testnet API.
    Only works in testnet mode.
    
    Args:
        symbol: Optional filter by trading pair
    """
    service = PaperTradingService(db)
    
    try:
        await service.sync_testnet_orders(symbol)
        return {"message": "Orders synced successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing orders: {str(e)}")
    finally:
        await service.close()


@router.post("/orders/process")
async def process_pending_orders(
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Process pending orders and check for fills (simulation mode only).
    
    Checks if limit/stop orders should be filled based on current market prices.
    This endpoint is primarily for simulation mode.
    
    Args:
        symbol: Optional filter by trading pair
    """
    service = PaperTradingService(db)
    
    try:
        await service.process_pending_orders(symbol)
        return {"message": "Pending orders processed"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing orders: {str(e)}")
    finally:
        await service.close()


@router.get("/account", response_model=AccountInfoResponse)
async def get_account_info(
    db: Session = Depends(get_db)
):
    """
    Get paper trading account information.
    
    **Testnet Mode**: Returns actual Binance Testnet account balances
    **Simulation Mode**: Returns local portfolio state
    """
    service = PaperTradingService(db)
    
    try:
        if service.mode == "testnet":
            account_info = await service.get_testnet_account_info()
            return AccountInfoResponse(
                mode="testnet",
                testnet_connected=True,
                balances=account_info.get('balances', []),
                can_trade=account_info.get('canTrade', False),
                account_type=account_info.get('accountType')
            )
        else:
            return AccountInfoResponse(
                mode="simulation",
                testnet_connected=False,
                balances=None,
                can_trade=True,
                account_type="SIMULATION"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account info: {str(e)}")
    finally:
        await service.close()
