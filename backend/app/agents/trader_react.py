"""
Trader ReAct Agent

Proposes specific trades using ReAct pattern with execution analysis tools.
"""
from typing import Dict, Any, Callable
from sqlalchemy.orm import Session

from app.agents.react_base import ReActAgent
from app.agents.react_tools import TraderTools


class TraderReAct(ReActAgent):
    """
    ReAct-enabled Trader that can dynamically analyze order books,
    check execution quality, and optimize entry points before proposing trades.
    """
    
    @property
    def name(self) -> str:
        return "trader_react"
    
    @property
    def role(self) -> str:
        return "Trading Decision Maker (ReAct)"
    
    def initialize_tools(self) -> Dict[str, Callable]:
        """Initialize tools available to Trader."""
        tools_instance = TraderTools(self.db)
        
        return {
            "fetch_order_book": tools_instance.fetch_order_book,
            "check_recent_fills": tools_instance.check_recent_fills,
            "calculate_slippage": tools_instance.calculate_slippage,
            "find_optimal_entry": tools_instance.find_optimal_entry,
            "check_exchange_status": tools_instance.check_exchange_status,
        }
    
    def build_prompt(self, context: Dict[str, Any]):
        """Build prompt - not used in ReAct mode."""
        raise NotImplementedError("ReAct agents use build_react_prompt()")
    
    def parse_response(self, response: str):
        """Parse response - not used in ReAct mode."""
        raise NotImplementedError("ReAct agents use parse_react_response()")
    
    async def analyze(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Analyze using ReAct loop.
        
        Expected context keys:
        - symbol: Trading pair symbol
        - current_price: Latest price
        - research_thesis: Output from Researcher
        - portfolio_info: Current portfolio state
        - available_cash: Cash available for trading
        """
        symbol = context.get("symbol", "UNKNOWN")
        current_price = context.get("current_price", 0)
        research = context.get("research_thesis", {})
        available_cash = context.get("available_cash", 0)
        
        # Extract research details
        direction = research.get("direction", "neutral")
        conviction = research.get("conviction", 0)
        thesis = research.get("investment_thesis", "No thesis provided")
        time_horizon = research.get("time_horizon", "short_term")
        
        task_description = f"""Convert this research thesis into a specific trade proposal for {symbol} at ${current_price:,.2f}

**RESEARCH THESIS:**
- Direction: {direction}
- Conviction: {conviction}%
- Time Horizon: {time_horizon}
- Thesis: {thesis}

**PORTFOLIO INFO:**
- Available Cash: ${available_cash:,.2f}

**CONVICTION-TO-SIZE GUIDELINES:**
- High conviction (80-100%): 3-5% of portfolio
- Medium conviction (60-79%): 1-3% of portfolio
- Low conviction (<60%): HOLD - do not trade

**YOUR TASK:**
1. First, check if conviction is sufficient to trade (>=60%)
2. If not trading, recommend HOLD
3. If trading:
   a. Check exchange status (use check_exchange_status)
   b. Analyze order book for entry optimization (use fetch_order_book)
   c. Check recent fills for market direction (use check_recent_fills)
   d. Find optimal entry point (use find_optimal_entry)
   e. Calculate expected slippage (use calculate_slippage)
   f. Set stop loss and take profit based on thesis and volatility
   g. Calculate appropriate position size based on conviction

**FINAL ANSWER FORMAT** (JSON):
{{
    "action": "buy" | "sell" | "hold",
    "reasoning": "Clear explanation of trade decision",
    "size": float (dollars),
    "entry_price": float,
    "entry_range_low": float,
    "entry_range_high": float,
    "stop_loss": float,
    "take_profit": float,
    "risk_reward_ratio": float,
    "execution_strategy": "market" | "limit" | "scaled",
    "urgency": "immediate" | "patient" | "none",
    "market_conditions": "Summary of order book / recent fills analysis",
    "conviction": 0-100,
    "tools_used": ["tool1", "tool2", ...]
}}

If conviction < 60%, recommend HOLD with action="hold"."""
        
        result = await self.react_loop(
            task_description=task_description,
            context=context,
            temperature=kwargs.get("temperature", 0.7)
        )
        
        return result
