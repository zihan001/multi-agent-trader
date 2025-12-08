"""
LangChain-based agents for trading decisions.

Uses LangChain's agent framework with ReAct pattern for:
- Researcher: Synthesizes analyst outputs with dynamic tool usage
- Trader: Proposes trades with order book analysis
- Risk Manager: Validates trades with portfolio queries
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool

from app.langchain.tools import (
    create_researcher_tools,
    create_trader_tools,
    create_risk_manager_tools,
)
from app.langchain.callbacks import DatabaseCallbackHandler
from app.core.config import settings
from app.agents.models import ResearchSynthesis, TradeProposal, RiskValidation


class LangChainResearcher:
    """
    LangChain-based Researcher agent using ReAct pattern.
    
    Synthesizes analyst outputs with ability to fetch news, query analysts,
    and gather additional data when faced with conflicts or uncertainty.
    """
    
    def __init__(self, db: Session, max_iterations: int = 3):
        """
        Initialize LangChain Researcher.
        
        Args:
            db: Database session
            max_iterations: Maximum reasoning iterations
        """
        self.db = db
        self.max_iterations = max_iterations
        self.name = "researcher_langchain"
        
        # Create LLM with callbacks
        callbacks = [DatabaseCallbackHandler(db, self.name)]
        
        if settings.llm_provider == "openrouter":
            base_url = settings.openrouter_base_url
        else:
            base_url = None
        
        self.llm = ChatOpenAI(
            model=settings.strong_model,
            temperature=0.7,
            openai_api_key=settings.llm_api_key,
            openai_api_base=base_url,
            callbacks=callbacks,
        )
        
        # Create tools
        self.tools = create_researcher_tools(db)
        
        # Create ReAct prompt (LangChain format)
        self.prompt = PromptTemplate.from_template("""Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (MUST be valid JSON only, NO comments or extra text)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: You are a Research Synthesizer for an AGGRESSIVE crypto trading firm. Synthesize the following analyst outputs into a coherent investment thesis:

{analyst_outputs}

Your task:
1. Analyze the three analyst recommendations (Technical, Sentiment, Tokenomics)
2. If analysts conflict, use tools to gather additional data
3. BIAS TOWARD ACTION: If 2 out of 3 analysts agree (even with moderate confidence 50-70%), favor taking a position. Sitting out has opportunity cost.
4. Produce a final investment thesis in JSON format with:
   - direction: string (bullish/bearish/neutral)
   - confidence: number (0-100, where >40 is tradeable, >60 is strong)
   - investment_thesis: string
   - primary_rationale: string
   - supporting_factors: array of strings
   - risk_factors: array of strings
   - time_horizon: string
   - key_conflicts_resolved: string
   - additional_research_conducted: string or array

IMPORTANT: Use 'confidence' as a NUMBER (not 'conviction' as text). Be aggressive: if 2/3 analysts agree with 50%+ confidence, aim for confidence 50-70. If all agree, aim for 70-90.

Remember: Markets reward decisive action. Look for tradeable setups, not perfect alignment.

Thought: {agent_scratchpad}""")
        
        # Create agent
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=max_iterations,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis using LangChain agent.
        
        Args:
            context: Analysis context with analyst outputs
            
        Returns:
            Analysis result with metadata
        """
        # Format analyst outputs
        analyst_outputs = f"""
Technical Analysis:
- Recommendation: {context['technical_analysis']['recommendation']}
- Confidence: {context['technical_analysis']['confidence']}%
- Insight: {context['technical_analysis']['key_insight']}
- Signals: {', '.join(context['technical_analysis']['top_signals'])}

Sentiment Analysis:
- Recommendation: {context['sentiment_analysis']['recommendation']}
- Confidence: {context['sentiment_analysis']['confidence']}%
- Insight: {context['sentiment_analysis']['key_insight']}
- Signals: {', '.join(context['sentiment_analysis']['top_signals'])}

Tokenomics Analysis:
- Recommendation: {context['tokenomics_analysis']['recommendation']}
- Confidence: {context['tokenomics_analysis']['confidence']}%
- Insight: {context['tokenomics_analysis']['key_insight']}
- Signals: {', '.join(context['tokenomics_analysis']['top_signals'])}
"""
        
        try:
            # Run agent
            result = await self.agent_executor.ainvoke({
                "analyst_outputs": analyst_outputs,
            })
            
            # Extract final answer
            output = result.get("output", "{}")
            
            # Parse JSON from Final Answer
            import json
            import re
            
            # Extract JSON from Final Answer or full output
            if "Final Answer:" in output:
                json_str = output.split("Final Answer:")[-1].strip()
            else:
                json_str = output.strip()
            
            # Remove markdown code blocks if present
            json_str = re.sub(r'^```json\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)
            json_str = json_str.strip()
            
            analysis = json.loads(json_str)
            
            # Convert string conviction to numeric confidence if needed
            if 'conviction' in analysis and 'confidence' not in analysis:
                conviction_map = {
                    'high': 80, 'strong': 80,
                    'medium': 60, 'moderate': 60,
                    'low': 40, 'weak': 40
                }
                conviction_str = str(analysis.get('conviction', '')).lower()
                analysis['confidence'] = conviction_map.get(conviction_str, 50)
            
            # Return with metadata
            return {
                "analysis": analysis,
                "metadata": {
                    "iterations": len(result.get("intermediate_steps", [])),
                    "tools_used": [step[0].tool for step in result.get("intermediate_steps", [])],
                }
            }
            
        except Exception as e:
            print(f"❌ Researcher analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Return fallback
            return {
                "analysis": {
                    "direction": "neutral",
                    "conviction": 50,
                    "investment_thesis": "Analysis failed",
                    "primary_rationale": f"Error: {str(e)}",
                    "supporting_factors": [],
                    "risk_factors": ["Analysis error"],
                    "time_horizon": "short_term",
                    "key_conflicts_resolved": "N/A",
                    "additional_research_conducted": "N/A"
                },
                "metadata": {
                    "iterations": 0,
                    "error": str(e)
                }
            }
    
    async def aanalyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for pipeline compatibility (calls analyze)."""
        return await self.analyze(context)


class LangChainTrader:
    """
    LangChain-based Trader agent using ReAct pattern.
    
    Proposes trades with ability to analyze order book, check execution quality,
    and optimize entry points.
    """
    
    def __init__(self, db: Session, max_iterations: int = 3):
        """
        Initialize LangChain Trader.
        
        Args:
            db: Database session
            max_iterations: Maximum reasoning iterations
        """
        self.db = db
        self.max_iterations = max_iterations
        self.name = "trader_langchain"
        
        # Create LLM with callbacks
        callbacks = [DatabaseCallbackHandler(db, self.name)]
        
        if settings.llm_provider == "openrouter":
            base_url = settings.openrouter_base_url
        else:
            base_url = None
        
        self.llm = ChatOpenAI(
            model=settings.strong_model,
            temperature=0.7,
            openai_api_key=settings.llm_api_key,
            openai_api_base=base_url,
            callbacks=callbacks,
        )
        
        # No tools needed - work directly from context
        self.tools = []
        
        # Create simple prompt (no ReAct, direct response)
        self.prompt = PromptTemplate.from_template("""You are an AGGRESSIVE Trading Decision Maker. Propose an optimal trade based on this research thesis:

{research_thesis}

Portfolio State:
- Available Cash: ${available_cash}
- Symbol: {symbol}
- Current Price: ${current_price}

Your task: Propose a trade in JSON format with:
- action: string (buy/sell/hold)
- size: number (USD amount, 0 if hold)
- entry_price: number (use current price)
- stop_loss: number
- take_profit: number
- risk_reward_ratio: number
- execution_strategy: string (e.g., "market order")
- confidence: number (0-100, match research confidence)
- market_conditions: string

TRADING PHILOSOPHY:
- If research confidence is >40 with clear bullish/bearish direction, YOU MUST PROPOSE A TRADE (not hold)
- IGNORE cash balance - always propose the trade if research supports it
- Use research confidence as your confidence
- For bullish: action=buy, set stop loss 2% below entry, take profit 4% above entry
- For bearish: action=sell, set stop loss 2% above entry, take profit 4% below entry
- Size calculation: High confidence (>60) = $400-600, Medium (40-60) = $200-400
- Risk-reward ratio should be around 2.0 (4% gain / 2% loss)
- Only return action=hold if research confidence <40 OR direction is neutral

CRITICAL: If research is bullish/bearish with >40 confidence, action MUST be buy/sell (NOT hold).

Respond with ONLY valid JSON, no extra text.

JSON:""")
        
        # Use LLM directly without ReAct agent
        self.agent = None
        self.agent_executor = None
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis using LangChain agent.
        
        Args:
            context: Trading context with research thesis and portfolio
            
        Returns:
            Trade proposal with metadata
        """
        research_thesis = f"""
Direction: {context['research_thesis']['direction']}
Confidence: {context['research_thesis'].get('confidence', context['research_thesis'].get('conviction', 50))}%
Thesis: {context['research_thesis']['investment_thesis']}
Time Horizon: {context['research_thesis']['time_horizon']}
"""
        
        try:
            # Call LLM directly with formatted prompt
            prompt_text = self.prompt.format(
                research_thesis=research_thesis,
                available_cash=context.get('available_cash', 10000),
                symbol=context.get('symbol', 'BTCUSDT'),
                current_price=context.get('current_price', 44500),
            )
            
            response = await self.llm.ainvoke(prompt_text)
            output = response.content
            
            # Parse JSON
            import json
            import re
            
            # Extract JSON from output (may be wrapped in markdown or mixed with text)
            json_str = output.strip()
            
            # Try to extract JSON block from markdown code fences
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            # Try plain code fences
            elif '```' in json_str:
                json_match = re.search(r'```\s*(\{.*?\})\s*```', json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
            # Try to find raw JSON object
            else:
                json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            json_str = json_str.strip()
            analysis = json.loads(json_str)
            
            # Convert string conviction to numeric confidence if needed
            if 'conviction' in analysis and 'confidence' not in analysis:
                conviction_map = {
                    'high': 80, 'strong': 80,
                    'medium': 60, 'moderate': 60,
                    'low': 40, 'weak': 40
                }
                conviction_str = str(analysis.get('conviction', '')).lower()
                analysis['confidence'] = conviction_map.get(conviction_str, 50)
            
            return {
                "analysis": analysis,
                "metadata": {
                    "iterations": 0,
                    "tools_used": [],
                }
            }
            
        except Exception as e:
            print(f"❌ Trader analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "analysis": {
                    "action": "hold",
                    "size": 0,
                    "entry_price": context.get('current_price', 0),
                    "stop_loss": 0,
                    "take_profit": 0,
                    "risk_reward_ratio": 0,
                    "execution_strategy": "N/A",
                    "conviction": 0,
                    "market_conditions": f"Error: {str(e)}",
                    "tools_used": []
                },
                "metadata": {
                    "iterations": 0,
                    "error": str(e)
                }
            }
    
    async def aanalyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for pipeline compatibility (calls analyze)."""
        return await self.analyze(context)


class LangChainRiskManager:
    """
    LangChain-based Risk Manager agent using ReAct pattern.
    
    Validates trades with ability to query portfolio exposure, calculate VaR,
    and simulate trade impact.
    """
    
    def __init__(self, db: Session, max_iterations: int = 3):
        """
        Initialize LangChain Risk Manager.
        
        Args:
            db: Database session
            max_iterations: Maximum reasoning iterations
        """
        self.db = db
        self.max_iterations = max_iterations
        self.name = "risk_manager_langchain"
        
        # Create LLM with callbacks
        callbacks = [DatabaseCallbackHandler(db, self.name)]
        
        if settings.llm_provider == "openrouter":
            base_url = settings.openrouter_base_url
        else:
            base_url = None
        
        self.llm = ChatOpenAI(
            model=settings.strong_model,
            temperature=0.7,
            openai_api_key=settings.llm_api_key,
            openai_api_base=base_url,
            callbacks=callbacks,
        )
        
        # No tools needed - work directly from context
        self.tools = []
        
        # Create simple prompt (no ReAct, direct response)
        self.prompt = PromptTemplate.from_template("""You are an AGGRESSIVE Risk Manager for a trading firm. Review this trade proposal:

{trade_proposal}

Portfolio State:
- Available Cash: ${available_cash}
- Total Equity: ${total_equity}

UPDATED AGGRESSIVE RISK RULES (LOWERED THRESHOLDS):
- Max position size: 30% of equity (increased from 20%)
- Max loss per trade: 3% of equity (increased from 2%)
- Min risk-reward ratio: 1.2:1 (lowered from 1.5:1)
- Min conviction: 40% (lowered from 60%)

APPROVAL PHILOSOPHY:
- If trade has >40% confidence with valid stop loss and R:R >1.2, APPROVE it
- Only reject if clear violations of max position size or max loss rules
- Default to "approved" unless there's a specific rule violation
- For small trades (<$1000), approve automatically if confidence >40%

Your task: Validate the trade and respond in JSON format with:
- decision: string ("approved", "modified", or "rejected")
- reasoning: string
- risk_score: number (0-100, where <30 is low risk)
- final_trade: object (the trade proposal, possibly modified)

CRITICAL: Be aggressive - approve trades that meet minimum thresholds. Don't be overly cautious.

Respond with ONLY valid JSON, no extra text.

JSON:""")
        
        # Use LLM directly without ReAct agent
        self.agent = None
        self.agent_executor = None
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run analysis using LangChain agent.
        
        Args:
            context: Risk validation context with trade and portfolio
            
        Returns:
            Risk validation result with metadata
        """
        trade_proposal = f"""
Action: {context['trade_proposal']['action']}
Size: ${context['trade_proposal']['size']:,.2f}
Entry: ${context['trade_proposal']['entry_price']:,.2f}
Stop Loss: ${context['trade_proposal']['stop_loss']:,.2f}
Take Profit: ${context['trade_proposal']['take_profit']:,.2f}
"""
        
        try:
            # Call LLM directly with formatted prompt
            prompt_text = self.prompt.format(
                trade_proposal=trade_proposal,
                available_cash=context.get('available_cash', 10000),
                total_equity=context.get('total_equity', 15000),
            )
            
            response = await self.llm.ainvoke(prompt_text)
            output = response.content
            
            # Parse JSON
            import json
            import re
            
            # Extract JSON from output (may be wrapped in markdown or mixed with text)
            json_str = output.strip()
            
            # Try to extract JSON block from markdown code fences
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            # Try plain code fences
            elif '```' in json_str:
                json_match = re.search(r'```\s*(\{.*?\})\s*```', json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
            # Try to find raw JSON object
            else:
                json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            json_str = json_str.strip()
            analysis = json.loads(json_str)
            
            return {
                "analysis": analysis,
                "metadata": {
                    "iterations": 0,
                    "tools_used": [],
                }
            }
            
        except Exception as e:
            print(f"❌ Risk Manager analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "analysis": {
                    "decision": "rejected",
                    "reasoning": f"Analysis error: {str(e)}",
                    "risk_checks_performed": [],
                    "violations_found": ["Analysis failed"],
                    "final_trade": context.get('trade_proposal', {}),
                    "risk_metrics": {}
                },
                "metadata": {
                    "iterations": 0,
                    "error": str(e)
                }
            }
    
    async def aanalyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for pipeline compatibility (calls analyze)."""
        return await self.analyze(context)
