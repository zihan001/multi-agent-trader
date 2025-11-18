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


class AgentPipeline:
    """
    Orchestrates the complete agent decision pipeline.
    
    Flow: Technical → Sentiment → Tokenomics → Researcher → Trader → Risk Manager
    """
    
    def __init__(self, db: Session, llm_client: Optional[LLMClient] = None):
        """
        Initialize the pipeline with all agents.
        
        Args:
            db: Database session
            llm_client: Optional shared LLM client
        """
        self.db = db
        self.llm_client = llm_client or LLMClient(db)
        
        # Initialize all agents with shared LLM client
        self.technical_analyst = TechnicalAnalyst(db, self.llm_client)
        self.sentiment_analyst = SentimentAnalyst(db, self.llm_client)
        self.tokenomics_analyst = TokenomicsAnalyst(db, self.llm_client)
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
            
            technical_result = self.technical_analyst.analyze(technical_context)
            result["agents"]["technical"] = technical_result
            
            # Step 2: Sentiment Analysis
            print(f"[{run_id}] Running Sentiment Analyst...")
            sentiment_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "price_change_24h": market_data.get("price_change_24h", 0),
                "sentiment_data": market_data.get("sentiment_data", {}),
            }
            
            sentiment_result = self.sentiment_analyst.analyze(sentiment_context)
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
            
            tokenomics_result = self.tokenomics_analyst.analyze(tokenomics_context)
            result["agents"]["tokenomics"] = tokenomics_result
            
            # Step 4: Research Synthesis
            print(f"[{run_id}] Running Researcher...")
            research_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "technical_analysis": technical_result.get("analysis"),
                "sentiment_analysis": sentiment_result.get("analysis"),
                "tokenomics_analysis": tokenomics_result.get("analysis"),
            }
            
            research_result = self.researcher.analyze(research_context)
            result["agents"]["researcher"] = research_result
            
            # Step 5: Trade Proposal
            print(f"[{run_id}] Running Trader...")
            trader_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "research_thesis": research_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("cash_balance", 0),
            }
            
            trader_result = self.trader.analyze(trader_context)
            result["agents"]["trader"] = trader_result
            
            # Step 6: Risk Management
            print(f"[{run_id}] Running Risk Manager...")
            risk_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "trade_proposal": trader_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("cash_balance", 0),
                "total_equity": portfolio_data.get("total_equity", 0),
                "current_positions": portfolio_data.get("positions", []),
            }
            
            risk_result = self.risk_manager.analyze(risk_context)
            result["agents"]["risk_manager"] = risk_result
            
            # Extract final decision
            result["final_decision"] = risk_result.get("analysis", {}).get("final_trade")
            result["status"] = "completed"
            
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
            
            # Step 2: Research Synthesis
            print(f"[{run_id}] Running Researcher...")
            research_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "technical_analysis": technical_result.get("analysis"),
                "sentiment_analysis": sentiment_result.get("analysis"),
                "tokenomics_analysis": tokenomics_result.get("analysis"),
            }
            
            research_result = await self.researcher.aanalyze(research_context)
            result["agents"]["researcher"] = research_result
            
            # Step 3: Trade Proposal
            print(f"[{run_id}] Running Trader...")
            trader_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "research_thesis": research_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("cash_balance", 0),
            }
            
            trader_result = await self.trader.aanalyze(trader_context)
            result["agents"]["trader"] = trader_result
            
            # Step 4: Risk Management
            print(f"[{run_id}] Running Risk Manager...")
            risk_context = {
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "trade_proposal": trader_result.get("analysis"),
                "portfolio_info": portfolio_data,
                "available_cash": portfolio_data.get("cash_balance", 0),
                "total_equity": portfolio_data.get("total_equity", 0),
                "current_positions": portfolio_data.get("positions", []),
            }
            
            risk_result = await self.risk_manager.aanalyze(risk_context)
            result["agents"]["risk_manager"] = risk_result
            
            # Extract final decision
            result["final_decision"] = risk_result.get("analysis", {}).get("final_trade")
            result["status"] = "completed"
            
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
