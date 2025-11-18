"""
Binance API integration for fetching market data.
"""
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.config import settings
from app.models.database import Candle
import logging

logger = logging.getLogger(__name__)


class BinanceClient:
    """Client for interacting with Binance public API."""
    
    def __init__(self):
        self.base_url = settings.binance_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def fetch_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List]:
        """
        Fetch OHLCV candlestick data from Binance.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of candles to fetch (max 1000)
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
        
        Returns:
            List of klines [timestamp, open, high, low, close, volume, ...]
        """
        url = f"{self.base_url}/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000)
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            raise
    
    async def fetch_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current price for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
        
        Returns:
            Dict with 'symbol' and 'price'
        """
        url = f"{self.base_url}/api/v3/ticker/price"
        params = {"symbol": symbol.upper()}
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching ticker price for {symbol}: {e}")
            raise
    
    async def fetch_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch 24-hour ticker statistics.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
        
        Returns:
            Dict with price change, volume, etc.
        """
        url = f"{self.base_url}/api/v3/ticker/24hr"
        params = {"symbol": symbol.upper()}
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching 24h ticker for {symbol}: {e}")
            raise


def save_candles_to_db(
    db: Session,
    symbol: str,
    timeframe: str,
    klines: List[List]
) -> int:
    """
    Save candlestick data to database.
    
    Args:
        db: Database session
        symbol: Trading pair symbol
        timeframe: Timeframe/interval
        klines: Raw kline data from Binance
    
    Returns:
        Number of candles saved
    """
    saved_count = 0
    
    for kline in klines:
        timestamp = datetime.fromtimestamp(kline[0] / 1000)
        
        # Check if candle already exists
        existing = db.query(Candle).filter(
            Candle.symbol == symbol,
            Candle.timestamp == timestamp,
            Candle.timeframe == timeframe
        ).first()
        
        if existing:
            # Update existing candle
            existing.open = float(kline[1])
            existing.high = float(kline[2])
            existing.low = float(kline[3])
            existing.close = float(kline[4])
            existing.volume = float(kline[5])
        else:
            # Create new candle
            candle = Candle(
                symbol=symbol,
                timestamp=timestamp,
                timeframe=timeframe,
                open=float(kline[1]),
                high=float(kline[2]),
                low=float(kline[3]),
                close=float(kline[4]),
                volume=float(kline[5])
            )
            db.add(candle)
            saved_count += 1
    
    db.commit()
    logger.info(f"Saved {saved_count} new candles for {symbol} {timeframe}")
    return saved_count


async def fetch_and_store_candles(
    db: Session,
    symbol: str,
    interval: str = "1h",
    limit: int = 100
) -> int:
    """
    Fetch candles from Binance and store in database.
    
    Args:
        db: Database session
        symbol: Trading pair symbol
        interval: Timeframe
        limit: Number of candles to fetch
    
    Returns:
        Number of candles saved
    """
    client = BinanceClient()
    try:
        klines = await client.fetch_klines(symbol, interval, limit)
        count = save_candles_to_db(db, symbol, interval, klines)
        return count
    finally:
        await client.close()


def get_latest_candles(
    db: Session,
    symbol: str,
    timeframe: str,
    limit: int = 100
) -> List[Candle]:
    """
    Get the most recent candles from database.
    
    Args:
        db: Database session
        symbol: Trading pair symbol
        timeframe: Timeframe
        limit: Number of candles to return
    
    Returns:
        List of Candle objects
    """
    candles = db.query(Candle).filter(
        Candle.symbol == symbol,
        Candle.timeframe == timeframe
    ).order_by(desc(Candle.timestamp)).limit(limit).all()
    
    # Return in chronological order
    return list(reversed(candles))


def get_candles_in_range(
    db: Session,
    symbol: str,
    timeframe: str,
    start_date: datetime,
    end_date: datetime
) -> List[Candle]:
    """
    Get candles within a date range.
    
    Args:
        db: Database session
        symbol: Trading pair symbol
        timeframe: Timeframe
        start_date: Start datetime
        end_date: End datetime
    
    Returns:
        List of Candle objects in chronological order
    """
    candles = db.query(Candle).filter(
        Candle.symbol == symbol,
        Candle.timeframe == timeframe,
        Candle.timestamp >= start_date,
        Candle.timestamp <= end_date
    ).order_by(Candle.timestamp).all()
    
    return candles


# Supported trading symbols
SUPPORTED_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "ADAUSDT",
]

# Supported timeframes
SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
