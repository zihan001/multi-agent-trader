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
        
        # Format candle data (last 5 for context, compact format)
        recent_candles = candles[-5:] if len(candles) > 5 else candles
        candle_summary = [
            f"{candle.get('close')},{candle.get('volume')}"
            for candle in recent_candles
        ]
        
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

RECENT CANDLES (close,volume): {', '.join(candle_summary)}

Return JSON with fields: trend, strength, key_levels (support[], resistance[]), indicators_summary (rsi, macd, emas), momentum, volume_analysis, key_observations[], recommendation, confidence (0-100), reasoning.

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
            Structured technical analysis
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
