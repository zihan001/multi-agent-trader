"""
Market data API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.services import binance
from app.services.indicators import IndicatorService, get_overbought_oversold_status
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/symbols")
async def get_supported_symbols():
    """Get list of supported trading symbols."""
    return {"symbols": binance.SUPPORTED_SYMBOLS}


@router.get("/timeframes", response_model=List[str])
async def get_supported_timeframes():
    """Get list of supported timeframes."""
    return binance.SUPPORTED_TIMEFRAMES


@router.get("/{symbol}/latest")
async def get_latest_market_data(
    symbol: str,
    timeframe: str = Query(default="1h", description="Timeframe/interval"),
    limit: int = Query(default=100, ge=1, le=500, description="Number of candles"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get latest market data with technical indicators for a symbol.
    
    This endpoint:
    1. Fetches latest candles from Binance (if not cached)
    2. Stores them in database
    3. Calculates technical indicators
    4. Returns OHLCV data + indicators
    """
    symbol = symbol.upper()
    
    if symbol not in binance.SUPPORTED_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {symbol} not supported. Supported symbols: {binance.SUPPORTED_SYMBOLS}"
        )
    
    if timeframe not in binance.SUPPORTED_TIMEFRAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Timeframe {timeframe} not supported. Supported timeframes: {binance.SUPPORTED_TIMEFRAMES}"
        )
    
    try:
        # Fetch and store latest candles from Binance
        logger.info(f"Fetching {limit} candles for {symbol} {timeframe}")
        await binance.fetch_and_store_candles(db, symbol, timeframe, limit)
        
        # Get candles from database
        candles = binance.get_latest_candles(db, symbol, timeframe, limit)
        
        if not candles:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {symbol}"
            )
        
        # Calculate indicators
        indicator_service = IndicatorService()
        indicator_data = indicator_service.calculate_from_candles(candles)
        
        # Get latest candle for basic info
        latest_candle = candles[-1]
        
        # Format candles for frontend
        candles_data = [
            {
                "timestamp": c.timestamp.isoformat(),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume
            }
            for c in candles
        ]
        
        return {
            "symbol": symbol,
            "candles": candles_data,
            "indicators": {
                "rsi": indicator_data['rsi_14'],
                "macd": indicator_data['macd'],
                "macd_signal": indicator_data['macd_signal'],
                "macd_hist": indicator_data['macd_diff'],
                "ema_12": indicator_data.get('ema_12', indicator_data['ema_9']),
                "ema_26": indicator_data.get('ema_26', indicator_data['ema_21']),
                "bb_upper": indicator_data['bb_upper'],
                "bb_middle": indicator_data['bb_middle'],
                "bb_lower": indicator_data['bb_lower'],
            },
            "latest_price": indicator_data['current_price']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching market data: {str(e)}"
        )


@router.post("/{symbol}/fetch")
async def fetch_historical_data(
    symbol: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=500, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger fetching historical data for a symbol.
    Useful for populating the database before backtesting.
    """
    symbol = symbol.upper()
    
    if symbol not in binance.SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
    
    try:
        count = await binance.fetch_and_store_candles(db, symbol, timeframe, limit)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles_saved": count,
            "message": f"Successfully fetched {count} new candles for {symbol}"
        }
    
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching data: {str(e)}"
        )
