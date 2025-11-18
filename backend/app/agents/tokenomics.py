"""
Tokenomics Analyst Agent

Assesses fundamental token metrics and on-chain data.
"""
import json
from typing import Dict, Any, List

from app.agents.base import AnalystAgent


class TokenomicsAnalyst(AnalystAgent):
    """
    Analyzes tokenomics and fundamental metrics.
    
    Examines:
    - Token supply and distribution
    - Market cap and liquidity
    - On-chain metrics (holders, transactions)
    - Token utility and use cases
    - Competitive positioning
    """
    
    @property
    def name(self) -> str:
        return "tokenomics_analyst"
    
    @property
    def role(self) -> str:
        return "Tokenomics & Fundamentals Specialist"
    
    def build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build prompt for tokenomics analysis.
        
        Expected context keys:
        - symbol: Trading pair symbol
        - token_data: Fundamental token information
        - market_cap: Market capitalization
        - volume_24h: 24h trading volume
        - current_price: Latest price
        """
        symbol = context.get("symbol", "UNKNOWN")
        current_price = context.get("current_price", 0)
        market_cap = context.get("market_cap", 0)
        volume_24h = context.get("volume_24h", 0)
        token_data = context.get("token_data", {})
        
        # Default token data if not provided
        if not token_data:
            token_data = {
                "total_supply": "N/A",
                "circulating_supply": "N/A",
                "max_supply": "N/A",
                "holders": "N/A",
                "token_type": "utility/governance/security",
                "blockchain": "network name",
                "use_cases": "primary token utilities"
            }
        
        # Calculate volume-to-market-cap ratio
        volume_mcap_ratio = (volume_24h / market_cap * 100) if market_cap > 0 else 0
        
        system_prompt = f"""You are an expert tokenomics analyst specializing in cryptocurrency fundamentals.

Your role is to assess the fundamental value and structure of crypto assets based on:
- Token supply dynamics and inflation
- Market cap and liquidity analysis
- On-chain metrics and holder distribution
- Token utility and real-world use cases
- Competitive advantages and positioning

Provide objective fundamental analysis to determine long-term viability and fair value."""

        user_prompt = f"""Analyze the tokenomics and fundamentals for {symbol}.

CURRENT PRICE: ${current_price:,.2f}
MARKET CAP: ${market_cap:,.0f}
24H VOLUME: ${volume_24h:,.0f}
VOLUME/MCAP RATIO: {volume_mcap_ratio:.2f}%

TOKEN DATA:
{json.dumps(token_data, indent=2)}

Provide your analysis in JSON format with the following structure:
{{
    "fundamental_rating": "strong|good|fair|weak|poor",
    "value_assessment": "overvalued|fairly_valued|undervalued",
    "supply_analysis": {{
        "inflation_rate": "high|moderate|low|deflationary",
        "supply_distribution": "concentrated|balanced|distributed",
        "unlock_schedule": "concerns about upcoming unlocks or emissions"
    }},
    "liquidity_analysis": {{
        "market_cap_size": "large|mid|small cap",
        "trading_liquidity": "high|moderate|low",
        "volume_quality": "assessment of volume/mcap ratio"
    }},
    "utility_assessment": {{
        "use_cases": "description of token utility",
        "network_activity": "high|moderate|low on-chain activity",
        "real_world_adoption": "assessment of actual usage"
    }},
    "competitive_position": "market position vs competitors",
    "strengths": ["strength 1", "strength 2", ...],
    "weaknesses": ["weakness 1", "weakness 2", ...],
    "key_risks": ["risk 1", "risk 2", ...],
    "key_observations": ["observation 1", "observation 2", ...],
    "long_term_outlook": "bullish|neutral|bearish",
    "trading_implication": "accumulate|buy|hold|reduce|sell",
    "confidence": 0-100,
    "reasoning": "brief explanation of fundamental analysis"
}}

Consider both quantitative metrics and qualitative factors.

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
            Structured tokenomics analysis
        """
        try:
            # Try to parse as JSON
            analysis = json.loads(response)
            
            # Validate required fields
            required_fields = [
                "fundamental_rating", "value_assessment", "supply_analysis",
                "liquidity_analysis", "utility_assessment", "competitive_position",
                "strengths", "weaknesses", "key_risks", "key_observations",
                "long_term_outlook", "trading_implication", "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    if field in ["strengths", "weaknesses", "key_risks", "key_observations"]:
                        analysis[field] = []
                    elif field in ["supply_analysis", "liquidity_analysis", "utility_assessment"]:
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
                "fundamental_rating": "unknown",
                "value_assessment": "unknown",
                "supply_analysis": {},
                "liquidity_analysis": {},
                "utility_assessment": {},
                "competitive_position": "unknown",
                "strengths": [],
                "weaknesses": [],
                "key_risks": [],
                "key_observations": [],
                "long_term_outlook": "neutral",
                "trading_implication": "hold",
                "confidence": 0,
                "reasoning": f"Failed to parse response: {response[:200]}",
                "parse_error": True
            }
