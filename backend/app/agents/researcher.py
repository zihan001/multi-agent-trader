"""
Researcher Agent

Synthesizes all analyst outputs into a unified investment thesis.
"""
import json
from typing import Dict, Any, List

from app.agents.base import DecisionAgent


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

Your role is to:
- Integrate technical, sentiment, and fundamental perspectives
- Resolve conflicts between different analyses
- Weigh short-term vs long-term factors
- Identify the strongest conviction signals
- Provide a clear, actionable market thesis

Consider:
- Time horizons (technical = short-term, fundamentals = long-term)
- Conviction levels from each analyst
- Conflicting signals and how to resolve them
- Risk-reward profiles

Provide a balanced, sophisticated synthesis that guides trading decisions."""

        user_prompt = f"""Synthesize the following analyses for {symbol} at ${current_price:,.2f}

TECHNICAL ANALYSIS:
{json.dumps(technical, indent=2)}

SENTIMENT ANALYSIS:
{json.dumps(sentiment, indent=2)}

TOKENOMICS ANALYSIS:
{json.dumps(tokenomics)}

Return JSON with fields: thesis_summary, market_view, conviction_level, time_horizon, analysis_synthesis (technical_weight, sentiment_weight, fundamental_weight, primary_driver), key_bull_cases[], key_bear_cases[], signal_conflicts, catalyst_watch[], risk_factors[], opportunity_assessment (setup_quality, risk_reward, timing), recommended_action, confidence (0-100), reasoning.

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
            
            # Validate required fields
            required_fields = [
                "thesis_summary", "market_view", "conviction_level", "time_horizon",
                "analysis_synthesis", "key_bull_cases", "key_bear_cases",
                "signal_conflicts", "catalyst_watch", "risk_factors",
                "opportunity_assessment", "recommended_action", "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    if field in ["key_bull_cases", "key_bear_cases", "catalyst_watch", "risk_factors"]:
                        analysis[field] = []
                    elif field in ["analysis_synthesis", "opportunity_assessment"]:
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
