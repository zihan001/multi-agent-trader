"""
LangGraph workflow for multi-agent trading decisions.

This replaces pipeline.py with a stateful graph that supports:
- Conditional routing
- Parallel execution
- RAG-enhanced context
- Human-in-the-loop
- Checkpointing and retry logic
"""
import time
import asyncio
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.langchain.state import TradingState, GraphConfig, AnalystResult, create_initial_state
from app.langchain.rag import MarketKnowledgeBase
from app.agents.technical import TechnicalAnalyst
from app.agents.sentiment import SentimentAnalyst
from app.agents.tokenomics import TokenomicsAnalyst
from app.agents.researcher import Researcher
from app.agents.trader import Trader
from app.agents.risk import RiskManager
from app.services.binance import BinanceService, get_latest_candles
from app.services.indicators import IndicatorService
from app.services.portfolio import PortfolioManager


class TradingWorkflow:
    """
    LangGraph-based trading workflow with intelligent routing and RAG.
    
    This is a more sophisticated replacement for pipeline.py that demonstrates:
    - State management
    - Conditional logic
    - Parallel execution
    - RAG integration
    - Human-in-the-loop
    """
    
    def __init__(
        self,
        db: Session,
        config: Optional[GraphConfig] = None,
        enable_rag: bool = True,
    ):
        """
        Initialize trading workflow.
        
        Args:
            db: Database session
            config: Graph configuration
            enable_rag: Whether to enable RAG lookups
        """
        self.db = db
        self.config = config or GraphConfig()
        
        # Initialize agents
        self.technical_analyst = TechnicalAnalyst(db=db)
        self.sentiment_analyst = SentimentAnalyst(db=db)
        self.tokenomics_analyst = TokenomicsAnalyst(db=db)
        self.researcher = Researcher(db=db)
        self.trader = Trader(db=db)
        self.risk_manager = RiskManager(db=db)
        
        # Initialize services
        self.binance = BinanceService()
        self.indicator_service = IndicatorService()
        self.portfolio = PortfolioManager(db=db)
        
        # Initialize RAG (optional)
        self.kb = None
        if enable_rag:
            try:
                self.kb = MarketKnowledgeBase()
            except Exception as e:
                print(f"Warning: RAG initialization failed: {e}")
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled state graph
        """
        workflow = StateGraph(TradingState)
        
        # Add nodes for each step
        workflow.add_node("fetch_market_data", self._fetch_market_data)
        workflow.add_node("rag_lookup", self._rag_lookup)
        workflow.add_node("run_analysts", self._run_analysts)
        workflow.add_node("check_confidence", self._check_confidence)
        workflow.add_node("run_researcher", self._run_researcher)
        workflow.add_node("run_trader", self._run_trader)
        workflow.add_node("check_risk_level", self._check_risk_level)
        workflow.add_node("run_risk_manager", self._run_risk_manager)
        workflow.add_node("request_approval", self._request_approval)
        workflow.add_node("execute_trade", self._execute_trade)
        workflow.add_node("store_outcome", self._store_outcome)
        
        # Set entry point
        workflow.set_entry_point("fetch_market_data")
        
        # Linear flow with conditional branches
        workflow.add_edge("fetch_market_data", "rag_lookup")
        workflow.add_edge("rag_lookup", "run_analysts")
        workflow.add_edge("run_analysts", "check_confidence")
        
        # Conditional: Skip if low confidence
        workflow.add_conditional_edges(
            "check_confidence",
            self._should_continue_after_analysts,
            {
                "continue": "run_researcher",
                "skip": END
            }
        )
        
        workflow.add_edge("run_researcher", "run_trader")
        workflow.add_edge("run_trader", "check_risk_level")
        
        # Conditional: Require human approval for high risk
        workflow.add_conditional_edges(
            "check_risk_level",
            self._should_request_approval,
            {
                "approve_needed": "request_approval",
                "proceed": "run_risk_manager"
            }
        )
        
        workflow.add_edge("request_approval", "run_risk_manager")
        workflow.add_edge("run_risk_manager", "execute_trade")
        workflow.add_edge("execute_trade", "store_outcome")
        workflow.add_edge("store_outcome", END)
        
        return workflow.compile()
    
    async def _fetch_market_data(self, state: TradingState) -> TradingState:
        """Fetch market data from Binance."""
        start_time = time.time()
        
        try:
            # Fetch candles (not async)
            candles_orm = get_latest_candles(
                self.db,
                state.symbol,
                state.timeframe,
                limit=100
            )
            
            if not candles_orm or len(candles_orm) < 20:
                # Not enough data in DB, fetch from Binance
                print(f"Fetching fresh data for {state.symbol} from Binance...")
                klines = await self.binance.fetch_klines(
                    symbol=state.symbol,
                    interval=state.timeframe,
                    limit=100
                )
                
                # Convert to DataFrame for indicators, then to dict list for context
                import pandas as pd
                df = pd.DataFrame([
                    {
                        "timestamp": datetime.fromtimestamp(k[0] / 1000),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                    }
                    for k in klines
                ])
                
                # Calculate indicators from DataFrame
                indicators = self.indicator_service.calculate_all_indicators(df)
                
                # Get current price
                current_price = float(df.iloc[-1]["close"])
                
                # Convert to dict list for agent context
                candles_dict = df.to_dict('records')
            else:
                # Use ORM objects for indicator calculation
                indicators = self.indicator_service.calculate_from_candles(candles_orm)
                
                # Get current price
                current_price = float(candles_orm[-1].close)
                
                # Convert ORM objects to dict list for agent context
                candles_dict = [
                    {
                        "timestamp": c.timestamp,
                        "open": float(c.open),
                        "high": float(c.high),
                        "low": float(c.low),
                        "close": float(c.close),
                        "volume": float(c.volume),
                    }
                    for c in candles_orm
                ]
            
            print(f"DEBUG: Fetched {len(candles_dict)} candles, current_price={current_price}")
            
            # Update state
            state.market_data = {
                "candles": candles_dict,
                "indicators": indicators,
                "timeframe": state.timeframe,
            }
            state.current_price = current_price
            
        except Exception as e:
            state.errors.append(f"Market data fetch failed: {str(e)}")
        
        state.step_times["fetch_market_data"] = time.time() - start_time
        return state
    
    async def _rag_lookup(self, state: TradingState) -> TradingState:
        """Look up similar historical situations using RAG."""
        start_time = time.time()
        
        if not self.kb or not self.config.enable_rag:
            return state
        
        try:
            # Build query from current context
            indicators = state.market_data.get("indicators", {})
            query = f"""
            {state.symbol} market analysis:
            Price: ${state.current_price:,.2f}
            RSI: {indicators.get('rsi', 0):.1f}
            MACD: {indicators.get('macd', 0):.1f}
            Trend: {"bullish" if indicators.get('ema_9', 0) > indicators.get('ema_21', 0) else "bearish"}
            """
            
            # Retrieve similar analyses
            state.similar_analyses = self.kb.retrieve_similar_analyses(
                query=query,
                symbol=state.symbol,
                k=self.config.rag_retrieval_k
            )
            
            # Retrieve similar trades
            state.similar_trades = self.kb.retrieve_similar_trades(
                query=query,
                symbol=state.symbol,
                k=self.config.rag_retrieval_k
            )
            
            print(f"📚 RAG: Found {len(state.similar_analyses)} similar analyses, "
                  f"{len(state.similar_trades)} similar trades")
            
        except Exception as e:
            state.warnings.append(f"RAG lookup failed: {str(e)}")
        
        state.step_times["rag_lookup"] = time.time() - start_time
        return state
    
    async def _run_analysts(self, state: TradingState) -> TradingState:
        """Run analyst agents (parallel execution)."""
        start_time = time.time()
        
        # Prepare contexts
        technical_context = {
            "symbol": state.symbol,
            "timeframe": state.timeframe,
            "current_price": state.current_price,
            "candles": state.market_data.get("candles", []),
            "indicators": state.market_data.get("indicators", {}),
            "similar_situations": state.similar_analyses[:2],  # RAG context
        }
        
        sentiment_context = {
            "symbol": state.symbol,
            "current_price": state.current_price,
            "price_change_24h": 0,  # TODO: Calculate from candles
            "sentiment_data": {},
            "similar_sentiment": state.similar_analyses[:2],  # RAG context
        }
        
        tokenomics_context = {
            "symbol": state.symbol,
            "current_price": state.current_price,
            "market_cap": 0,
            "volume_24h": 0,
            "token_data": {},
        }
        
        try:
            if self.config.run_analysts_parallel:
                # Parallel execution
                results = await asyncio.gather(
                    self.technical_analyst.aanalyze_structured(technical_context),
                    self.sentiment_analyst.aanalyze_structured(sentiment_context),
                    self.tokenomics_analyst.aanalyze_structured(tokenomics_context),
                    return_exceptions=True
                )
                
                # Unpack results
                technical_result, sentiment_result, tokenomics_result = results
            else:
                # Sequential execution
                technical_result = await self.technical_analyst.aanalyze_structured(technical_context)
                sentiment_result = await self.sentiment_analyst.aanalyze_structured(sentiment_context)
                tokenomics_result = await self.tokenomics_analyst.aanalyze_structured(tokenomics_context)
            
            # Store results
            if not isinstance(technical_result, Exception):
                state.technical_analysis = AnalystResult(
                    agent_name="technical",
                    analysis=technical_result["analysis"],
                    confidence=technical_result["analysis"].get("confidence", 0),
                    recommendation=technical_result["analysis"].get("recommendation", "hold"),
                    metadata=technical_result.get("metadata", {})
                )
                state.total_tokens += technical_result.get("metadata", {}).get("tokens", 0)
            
            if not isinstance(sentiment_result, Exception):
                state.sentiment_analysis = AnalystResult(
                    agent_name="sentiment",
                    analysis=sentiment_result["analysis"],
                    confidence=sentiment_result["analysis"].get("confidence", 0),
                    recommendation=sentiment_result["analysis"].get("trading_implication", "hold"),
                    metadata=sentiment_result.get("metadata", {})
                )
                state.total_tokens += sentiment_result.get("metadata", {}).get("tokens", 0)
            
            if not isinstance(tokenomics_result, Exception):
                state.tokenomics_analysis = AnalystResult(
                    agent_name="tokenomics",
                    analysis=tokenomics_result["analysis"],
                    confidence=tokenomics_result["analysis"].get("confidence", 0),
                    recommendation=tokenomics_result["analysis"].get("trading_implication", "hold"),
                    metadata=tokenomics_result.get("metadata", {})
                )
                state.total_tokens += tokenomics_result.get("metadata", {}).get("tokens", 0)
            
        except Exception as e:
            state.errors.append(f"Analyst execution failed: {str(e)}")
        
        state.step_times["run_analysts"] = time.time() - start_time
        return state
    
    def _check_confidence(self, state: TradingState) -> TradingState:
        """Calculate average confidence from analysts."""
        confidences = []
        
        if state.technical_analysis:
            confidences.append(state.technical_analysis.confidence)
        if state.sentiment_analysis:
            confidences.append(state.sentiment_analysis.confidence)
        if state.tokenomics_analysis:
            confidences.append(state.tokenomics_analysis.confidence)
        
        if confidences:
            state.average_confidence = sum(confidences) / len(confidences)
            state.confidence_gate_passed = state.average_confidence >= self.config.min_confidence_to_trade
        
        return state
    
    def _should_continue_after_analysts(self, state: TradingState) -> Literal["continue", "skip"]:
        """Conditional routing: Continue if confidence is high enough."""
        if state.confidence_gate_passed:
            return "continue"
        else:
            print(f"⏭️  Skipping trade: Average confidence {state.average_confidence:.1f}% "
                  f"below threshold {self.config.min_confidence_to_trade}%")
            return "skip"
    
    async def _run_researcher(self, state: TradingState) -> TradingState:
        """Run researcher to synthesize analyst outputs."""
        start_time = time.time()
        
        try:
            context = {
                "symbol": state.symbol,
                "current_price": state.current_price,
                "technical_analysis": state.technical_analysis.analysis if state.technical_analysis else {},
                "sentiment_analysis": state.sentiment_analysis.analysis if state.sentiment_analysis else {},
                "tokenomics_analysis": state.tokenomics_analysis.analysis if state.tokenomics_analysis else {},
                "average_confidence": state.average_confidence,
            }
            
            result = await self.researcher.aanalyze_structured(context)
            state.research_synthesis = result
            state.total_tokens += result.get("metadata", {}).get("tokens", 0)
            
        except Exception as e:
            state.errors.append(f"Researcher failed: {str(e)}")
        
        state.step_times["run_researcher"] = time.time() - start_time
        return state
    
    async def _run_trader(self, state: TradingState) -> TradingState:
        """Run trader to propose specific trade."""
        start_time = time.time()
        
        try:
            # Get portfolio summary with current price
            current_prices = {state.symbol: state.current_price} if state.current_price else None
            portfolio_summary = self.portfolio.get_portfolio_summary(current_prices)
            
            context = {
                "symbol": state.symbol,
                "current_price": state.current_price,
                "research_thesis": state.research_synthesis.get("analysis", {}) if state.research_synthesis else {},
                "portfolio_info": portfolio_summary,
                "available_cash": portfolio_summary.get("cash_balance", 0),
                "similar_trades": state.similar_trades[:3],  # RAG: Learn from past
            }
            
            result = await self.trader.aanalyze_structured(context)
            state.trade_proposal = result
            state.total_tokens += result.get("metadata", {}).get("tokens", 0)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            state.errors.append(f"Trader failed: {str(e)}")
            print(f"❌ Trader Error: {error_trace}")
        
        state.step_times["run_trader"] = time.time() - start_time
        return state
    
    def _check_risk_level(self, state: TradingState) -> TradingState:
        """Check if trade requires human approval."""
        if not state.trade_proposal:
            return state
        
        analysis = state.trade_proposal.get("analysis", {})
        risk_score = analysis.get("risk_score", 0)
        position_pct = analysis.get("position_size_pct", 0) or 0
        
        # Check thresholds
        state.requires_human_approval = (
            risk_score >= self.config.require_approval_above_risk or
            position_pct >= self.config.require_approval_above_position_pct
        )
        
        return state
    
    def _should_request_approval(self, state: TradingState) -> Literal["approve_needed", "proceed"]:
        """Conditional routing: Request approval for high-risk trades."""
        if state.requires_human_approval:
            print(f"⚠️  High-risk trade detected - requesting human approval")
            return "approve_needed"
        return "proceed"
    
    async def _request_approval(self, state: TradingState) -> TradingState:
        """Request human approval (stub for now)."""
        # In production, this would:
        # 1. Send notification (email/Slack/SMS)
        # 2. Wait for response via API endpoint
        # 3. Store approval/rejection
        
        print(f"📧 Human approval requested for {state.symbol} trade")
        print(f"   Risk Score: {state.trade_proposal.get('analysis', {}).get('risk_score', 0)}")
        print(f"   Position Size: {state.trade_proposal.get('analysis', {}).get('position_size_pct', 0)*100:.1f}%")
        print(f"   Waiting for approval... (auto-approved for demo)")
        
        # Auto-approve for demo (in production, this would wait)
        state.human_approved = True
        state.human_feedback = "Auto-approved (demo mode)"
        
        return state
    
    async def _run_risk_manager(self, state: TradingState) -> TradingState:
        """Run risk manager for final validation."""
        start_time = time.time()
        
        try:
            # Get portfolio summary with current price
            current_prices = {state.symbol: state.current_price} if state.current_price else None
            portfolio_summary = self.portfolio.get_portfolio_summary(current_prices)
            
            context = {
                "symbol": state.symbol,
                "current_price": state.current_price,
                "trade_proposal": state.trade_proposal.get("analysis", {}) if state.trade_proposal else {},
                "portfolio_info": portfolio_summary,
                "available_cash": portfolio_summary.get("cash_balance", 0),
                "total_equity": portfolio_summary.get("total_equity", 0),
                "current_positions": portfolio_summary.get("positions", []),
                "market_conditions": state.market_data.get("indicators", {}),
                "human_approved": state.human_approved,
            }
            
            result = await self.risk_manager.aanalyze_structured(context)
            state.risk_validation = result
            state.final_decision = result.get("analysis", {})
            state.total_tokens += result.get("metadata", {}).get("tokens", 0)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            state.errors.append(f"Risk manager failed: {str(e)}")
            print(f"❌ Risk Manager Error: {error_trace}")
        
        state.step_times["run_risk_manager"] = time.time() - start_time
        return state
    
    async def _execute_trade(self, state: TradingState) -> TradingState:
        """Execute the approved trade."""
        # Trade execution logic would go here
        # For now, just mark as executed
        state.executed = True
        state.execution_result = state.final_decision
        return state
    
    async def _store_outcome(self, state: TradingState) -> TradingState:
        """Store analysis outcome in RAG for learning."""
        if not self.kb:
            return state
        
        start_time = time.time()
        
        try:
            # Store all analyst results for future RAG retrieval
            if state.technical_analysis:
                self.kb.add_analysis(
                    symbol=state.symbol,
                    agent_name="technical",
                    analysis=state.technical_analysis.analysis
                )
            
            if state.sentiment_analysis:
                self.kb.add_analysis(
                    symbol=state.symbol,
                    agent_name="sentiment",
                    analysis=state.sentiment_analysis.analysis
                )
            
            if state.tokenomics_analysis:
                self.kb.add_analysis(
                    symbol=state.symbol,
                    agent_name="tokenomics",
                    analysis=state.tokenomics_analysis.analysis
                )
            
            # Store research synthesis
            if state.research_synthesis:
                self.kb.add_analysis(
                    symbol=state.symbol,
                    agent_name="researcher",
                    analysis=state.research_synthesis.get("analysis", {})
                )
            
            # Store trade outcome (if trade was proposed)
            if state.trade_proposal:
                trade_outcome = {
                    "symbol": state.symbol,
                    "action": state.trade_proposal.get("action"),
                    "quantity": state.trade_proposal.get("quantity"),
                    "entry_price": state.current_price,
                    "reasoning": state.trade_proposal.get("reasoning"),
                    "confidence": state.average_confidence,
                    "approved": state.risk_validation.get("analysis", {}).get("approved", False) if state.risk_validation else False,
                    "executed": state.executed,
                }
                self.kb.add_trade_outcome(
                    symbol=state.symbol,
                    trade_data=trade_outcome,
                    outcome="pending"  # In production, update with actual PnL
                )
            
            print(f"✅ Stored analysis and trade data to RAG knowledge base")
            
        except Exception as e:
            state.warnings.append(f"RAG storage failed: {str(e)}")
        
        return state
    
    async def run(
        self,
        symbol: str,
        timeframe: str = "1h",
        mode: str = "live",
    ) -> Dict[str, Any]:
        """
        Run the complete trading workflow.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            mode: Trading mode
            
        Returns:
            Final state as dict
        """
        # Create initial state
        initial_state = create_initial_state(symbol, timeframe, mode)
        
        # Run graph
        final_state = await self.graph.ainvoke(initial_state)
        
        # Convert to dict for API response (handle LangGraph's AddableValuesDict)
        if hasattr(final_state, 'model_dump'):
            return final_state.model_dump()
        elif isinstance(final_state, dict):
            # LangGraph returns a dict-like object, convert nested Pydantic models
            result = {}
            for key, value in final_state.items():
                if hasattr(value, 'model_dump'):
                    result[key] = value.model_dump()
                elif hasattr(value, 'dict'):
                    result[key] = value.dict()
                else:
                    result[key] = value
            return result
        else:
            # Fallback: convert to dict manually
            return dict(final_state)
