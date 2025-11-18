"""
Technical Analyst Agent

Analyzes price action and technical indicators to provide trading insights.
"""
import json
from typing import Dict, Any, List

from app.agents.base import AnalystAgent


class TechnicalAnalyst(AnalystAgent):
    """
    Analyzes technical indicators and price patterns.
    
    Examines:
    - Price trends and momentum
    - Key technical indicators (RSI, MACD, EMAs)
    - Support/resistance levels
    - Volume analysis
    """
    
    @property
    def name(self) -> str:
        return "technical_analyst"
    
    @property
    def role(self) -> str:
        return "Technical Analysis Specialist"
    
    def build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build prompt for technical analysis.
        
        Expected context keys:
        - symbol: Trading pair symbol
        - timeframe: Timeframe (e.g., '1h', '4h', '1d')
        - candles: Recent candle data (OHLCV)
        - indicators: Calculated technical indicators
        - current_price: Latest price
        """
        symbol = context.get("symbol", "UNKNOWN")
        timeframe = context.get("timeframe", "1h")
        current_price = context.get("current_price", 0)
        indicators = context.get("indicators", {})
        candles = context.get("candles", [])
        
        # Format candle data (last 10 for context)
        recent_candles = candles[-10:] if len(candles) > 10 else candles
        candle_summary = []
        for candle in recent_candles:
            candle_summary.append(
                f"Open: {candle.get('open')}, High: {candle.get('high')}, "
                f"Low: {candle.get('low')}, Close: {candle.get('close')}, "
                f"Volume: {candle.get('volume')}"
            )
        
        system_prompt = f"""You are an expert technical analyst specializing in cryptocurrency trading.

Your role is to analyze price action and technical indicators to determine market direction and strength.

Provide clear, actionable technical analysis based on:
- Price trends and momentum
- Technical indicators (RSI, MACD, EMAs)
- Support and resistance levels
- Volume patterns

Be concise but thorough. Focus on what matters for trading decisions."""

        user_prompt = f"""Analyze the technical situation for {symbol} on the {timeframe} timeframe.

CURRENT PRICE: ${current_price:,.2f}

TECHNICAL INDICATORS:
{json.dumps(indicators, indent=2)}

RECENT PRICE ACTION (last 10 candles):
{chr(10).join(candle_summary)}

Provide your analysis in JSON format with the following structure:
{{
    "trend": "bullish|bearish|neutral",
    "strength": "strong|moderate|weak",
    "key_levels": {{
        "support": [list of support prices],
        "resistance": [list of resistance prices]
    }},
    "indicators_summary": {{
        "rsi": "overbought|oversold|neutral with value",
        "macd": "bullish|bearish|neutral signal",
        "emas": "price above|below|between EMAs"
    }},
    "momentum": "increasing|decreasing|stable",
    "volume_analysis": "high|normal|low volume, trend confirmation",
    "key_observations": ["observation 1", "observation 2", ...],
    "recommendation": "buy|sell|hold",
    "confidence": 0-100,
    "reasoning": "brief explanation of your analysis"
}}

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
            Structured technical analysis
        """
        try:
            # Try to parse as JSON
            analysis = json.loads(response)
            
            # Validate required fields
            required_fields = [
                "trend", "strength", "key_levels", "indicators_summary",
                "momentum", "volume_analysis", "key_observations",
                "recommendation", "confidence", "reasoning"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = None
            
            # Ensure confidence is a number
            if isinstance(analysis["confidence"], str):
                analysis["confidence"] = int(analysis["confidence"])
            
            return analysis
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return error structure
            return {
                "trend": "unknown",
                "strength": "unknown",
                "key_levels": {"support": [], "resistance": []},
                "indicators_summary": {},
                "momentum": "unknown",
                "volume_analysis": "unknown",
                "key_observations": [],
                "recommendation": "hold",
                "confidence": 0,
                "reasoning": f"Failed to parse response: {response[:200]}",
                "parse_error": True
            }
