"""
Researcher ReAct Agent

Synthesizes analyst outputs using ReAct pattern with dynamic tool usage.
"""
from typing import Dict, Any, Callable
from sqlalchemy.orm import Session

from app.agents.react_base import ReActAgent
from app.agents.react_tools import ResearcherTools


class ResearcherReAct(ReActAgent):
    """
    ReAct-enabled Researcher that can dynamically fetch additional information
    to resolve conflicts and strengthen investment thesis.
    """
    
    @property
    def name(self) -> str:
        return "researcher_react"
    
    @property
    def role(self) -> str:
        return "Research Synthesizer (ReAct)"
    
    def initialize_tools(self) -> Dict[str, Callable]:
        """Initialize tools available to Researcher."""
        tools_instance = ResearcherTools(self.db)
        
        return {
            "fetch_recent_news": tools_instance.fetch_recent_news,
            "query_analyst": tools_instance.query_analyst,
            "fetch_additional_indicators": tools_instance.fetch_additional_indicators,
            "compare_historical_patterns": tools_instance.compare_historical_patterns,
            "fetch_order_book_snapshot": tools_instance.fetch_order_book_snapshot,
        }
    
    def build_prompt(self, context: Dict[str, Any]):
        """Build prompt - not used in ReAct mode."""
        raise NotImplementedError("ReAct agents use build_react_prompt()")
    
    def parse_response(self, response: str):
        """Parse response - not used in ReAct mode."""
        raise NotImplementedError("ReAct agents use parse_react_response()")
    
    async def analyze(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Analyze using ReAct loop.
        
        Expected context keys:
        - symbol: Trading pair symbol
        - current_price: Latest price
        - technical_analysis: Compressed output from Technical Analyst
        - sentiment_analysis: Compressed output from Sentiment Analyst
        - tokenomics_analysis: Compressed output from Tokenomics Analyst
        """
        symbol = context.get("symbol", "UNKNOWN")
        current_price = context.get("current_price", 0)
        technical = context.get("technical_analysis", {})
        sentiment = context.get("sentiment_analysis", {})
        tokenomics = context.get("tokenomics_analysis", {})
        
        task_description = f"""Synthesize analysis from three analysts into a unified investment thesis for {symbol} at ${current_price:,.2f}

**ANALYST OUTPUTS:**

Technical Analysis:
- Recommendation: {technical.get('recommendation', 'N/A')}
- Confidence: {technical.get('confidence', 0)}%
- Key Insight: {technical.get('key_insight', 'N/A')}
- Top Signals: {technical.get('top_signals', [])}

Sentiment Analysis:
- Recommendation: {sentiment.get('recommendation', 'N/A')}
- Confidence: {sentiment.get('confidence', 0)}%
- Key Insight: {sentiment.get('key_insight', 'N/A')}
- Top Signals: {sentiment.get('top_signals', [])}

Tokenomics Analysis:
- Recommendation: {tokenomics.get('recommendation', 'N/A')}
- Confidence: {tokenomics.get('confidence', 0)}%
- Key Insight: {tokenomics.get('key_insight', 'N/A')}
- Top Signals: {tokenomics.get('top_signals', [])}

**YOUR TASK:**
1. Review all three analyst recommendations
2. Identify agreements and conflicts
3. Use tools if you need additional information to resolve conflicts
4. Weigh perspectives based on confidence levels
5. Synthesize into a unified investment thesis

**FINAL ANSWER FORMAT** (JSON):
{{
    "investment_thesis": "Clear 2-3 sentence thesis",
    "direction": "bullish" | "bearish" | "neutral",
    "conviction": 0-100,
    "primary_rationale": "Main reason for thesis",
    "supporting_factors": ["factor1", "factor2", "factor3"],
    "risk_factors": ["risk1", "risk2", "risk3"],
    "time_horizon": "short_term" | "medium_term" | "long_term",
    "key_conflicts_resolved": "How you resolved any analyst disagreements",
    "additional_research_conducted": "Summary of any tools used"
}}
"""
        
        result = await self.react_loop(
            task_description=task_description,
            context=context,
            temperature=kwargs.get("temperature", 0.7)
        )
        
        return result
