"""
Technical Analyst Agent

Analyzes price action and technical indicators to provide trading insights.
"""
import json
from typing import Dict, Any, List, Type
from pydantic import BaseModel

from app.agents.base import AnalystAgent
from app.agents.models import TechnicalAnalysis


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
    
    def get_response_model(self) -> Type[BaseModel]:
        """Return Pydantic model for structured outputs."""
        return TechnicalAnalysis
    
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

**IMPORTANT**: Return ONLY the structured data in JSON format. Do NOT wrap your response in markdown code blocks or any other formatting.

**CHAIN-OF-THOUGHT REASONING REQUIRED:**
Think step-by-step through your analysis in the 'thought_process' field:
1. First, assess the overall trend (bullish/bearish/sideways)
2. Then, evaluate momentum indicators (RSI, MACD)
3. Next, identify key support/resistance levels
4. Analyze volume patterns and their implications
5. Finally, synthesize everything into a clear recommendation

**CONFIDENCE GUIDELINES:**
- High confidence (80-100): Clear trend, aligned indicators, strong volume confirmation
- Medium confidence (50-79): Mixed signals, some conflicting indicators
- Low confidence (<50): Unclear trend, contradictory signals, low volume

Be thorough and show your reasoning process. Quality over speed."""

        user_prompt = f"""Analyze the technical situation for {symbol} on the {timeframe} timeframe.

CURRENT PRICE: ${current_price:,.2f}

TECHNICAL INDICATORS:
{json.dumps(indicators, indent=2)}

RECENT CANDLES (close,volume): {', '.join(candle_summary)}

**REQUIRED OUTPUT:**
You MUST provide ALL of the following fields:
- thought_process: Your step-by-step reasoning
- trend: bullish/bearish/sideways/uncertain  
- strength: strong/moderate/weak
- key_levels: {{support: [...], resistance: [...]}}
- indicators_summary: {{rsi: "...", macd: "...", emas: "..."}}
- momentum: momentum assessment string
- volume_analysis: volume pattern analysis string
- key_observations: list of 1-5 key points
- recommendation: strong_buy/buy/hold/sell/strong_sell
- confidence: number 0-100
- reasoning: why you made this recommendation
- risk_factors: list of 0-5 risk factors

Analyze the technical setup and provide ALL required fields."""

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
            
            # Validate required fields (now includes thought_process and risk_factors)
            required_fields = [
                "thought_process", "trend", "strength", "key_levels", "indicators_summary",
                "momentum", "volume_analysis", "key_observations",
                "recommendation", "confidence", "reasoning", "risk_factors"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    if field in ["key_observations", "risk_factors"]:
                        analysis[field] = []
                    elif field in ["key_levels", "indicators_summary"]:
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
                "risk_factors": ["Unable to analyze due to parsing error"],
                "parse_error": True
            }
