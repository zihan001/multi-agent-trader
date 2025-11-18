"""
Trader Agent

Proposes specific trades based on research thesis.
"""
import json
from typing import Dict, Any, List

from app.agents.base import DecisionAgent


class Trader(DecisionAgent):
    """
    Converts research thesis into specific trade proposals.
    
    Determines:
    - Entry/exit prices
    - Position sizing
    - Stop loss and take profit levels
    - Trade timing and urgency
    """
    
    @property
    def name(self) -> str:
        return "trader"
    
    @property
    def role(self) -> str:
        return "Trading Decision Maker"
    
    def build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build prompt for trade proposal.
        
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
        portfolio = context.get("portfolio_info", {})
        available_cash = context.get("available_cash", 0)
        
        system_prompt = f"""You are an expert trader responsible for executing investment theses through specific trade proposals.

Your role is to:
- Convert research insights into concrete trade plans
- Determine optimal entry and exit points
- Size positions appropriately
- Set stop losses and take profit targets
- Assess trade timing and urgency

Consider:
- Risk management principles
- Market liquidity and slippage
- Current portfolio exposure
- Trade execution feasibility

Provide specific, actionable trade proposals with clear parameters."""

        user_prompt = f"""Propose a trade for {symbol} at ${current_price:,.2f}

RESEARCH THESIS:
{json.dumps(research, indent=2)}

PORTFOLIO INFORMATION:
{json.dumps(portfolio, indent=2)}

AVAILABLE CASH: ${available_cash:,.2f}

Provide your trade proposal in JSON format with the following structure:
{{
    "action": "buy|sell|hold|close",
    "urgency": "immediate|soon|wait|no_rush",
    "trade_rationale": "why this trade makes sense now",
    "entry_strategy": {{
        "recommended_price": price to enter (or null for market order),
        "price_range": {{
            "min": minimum acceptable entry,
            "max": maximum acceptable entry
        }},
        "order_type": "market|limit|stop_limit",
        "timing": "immediate|wait_for_dip|wait_for_breakout"
    }},
    "position_sizing": {{
        "recommended_size_usd": dollar amount to invest,
        "recommended_size_pct": percentage of available cash,
        "rationale": "why this size is appropriate"
    }},
    "exit_strategy": {{
        "take_profit_levels": [
            {{"price": target1, "size_pct": percentage_to_sell, "reasoning": "why this level"}},
            {{"price": target2, "size_pct": percentage_to_sell, "reasoning": "why this level"}}
        ],
        "stop_loss": {{
            "price": stop_loss_price,
            "reasoning": "why this level"
        }},
        "trailing_stop": {{
            "enabled": true|false,
            "percentage": percentage_below_peak
        }}
    }},
    "risk_assessment": {{
        "max_loss_usd": maximum potential loss,
        "max_loss_pct": percentage of position,
        "reward_risk_ratio": expected_gain / max_loss,
        "key_risks": ["risk 1", "risk 2", ...]
    }},
    "execution_notes": "any special considerations for execution",
    "time_horizon": "scalp|day|swing|position",
    "confidence": 0-100,
    "reasoning": "detailed explanation of trade proposal"
}}

If the recommendation is "hold" or "no trade", explain why and what conditions would trigger a trade.

Respond ONLY with valid JSON, no additional text."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured trade proposal
        """
        try:
            # Try to parse as JSON
            proposal = json.loads(response)
            
            # Validate required fields
            required_fields = [
                "action", "urgency", "trade_rationale", "entry_strategy",
                "position_sizing", "exit_strategy", "risk_assessment",
                "execution_notes", "time_horizon", "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in proposal:
                    if field in ["entry_strategy", "position_sizing", "exit_strategy", "risk_assessment"]:
                        proposal[field] = {}
                    else:
                        proposal[field] = None
            
            # Ensure confidence is a number
            if isinstance(proposal.get("confidence"), str):
                proposal["confidence"] = int(proposal["confidence"])
            
            # Validate action is one of expected values
            valid_actions = ["buy", "sell", "hold", "close"]
            if proposal.get("action") not in valid_actions:
                proposal["action"] = "hold"
            
            return proposal
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return safe default (hold)
            return {
                "action": "hold",
                "urgency": "no_rush",
                "trade_rationale": "Error parsing trade proposal",
                "entry_strategy": {},
                "position_sizing": {},
                "exit_strategy": {},
                "risk_assessment": {},
                "execution_notes": "Parse error - holding position",
                "time_horizon": "position",
                "confidence": 0,
                "reasoning": f"Failed to parse response: {response[:200]}",
                "parse_error": True
            }
