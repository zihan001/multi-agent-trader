"""
LangChain tools for trading agents.

Converts our trading tools into LangChain Tool format for use with
LangChain agents (ReAct, OpenAI Functions, etc.).
"""
from typing import Optional, Dict, Any
from langchain_core.tools import Tool, StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.binance import BinanceService
from app.services.portfolio import PortfolioManager
from app.services.sentiment import SentimentService


# ============================================================================
# RESEARCHER TOOLS
# ============================================================================

class FetchNewsInput(BaseModel):
    """Input for fetch_recent_news."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    hours: int = Field(default=24, description="Number of hours to look back")


class QueryAnalystInput(BaseModel):
    """Input for query_analyst."""
    analyst_name: str = Field(description="Analyst name: technical, sentiment, or tokenomics")
    question: str = Field(description="Specific question to ask the analyst")


class FetchIndicatorsInput(BaseModel):
    """Input for fetch_additional_indicators."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    timeframe: str = Field(default="1h", description="Timeframe for indicators")


class CompareHistoricalInput(BaseModel):
    """Input for compare_historical_patterns."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    pattern_type: str = Field(description="Type of pattern to compare")


class FetchOrderBookSnapshotInput(BaseModel):
    """Input for fetch_order_book_snapshot."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    depth: int = Field(default=10, description="Order book depth")


def create_researcher_tools(db: Session) -> list[Tool]:
    """Create LangChain tools for Researcher agent."""
    binance = BinanceService()
    sentiment_service = SentimentService(db)
    
    def fetch_recent_news(symbol: str, hours: int = 24) -> str:
        """Fetch recent crypto news and sentiment for a symbol."""
        try:
            # Simulate news fetching
            return f"{{\"symbol\": \"{symbol}\", \"timeframe\": \"last_{hours}_hours\", \"sentiment\": \"neutral\", \"headline_count\": 12, \"average_sentiment\": 0.15, \"key_topics\": [\"regulation\", \"adoption\", \"technical_analysis\"]}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to fetch news: {str(e)}\"}}"
    
    def query_analyst(analyst_name: str, question: str) -> str:
        """Query a specific analyst for additional details."""
        try:
            # Return structured response
            return f"{{\"analyst\": \"{analyst_name}\", \"question\": \"{question}\", \"response\": \"Based on current data, the {analyst_name} analysis suggests careful monitoring of key levels.\"}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to query analyst: {str(e)}\"}}"
    
    def fetch_additional_indicators(symbol: str, timeframe: str = "1h") -> str:
        """Fetch additional technical indicators not in main analysis."""
        try:
            # Simulate fetching additional indicators
            return f"{{\"symbol\": \"{symbol}\", \"timeframe\": \"{timeframe}\", \"volume_profile\": \"balanced\", \"orderflow\": \"neutral\", \"market_structure\": \"range\"}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to fetch indicators: {str(e)}\"}}"
    
    def compare_historical_patterns(symbol: str, pattern_type: str) -> str:
        """Compare current pattern to historical occurrences."""
        try:
            return f"{{\"symbol\": \"{symbol}\", \"pattern\": \"{pattern_type}\", \"historical_matches\": 5, \"success_rate\": 0.65, \"average_move\": \"+4.2%\"}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to compare patterns: {str(e)}\"}}"
    
    def fetch_order_book_snapshot(symbol: str, depth: int = 10) -> str:
        """Fetch current order book snapshot."""
        try:
            ticker = binance.get_ticker(symbol)
            return f"{{\"symbol\": \"{symbol}\", \"bid\": {ticker.get('bid', 0)}, \"ask\": {ticker.get('ask', 0)}, \"spread_bps\": {ticker.get('spread_bps', 5)}, \"depth\": {depth}}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to fetch order book: {str(e)}\"}}"
    
    return [
        StructuredTool.from_function(
            func=fetch_recent_news,
            name="fetch_recent_news",
            description="Fetch recent news and sentiment data for a cryptocurrency. Use when analysts conflict or you need current market narrative.",
            args_schema=FetchNewsInput,
        ),
        StructuredTool.from_function(
            func=query_analyst,
            name="query_analyst",
            description="Ask a specific analyst (technical/sentiment/tokenomics) for clarification or additional details.",
            args_schema=QueryAnalystInput,
        ),
        StructuredTool.from_function(
            func=fetch_additional_indicators,
            name="fetch_additional_indicators",
            description="Fetch additional technical indicators like volume profile, order flow, market structure.",
            args_schema=FetchIndicatorsInput,
        ),
        StructuredTool.from_function(
            func=compare_historical_patterns,
            name="compare_historical_patterns",
            description="Compare current chart pattern to historical occurrences and success rates.",
            args_schema=CompareHistoricalInput,
        ),
        StructuredTool.from_function(
            func=fetch_order_book_snapshot,
            name="fetch_order_book_snapshot",
            description="Get current order book snapshot with bid/ask spread and depth.",
            args_schema=FetchOrderBookSnapshotInput,
        ),
    ]


# ============================================================================
# TRADER TOOLS
# ============================================================================

class FetchOrderBookInput(BaseModel):
    """Input for fetch_order_book."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    limit: int = Field(default=20, description="Number of price levels")


class CheckRecentFillsInput(BaseModel):
    """Input for check_recent_fills."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    limit: int = Field(default=50, description="Number of recent trades")


class CalculateSlippageInput(BaseModel):
    """Input for calculate_slippage."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    size: float = Field(description="Trade size in dollars")
    side: str = Field(description="Trade side: buy or sell")


class FindOptimalEntryInput(BaseModel):
    """Input for find_optimal_entry."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    direction: str = Field(description="Trade direction: 'buy' or 'sell' (or 'long'/'short')")
    size: float = Field(description="Trade size in dollars (positive number)")


class CheckExchangeStatusInput(BaseModel):
    """Input for check_exchange_status."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")


def create_trader_tools(db: Session) -> list[Tool]:
    """Create LangChain tools for Trader agent."""
    binance = BinanceService()
    
    def fetch_order_book(symbol: str, limit: int = 20) -> str:
        """Fetch current order book with bid/ask levels."""
        try:
            # Return mock order book data (real Binance order book API requires different endpoint)
            return f"{{\"symbol\": \"{symbol}\", \"best_bid\": 44495.50, \"best_ask\": 44505.50, \"spread_bps\": 2.2, \"bid_liquidity\": 50000, \"ask_liquidity\": 45000}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to fetch order book: {str(e)}\"}}"
    
    def check_recent_fills(symbol: str, limit: int = 50) -> str:
        """Check recent trade fills to assess execution quality."""
        try:
            return f"{{\"symbol\": \"{symbol}\", \"recent_trades\": {limit}, \"avg_size\": 1500, \"largest_trade\": 25000, \"execution_pattern\": \"mixed\"}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to check fills: {str(e)}\"}}"
    
    def calculate_slippage(symbol: str, size: float, side: str) -> str:
        """Calculate expected slippage for trade size."""
        try:
            slippage_bps = max(5, size / 10000)  # Simple model
            return f"{{\"symbol\": \"{symbol}\", \"size\": {size}, \"side\": \"{side}\", \"expected_slippage_bps\": {slippage_bps:.1f}, \"impact\": \"low\"}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to calculate slippage: {str(e)}\"}}"
    
    def find_optimal_entry(symbol: str, direction: str, size: float) -> str:
        """Find optimal entry point based on order book."""
        try:
            # Normalize direction (accept buy/sell or long/short)
            normalized_direction = direction.lower()
            if normalized_direction in ['buy', 'long']:
                normalized_direction = 'long'
            elif normalized_direction in ['sell', 'short']:
                normalized_direction = 'short'
            
            # Use placeholder price (Trader has actual current_price in context)
            price = 44500
            offset = 0.001 if normalized_direction == "long" else -0.001
            optimal_price = price * (1 + offset)
            return f"{{\"symbol\": \"{symbol}\", \"direction\": \"{normalized_direction}\", \"current_price\": {price}, \"optimal_entry\": {optimal_price:.2f}, \"reasoning\": \"Better liquidity at this level\"}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to find optimal entry: {str(e)}\"}}"
    
    def check_exchange_status(symbol: str) -> str:
        """Check if exchange is operational and symbol is tradable."""
        try:
            # Return mock exchange status (assume operational)
            return f"{{\"symbol\": \"{symbol}\", \"status\": \"operational\", \"tradable\": true, \"market_hours\": \"24/7\"}}"
        except Exception as e:
            return f"{{\"error\": \"Exchange status check failed: {str(e)}\"}}"
    
    return [
        StructuredTool.from_function(
            func=fetch_order_book,
            name="fetch_order_book",
            description="Fetch current order book with bid/ask levels and liquidity. Use for execution planning.",
            args_schema=FetchOrderBookInput,
        ),
        StructuredTool.from_function(
            func=check_recent_fills,
            name="check_recent_fills",
            description="Check recent trade fills to assess execution quality and market activity.",
            args_schema=CheckRecentFillsInput,
        ),
        StructuredTool.from_function(
            func=calculate_slippage,
            name="calculate_slippage",
            description="Calculate expected slippage for a given trade size and side.",
            args_schema=CalculateSlippageInput,
        ),
        StructuredTool.from_function(
            func=find_optimal_entry,
            name="find_optimal_entry",
            description="Find optimal entry price based on order book liquidity and direction.",
            args_schema=FindOptimalEntryInput,
        ),
        StructuredTool.from_function(
            func=check_exchange_status,
            name="check_exchange_status",
            description="Check if exchange is operational and symbol is currently tradable.",
            args_schema=CheckExchangeStatusInput,
        ),
    ]


# ============================================================================
# RISK MANAGER TOOLS
# ============================================================================

class GetPortfolioExposureInput(BaseModel):
    """Input for get_portfolio_exposure."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")


class CalculateVaRInput(BaseModel):
    """Input for calculate_var."""
    confidence: float = Field(default=0.95, description="Confidence level (0.95 = 95%)")
    horizon_days: int = Field(default=1, description="Time horizon in days")


class SimulateTradeImpactInput(BaseModel):
    """Input for simulate_trade_impact."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    size: float = Field(description="Trade size in dollars")
    entry_price: float = Field(description="Entry price")
    stop_loss: float = Field(description="Stop loss price")
    take_profit: float = Field(description="Take profit price")


class CheckCorrelationInput(BaseModel):
    """Input for check_correlation."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")


class FetchRecentVolatilityInput(BaseModel):
    """Input for fetch_recent_volatility."""
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    days: int = Field(default=30, description="Number of days for volatility calculation")


def create_risk_manager_tools(db: Session) -> list[Tool]:
    """Create LangChain tools for Risk Manager agent."""
    portfolio_manager = PortfolioManager(db)
    
    def get_portfolio_exposure(symbol: str) -> str:
        """Get current portfolio exposure to a symbol."""
        try:
            positions = portfolio_manager.get_positions()
            exposure = sum(p.current_value for p in positions if p.symbol == symbol)
            total_equity = portfolio_manager.get_portfolio_summary()['total_equity']
            exposure_pct = (exposure / total_equity * 100) if total_equity > 0 else 0
            return f"{{\"symbol\": \"{symbol}\", \"exposure_usd\": {exposure:.2f}, \"exposure_pct\": {exposure_pct:.2f}, \"total_equity\": {total_equity:.2f}}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to get exposure: {str(e)}\"}}"
    
    def calculate_var(confidence: float = 0.95, horizon_days: int = 1) -> str:
        """Calculate Value at Risk for current portfolio."""
        try:
            portfolio = portfolio_manager.get_portfolio_summary()
            # Simple VaR calculation
            var_estimate = portfolio['total_equity'] * 0.02 * (horizon_days ** 0.5)
            return f"{{\"confidence\": {confidence}, \"horizon_days\": {horizon_days}, \"var_usd\": {var_estimate:.2f}, \"var_pct\": {(var_estimate/portfolio['total_equity']*100):.2f}}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to calculate VaR: {str(e)}\"}}"
    
    def simulate_trade_impact(symbol: str, size: float, entry_price: float, stop_loss: float, take_profit: float) -> str:
        """Simulate impact of proposed trade on portfolio risk."""
        try:
            max_loss = abs(entry_price - stop_loss) * (size / entry_price)
            max_gain = abs(take_profit - entry_price) * (size / entry_price)
            risk_reward = max_gain / max_loss if max_loss > 0 else 0
            
            portfolio = portfolio_manager.get_portfolio_summary()
            loss_pct = (max_loss / portfolio['total_equity'] * 100) if portfolio['total_equity'] > 0 else 0
            
            return f"{{\"symbol\": \"{symbol}\", \"max_loss_usd\": {max_loss:.2f}, \"max_loss_pct\": {loss_pct:.2f}, \"max_gain_usd\": {max_gain:.2f}, \"risk_reward\": {risk_reward:.2f}}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to simulate impact: {str(e)}\"}}"
    
    def check_correlation(symbol: str) -> str:
        """Check correlation between symbol and existing positions."""
        try:
            positions = portfolio_manager.get_positions()
            # Simplified correlation check
            return f"{{\"symbol\": \"{symbol}\", \"existing_positions\": {len(positions)}, \"correlation\": \"low\", \"diversification_benefit\": true}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to check correlation: {str(e)}\"}}"
    
    def fetch_recent_volatility(symbol: str, days: int = 30) -> str:
        """Fetch recent volatility metrics for a symbol."""
        try:
            # Simulate volatility data
            return f"{{\"symbol\": \"{symbol}\", \"days\": {days}, \"volatility_pct\": 3.2, \"max_drawdown\": -8.5, \"sharpe_ratio\": 1.2}}"
        except Exception as e:
            return f"{{\"error\": \"Failed to fetch volatility: {str(e)}\"}}"
    
    return [
        StructuredTool.from_function(
            func=get_portfolio_exposure,
            name="get_portfolio_exposure",
            description="Get current portfolio exposure to a specific symbol in dollars and percentage.",
            args_schema=GetPortfolioExposureInput,
        ),
        StructuredTool.from_function(
            func=calculate_var,
            name="calculate_var",
            description="Calculate Value at Risk (VaR) for the portfolio at a given confidence level.",
            args_schema=CalculateVaRInput,
        ),
        StructuredTool.from_function(
            func=simulate_trade_impact,
            name="simulate_trade_impact",
            description="Simulate the impact of a proposed trade on portfolio risk metrics.",
            args_schema=SimulateTradeImpactInput,
        ),
        StructuredTool.from_function(
            func=check_correlation,
            name="check_correlation",
            description="Check correlation between a symbol and existing portfolio positions.",
            args_schema=CheckCorrelationInput,
        ),
        StructuredTool.from_function(
            func=fetch_recent_volatility,
            name="fetch_recent_volatility",
            description="Fetch recent volatility metrics (vol, drawdown, Sharpe) for a symbol.",
            args_schema=FetchRecentVolatilityInput,
        ),
    ]
