"""
Tokenomics Analyst Agent

Assesses fundamental token metrics and on-chain data.
"""
import json
from typing import Dict, Any, List, Type
from pydantic import BaseModel

from app.agents.base import AnalystAgent
from app.agents.models import TokenomicsAnalysis


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
    
    def get_response_model(self) -> Type[BaseModel]:
        """Return Pydantic model for structured outputs."""
        return TokenomicsAnalysis
    
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
        
        # Check if we have real tokenomics data
        has_real_data = token_data and token_data.get("data_quality") == "COMPREHENSIVE"
        
        # Format tokenomics data for prompt
        if has_real_data:
            # Extract key metrics from comprehensive tokenomics data
            supply_data = token_data.get("supply_data", {})
            market_data_tok = token_data.get("market_data", {})
            supply_analysis = token_data.get("supply_analysis", {})
            liquidity_analysis = token_data.get("liquidity_analysis", {})
            developer_assessment = token_data.get("developer_assessment", {})
            community_data = token_data.get("community_data", {})
            price_changes = token_data.get("price_changes", {})
            
            tokenomics_summary = {
                "coin_name": token_data.get("coin_name", symbol),
                "blockchain": token_data.get("blockchain", "unknown"),
                "categories": token_data.get("categories", []),
                "supply": {
                    "circulating": supply_data.get("circulating", 0),
                    "total": supply_data.get("total", 0),
                    "max": supply_data.get("max", "unlimited"),
                    "percentage_circulating": supply_data.get("percentage_circulating", 0),
                    "inflation_type": supply_analysis.get("inflation_type", "unknown"),
                    "inflation_pressure": supply_analysis.get("inflation_pressure", "unknown"),
                },
                "market": {
                    "market_cap": market_data_tok.get("market_cap", 0),
                    "market_cap_rank": market_data_tok.get("market_cap_rank", 0),
                    "market_cap_tier": liquidity_analysis.get("market_cap_tier", "unknown"),
                    "liquidity_rating": liquidity_analysis.get("liquidity_rating", "unknown"),
                    "volume_rating": liquidity_analysis.get("volume_rating", "unknown"),
                    "volume_to_mcap_ratio": market_data_tok.get("volume_to_mcap_ratio", 0),
                    "fdv_to_mcap_ratio": market_data_tok.get("fdv_to_mcap_ratio", 0),
                },
                "price_performance": {
                    "24h": price_changes.get("24h", 0),
                    "7d": price_changes.get("7d", 0),
                    "30d": price_changes.get("30d", 0),
                    "1y": price_changes.get("1y", 0),
                    "ath_change": market_data_tok.get("ath_change_percentage", 0),
                    "atl_change": market_data_tok.get("atl_change_percentage", 0),
                },
                "community": {
                    "twitter_followers": community_data.get("twitter_followers", 0),
                    "reddit_subscribers": community_data.get("reddit_subscribers", 0),
                    "telegram_users": community_data.get("telegram_users", 0),
                },
                "developer": {
                    "activity_level": developer_assessment.get("activity_level", "unknown"),
                    "project_health": developer_assessment.get("project_health", "unknown"),
                    "commits_4_weeks": token_data.get("developer_data", {}).get("commit_count_4_weeks", 0),
                },
                "data_quality": "REAL_DATA"
            }
        else:
            # Fallback with warning
            tokenomics_summary = {
                "data_quality": "MOCK_DATA_WARNING",
                "warning": "Real tokenomics data unavailable. Analysis will be limited.",
                "basic_metrics": {
                    "current_price": current_price,
                    "volume_24h": volume_24h,
                }
            }
        
        # Calculate volume-to-market-cap ratio from context
        volume_mcap_ratio = (volume_24h / market_cap * 100) if market_cap > 0 else 0
        
        system_prompt = f"""You are an expert tokenomics analyst specializing in cryptocurrency fundamentals.

Your role is to assess the fundamental value and structure of crypto assets.

**CHAIN-OF-THOUGHT REASONING REQUIRED:**
1. First, evaluate token supply structure (inflationary/deflationary/stable)
2. Then, assess liquidity and market cap health
3. Analyze token utility and real-world adoption
4. Consider competitive positioning
5. Synthesize into value assessment

**FEW-SHOT EXAMPLE:**
Good Analysis:
- "Token has capped supply of 21M with 90% already in circulation, reducing inflation risk. Market cap of $50B puts it in top 10, indicating strong liquidity. However, use case is limited to speculation with minimal real-world adoption. Competition from similar projects is intense. Value Assessment: Fairly valued but lacks fundamental growth drivers."

Poor Analysis:
- "Low supply. High market cap. Good token."

**CONFIDENCE GUIDELINES:**
- High confidence (80-100): Clear fundamentals, strong data, proven use case, good competitive position
- Medium confidence (50-79): Some data gaps, moderate competition, developing use case
- Low confidence (<50): Insufficient data, unclear utility, high competition, speculative

Provide objective fundamental analysis to determine long-term viability and fair value."""

        user_prompt = f"""Analyze the tokenomics and fundamentals for {symbol}.

CURRENT PRICE: ${current_price:,.2f}
MARKET CAP: ${market_cap:,.0f}
24H VOLUME: ${volume_24h:,.0f}
VOLUME/MCAP RATIO: {volume_mcap_ratio:.2f}%

TOKENOMICS DATA ({tokenomics_summary.get('data_quality', 'UNKNOWN')}):
{json.dumps(tokenomics_summary, indent=2)}

**DATA SOURCES AVAILABLE:**
- Supply Metrics: {'✓' if has_real_data else '✗'}
- Market Metrics: {'✓' if has_real_data else '✗'}
- Community Data: {'✓' if has_real_data else '✗'}
- Developer Activity: {'✓' if has_real_data else '✗'}

**REQUIRED ANALYSIS STEPS:**
1. Supply Analysis: Is the token inflationary or deflationary?
2. Liquidity Assessment: Is there sufficient trading liquidity?
3. Utility Evaluation: Does the token have real-world use cases?
4. Competitive Analysis: How does it compare to alternatives?
5. Value Determination: Is it overvalued, fairly valued, or undervalued?

Return JSON with fields:
- thought_process: string (your step-by-step reasoning)
- fundamental_rating: string (strong/moderate/weak/poor)
- value_assessment: string (undervalued/fairly_valued/overvalued)
- supply_analysis: object (inflation_rate, supply_distribution, unlock_schedule)
- liquidity_analysis: object (market_cap_size, trading_liquidity, volume_quality)
- utility_assessment: object (use_cases, network_activity, real_world_adoption)
- competitive_position: string
- strengths: array of strings
- weaknesses: array of strings
- key_risks: array of strings
- key_observations: array of strings
- long_term_outlook: string (bullish/neutral/bearish)
- trading_implication: string
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
            Structured tokenomics analysis
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
            
            # Validate required fields (now includes thought_process)
            required_fields = [
                "thought_process", "fundamental_rating", "value_assessment", "supply_analysis",
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
                "thought_process": "Error parsing LLM response",
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
