"""
Researcher Agent

Synthesizes all analyst outputs into a unified investment thesis.
"""
import json
from typing import Dict, Any, List, Type
from pydantic import BaseModel

from app.agents.base import DecisionAgent
from app.agents.models import ResearchSynthesis


class Researcher(DecisionAgent):
    """
    Synthesizes analysis from Technical, Sentiment, and Tokenomics analysts
    into a coherent investment thesis.
    
    Weighs different perspectives and resolves conflicts to provide
    a unified market view and recommendation.
    """
    
    @property
    def name(self) -> str:
        return "researcher"
    
    @property
    def role(self) -> str:
        return "Research Synthesizer"
    
    def get_response_model(self) -> Type[BaseModel]:
        """Return Pydantic model for structured outputs."""
        return ResearchSynthesis
    
    def build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build prompt for research synthesis.
        
        Expected context keys:
        - symbol: Trading pair symbol
        - current_price: Latest price
        - technical_analysis: Output from Technical Analyst
        - sentiment_analysis: Output from Sentiment Analyst
        - tokenomics_analysis: Output from Tokenomics Analyst
        """
        symbol = context.get("symbol", "UNKNOWN")
        current_price = context.get("current_price", 0)
        technical = context.get("technical_analysis", {})
        sentiment = context.get("sentiment_analysis", {})
        tokenomics = context.get("tokenomics_analysis", {})
        
        system_prompt = f"""You are a senior research analyst responsible for synthesizing multiple analyses into a unified investment thesis.

**CHAIN-OF-THOUGHT REASONING REQUIRED:**
1. First, review each analyst's recommendation and confidence level
2. Identify areas of agreement and disagreement
3. Weigh each perspective based on confidence and time horizon
4. Resolve conflicts by prioritizing strongest signals
5. Synthesize into a coherent investment thesis
6. Assess overall conviction level

**FEW-SHOT EXAMPLE:**
Good Synthesis:
- "Technical (85% conf): Strong bullish trend. Sentiment (45% conf): Neutral-to-positive. Tokenomics (70% conf): Fairly valued. Analysis: Technical strength is highly confident and confirmed by fundamentals. Sentiment uncertainty is less critical given strong technical setup. THESIS: High-conviction bullish, but monitor sentiment for reversal signals."

Poor Synthesis:
- "Two analysts are bullish. One is neutral. So we're bullish."

**CONFLICT RESOLUTION RULES:**
1. High-confidence signals override low-confidence signals
2. Technical analysis weighted more for short-term trades
3. Fundamentals weighted more for position trades
4. Extreme sentiment can override technical/fundamental consensus
5. When analysts disagree strongly, reduce overall conviction

**CONFIDENCE GUIDELINES:**
- High conviction (80-100): Strong agreement across analysts, high confidence levels
- Medium conviction (50-79): Majority agreement, some conflicts resolved
- Low conviction (40-49): Moderate disagreement, but tradeable signals exist
- Very low conviction (<40): Significant disagreement, conflicting signals

**TRADING BIAS:**
Favor actionable trades over holding. If 2 out of 3 analysts agree with confidence >50%, consider it actionable even if the third disagrees. Markets reward decisive action - sitting on the sidelines has opportunity cost. Look for tradeable setups, not perfect alignment.

Provide a synthesis that identifies trading opportunities and actionable setups."""

        user_prompt = f"""Synthesize the following analyses for {symbol} at ${current_price:,.2f}

TECHNICAL ANALYSIS:
{json.dumps(technical, indent=2)}

SENTIMENT ANALYSIS:
{json.dumps(sentiment, indent=2)}

TOKENOMICS ANALYSIS:
{json.dumps(tokenomics, indent=2)}

**REQUIRED SYNTHESIS STEPS:**
1. Agreement Analysis: Where do analysts agree/disagree?
2. Confidence Weighting: Which signals are most confident?
3. Conflict Resolution: How to resolve disagreements?
4. Time Horizon Assessment: Short-term vs long-term outlook
5. Thesis Formulation: What's the unified investment view?
6. Conviction Determination: How confident are we overall?

**IMPORTANT:** If overall confidence from analysts is low (<60 average), recommend HOLD unless there's a compelling contrarian opportunity.

Return JSON with fields:
- thought_process: string (your step-by-step synthesis reasoning)
- analyst_summary: object (technical_confidence, sentiment_confidence, tokenomics_confidence, agreement_level)
- thesis_summary: string
- market_view: string (strongly_bullish/bullish/neutral/bearish/strongly_bearish)
- conviction_level: string (high/medium/low)
- time_horizon: string (short_term/medium_term/long_term/mixed)
- analysis_synthesis: object (technical_weight, sentiment_weight, fundamental_weight, primary_driver, conflict_resolution)
- key_bull_cases: array of strings
- key_bear_cases: array of strings
- signal_conflicts: string
- catalyst_watch: array of strings
- risk_factors: array of strings
- opportunity_assessment: object (setup_quality, risk_reward, timing)
- recommended_action: string (strong_buy/buy/hold/sell/strong_sell)
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
            Structured research synthesis
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
            analysis = json.loads(response)
            
            # Validate required fields (now includes thought_process and analyst_summary)
            required_fields = [
                "thought_process", "analyst_summary", "thesis_summary", "market_view", "conviction_level", "time_horizon",
                "analysis_synthesis", "key_bull_cases", "key_bear_cases",
                "signal_conflicts", "catalyst_watch", "risk_factors",
                "opportunity_assessment", "recommended_action", "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    if field in ["key_bull_cases", "key_bear_cases", "catalyst_watch", "risk_factors"]:
                        analysis[field] = []
                    elif field in ["analysis_synthesis", "opportunity_assessment", "analyst_summary"]:
                        analysis[field] = {}
                    else:
                        analysis[field] = None
            
            # Ensure confidence is a number
            if isinstance(analysis.get("confidence"), str):
                analysis["confidence"] = int(analysis["confidence"])
            
            return analysis
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return error structure
            return {
                "thought_process": "Error parsing LLM response",
                "analyst_summary": {},
                "thesis_summary": "Failed to synthesize analysis",
                "market_view": "neutral",
                "conviction_level": "low",
                "time_horizon": "mixed",
                "analysis_synthesis": {},
                "key_bull_cases": [],
                "key_bear_cases": [],
                "signal_conflicts": "unknown",
                "catalyst_watch": [],
                "risk_factors": [],
                "opportunity_assessment": {},
                "recommended_action": "hold",
                "confidence": 0,
                "reasoning": f"Failed to parse response: {response[:200]}",
                "parse_error": True
            }
