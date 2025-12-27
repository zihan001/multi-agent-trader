"""
ReAct Agent Tools

Tools that ReAct agents can use for dynamic decision-making.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.binance import BinanceService
from app.services.indicators import IndicatorService
from app.services.portfolio import PortfolioManager
from app.services.sentiment import SentimentService
from app.services.tokenomics import TokenomicsService


class ResearcherTools:
    """Tools available to Researcher ReAct agent."""
    
    def __init__(self, db: Session):
        self.db = db
        self.binance = BinanceService()
        self.indicator_service = IndicatorService()
    
    async def fetch_recent_news(self, symbol: str, hours: int = 24) -> Dict[str, Any]:
        """
        Fetch breaking news for a symbol in the last N hours.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            hours: Look back period in hours
            
        Returns:
            Dict with news summary
        """
        # In a real implementation, this would call a news API
        # For now, return placeholder that indicates no major news
        return {
            "symbol": symbol,
            "timeframe": f"last_{hours}_hours",
            "major_events": [],
            "sentiment": "neutral",
            "summary": "No major breaking news detected in the specified timeframe."
        }
    
    async def query_analyst(
        self, 
        analyst_type: str, 
        question: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Re-query a specific analyst with follow-up question.
        
        Args:
            analyst_type: "technical", "sentiment", or "tokenomics"
            question: Follow-up question
            context: Additional context needed
            
        Returns:
            Answer string
        """
        # This would re-invoke the specific analyst with focused question
        # For now, return that feature is coming soon
        return f"Re-querying {analyst_type} analyst: Feature coming soon. Original analysis stands."
    
    async def fetch_additional_indicators(
        self, 
        symbol: str, 
        timeframe: str = "1h",
        indicators: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch additional technical indicators not in original analysis.
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe for indicators
            indicators: List of indicator names (e.g., ["stoch_rsi", "obv"])
            
        Returns:
            Dict of indicator values
        """
        if indicators is None:
            indicators = ["stoch_rsi", "obv", "atr"]
        
        try:
            # Fetch recent candles
            candles = self.binance.get_klines(symbol, timeframe, limit=100)
            if not candles:
                return {"error": "Failed to fetch candle data"}
            
            # Calculate additional indicators
            result = {}
            
            # Stochastic RSI
            if "stoch_rsi" in indicators:
                import pandas as pd
                df = pd.DataFrame(candles)
                closes = df['close'].astype(float)
                
                # Simple stoch RSI approximation
                rsi = self._calculate_rsi(closes, 14)
                stoch = (rsi.iloc[-1] - rsi.iloc[-14:].min()) / (rsi.iloc[-14:].max() - rsi.iloc[-14:].min()) * 100
                result["stoch_rsi"] = round(stoch, 2)
            
            # OBV (On-Balance Volume)
            if "obv" in indicators:
                import pandas as pd
                df = pd.DataFrame(candles)
                closes = df['close'].astype(float)
                volumes = df['volume'].astype(float)
                
                obv = 0
                for i in range(1, len(closes)):
                    if closes.iloc[i] > closes.iloc[i-1]:
                        obv += volumes.iloc[i]
                    elif closes.iloc[i] < closes.iloc[i-1]:
                        obv -= volumes.iloc[i]
                
                result["obv"] = round(obv, 2)
            
            # ATR (Average True Range)
            if "atr" in indicators:
                import pandas as pd
                df = pd.DataFrame(candles)
                highs = df['high'].astype(float)
                lows = df['low'].astype(float)
                closes = df['close'].astype(float)
                
                tr = pd.concat([
                    highs - lows,
                    (highs - closes.shift()).abs(),
                    (lows - closes.shift()).abs()
                ], axis=1).max(axis=1)
                
                atr = tr.iloc[-14:].mean()
                result["atr"] = round(atr, 2)
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI."""
        import pandas as pd
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    async def compare_historical_patterns(
        self,
        symbol: str,
        current_pattern: str
    ) -> Dict[str, Any]:
        """
        Find similar historical patterns and their outcomes.
        
        Args:
            symbol: Trading pair
            current_pattern: Description of current pattern
            
        Returns:
            Historical pattern matches with outcomes
        """
        # This would use ML or pattern matching
        # For now, return placeholder
        return {
            "matches_found": 0,
            "summary": "Historical pattern matching feature coming soon."
        }
    
    async def fetch_order_book_snapshot(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """
        Get current order book snapshot.
        
        Args:
            symbol: Trading pair
            depth: Number of levels to fetch
            
        Returns:
            Order book data with bid/ask walls
        """
        try:
            order_book = self.binance.get_order_book(symbol, limit=depth)
            
            # Analyze for significant walls
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            # Find largest bid wall
            max_bid = max(bids, key=lambda x: float(x[1])) if bids else None
            max_ask = max(asks, key=lambda x: float(x[1])) if asks else None
            
            return {
                "symbol": symbol,
                "bid_wall": {
                    "price": float(max_bid[0]) if max_bid else None,
                    "volume": float(max_bid[1]) if max_bid else None
                },
                "ask_wall": {
                    "price": float(max_ask[0]) if max_ask else None,
                    "volume": float(max_ask[1]) if max_ask else None
                },
                "spread": float(asks[0][0]) - float(bids[0][0]) if bids and asks else None,
                "depth_levels": depth
            }
        except Exception as e:
            return {"error": str(e)}


class RiskManagerTools:
    """Tools available to Risk Manager ReAct agent."""
    
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_manager = PortfolioManager(db)
    
    def get_portfolio_exposure(self, symbol: str = None, run_id: str = None) -> Dict[str, Any]:
        """
        Get current portfolio exposure, optionally filtered by symbol.
        
        Args:
            symbol: Filter by specific symbol (optional)
            run_id: Run ID for portfolio context
            
        Returns:
            Exposure details
        """
        try:
            portfolio = self.portfolio_manager.get_portfolio_summary(run_id=run_id)
            
            if symbol:
                # Find specific position
                positions = portfolio.get('positions', [])
                symbol_position = next((p for p in positions if p['symbol'] == symbol), None)
                
                return {
                    "symbol": symbol,
                    "current_position": symbol_position,
                    "total_equity": portfolio.get('total_equity', 0),
                    "position_pct": (symbol_position['value'] / portfolio['total_equity'] * 100) if symbol_position else 0
                }
            else:
                # Return overall exposure
                return {
                    "total_equity": portfolio.get('total_equity', 0),
                    "cash_balance": portfolio.get('cash_balance', 0),
                    "total_position_value": portfolio.get('total_position_value', 0),
                    "exposure_pct": (portfolio.get('total_position_value', 0) / portfolio.get('total_equity', 1) * 100),
                    "num_positions": len(portfolio.get('positions', []))
                }
        except Exception as e:
            return {"error": str(e)}
    
    def calculate_var(
        self,
        portfolio_value: float,
        position_size: float,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk for a position.
        
        Args:
            portfolio_value: Total portfolio value
            position_size: Size of proposed position
            confidence_level: VaR confidence level (default 95%)
            
        Returns:
            VaR value in dollars
        """
        # Simplified VaR calculation (assumes 2% daily volatility for crypto)
        volatility = 0.02
        z_score = 1.645 if confidence_level == 0.95 else 1.96  # 95% or 99%
        var = position_size * volatility * z_score
        
        return round(var, 2)
    
    def simulate_trade_impact(
        self,
        current_equity: float,
        trade_size: float,
        stop_loss_pct: float,
        take_profit_pct: float
    ) -> Dict[str, Any]:
        """
        Simulate the impact of a trade on portfolio.
        
        Args:
            current_equity: Current portfolio equity
            trade_size: Proposed trade size in dollars
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            
        Returns:
            Impact analysis
        """
        max_loss = trade_size * abs(stop_loss_pct) / 100
        max_gain = trade_size * abs(take_profit_pct) / 100
        
        return {
            "trade_size": trade_size,
            "max_loss_dollars": round(max_loss, 2),
            "max_loss_portfolio_pct": round(max_loss / current_equity * 100, 2),
            "max_gain_dollars": round(max_gain, 2),
            "max_gain_portfolio_pct": round(max_gain / current_equity * 100, 2),
            "risk_reward_ratio": round(max_gain / max_loss, 2) if max_loss > 0 else 0,
            "equity_after_loss": round(current_equity - max_loss, 2),
            "equity_after_gain": round(current_equity + max_gain, 2)
        }
    
    def check_correlation(self, symbol: str, existing_positions: List[Dict]) -> Dict[str, Any]:
        """
        Check correlation between proposed symbol and existing positions.
        
        Args:
            symbol: Proposed symbol
            existing_positions: List of current positions
            
        Returns:
            Correlation analysis
        """
        # Simplified correlation check (would use actual price correlation in production)
        # For crypto, assume BTC correlates highly with most alts
        correlations = {}
        
        for pos in existing_positions:
            pos_symbol = pos.get('symbol', '')
            
            # Simple heuristic correlation
            if 'BTC' in symbol and 'BTC' in pos_symbol:
                correlations[pos_symbol] = 1.0
            elif 'BTC' in symbol or 'BTC' in pos_symbol:
                correlations[pos_symbol] = 0.7  # Most crypto correlates with BTC
            else:
                correlations[pos_symbol] = 0.5  # Alt-to-alt moderate correlation
        
        avg_correlation = sum(correlations.values()) / len(correlations) if correlations else 0
        
        return {
            "symbol": symbol,
            "correlations": correlations,
            "average_correlation": round(avg_correlation, 2),
            "diversification_score": round((1 - avg_correlation) * 100, 1),
            "warning": "High correlation detected" if avg_correlation > 0.8 else None
        }
    
    def fetch_recent_volatility(self, symbol: str, period: int = 30) -> Dict[str, Any]:
        """
        Fetch recent volatility metrics.
        
        Args:
            symbol: Trading pair
            period: Period in days
            
        Returns:
            Volatility metrics
        """
        try:
            binance = BinanceService()
            candles = binance.get_klines(symbol, "1d", limit=period)
            
            if not candles:
                return {"error": "Failed to fetch candle data"}
            
            import pandas as pd
            df = pd.DataFrame(candles)
            closes = df['close'].astype(float)
            
            # Calculate daily returns
            returns = closes.pct_change().dropna()
            
            # Volatility metrics
            volatility = returns.std() * (365 ** 0.5)  # Annualized
            recent_vol = returns.iloc[-7:].std() * (365 ** 0.5)  # Last 7 days
            
            return {
                "symbol": symbol,
                "period_days": period,
                "annualized_volatility": round(volatility * 100, 2),
                "recent_volatility_7d": round(recent_vol * 100, 2),
                "volatility_trend": "increasing" if recent_vol > volatility else "decreasing",
                "volatility_regime": "high" if volatility > 0.6 else "moderate" if volatility > 0.3 else "low"
            }
        except Exception as e:
            return {"error": str(e)}


class TraderTools:
    """Tools available to Trader ReAct agent."""
    
    def __init__(self, db: Session):
        self.db = db
        self.binance = BinanceService()
    
    def fetch_order_book(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """
        Get detailed order book for execution analysis.
        
        Args:
            symbol: Trading pair
            depth: Number of price levels
            
        Returns:
            Order book with analysis
        """
        try:
            order_book = self.binance.get_order_book(symbol, limit=depth)
            
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            # Calculate cumulative volume
            bid_volumes = [float(b[1]) for b in bids]
            ask_volumes = [float(a[1]) for a in asks]
            
            total_bid_volume = sum(bid_volumes)
            total_ask_volume = sum(ask_volumes)
            
            return {
                "symbol": symbol,
                "best_bid": float(bids[0][0]) if bids else None,
                "best_ask": float(asks[0][0]) if asks else None,
                "spread": float(asks[0][0]) - float(bids[0][0]) if bids and asks else None,
                "spread_pct": ((float(asks[0][0]) - float(bids[0][0])) / float(bids[0][0]) * 100) if bids and asks else None,
                "total_bid_volume": round(total_bid_volume, 2),
                "total_ask_volume": round(total_ask_volume, 2),
                "buy_sell_ratio": round(total_bid_volume / total_ask_volume, 2) if total_ask_volume > 0 else 0,
                "market_imbalance": "buy_pressure" if total_bid_volume > total_ask_volume else "sell_pressure"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_recent_fills(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Check recent trade fills for execution quality analysis.
        
        Args:
            symbol: Trading pair
            limit: Number of recent trades
            
        Returns:
            Recent fill analysis
        """
        try:
            trades = self.binance.get_recent_trades(symbol, limit=limit)
            
            if not trades:
                return {"error": "No recent trades found"}
            
            import pandas as pd
            df = pd.DataFrame(trades)
            df['price'] = df['price'].astype(float)
            df['qty'] = df['qty'].astype(float)
            
            # Analyze fills
            avg_price = df['price'].mean()
            price_std = df['price'].std()
            total_volume = df['qty'].sum()
            
            # Buy vs sell pressure
            buy_trades = df[df['isBuyerMaker'] == False]
            sell_trades = df[df['isBuyerMaker'] == True]
            
            return {
                "symbol": symbol,
                "trades_analyzed": len(trades),
                "avg_fill_price": round(avg_price, 2),
                "price_std_dev": round(price_std, 2),
                "total_volume": round(total_volume, 4),
                "buy_count": len(buy_trades),
                "sell_count": len(sell_trades),
                "buy_sell_ratio": round(len(buy_trades) / len(sell_trades), 2) if len(sell_trades) > 0 else 0,
                "market_direction": "buying" if len(buy_trades) > len(sell_trades) else "selling"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def calculate_slippage(
        self,
        symbol: str,
        order_size: float,
        side: str = "buy"
    ) -> Dict[str, Any]:
        """
        Estimate slippage for a given order size.
        
        Args:
            symbol: Trading pair
            order_size: Order size in base currency
            side: "buy" or "sell"
            
        Returns:
            Slippage estimation
        """
        try:
            order_book = self.binance.get_order_book(symbol, limit=100)
            
            levels = order_book.get('asks' if side == "buy" else 'bids', [])
            
            if not levels:
                return {"error": "No order book data"}
            
            # Calculate weighted average fill price
            remaining_size = order_size
            total_cost = 0
            best_price = float(levels[0][0])
            
            for price, volume in levels:
                price = float(price)
                volume = float(volume)
                
                fill_amount = min(remaining_size, volume)
                total_cost += fill_amount * price
                remaining_size -= fill_amount
                
                if remaining_size <= 0:
                    break
            
            avg_fill_price = total_cost / order_size if order_size > 0 else best_price
            slippage_pct = ((avg_fill_price - best_price) / best_price * 100) if side == "buy" else ((best_price - avg_fill_price) / best_price * 100)
            
            return {
                "symbol": symbol,
                "order_size": order_size,
                "side": side,
                "best_price": best_price,
                "estimated_avg_price": round(avg_fill_price, 2),
                "estimated_slippage_pct": round(slippage_pct, 4),
                "estimated_cost": round(abs(slippage_pct) * order_size * best_price / 100, 2),
                "filled": remaining_size == 0,
                "unfilled_amount": remaining_size if remaining_size > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def find_optimal_entry(
        self,
        symbol: str,
        target_price: float,
        support_level: float = None,
        resistance_level: float = None
    ) -> Dict[str, Any]:
        """
        Find optimal entry point based on current market structure.
        
        Args:
            symbol: Trading pair
            target_price: Proposed entry price
            support_level: Known support level
            resistance_level: Known resistance level
            
        Returns:
            Entry point recommendation
        """
        try:
            # Get current price
            ticker = self.binance.get_ticker(symbol)
            current_price = float(ticker.get('lastPrice', 0))
            
            # Get order book for micro structure
            order_book = self.binance.get_order_book(symbol, limit=50)
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            # Find significant bid walls (support)
            bid_walls = []
            if bids:
                avg_bid_vol = sum(float(b[1]) for b in bids) / len(bids)
                bid_walls = [float(b[0]) for b in bids if float(b[1]) > avg_bid_vol * 3]
            
            # Find nearest bid wall to target
            nearest_support = None
            if bid_walls:
                below_target = [b for b in bid_walls if b <= target_price]
                nearest_support = max(below_target) if below_target else None
            
            # Recommendation logic
            if nearest_support and abs(nearest_support - target_price) / target_price < 0.01:
                # Support close to target
                recommendation = nearest_support
                reason = f"Strong bid wall at ${nearest_support:,.2f} provides support near target"
            elif support_level and abs(support_level - target_price) / target_price < 0.015:
                # Known support close to target
                recommendation = support_level
                reason = f"Technical support level at ${support_level:,.2f} aligns with target"
            else:
                recommendation = target_price
                reason = "Target price acceptable, no nearby support to optimize entry"
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "target_price": target_price,
                "recommended_entry": round(recommendation, 2),
                "adjustment_pct": round((recommendation - target_price) / target_price * 100, 2),
                "reason": reason,
                "nearest_support": nearest_support,
                "bid_walls_detected": len(bid_walls)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_exchange_status(self, symbol: str) -> Dict[str, Any]:
        """
        Check if symbol is currently tradable on exchange.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Exchange status for symbol
        """
        try:
            # In production, would check exchange info API
            # For now, return that it's tradable
            return {
                "symbol": symbol,
                "status": "TRADING",
                "is_tradable": True,
                "permissions": ["SPOT", "MARGIN"],
                "filters": "active"
            }
        except Exception as e:
            return {"error": str(e), "is_tradable": False}
