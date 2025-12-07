"""
Configuration API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.engines.factory import DecisionEngineFactory
from app.core.config import settings

router = APIRouter(prefix="/config", tags=["configuration"])


class TradingModeResponse(BaseModel):
    """Response model for trading mode endpoint."""
    mode: str
    engine_info: Dict[str, Any]


@router.get("/mode", response_model=TradingModeResponse)
async def get_trading_mode():
    """
    Get the current trading mode and engine configuration.
    
    Returns:
        Current trading mode and detailed engine information
    """
    engine_info = DecisionEngineFactory.get_current_engine_info()
    
    return TradingModeResponse(
        mode=settings.trading_mode,
        engine_info=engine_info
    )


@router.get("/capabilities")
async def get_engine_capabilities():
    """
    Get information about all available decision engines.
    
    Returns:
        Dictionary with information about LLM and rule-based engines
    """
    return DecisionEngineFactory.get_available_engines()


# Note: POST /config/mode for changing mode at runtime would require
# dynamic config reloading which is complex. For now, mode is set via
# environment variables and requires restart to change.
# This can be added in future if needed for admin UI.
