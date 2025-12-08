"""
Sentiment Analyst Agent

Evaluates market sentiment from various sources.
"""
import json
from typing import Dict, Any, List, Type
from pydantic import BaseModel

from app.agents.base import AnalystAgent
from app.agents.models import SentimentAnalysis


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
    
    def get_response_model(self) -> Type[BaseModel]:
        """Return Pydantic model for structured outputs."""
        return SentimentAnalysis
    
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
        
        # Check if we have real sentiment data
        has_real_data = sentiment_data and sentiment_data.get("data_sources_available")
        
        # Format sentiment data for prompt
        if has_real_data:
            # Extract key metrics from comprehensive sentiment data
            fear_greed = sentiment_data.get("fear_greed_index", {})
            coingecko = sentiment_data.get("coingecko_data", {})
            volume_sent = sentiment_data.get("volume_sentiment", {})
            tech_sent = sentiment_data.get("technical_sentiment", {})
            
            sentiment_summary = {
                "overall_sentiment_score": sentiment_data.get("overall_sentiment_score", 0),
                "sentiment_classification": sentiment_data.get("sentiment_classification", "Unknown"),
                "fear_greed_index": fear_greed.get("value") if fear_greed else None,
                "fear_greed_classification": fear_greed.get("classification") if fear_greed else None,
                "volume_sentiment": volume_sent.get("sentiment_signal", "neutral"),
                "volume_conviction": volume_sent.get("conviction", "low"),
                "volume_ratio": volume_sent.get("volume_ratio", 1.0),
                "technical_sentiment": tech_sent.get("overall_technical_sentiment", "neutral"),
                "rsi_sentiment": tech_sent.get("rsi_sentiment", "neutral"),
                "rsi_value": tech_sent.get("rsi_value", 50),
                "extremes_detected": tech_sent.get("extremes_detected", []),
                "coingecko_sentiment_up": coingecko.get("sentiment_votes_up") if coingecko else None,
                "coingecko_market_cap_rank": coingecko.get("market_cap_rank") if coingecko else None,
                "data_quality": "REAL_DATA"
            }
        else:
            # Fallback to mock data with warning
            sentiment_summary = {
                "overall_sentiment_score": 0,
                "sentiment_classification": "Unknown",
                "data_quality": "MOCK_DATA_WARNING",
                "warning": "Real sentiment data unavailable. Analysis will be limited to price action only."
            }
        
        system_prompt = f"""You are an expert sentiment analyst specializing in cryptocurrency markets.

Your role is to evaluate market psychology, trader sentiment, and crowd behavior to predict potential market moves.

**CHAIN-OF-THOUGHT REASONING REQUIRED:**
1. First, assess overall sentiment direction (bullish/bearish/neutral)
2. Then, evaluate sentiment strength (is it extreme or moderate?)
3. Identify contrarian signals (extreme sentiment often signals reversals)
4. Consider sentiment vs price action alignment
5. Synthesize into actionable insights

**FEW-SHOT EXAMPLE:**
Good Analysis:
- "Sentiment score +75 indicates strong bullish sentiment. However, this is approaching extreme levels historically associated with tops. Social media mentions up 300% with mainly retail FOMO. News coverage overly optimistic. CONTRARIAN SIGNAL: Extreme greed suggests potential reversal. Recommendation: Caution warranted."

Poor Analysis:
- "Everyone is bullish. Sentiment is high."

**CONFIDENCE GUIDELINES:**
- High confidence (80-100): Clear sentiment direction, multiple confirming sources, historical patterns align
- Medium confidence (50-79): Mixed signals, some sources conflict
- Low confidence (<50): Unclear sentiment, insufficient data, contradictory signals

Be objective and consider contrarian indicators. Strong sentiment extremes often signal reversals."""

        user_prompt = f"""Analyze market sentiment for {symbol}.

CURRENT PRICE: ${current_price:,.2f}
24H CHANGE: {price_change_24h:+.2f}%

SENTIMENT DATA ({sentiment_summary.get('data_quality', 'UNKNOWN')}):
{json.dumps(sentiment_summary, indent=2)}

**DATA SOURCES AVAILABLE:**
- Fear & Greed Index: {'✓' if sentiment_summary.get('fear_greed_index') is not None else '✗'}
- CoinGecko Sentiment: {'✓' if sentiment_summary.get('coingecko_sentiment_up') is not None else '✗'}
- Volume Analysis: ✓
- Technical Sentiment: ✓

**REQUIRED ANALYSIS STEPS:**
1. Overall Sentiment: What's the crowd mood?
2. Sentiment Strength: How extreme is it?
3. Contrarian Analysis: Are we at sentiment extremes?
4. Sentiment-Price Alignment: Does sentiment match price action?
5. Trading Implications: What does this mean for our position?

Return JSON with fields:
- thought_process: string (your step-by-step reasoning)
- overall_sentiment: string (bullish/bearish/neutral)
- sentiment_score: number (-100 to 100)
- sentiment_strength: string (extreme/strong/moderate/weak)
- key_factors: object (social_media, news_coverage, fear_greed, volume_interest)
- contrarian_signals: array of strings
- crowd_psychology: string
- sentiment_trend: string (improving/deteriorating/stable)
- key_observations: array of strings
- trading_implication: string
- confidence: number (0-100)
- reasoning: string
- risk_factors: array of strings

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
            Structured sentiment analysis
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
            
            # Validate required fields (now includes thought_process and risk_factors)
            required_fields = [
                "thought_process", "overall_sentiment", "sentiment_score", "sentiment_strength",
                "key_factors", "contrarian_signals", "crowd_psychology",
                "sentiment_trend", "key_observations", "trading_implication",
                "confidence", "reasoning", "risk_factors"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    if field in ["contrarian_signals", "key_observations", "risk_factors"]:
                        analysis[field] = []
                    elif field == "key_factors":
                        analysis[field] = {}
                    else:
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
                "thought_process": "Error parsing LLM response",
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
                "risk_factors": ["Unable to analyze due to parsing error"],
                "parse_error": True
            }
