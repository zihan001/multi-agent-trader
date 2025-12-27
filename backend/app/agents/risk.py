"""
Risk Manager Agent

Validates and adjusts trade proposals to enforce risk limits.
"""
import json
from typing import Dict, Any, List, Type
from pydantic import BaseModel

from app.agents.base import DecisionAgent
from app.agents.models import RiskValidation
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
    
    def get_response_model(self) -> Type[BaseModel]:
        """Return Pydantic model for structured outputs."""
        return RiskValidation
    
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

**CHAIN-OF-THOUGHT REASONING REQUIRED:**
1. First, review the trade proposal and research thesis
2. Check each risk rule systematically
3. Calculate actual risk metrics
4. Identify any violations or concerns
5. Determine if modifications are needed
6. Make final approve/modify/reject decision

**RISK VALIDATION CHECKLIST:**
□ Position size within limits? (Max {settings.max_position_size_pct * 100}% of portfolio)
□ Total exposure acceptable? (Max {settings.max_total_exposure_pct * 100}% of portfolio)
□ Stop loss properly set? (Required, reasonable distance)
□ Risk-reward ratio adequate? (Min 1.2:1, lower threshold for aggressive trading)
□ Max loss per trade reasonable? (Max 2% of portfolio)
□ Trade conviction sufficient? (Min 40% from research, lowered for more trades)
□ Portfolio not over-concentrated? (Check correlation)

**FEW-SHOT EXAMPLE:**
Good Risk Assessment:
- "Proposal: Buy $5,000 (5% of $100k portfolio). Stop loss at -1.8%, take profit at +4.5%. Risk-Reward: 2.5:1 ✓. Max loss: $90 (0.09% portfolio) ✓. Current exposure: 15%, new total: 20% (under 80% limit) ✓. Research conviction: 82% ✓. All checks passed. DECISION: Approved."

Poor Risk Assessment:
- "Looks okay. Approved."

**COLLABORATIVE VALIDATION:**
You can request clarification from the Trader if:
- Stop loss seems too tight or too wide
- Position size doesn't match conviction level
- Risk-reward ratio is unclear
- Execution timing is ambiguous

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
{json.dumps(current_positions, indent=2)}

**REQUIRED VALIDATION STEPS:**
1. Rule Checking: Go through each risk rule systematically
2. Metric Calculation: Calculate actual risk metrics
3. Violation Detection: Identify any rule violations
4. Modification Assessment: Can we fix issues or must reject?
5. Final Decision: Approve/Modify/Reject with clear reasoning

**VALIDATION RULES:**
- Position Size: Max {settings.max_position_size_pct * 100}% per position
- Total Exposure: Max {settings.max_total_exposure_pct * 100}% across all positions
- Stop Loss: Required, reasonable distance (0.5-5% typical)
- Risk-Reward: Minimum 1.2:1 ratio (lowered for aggressive trading)
- Max Loss: Maximum 2% of portfolio per trade
- Conviction: Minimum 40% from research/trader (lowered to enable more trades)

Return JSON with fields:
- thought_process: string (your step-by-step validation reasoning)
- decision: string (approved/rejected/modified)
- risk_assessment: object (position_size_check: object with passes/value/limit, exposure_check: object, stop_loss_check: object, risk_reward_check: object, concentration_check: object, conviction_check: object)
- modifications: object (position_size_usd, stop_loss, take_profit, reasoning)
- final_trade: object (action, size_usd, entry_price, stop_loss, take_profit, max_loss_pct) or null if rejected
- risk_metrics: object (position_size_pct, new_total_exposure_pct, max_loss_usd, max_loss_pct_portfolio, risk_reward_ratio, passes_all_checks)
- concerns: array of strings
- recommendations: array of strings
- rejection_reason: string or null
- confidence: number (0-100)
- reasoning: string

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
            
            # Validate required fields (now includes thought_process)
            required_fields = [
                "thought_process", "decision", "risk_assessment", "modifications", "final_trade",
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
            
            # Ensure take_profit and stop_loss are single values, not lists
            final_trade = assessment.get("final_trade", {})
            if isinstance(final_trade.get("take_profit"), list):
                # Take the first value if it's a list
                final_trade["take_profit"] = float(final_trade["take_profit"][0]) if final_trade["take_profit"] else None
            if isinstance(final_trade.get("stop_loss"), list):
                # Take the first value if it's a list
                final_trade["stop_loss"] = float(final_trade["stop_loss"][0]) if final_trade["stop_loss"] else None
            
            return assessment
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return safe default (reject)
            return {
                "thought_process": "Error parsing LLM response",
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
