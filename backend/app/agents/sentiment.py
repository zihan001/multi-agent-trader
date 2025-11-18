"""
Sentiment Analyst Agent

Evaluates market sentiment from various sources.
"""
import json
from typing import Dict, Any, List

from app.agents.base import AnalystAgent


class SentimentAnalyst(AnalystAgent):
    """
    Analyzes market sentiment to gauge trader psychology and market mood.
    
    Examines:
    - Social media sentiment (mock data initially)
    - News sentiment
    - Fear & Greed indicators
    - Community discussion trends
    """
    
    @property
    def name(self) -> str:
        return "sentiment_analyst"
    
    @property
    def role(self) -> str:
        return "Market Sentiment Specialist"
    
    def build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build prompt for sentiment analysis.
        
        Expected context keys:
        - symbol: Trading pair symbol
        - sentiment_data: Sentiment indicators and data
        - current_price: Latest price
        - price_change_24h: 24h price change percentage
        """
        symbol = context.get("symbol", "UNKNOWN")
        current_price = context.get("current_price", 0)
        price_change_24h = context.get("price_change_24h", 0)
        sentiment_data = context.get("sentiment_data", {})
        
        # Default sentiment data if not provided
        if not sentiment_data:
            sentiment_data = {
                "social_mentions": "moderate",
                "news_tone": "neutral",
                "fear_greed_index": 50,
                "trading_volume_trend": "stable",
                "retail_interest": "moderate"
            }
        
        system_prompt = f"""You are an expert sentiment analyst specializing in cryptocurrency markets.

Your role is to evaluate market psychology, trader sentiment, and crowd behavior to predict potential market moves.

Analyze sentiment signals from:
- Social media activity and trends
- News coverage and tone
- Fear & Greed indicators
- Trading volume and interest
- Community discussions

Be objective and consider contrarian indicators. Strong sentiment extremes often signal reversals."""

        user_prompt = f"""Analyze market sentiment for {symbol}.

CURRENT PRICE: ${current_price:,.2f}
24H CHANGE: {price_change_24h:+.2f}%

SENTIMENT DATA:
{json.dumps(sentiment_data, indent=2)}

Provide your analysis in JSON format with the following structure:
{{
    "overall_sentiment": "extremely_bullish|bullish|neutral|bearish|extremely_bearish",
    "sentiment_score": -100 to 100 (negative = bearish, positive = bullish),
    "sentiment_strength": "strong|moderate|weak",
    "key_factors": {{
        "social_media": "analysis of social sentiment",
        "news_coverage": "analysis of news tone",
        "fear_greed": "analysis of fear/greed levels",
        "volume_interest": "analysis of trading activity"
    }},
    "contrarian_signals": ["any extreme sentiment signals that may indicate reversal"],
    "crowd_psychology": "description of current market psychology",
    "sentiment_trend": "improving|deteriorating|stable",
    "key_observations": ["observation 1", "observation 2", ...],
    "trading_implication": "buy|sell|hold",
    "confidence": 0-100,
    "reasoning": "brief explanation of sentiment analysis"
}}

Note: Be especially alert for extreme sentiment that could indicate market tops or bottoms.

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
            Structured sentiment analysis
        """
        try:
            # Try to parse as JSON
            analysis = json.loads(response)
            
            # Validate required fields
            required_fields = [
                "overall_sentiment", "sentiment_score", "sentiment_strength",
                "key_factors", "contrarian_signals", "crowd_psychology",
                "sentiment_trend", "key_observations", "trading_implication",
                "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = None
            
            # Ensure numeric fields are numbers
            if isinstance(analysis.get("sentiment_score"), str):
                analysis["sentiment_score"] = int(analysis["sentiment_score"])
            if isinstance(analysis.get("confidence"), str):
                analysis["confidence"] = int(analysis["confidence"])
            
            # Clamp sentiment_score to -100 to 100
            if analysis.get("sentiment_score") is not None:
                analysis["sentiment_score"] = max(-100, min(100, analysis["sentiment_score"]))
            
            return analysis
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return error structure
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0,
                "sentiment_strength": "unknown",
                "key_factors": {},
                "contrarian_signals": [],
                "crowd_psychology": "unknown",
                "sentiment_trend": "unknown",
                "key_observations": [],
                "trading_implication": "hold",
                "confidence": 0,
                "reasoning": f"Failed to parse response: {response[:200]}",
                "parse_error": True
            }
