"""
Agent Pipeline Orchestrator

Coordinates the full multi-agent decision-making flow.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.agents.llm_client import LLMClient, BudgetExceededError
from app.agents.technical import TechnicalAnalyst
from app.agents.sentiment import SentimentAnalyst
from app.agents.tokenomics import TokenomicsAnalyst
from app.agents.researcher import Researcher
from app.agents.trader import Trader
from app.agents.risk import RiskManager

# Import ReAct agents
from app.agents.researcher_react import ResearcherReAct
from app.agents.trader_react import TraderReAct
from app.agents.risk_manager_react import RiskManagerReAct

# Import LangChain agents
from app.langchain.agents import LangChainResearcher, LangChainTrader, LangChainRiskManager


def compress_analyst_output(full_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only decision-relevant fields from analyst output to reduce token usage.
    
    Reduces typical analyst output from 400-600 tokens to ~150-200 tokens.
    Now includes thought_process for better synthesis.
    """
    if not full_analysis:
        return {}
    
    return {
        "recommendation": full_analysis.get("recommendation") or full_analysis.get("trading_implication"),
        "confidence": full_analysis.get("confidence", 0),
        "key_insight": full_analysis.get("reasoning", "")[:150],  # Truncate reasoning to 150 chars
        "top_signals": full_analysis.get("key_observations", [])[:2],  # Top 2 observations only
        "thought_summary": full_analysis.get("thought_process", "")[:200] if full_analysis.get("thought_process") else None  # Include reasoning process
    }


def check_confidence_gate(agent_name: str, analysis: Dict[str, Any], min_confidence: int = 40) -> tuple[bool, str]:
    """
    Check if agent analysis meets minimum confidence threshold.
    
    Args:
        agent_name: Name of the agent
        analysis: Agent analysis output
        min_confidence: Minimum confidence threshold (default 40%)
        
    Returns:
        Tuple of (passes, message)
    """
    # Handle numeric confidence
    confidence = analysis.get("confidence", analysis.get("conviction", 0))
    
    # Handle conviction_level string (high/medium/low) and map to numbers
    if isinstance(confidence, str):
        conviction_map = {"high": 80, "medium": 60, "low": 40}
        confidence = conviction_map.get(confidence.lower(), 0)
    
    if confidence < min_confidence:
        return False, f"{agent_name} confidence ({confidence}%) below minimum threshold ({min_confidence}%)"
    
    return True, f"{agent_name} confidence ({confidence}%) passes threshold"


def calculate_average_confidence(analyses: Dict[str, Any]) -> float:
    """
    Calculate average confidence across analyst outputs.
    
    Args:
        analyses: Dict of agent analyses
        
    Returns:
        Average confidence level
    """
    confidences = []
    for analysis in analyses.values():
        if isinstance(analysis, dict) and "analysis" in analysis:
            conf = analysis["analysis"].get("confidence", 0)
            confidences.append(conf)
    
    return sum(confidences) / len(confidences) if confidences else 0


class AgentPipeline:
    """
    Orchestrates the complete agent decision pipeline.
    
    Flow: Technical → Sentiment → Tokenomics → Researcher → Trader → Risk Manager
    
    Supports both classic Instructor-based agents and ReAct agents.
    """
    
    def __init__(
        self, 
        db: Session, 
        llm_client: Optional[LLMClient] = None, 
        use_react: bool = False,
        use_langchain: bool = False
    ):
        """
        Initialize the pipeline with all agents.
        
        Args:
            db: Database session
            llm_client: Optional shared LLM client
            use_react: If True, use custom ReAct agents (deprecated, use use_langchain)
            use_langchain: If True, use LangChain agents for Researcher, Trader, and Risk Manager
        """
        self.db = db
        self.llm_client = llm_client or LLMClient(db)
        self.use_react = use_react
        self.use_langchain = use_langchain
        
        # Initialize analyst agents (always classic)
        self.technical_analyst = TechnicalAnalyst(db, self.llm_client)
        self.sentiment_analyst = SentimentAnalyst(db, self.llm_client)
        self.tokenomics_analyst = TokenomicsAnalyst(db, self.llm_client)
        
        # Initialize decision agents (classic, custom ReAct, or LangChain)
        if use_langchain:
            print("🔗 Initializing LangChain agents for Researcher, Trader, and Risk Manager")
            self.researcher = LangChainResearcher(db, max_iterations=3)
            self.trader = LangChainTrader(db, max_iterations=3)
            self.risk_manager = LangChainRiskManager(db, max_iterations=3)
        elif use_react:
            print("🤖 Initializing ReAct agents for Researcher, Trader, and Risk Manager")
            self.researcher = ResearcherReAct(db, self.llm_client, max_iterations=3)
            self.trader = TraderReAct(db, self.llm_client, max_iterations=3)
            self.risk_manager = RiskManagerReAct(db, self.llm_client, max_iterations=3)
        else:
            self.researcher = Researcher(db, self.llm_client)
            self.trader = Trader(db, self.llm_client)
            self.risk_manager = RiskManager(db, self.llm_client)
    
    def run(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full agent pipeline.
        
        Args:
            symbol: Trading pair symbol
            market_data: Market data context (price, candles, indicators, etc.)
            portfolio_data: Portfolio state (positions, cash, equity, etc.)
            run_id: Optional run identifier for grouping
            
        Returns:
            Complete pipeline result with all agent outputs and final decision
        """
        run_id = run_id or f"run_{datetime.utcnow().isoformat()}"
        
        result = {
            "run_id": run_id,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started",
            "agents": {},
            "final_decision": None,
            "errors": []
        }
        
        try:
            # Step 1: Technical Analysis
            print(f"[{run_id}] Running Technical Analyst...")
            technical_context = {
                "symbol": symbol,
                "timeframe": market_data.get("timeframe", "1h"),
                "current_price": market_data.get("current_price"),
                "candles": market_data.get("candles", []),
                "indicators": market_data.get("indicators", {}),
            }
            
            technical_result = self.technical_analyst.analyze_structured(technical_context)
            result["agents"]["technical"] = technical_result
            
            # Step 2: Sentiment Analysis
            print(f"[{run_id}] Running Sentiment Analyst...")
            sentiment_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "price_change_24h": market_data.get("price_change_24h", 0),
                "sentiment_data": market_data.get("sentiment_data", {}),
            }
            
            sentiment_result = self.sentiment_analyst.analyze_structured(sentiment_context)
            result["agents"]["sentiment"] = sentiment_result
            
            # Step 3: Tokenomics Analysis
            print(f"[{run_id}] Running Tokenomics Analyst...")
            tokenomics_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "market_cap": market_data.get("market_cap", 0),
                "volume_24h": market_data.get("volume_24h", 0),
                "token_data": market_data.get("token_data", {}),
            }
            
            tokenomics_result = self.tokenomics_analyst.analyze_structured(tokenomics_context)
            result["agents"]["tokenomics"] = tokenomics_result
            
            # Check analyst confidence levels
            avg_analyst_confidence = calculate_average_confidence({
                "technical": technical_result,
                "sentiment": sentiment_result,
                "tokenomics": tokenomics_result
            })
            print(f"[{run_id}] Average analyst confidence: {avg_analyst_confidence:.1f}%")
            
            # Step 4: Research Synthesis
            print(f"[{run_id}] Running Researcher{'(ReAct)' if self.use_react else ''}...")
            research_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "technical_analysis": compress_analyst_output(technical_result.get("analysis")),
                "sentiment_analysis": compress_analyst_output(sentiment_result.get("analysis")),
                "tokenomics_analysis": compress_analyst_output(tokenomics_result.get("analysis")),
                "average_analyst_confidence": avg_analyst_confidence,
            }
            
            if self.use_react:
                # ReAct agents are async only
                import asyncio
                research_result = asyncio.run(self.researcher.analyze(research_context))
            else:
                research_result = self.researcher.analyze_structured(research_context)
            result["agents"]["researcher"] = research_result
            
            # Confidence gate: Check research conviction
            # Handle both conviction_level (string) and conviction (number)
            analysis = research_result.get("analysis", {})
            research_confidence = analysis.get("conviction_level", analysis.get("conviction", 0))
            passes_gate, gate_message = check_confidence_gate("Researcher", analysis, min_confidence=40)
            print(f"[{run_id}] {gate_message}")
            
            if not passes_gate:
                print(f"[{run_id}] Research confidence below threshold. Recommending HOLD.")
                result["final_decision"] = {
                    "action": "hold",
                    "reason": f"Insufficient conviction: {gate_message}",
                    "confidence": research_confidence
                }
                result["status"] = "completed_hold"
                result["confidence_gate_triggered"] = True
                
                # Calculate costs
                total_cost = sum(
                    agent_result.get("metadata", {}).get("cost", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_cost"] = total_cost
                total_tokens = sum(
                    agent_result.get("metadata", {}).get("tokens", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_tokens"] = total_tokens
                
                return result
            
            # Step 5: Trade Proposal
            print(f"[{run_id}] Running Trader{'(ReAct)' if self.use_react else ''}...")
            trader_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "research_thesis": research_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("summary", {}).get("cash_balance", 0),
            }
            
            if self.use_react:
                import asyncio
                trader_result = asyncio.run(self.trader.analyze(trader_context))
            else:
                trader_result = self.trader.analyze_structured(trader_context)
            result["agents"]["trader"] = trader_result
            
            # Confidence gate: Check trader conviction
            trader_confidence = trader_result.get("analysis", {}).get("confidence", 0)
            trader_action = trader_result.get("analysis", {}).get("action", "hold")
            
            if trader_action == "hold":
                print(f"[{run_id}] Trader recommends HOLD (confidence: {trader_confidence}%). Skipping risk management.")
                result["final_decision"] = {
                    "action": "hold",
                    "reason": "Trader recommendation: insufficient conviction or no actionable setup",
                    "confidence": trader_confidence
                }
                result["status"] = "completed_hold"
                
                # Calculate costs
                total_cost = sum(
                    agent_result.get("metadata", {}).get("cost", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_cost"] = total_cost
                total_tokens = sum(
                    agent_result.get("metadata", {}).get("tokens", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_tokens"] = total_tokens
                
                return result
            
            # Step 6: Risk Management
            print(f"[{run_id}] Running Risk Manager{'(ReAct)' if self.use_react else ''}...")
            risk_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "trade_proposal": trader_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("summary", {}).get("cash_balance", 0),
                "total_equity": portfolio_data.get("summary", {}).get("total_equity", 0),
                "current_positions": portfolio_data.get("positions", []),
            }
            
            if self.use_react:
                import asyncio
                risk_result = asyncio.run(self.risk_manager.analyze(risk_context))
            else:
                risk_result = self.risk_manager.analyze_structured(risk_context)
            result["agents"]["risk_manager"] = risk_result
            
            # Extract final decision and add validation flag
            risk_decision = risk_result.get("analysis", {}).get("decision", "rejected")
            result["final_decision"] = risk_result.get("analysis", {}).get("final_trade")
            result["risk_decision"] = risk_decision
            result["status"] = "completed"
            
            # Add warning if risk manager modified or rejected
            if risk_decision == "rejected":
                print(f"[{run_id}] WARNING: Risk Manager REJECTED the trade proposal")
                result["final_decision"] = {
                    "action": "hold",
                    "reason": risk_result.get("analysis", {}).get("rejection_reason", "Risk rules violated"),
                    "confidence": 0
                }
            elif risk_decision == "modified":
                print(f"[{run_id}] INFO: Risk Manager MODIFIED the trade proposal")
            
            # Calculate total cost
            total_cost = sum(
                agent_result.get("metadata", {}).get("cost", 0)
                for agent_result in result["agents"].values()
            )
            result["total_cost"] = total_cost
            
            # Calculate total tokens
            total_tokens = sum(
                agent_result.get("metadata", {}).get("tokens", 0)
                for agent_result in result["agents"].values()
            )
            result["total_tokens"] = total_tokens
            
            print(f"[{run_id}] Pipeline completed successfully")
            print(f"[{run_id}] Total cost: ${total_cost:.4f}")
            print(f"[{run_id}] Total tokens: {total_tokens}")
            print(f"[{run_id}] Final decision: {result['final_decision']}")
            
        except BudgetExceededError as e:
            result["status"] = "failed"
            result["errors"].append({
                "type": "budget_exceeded",
                "message": str(e)
            })
            print(f"[{run_id}] Pipeline failed: Budget exceeded - {e}")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append({
                "type": "pipeline_error",
                "message": str(e)
            })
            print(f"[{run_id}] Pipeline failed: {e}")
        
        return result
    
    async def arun(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_data: Dict[str, Any],
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full agent pipeline asynchronously.
        
        Args:
            symbol: Trading pair symbol
            market_data: Market data context
            portfolio_data: Portfolio state
            run_id: Optional run identifier
            
        Returns:
            Complete pipeline result with all agent outputs and final decision
        """
        run_id = run_id or f"run_{datetime.utcnow().isoformat()}"
        
        result = {
            "run_id": run_id,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started",
            "agents": {},
            "final_decision": None,
            "errors": []
        }
        
        try:
            # Step 1: Run all analysts in parallel
            print(f"[{run_id}] Running all analysts...")
            
            technical_context = {
                "symbol": symbol,
                "timeframe": market_data.get("timeframe", "1h"),
                "current_price": market_data.get("current_price"),
                "candles": market_data.get("candles", []),
                "indicators": market_data.get("indicators", {}),
            }
            
            sentiment_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "price_change_24h": market_data.get("price_change_24h", 0),
                "sentiment_data": market_data.get("sentiment_data", {}),
            }
            
            tokenomics_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "market_cap": market_data.get("market_cap", 0),
                "volume_24h": market_data.get("volume_24h", 0),
                "token_data": market_data.get("token_data", {}),
            }
            
            # Run analysts in parallel
            import asyncio
            technical_result, sentiment_result, tokenomics_result = await asyncio.gather(
                self.technical_analyst.aanalyze(technical_context),
                self.sentiment_analyst.aanalyze(sentiment_context),
                self.tokenomics_analyst.aanalyze(tokenomics_context),
            )
            
            result["agents"]["technical"] = technical_result
            result["agents"]["sentiment"] = sentiment_result
            result["agents"]["tokenomics"] = tokenomics_result
            
            # Check analyst confidence levels
            avg_analyst_confidence = calculate_average_confidence({
                "technical": technical_result,
                "sentiment": sentiment_result,
                "tokenomics": tokenomics_result
            })
            print(f"[{run_id}] Average analyst confidence: {avg_analyst_confidence:.1f}%")
            
            # Step 2: Research Synthesis
            print(f"[{run_id}] Running Researcher...")
            research_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "technical_analysis": compress_analyst_output(technical_result.get("analysis")),
                "sentiment_analysis": compress_analyst_output(sentiment_result.get("analysis")),
                "tokenomics_analysis": compress_analyst_output(tokenomics_result.get("analysis")),
                "average_analyst_confidence": avg_analyst_confidence,
            }
            
            research_result = await self.researcher.aanalyze(research_context)
            result["agents"]["researcher"] = research_result
            
            # Confidence gate: Check research conviction
            # Handle both conviction_level (string) and conviction (number)
            analysis = research_result.get("analysis", {})
            research_confidence = analysis.get("conviction_level", analysis.get("conviction", 0))
            passes_gate, gate_message = check_confidence_gate("Researcher", analysis, min_confidence=40)
            print(f"[{run_id}] {gate_message}")
            
            if not passes_gate:
                print(f"[{run_id}] Research confidence below threshold. Recommending HOLD.")
                result["final_decision"] = {
                    "action": "hold",
                    "reason": f"Insufficient conviction: {gate_message}",
                    "confidence": research_confidence
                }
                result["status"] = "completed_hold"
                result["confidence_gate_triggered"] = True
                
                # Calculate costs
                total_cost = sum(
                    agent_result.get("metadata", {}).get("cost", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_cost"] = total_cost
                total_tokens = sum(
                    agent_result.get("metadata", {}).get("tokens", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_tokens"] = total_tokens
                
                return result
            
            # Step 3: Trade Proposal
            print(f"[{run_id}] Running Trader...")
            trader_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "research_thesis": research_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("summary", {}).get("cash_balance", 0),
            }
            
            trader_result = await self.trader.aanalyze(trader_context)
            result["agents"]["trader"] = trader_result
            
            # Confidence gate: Check trader conviction
            trader_confidence = trader_result.get("analysis", {}).get("confidence", 0)
            trader_action = trader_result.get("analysis", {}).get("action", "hold")
            
            if trader_action == "hold":
                print(f"[{run_id}] Trader recommends HOLD (confidence: {trader_confidence}%). Skipping risk management.")
                result["final_decision"] = {
                    "action": "hold",
                    "reason": "Trader recommendation: insufficient conviction or no actionable setup",
                    "confidence": trader_confidence
                }
                result["status"] = "completed_hold"
                
                # Calculate costs
                total_cost = sum(
                    agent_result.get("metadata", {}).get("cost", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_cost"] = total_cost
                total_tokens = sum(
                    agent_result.get("metadata", {}).get("tokens", 0)
                    for agent_result in result["agents"].values()
                )
                result["total_tokens"] = total_tokens
                
                return result
            
            # Step 4: Risk Management
            print(f"[{run_id}] Running Risk Manager...")
            risk_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "trade_proposal": trader_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("summary", {}).get("cash_balance", 0),
                "total_equity": portfolio_data.get("summary", {}).get("total_equity", 0),
                "current_positions": portfolio_data.get("positions", []),
            }
            
            risk_result = await self.risk_manager.aanalyze(risk_context)
            result["agents"]["risk_manager"] = risk_result
            
            # Extract final decision and add validation flag
            risk_decision = risk_result.get("analysis", {}).get("decision", "rejected")
            result["final_decision"] = risk_result.get("analysis", {}).get("final_trade")
            result["risk_decision"] = risk_decision
            result["status"] = "completed"
            
            # Add warning if risk manager modified or rejected
            if risk_decision == "rejected":
                print(f"[{run_id}] WARNING: Risk Manager REJECTED the trade proposal")
                result["final_decision"] = {
                    "action": "hold",
                    "reason": risk_result.get("analysis", {}).get("rejection_reason", "Risk rules violated"),
                    "confidence": 0
                }
            elif risk_decision == "modified":
                print(f"[{run_id}] INFO: Risk Manager MODIFIED the trade proposal")
            
            # Calculate total cost and tokens
            total_cost = sum(
                agent_result.get("metadata", {}).get("cost", 0)
                for agent_result in result["agents"].values()
            )
            result["total_cost"] = total_cost
            
            total_tokens = sum(
                agent_result.get("metadata", {}).get("tokens", 0)
                for agent_result in result["agents"].values()
            )
            result["total_tokens"] = total_tokens
            
            print(f"[{run_id}] Pipeline completed successfully")
            print(f"[{run_id}] Total cost: ${total_cost:.4f}")
            print(f"[{run_id}] Total tokens: {total_tokens}")
            print(f"[{run_id}] Final decision: {result['final_decision']}")
            
        except BudgetExceededError as e:
            result["status"] = "failed"
            result["errors"].append({
                "type": "budget_exceeded",
                "message": str(e)
            })
            print(f"[{run_id}] Pipeline failed: Budget exceeded - {e}")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append({
                "type": "pipeline_error",
                "message": str(e)
            })
            print(f"[{run_id}] Pipeline failed: {e}")
        
        return result
