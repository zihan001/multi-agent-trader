"""
Sentiment Data Service

Aggregates real market sentiment data from multiple sources.
"""
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class SentimentService:
    """
    Fetches and aggregates sentiment data from multiple sources.
    
    Data Sources:
    1. Crypto Fear & Greed Index (free, no API key)
    2. Binance volume analysis (already have access)
    3. CoinGecko market data (free, optional API key)
    4. Technical sentiment indicators (RSI, volatility)
    """
    
    def __init__(self, db: Session):
        """
        Initialize sentiment service.
        
        Args:
            db: Database session for caching
        """
        self.db = db
        self.client = httpx.AsyncClient(timeout=10.0)
        
        # API endpoints
        self.fear_greed_url = "https://api.alternative.me/fng/"
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def fetch_fear_greed_index(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Crypto Fear & Greed Index.
        
        Returns:
            {
                "value": 50,  # 0-100
                "classification": "Neutral",  # Extreme Fear, Fear, Neutral, Greed, Extreme Greed
                "timestamp": datetime
            }
        """
        try:
            response = await self.client.get(self.fear_greed_url, params={"limit": 1})
            response.raise_for_status()
            data = response.json()
            
            if data and "data" in data and len(data["data"]) > 0:
                fng = data["data"][0]
                return {
                    "value": int(fng["value"]),
                    "classification": fng["value_classification"],
                    "timestamp": datetime.fromtimestamp(int(fng["timestamp"]))
                }
        except Exception as e:
            logger.warning(f"Failed to fetch Fear & Greed Index: {e}")
            return None
    
    async def fetch_coingecko_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch CoinGecko market data for sentiment analysis.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            {
                "market_cap_rank": 1,
                "sentiment_votes_up": 75.5,
                "sentiment_votes_down": 24.5,
                "price_change_24h": 2.5,
                "price_change_7d": -1.2,
                "volume_24h": 25000000000,
                "social_score": 85.3
            }
        """
        try:
            # Map Binance symbols to CoinGecko IDs
            symbol_map = {
                "BTCUSDT": "bitcoin",
                "ETHUSDT": "ethereum",
                "SOLUSDT": "solana",
                "BNBUSDT": "binancecoin",
                "ADAUSDT": "cardano",
                "XRPUSDT": "ripple",
                "DOGEUSDT": "dogecoin",
                "MATICUSDT": "matic-network",
                "DOTUSDT": "polkadot",
                "LINKUSDT": "chainlink",
            }
            
            coin_id = symbol_map.get(symbol.upper())
            if not coin_id:
                logger.warning(f"No CoinGecko mapping for {symbol}")
                return None
            
            # Fetch coin data
            url = f"{self.coingecko_url}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "false",
                "sparkline": "false"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract sentiment-relevant data
            market_data = data.get("market_data", {})
            community_data = data.get("community_data", {})
            sentiment_data = data.get("sentiment_votes_up_percentage", 0)
            
            return {
                "market_cap_rank": data.get("market_cap_rank", 0),
                "sentiment_votes_up": sentiment_data,
                "sentiment_votes_down": 100 - sentiment_data,
                "price_change_24h": market_data.get("price_change_percentage_24h", 0),
                "price_change_7d": market_data.get("price_change_percentage_7d", 0),
                "volume_24h": market_data.get("total_volume", {}).get("usd", 0),
                "market_cap_change_24h": market_data.get("market_cap_change_percentage_24h", 0),
                "twitter_followers": community_data.get("twitter_followers", 0),
                "reddit_subscribers": community_data.get("reddit_subscribers", 0),
                "reddit_active_accounts": community_data.get("reddit_accounts_active_48h", 0),
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch CoinGecko data for {symbol}: {e}")
            return None
    
    def analyze_volume_sentiment(
        self,
        current_volume: float,
        avg_volume: float,
        price_change: float
    ) -> Dict[str, Any]:
        """
        Analyze volume patterns for sentiment signals.
        
        Args:
            current_volume: Current 24h volume
            avg_volume: Average volume (e.g., 7-day average)
            price_change: Price change percentage
            
        Returns:
            {
                "volume_trend": "increasing" | "decreasing" | "stable",
                "volume_ratio": 1.5,  # current / average
                "sentiment_signal": "bullish" | "bearish" | "neutral",
                "conviction": "high" | "moderate" | "low"
            }
        """
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Classify volume trend
        if volume_ratio > 1.5:
            volume_trend = "increasing"
        elif volume_ratio < 0.7:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"
        
        # Determine sentiment based on volume + price action
        if volume_ratio > 1.5 and price_change > 2:
            sentiment_signal = "bullish"
            conviction = "high"
        elif volume_ratio > 1.5 and price_change < -2:
            sentiment_signal = "bearish"
            conviction = "high"
        elif volume_ratio > 1.3 and price_change > 0:
            sentiment_signal = "bullish"
            conviction = "moderate"
        elif volume_ratio > 1.3 and price_change < 0:
            sentiment_signal = "bearish"
            conviction = "moderate"
        else:
            sentiment_signal = "neutral"
            conviction = "low"
        
        return {
            "volume_trend": volume_trend,
            "volume_ratio": round(volume_ratio, 2),
            "sentiment_signal": sentiment_signal,
            "conviction": conviction
        }
    
    def analyze_technical_sentiment(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        """
        Derive sentiment from technical indicators.
        
        Args:
            indicators: Dict of technical indicators (RSI, MACD, etc.)
            
        Returns:
            {
                "rsi_sentiment": "extreme_fear" | "fear" | "neutral" | "greed" | "extreme_greed",
                "momentum_sentiment": "bullish" | "bearish" | "neutral",
                "overall_technical_sentiment": "bullish" | "bearish" | "neutral",
                "extremes_detected": ["oversold", "overbought"]
            }
        """
        rsi = indicators.get("rsi", 50)
        macd = indicators.get("macd", 0)
        macd_signal = indicators.get("macd_signal", 0)
        
        # RSI sentiment levels
        if rsi >= 80:
            rsi_sentiment = "extreme_greed"
        elif rsi >= 70:
            rsi_sentiment = "greed"
        elif rsi <= 20:
            rsi_sentiment = "extreme_fear"
        elif rsi <= 30:
            rsi_sentiment = "fear"
        else:
            rsi_sentiment = "neutral"
        
        # MACD momentum
        if macd > macd_signal and macd > 0:
            momentum_sentiment = "bullish"
        elif macd < macd_signal and macd < 0:
            momentum_sentiment = "bearish"
        else:
            momentum_sentiment = "neutral"
        
        # Overall technical sentiment
        if rsi > 60 and momentum_sentiment == "bullish":
            overall = "bullish"
        elif rsi < 40 and momentum_sentiment == "bearish":
            overall = "bearish"
        else:
            overall = "neutral"
        
        # Detect extremes
        extremes = []
        if rsi >= 70:
            extremes.append("overbought")
        if rsi <= 30:
            extremes.append("oversold")
        
        return {
            "rsi_sentiment": rsi_sentiment,
            "rsi_value": round(rsi, 2),
            "momentum_sentiment": momentum_sentiment,
            "overall_technical_sentiment": overall,
            "extremes_detected": extremes
        }
    
    async def get_comprehensive_sentiment(
        self,
        symbol: str,
        current_price: float,
        price_change_24h: float,
        volume_24h: float,
        avg_volume: float,
        indicators: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Aggregate sentiment data from all sources.
        
        Args:
            symbol: Trading pair symbol
            current_price: Current price
            price_change_24h: 24h price change percentage
            volume_24h: 24h volume
            avg_volume: Average volume for comparison
            indicators: Technical indicators
            
        Returns:
            Comprehensive sentiment data dict
        """
        # Fetch external sentiment data (parallel)
        fear_greed_task = self.fetch_fear_greed_index()
        coingecko_task = self.fetch_coingecko_sentiment(symbol)
        
        fear_greed = await fear_greed_task
        coingecko = await coingecko_task
        
        # Analyze internal signals
        volume_sentiment = self.analyze_volume_sentiment(
            volume_24h, avg_volume, price_change_24h
        )
        technical_sentiment = self.analyze_technical_sentiment(indicators)
        
        # Calculate overall sentiment score (-100 to 100)
        sentiment_score = self._calculate_aggregate_score(
            fear_greed, coingecko, volume_sentiment, technical_sentiment, price_change_24h
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            
            # External data
            "fear_greed_index": fear_greed,
            "coingecko_data": coingecko,
            
            # Internal analysis
            "volume_sentiment": volume_sentiment,
            "technical_sentiment": technical_sentiment,
            
            # Aggregate metrics
            "overall_sentiment_score": sentiment_score,
            "sentiment_classification": self._classify_sentiment(sentiment_score),
            "data_sources_available": {
                "fear_greed": fear_greed is not None,
                "coingecko": coingecko is not None,
                "volume": True,
                "technical": True
            }
        }
    
    def _calculate_aggregate_score(
        self,
        fear_greed: Optional[Dict],
        coingecko: Optional[Dict],
        volume_sentiment: Dict,
        technical_sentiment: Dict,
        price_change: float
    ) -> int:
        """
        Calculate aggregate sentiment score from all sources.
        
        Returns:
            Score from -100 (extreme fear) to 100 (extreme greed)
        """
        scores = []
        weights = []
        
        # Fear & Greed Index (weight: 0.3)
        if fear_greed:
            fg_score = (fear_greed["value"] - 50) * 2  # Scale to -100 to 100
            scores.append(fg_score)
            weights.append(0.3)
        
        # CoinGecko sentiment (weight: 0.2)
        if coingecko:
            cg_score = (coingecko["sentiment_votes_up"] - 50) * 2
            scores.append(cg_score)
            weights.append(0.2)
        
        # Volume sentiment (weight: 0.2)
        volume_score_map = {
            "bullish": 50,
            "bearish": -50,
            "neutral": 0
        }
        conviction_multiplier = {"high": 1.0, "moderate": 0.6, "low": 0.3}
        volume_score = (
            volume_score_map[volume_sentiment["sentiment_signal"]] *
            conviction_multiplier[volume_sentiment["conviction"]]
        )
        scores.append(volume_score)
        weights.append(0.2)
        
        # Technical sentiment (weight: 0.2)
        tech_score_map = {"bullish": 40, "bearish": -40, "neutral": 0}
        rsi_score_map = {
            "extreme_greed": 80, "greed": 50, "neutral": 0,
            "fear": -50, "extreme_fear": -80
        }
        tech_score = (
            tech_score_map[technical_sentiment["overall_technical_sentiment"]] * 0.6 +
            rsi_score_map[technical_sentiment["rsi_sentiment"]] * 0.4
        )
        scores.append(tech_score)
        weights.append(0.2)
        
        # Price action (weight: 0.1)
        price_score = max(-100, min(100, price_change * 10))  # ±10% = ±100 score
        scores.append(price_score)
        weights.append(0.1)
        
        # Weighted average
        if not scores:
            return 0
        
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        
        return int(weighted_sum / total_weight)
    
    def _classify_sentiment(self, score: int) -> str:
        """
        Classify sentiment score into category.
        
        Args:
            score: Sentiment score (-100 to 100)
            
        Returns:
            Classification string
        """
        if score >= 60:
            return "Extreme Greed"
        elif score >= 30:
            return "Greed"
        elif score >= -30:
            return "Neutral"
        elif score >= -60:
            return "Fear"
        else:
            return "Extreme Fear"
