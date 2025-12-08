"""
Trader Agent

Proposes specific trades based on research thesis.
"""
import json
from typing import Dict, Any, List, Type
from pydantic import BaseModel

from app.agents.base import DecisionAgent
from app.agents.models import TradeProposal


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
    
    def get_response_model(self) -> Type[BaseModel]:
        """Return Pydantic model for structured outputs."""
        return TradeProposal
    
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

**CHAIN-OF-THOUGHT REASONING REQUIRED:**
1. First, interpret the research thesis and conviction level
2. Determine if thesis is actionable (skip trades with low conviction)
3. Calculate appropriate position size based on conviction
4. Identify optimal entry points and price ranges
5. Set risk parameters (stop loss, take profit)
6. Assess execution timing and urgency

**FEW-SHOT EXAMPLE:**
Good Trade Proposal:
- "Research shows high-conviction bullish thesis (82% conf). Current price $44,500, support at $43,800. Proposal: Buy 5% of portfolio ($5,000) at $44,200-$44,500 range. Stop loss at $43,600 (-1.8%), take profit at $46,500 (+4.5%). Risk-reward: 2.5:1. Execution: Limit order, good timing as price consolidates near support."

Poor Trade Proposal:
- "Buy some BTC. Put stop loss somewhere below."

**CONFIDENCE-TO-SIZE MAPPING (AGGRESSIVE TRADING):**
- High conviction (80-100): 4-6% position size (increased for aggression)
- Medium conviction (50-79): 2-4% position size (take medium conviction trades!)
- Low conviction (40-49): 0.5-1% position size (small speculative positions)
- Very low conviction (<40): HOLD

**UPDATED TRADING PHILOSOPHY:**
We favor ACTION over waiting. If research conviction is ≥40% AND direction is clear (not neutral), propose a trade. 
Small positions on lower conviction still capture opportunities. Only HOLD if:
1. Conviction < 40%, OR
2. Research direction is explicitly "neutral" with no bias

Provide specific, actionable trade proposals. Err on the side of taking positions."""

        user_prompt = f"""Propose a trade for {symbol} at ${current_price:,.2f}

RESEARCH THESIS:
{json.dumps(research, indent=2)}

PORTFOLIO INFORMATION:
{json.dumps(portfolio, indent=2)}

AVAILABLE CASH: ${available_cash:,.2f}

**REQUIRED TRADE PLANNING STEPS:**
1. Thesis Interpretation: What's the research conviction level and direction?
2. Actionability Check: Is conviction ≥40% AND direction non-neutral? If yes, trade!
3. Position Sizing: Calculate size based on conviction (use mapping above)
4. Entry Planning: Where to enter? What price range?
5. Risk Management: Set stop loss and take profit levels
6. Execution Timing: When to execute? How urgent?

**AGGRESSIVE APPROACH:** Only HOLD if conviction < 40% OR direction is neutral with no edge.

Return JSON with fields:
- thought_process: string (your step-by-step trade planning reasoning)
- action: string (buy/sell/hold/close)
- urgency: string (immediate/soon/no_rush/hold)
- trade_rationale: string
- conviction_check: object (research_confidence, passes_threshold, size_justification)
- entry_strategy: object (recommended_price, price_range, order_type, timing)
- position_sizing: object (recommended_size_usd, recommended_size_pct, rationale)
- exit_strategy: object (take_profit_levels: array, stop_loss, trailing_stop)
- risk_assessment: object (max_loss_usd, max_loss_pct, reward_risk_ratio, key_risks: array)
- execution_notes: string
- time_horizon: string (scalp/day_trade/swing/position)
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
            Structured trade proposal
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
            proposal = json.loads(response)
            
            # Validate required fields (now includes thought_process and conviction_check)
            required_fields = [
                "thought_process", "action", "urgency", "trade_rationale", "conviction_check",
                "entry_strategy", "position_sizing", "exit_strategy", "risk_assessment",
                "execution_notes", "time_horizon", "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in proposal:
                    if field in ["entry_strategy", "position_sizing", "exit_strategy", "risk_assessment", "conviction_check"]:
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
                "thought_process": "Error parsing LLM response",
                "action": "hold",
                "urgency": "no_rush",
                "trade_rationale": "Error parsing trade proposal",
                "conviction_check": {},
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
