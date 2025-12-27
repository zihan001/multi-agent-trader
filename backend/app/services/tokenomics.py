"""
Tokenomics Data Service

Fetches real token fundamentals, on-chain metrics, and supply data.
"""
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class TokenomicsService:
    """
    Fetches tokenomics and fundamental data from multiple sources.
    
    Data Sources:
    1. CoinGecko API (free) - Market data, supply metrics, developer activity
    2. Binance API (already integrated) - Volume, market cap
    3. Calculated metrics - Supply velocity, holder concentration estimates
    """
    
    def __init__(self, db: Session):
        """
        Initialize tokenomics service.
        
        Args:
            db: Database session for caching
        """
        self.db = db
        self.client = httpx.AsyncClient(timeout=10.0)
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def fetch_coingecko_tokenomics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive tokenomics data from CoinGecko.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            {
                "market_data": {...},
                "supply_data": {...},
                "developer_data": {...},
                "community_data": {...}
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
                "AVAXUSDT": "avalanche-2",
                "ATOMUSDT": "cosmos",
                "UNIUSDT": "uniswap",
                "LTCUSDT": "litecoin",
                "NEARUSDT": "near",
            }
            
            coin_id = symbol_map.get(symbol.upper())
            if not coin_id:
                logger.warning(f"No CoinGecko mapping for {symbol}")
                return None
            
            # Fetch comprehensive coin data
            url = f"{self.coingecko_url}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "true",
                "sparkline": "false"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract tokenomics data
            market_data = data.get("market_data", {})
            community_data = data.get("community_data", {})
            developer_data = data.get("developer_data", {})
            
            # Supply metrics
            circulating_supply = market_data.get("circulating_supply", 0)
            total_supply = market_data.get("total_supply", 0)
            max_supply = market_data.get("max_supply")
            
            # Calculate supply percentage
            supply_percentage = 0
            if max_supply and max_supply > 0:
                supply_percentage = (circulating_supply / max_supply) * 100
            elif total_supply and total_supply > 0:
                supply_percentage = (circulating_supply / total_supply) * 100
            
            # Market metrics
            market_cap = market_data.get("market_cap", {}).get("usd", 0)
            fully_diluted_valuation = market_data.get("fully_diluted_valuation", {}).get("usd", 0)
            total_volume = market_data.get("total_volume", {}).get("usd", 0)
            
            # Calculate velocity (volume / market cap)
            velocity = (total_volume / market_cap) if market_cap > 0 else 0
            
            # Valuation metrics
            price_to_book = market_data.get("price_to_book_ratio", 0)
            
            return {
                "symbol": symbol,
                "coin_id": coin_id,
                "name": data.get("name", "Unknown"),
                "blockchain": data.get("asset_platform_id", "native"),
                "categories": data.get("categories", [])[:5],  # Top 5 categories
                
                # Supply data
                "supply": {
                    "circulating": circulating_supply,
                    "total": total_supply,
                    "max": max_supply,
                    "percentage_circulating": round(supply_percentage, 2),
                    "is_inflationary": max_supply is None or total_supply > (max_supply or 0),
                },
                
                # Market data
                "market": {
                    "market_cap": market_cap,
                    "market_cap_rank": data.get("market_cap_rank", 0),
                    "fully_diluted_valuation": fully_diluted_valuation,
                    "fdv_to_mcap_ratio": round(fully_diluted_valuation / market_cap, 2) if market_cap > 0 else 0,
                    "volume_24h": total_volume,
                    "volume_to_mcap_ratio": round(velocity, 4),
                    "ath_price": market_data.get("ath", {}).get("usd", 0),
                    "ath_change_percentage": market_data.get("ath_change_percentage", {}).get("usd", 0),
                    "atl_price": market_data.get("atl", {}).get("usd", 0),
                    "atl_change_percentage": market_data.get("atl_change_percentage", {}).get("usd", 0),
                },
                
                # Price changes
                "price_changes": {
                    "24h": market_data.get("price_change_percentage_24h", 0),
                    "7d": market_data.get("price_change_percentage_7d", 0),
                    "30d": market_data.get("price_change_percentage_30d", 0),
                    "1y": market_data.get("price_change_percentage_1y", 0),
                },
                
                # Community metrics
                "community": {
                    "twitter_followers": community_data.get("twitter_followers", 0),
                    "reddit_subscribers": community_data.get("reddit_subscribers", 0),
                    "reddit_active_48h": community_data.get("reddit_accounts_active_48h", 0),
                    "telegram_users": community_data.get("telegram_channel_user_count", 0),
                },
                
                # Developer activity
                "developer": {
                    "forks": developer_data.get("forks", 0),
                    "stars": developer_data.get("stars", 0),
                    "subscribers": developer_data.get("subscribers", 0),
                    "total_issues": developer_data.get("total_issues", 0),
                    "closed_issues": developer_data.get("closed_issues", 0),
                    "pull_requests_merged": developer_data.get("pull_requests_merged", 0),
                    "commit_count_4_weeks": developer_data.get("commit_count_4_weeks", 0),
                },
                
                # Links
                "links": {
                    "homepage": data.get("links", {}).get("homepage", [""])[0],
                    "blockchain_site": data.get("links", {}).get("blockchain_site", [""])[0],
                    "official_forum_url": data.get("links", {}).get("official_forum_url", [""])[0],
                },
                
                "last_updated": data.get("last_updated", ""),
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch CoinGecko tokenomics for {symbol}: {e}")
            return None
    
    def analyze_supply_structure(self, supply_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Analyze token supply structure and inflation.
        
        Args:
            supply_data: Supply metrics from CoinGecko
            
        Returns:
            {
                "inflation_type": "deflationary" | "fixed" | "inflationary" | "unknown",
                "supply_status": "fully_circulating" | "partial" | "early_stage",
                "inflation_pressure": "high" | "moderate" | "low" | "none"
            }
        """
        circulating = supply_data.get("circulating", 0)
        total = supply_data.get("total", 0)
        max_supply = supply_data.get("max")
        percentage = supply_data.get("percentage_circulating", 0)
        
        # Determine inflation type
        if max_supply and max_supply > 0:
            if total >= max_supply:
                inflation_type = "deflationary"
            else:
                inflation_type = "fixed"
        elif supply_data.get("is_inflationary"):
            inflation_type = "inflationary"
        else:
            inflation_type = "unknown"
        
        # Supply circulation status
        if percentage >= 95:
            supply_status = "fully_circulating"
        elif percentage >= 60:
            supply_status = "partial"
        else:
            supply_status = "early_stage"
        
        # Inflation pressure (based on how much supply is yet to be released)
        if percentage >= 95:
            inflation_pressure = "none"
        elif percentage >= 80:
            inflation_pressure = "low"
        elif percentage >= 60:
            inflation_pressure = "moderate"
        else:
            inflation_pressure = "high"
        
        return {
            "inflation_type": inflation_type,
            "supply_status": supply_status,
            "inflation_pressure": inflation_pressure
        }
    
    def analyze_liquidity(self, market_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Analyze market liquidity and trading activity.
        
        Args:
            market_data: Market metrics
            
        Returns:
            {
                "market_cap_tier": "mega" | "large" | "mid" | "small" | "micro",
                "liquidity_rating": "excellent" | "good" | "fair" | "poor",
                "volume_rating": "high" | "moderate" | "low"
            }
        """
        market_cap = market_data.get("market_cap", 0)
        volume_ratio = market_data.get("volume_to_mcap_ratio", 0)
        
        # Market cap tiers
        if market_cap >= 100_000_000_000:  # $100B+
            market_cap_tier = "mega"
        elif market_cap >= 10_000_000_000:  # $10B+
            market_cap_tier = "large"
        elif market_cap >= 1_000_000_000:  # $1B+
            market_cap_tier = "mid"
        elif market_cap >= 100_000_000:  # $100M+
            market_cap_tier = "small"
        else:
            market_cap_tier = "micro"
        
        # Liquidity rating (based on market cap + volume)
        if market_cap >= 10_000_000_000 and volume_ratio >= 0.05:
            liquidity_rating = "excellent"
        elif market_cap >= 1_000_000_000 and volume_ratio >= 0.03:
            liquidity_rating = "good"
        elif market_cap >= 100_000_000 and volume_ratio >= 0.01:
            liquidity_rating = "fair"
        else:
            liquidity_rating = "poor"
        
        # Volume rating
        if volume_ratio >= 0.1:  # 10%+ daily turnover
            volume_rating = "high"
        elif volume_ratio >= 0.03:  # 3%+ daily turnover
            volume_rating = "moderate"
        else:
            volume_rating = "low"
        
        return {
            "market_cap_tier": market_cap_tier,
            "liquidity_rating": liquidity_rating,
            "volume_rating": volume_rating
        }
    
    def assess_developer_activity(self, developer_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Assess developer activity level.
        
        Args:
            developer_data: Developer metrics
            
        Returns:
            {
                "activity_level": "very_active" | "active" | "moderate" | "low" | "dormant",
                "project_health": "healthy" | "stable" | "declining" | "unknown"
            }
        """
        commits_4w = developer_data.get("commit_count_4_weeks", 0)
        total_issues = developer_data.get("total_issues", 0)
        closed_issues = developer_data.get("closed_issues", 0)
        
        # Activity level based on commits
        if commits_4w >= 100:
            activity_level = "very_active"
        elif commits_4w >= 50:
            activity_level = "active"
        elif commits_4w >= 10:
            activity_level = "moderate"
        elif commits_4w >= 1:
            activity_level = "low"
        else:
            activity_level = "dormant"
        
        # Project health based on issue resolution
        if total_issues > 0:
            resolution_rate = closed_issues / total_issues
            if resolution_rate >= 0.8:
                project_health = "healthy"
            elif resolution_rate >= 0.5:
                project_health = "stable"
            else:
                project_health = "declining"
        else:
            project_health = "unknown"
        
        return {
            "activity_level": activity_level,
            "project_health": project_health
        }
    
    async def get_comprehensive_tokenomics(
        self,
        symbol: str,
        current_price: float,
        market_cap: float,
        volume_24h: float
    ) -> Dict[str, Any]:
        """
        Aggregate comprehensive tokenomics data.
        
        Args:
            symbol: Trading pair symbol
            current_price: Current price
            market_cap: Market capitalization
            volume_24h: 24h trading volume
            
        Returns:
            Comprehensive tokenomics data dict
        """
        # Fetch CoinGecko data
        coingecko_data = await self.fetch_coingecko_tokenomics(symbol)
        
        if not coingecko_data:
            # Fallback to basic metrics if CoinGecko unavailable
            return {
                "symbol": symbol,
                "data_quality": "LIMITED_DATA",
                "basic_metrics": {
                    "current_price": current_price,
                    "market_cap": market_cap,
                    "volume_24h": volume_24h,
                    "volume_to_mcap_ratio": volume_24h / market_cap if market_cap > 0 else 0,
                },
                "warning": "Limited data available. CoinGecko API unavailable."
            }
        
        # Analyze supply structure
        supply_analysis = self.analyze_supply_structure(coingecko_data["supply"])
        
        # Analyze liquidity
        liquidity_analysis = self.analyze_liquidity(coingecko_data["market"])
        
        # Assess developer activity
        developer_assessment = self.assess_developer_activity(coingecko_data["developer"])
        
        # Combine all data
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "coin_name": coingecko_data["name"],
            "blockchain": coingecko_data["blockchain"],
            "categories": coingecko_data["categories"],
            
            # Raw data
            "supply_data": coingecko_data["supply"],
            "market_data": coingecko_data["market"],
            "price_changes": coingecko_data["price_changes"],
            "community_data": coingecko_data["community"],
            "developer_data": coingecko_data["developer"],
            
            # Analysis
            "supply_analysis": supply_analysis,
            "liquidity_analysis": liquidity_analysis,
            "developer_assessment": developer_assessment,
            
            # Links
            "links": coingecko_data["links"],
            
            "data_quality": "COMPREHENSIVE",
            "data_sources_available": {
                "coingecko": True,
                "supply_metrics": True,
                "market_metrics": True,
                "community_metrics": True,
                "developer_metrics": True,
            }
        }
