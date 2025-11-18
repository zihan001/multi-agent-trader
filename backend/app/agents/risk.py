"""
Risk Manager Agent

Validates and adjusts trade proposals to enforce risk limits.
"""
import json
from typing import Dict, Any, List

from app.agents.base import DecisionAgent
from app.core.config import settings


class RiskManager(DecisionAgent):
    """
    Final gatekeeper that validates trade proposals against risk rules.
    
    Enforces:
    - Position sizing limits
    - Portfolio exposure limits
    - Stop loss requirements
    - Risk-reward ratios
    - Account protection rules
    """
    
    @property
    def name(self) -> str:
        return "risk_manager"
    
    @property
    def role(self) -> str:
        return "Risk Management Specialist"
    
    def build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build prompt for risk validation.
        
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
        portfolio = context.get("portfolio_info", {})
        available_cash = context.get("available_cash", 0)
        total_equity = context.get("total_equity", 0)
        current_positions = context.get("current_positions", [])
        
        # Calculate current exposure
        total_position_value = sum(pos.get("value", 0) for pos in current_positions)
        current_exposure_pct = (total_position_value / total_equity * 100) if total_equity > 0 else 0
        
        system_prompt = f"""You are a risk management specialist responsible for protecting trading capital.

Your role is to:
- Validate trade proposals against risk limits
- Adjust position sizes if too aggressive
- Ensure stop losses are appropriate
- Verify risk-reward ratios are acceptable
- Reject trades that violate risk rules
- Protect against excessive portfolio concentration

RISK LIMITS:
- Max position size: {settings.max_position_size_pct * 100}% of portfolio
- Max total exposure: {settings.max_total_exposure_pct * 100}% of portfolio
- Minimum risk-reward ratio: 1.5:1
- Required stop loss: Yes, always
- Max loss per trade: 2% of portfolio

Your primary duty is capital preservation. Be conservative and err on the side of caution."""

        user_prompt = f"""Review this trade proposal for {symbol} at ${current_price:,.2f}

TRADE PROPOSAL:
{json.dumps(trade_proposal, indent=2)}

PORTFOLIO STATE:
- Total Equity: ${total_equity:,.2f}
- Available Cash: ${available_cash:,.2f}
- Current Exposure: {current_exposure_pct:.1f}%
- Open Positions: {len(current_positions)}

CURRENT POSITIONS:
{json.dumps(current_positions)}

Return JSON with fields: decision, risk_assessment (position_size_check, exposure_check, stop_loss_check, risk_reward_check, concentration_check), modifications (position_size_usd, stop_loss, take_profit, reasoning), final_trade (action, size_usd, entry_price, stop_loss, take_profit, max_loss_pct), risk_metrics (position_size_pct, new_total_exposure_pct, max_loss_usd, max_loss_pct_portfolio, risk_reward_ratio, passes_all_checks), concerns[], recommendations[], rejection_reason, confidence (0-100), reasoning. Reject/modify trades violating risk rules.

Respond ONLY with valid JSON."""

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
            Structured risk assessment
        """
        try:
            # Strip markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                # Remove ```json and closing ```
                lines = response.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response = "\n".join(lines)
            
            # Try to parse as JSON
            assessment = json.loads(response)
            
            # Validate required fields
            required_fields = [
                "decision", "risk_assessment", "modifications", "final_trade",
                "risk_metrics", "concerns", "recommendations",
                "rejection_reason", "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in assessment:
                    if field in ["concerns", "recommendations"]:
                        assessment[field] = []
                    elif field in ["risk_assessment", "modifications", "final_trade", "risk_metrics"]:
                        assessment[field] = {}
                    else:
                        assessment[field] = None
            
            # Ensure confidence is a number
            if isinstance(assessment.get("confidence"), str):
                assessment["confidence"] = int(assessment["confidence"])
            
            # Validate decision is one of expected values
            valid_decisions = ["approved", "rejected", "modified"]
            if assessment.get("decision") not in valid_decisions:
                assessment["decision"] = "rejected"
                assessment["rejection_reason"] = "Invalid decision format"
            
            # Ensure final_trade.action is valid
            valid_actions = ["buy", "sell", "hold", "close"]
            if assessment.get("final_trade", {}).get("action") not in valid_actions:
                assessment["final_trade"]["action"] = "hold"
            
            return assessment
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return safe default (reject)
            return {
                "decision": "rejected",
                "risk_assessment": {},
                "modifications": {},
                "final_trade": {
                    "action": "hold",
                    "size_usd": 0,
                    "entry_price": None,
                    "stop_loss": None,
                    "take_profit": None,
                    "max_loss_pct": 0
                },
                "risk_metrics": {},
                "concerns": ["Failed to parse risk assessment"],
                "recommendations": ["Review trade manually"],
                "rejection_reason": f"Parse error: {response[:200]}",
                "confidence": 0,
                "reasoning": "Failed to parse risk assessment - rejecting for safety",
                "parse_error": True
            }
