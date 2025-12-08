"""
Risk Manager ReAct Agent

Validates trade proposals using ReAct pattern with dynamic risk analysis tools.
"""
from typing import Dict, Any, Callable
from sqlalchemy.orm import Session

from app.agents.react_base import ReActAgent
from app.agents.react_tools import RiskManagerTools
from app.core.config import settings


class RiskManagerReAct(ReActAgent):
    """
    ReAct-enabled Risk Manager that can dynamically query portfolio state
    and perform advanced risk calculations before approving trades.
    """
    
    @property
    def name(self) -> str:
        return "risk_manager_react"
    
    @property
    def role(self) -> str:
        return "Risk Management Specialist (ReAct)"
    
    def initialize_tools(self) -> Dict[str, Callable]:
        """Initialize tools available to Risk Manager."""
        tools_instance = RiskManagerTools(self.db)
        
        return {
            "get_portfolio_exposure": tools_instance.get_portfolio_exposure,
            "calculate_var": tools_instance.calculate_var,
            "simulate_trade_impact": tools_instance.simulate_trade_impact,
            "check_correlation": tools_instance.check_correlation,
            "fetch_recent_volatility": tools_instance.fetch_recent_volatility,
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
        - trade_proposal: Output from Trader
        - portfolio_info: Current portfolio state
        - available_cash: Cash available for trading
        - total_equity: Total portfolio value
        - current_positions: List of open positions
        """
        symbol = context.get("symbol", "UNKNOWN")
        current_price = context.get("current_price", 0)
        trade_proposal = context.get("trade_proposal", {})
        available_cash = context.get("available_cash", 0)
        total_equity = context.get("total_equity", 0)
        
        # Extract trade details
        action = trade_proposal.get("action", "hold")
        size = trade_proposal.get("size", 0)
        entry_price = trade_proposal.get("entry_price", 0)
        stop_loss = trade_proposal.get("stop_loss", 0)
        take_profit = trade_proposal.get("take_profit", 0)
        
        task_description = f"""Validate and potentially adjust this trade proposal for {symbol} at ${current_price:,.2f}

**TRADE PROPOSAL:**
- Action: {action}
- Size: ${size:,.2f} ({size / total_equity * 100:.1f}% of portfolio)
- Entry Price: ${entry_price:,.2f}
- Stop Loss: ${stop_loss:,.2f} ({(stop_loss - entry_price) / entry_price * 100:.1f}% from entry)
- Take Profit: ${take_profit:,.2f} ({(take_profit - entry_price) / entry_price * 100:.1f}% from entry)

**PORTFOLIO STATE:**
- Total Equity: ${total_equity:,.2f}
- Available Cash: ${available_cash:,.2f}
- Cash Utilization: {(size / available_cash * 100):.1f}% if executed

**RISK RULES TO ENFORCE:**
- Max position size: {settings.max_position_size_pct * 100}% of portfolio
- Max total exposure: {settings.max_total_exposure_pct * 100}% of portfolio
- Max loss per trade: 2% of portfolio
- Min risk-reward ratio: 1.5:1
- Stop loss: Required and reasonable

**YOUR TASK:**
1. Check current portfolio exposure for this symbol (use get_portfolio_exposure)
2. Calculate risk metrics (use simulate_trade_impact, calculate_var)
3. Check volatility to validate stop loss distance (use fetch_recent_volatility)
4. Check correlation with existing positions (use check_correlation)
5. Verify all risk rules are satisfied
6. Decide: APPROVE, MODIFY (with adjustments), or REJECT (with reason)

**FINAL ANSWER FORMAT** (JSON):
{{
    "decision": "approved" | "modified" | "rejected",
    "reasoning": "Clear explanation of decision",
    "risk_checks_performed": ["check1", "check2", ...],
    "violations_found": ["violation1", ...] or [],
    "final_trade": {{
        "action": "buy" | "sell" | "hold",
        "size": float,
        "entry_price": float,
        "stop_loss": float,
        "take_profit": float,
        "modifications_made": "What was changed and why" or null
    }},
    "risk_metrics": {{
        "max_loss_dollars": float,
        "max_loss_portfolio_pct": float,
        "risk_reward_ratio": float,
        "position_size_pct": float,
        "total_exposure_pct": float
    }},
    "confidence": 0-100
}}

If rejecting, set final_trade.action to "hold" and explain in reasoning."""
        
        result = await self.react_loop(
            task_description=task_description,
            context=context,
            temperature=kwargs.get("temperature", 0.7)
        )
        
        return result
