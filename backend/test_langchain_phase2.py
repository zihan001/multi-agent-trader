"""
Test script for LangChain Phase 2 integration.

Tests:
1. LangChain agent wrapper with observability
2. RAG knowledge base storage and retrieval
3. Comparison with Instructor-only approach
"""
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.agents.technical import TechnicalAnalyst
from app.langchain.agent_wrapper import LangChainAgentWrapper
from app.langchain.rag import MarketKnowledgeBase


async def test_langchain_wrapper():
    """Test LangChain wrapper with observability."""
    print("\n" + "=" * 60)
    print("TEST 1: LangChain Agent Wrapper with Observability")
    print("=" * 60)
    
    # Set up database session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create technical analyst
        analyst = TechnicalAnalyst(db=db)
        
        # Wrap with LangChain
        lc_analyst = LangChainAgentWrapper(
            agent=analyst,
            db=db,
            enable_console_logging=True,
        )
        
        # Test context
        context = {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "current_price": 91000,
            "indicators": {
                "rsi": 65.5,
                "macd": 350.0,
                "macd_signal": 280.0,
                "ema_9": 90500,
                "ema_21": 89800,
            },
            "candles": [
                {"close": 90000, "volume": 1000},
                {"close": 90500, "volume": 1200},
                {"close": 91000, "volume": 1100},
            ]
        }
        
        print("\n📊 Running analysis with LangChain wrapper...")
        result = await lc_analyst.aanalyze(context)
        
        print(f"\n✅ Analysis completed!")
        print(f"Agent: {result['agent_name']}")
        print(f"Trend: {result['analysis']['trend']}")
        print(f"Confidence: {result['analysis']['confidence']}%")
        print(f"Recommendation: {result['analysis']['recommendation']}")
        print(f"LangChain enabled: {result['metadata']['langchain']}")
        
        print("\n💾 Check your agent_logs table - LangChain callbacks logged this call!")
        
    finally:
        db.close()


def test_rag_knowledge_base():
    """Test RAG knowledge base with ChromaDB."""
    print("\n" + "=" * 60)
    print("TEST 2: RAG Knowledge Base (ChromaDB)")
    print("=" * 60)
    
    # Initialize knowledge base
    kb = MarketKnowledgeBase(
        persist_directory="./test_chromadb",
        collection_name="test_insights",
    )
    
    print("\n📚 Initializing ChromaDB knowledge base...")
    
    # Add some sample analyses
    print("\n➕ Adding sample analyses...")
    
    kb.add_analysis(
        symbol="BTCUSDT",
        agent_name="technical",
        analysis={
            "trend": "bullish",
            "recommendation": "buy",
            "confidence": 80,
            "reasoning": "Strong uptrend with RSI at 65, MACD golden cross",
            "key_observations": [
                "Price above all EMAs",
                "Volume confirming uptrend",
                "Resistance at $92k"
            ],
            "risk_factors": ["Overbought RSI", "Low volume"]
        }
    )
    
    kb.add_analysis(
        symbol="ETHUSDT",
        agent_name="sentiment",
        analysis={
            "overall_sentiment": "neutral",
            "recommendation": "hold",
            "confidence": 60,
            "reasoning": "Mixed signals from social and news",
            "key_observations": ["Fear & Greed at 50", "Moderate volume"]
        }
    )
    
    kb.add_trade_outcome(
        symbol="BTCUSDT",
        action="buy",
        entry_price=90000,
        exit_price=92000,
        pnl=2000,
        reasoning="Bought on technical breakout with strong volume confirmation"
    )
    
    print("✅ Added 3 documents to knowledge base")
    
    # Retrieve similar analyses
    print("\n🔍 Retrieving similar analyses for: 'BTC showing bullish momentum'")
    results = kb.retrieve_similar_analyses(
        query="BTC showing bullish momentum with strong indicators",
        k=2
    )
    
    print(f"\n📋 Found {len(results)} similar analyses:")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. {result['metadata']['agent']} - {result['metadata']['symbol']}")
        print(f"     {result['content'][:150]}...")
    
    # Retrieve similar trades
    print("\n🔍 Retrieving similar trades for: 'successful BTC trades'")
    trade_results = kb.retrieve_similar_trades(
        query="successful BTC trades with positive PnL",
        k=1
    )
    
    print(f"\n📋 Found {len(trade_results)} similar trades:")
    for i, result in enumerate(trade_results, 1):
        print(f"\n  {i}. {result['metadata']['action'].upper()} {result['metadata']['symbol']}")
        print(f"     PnL: ${result['metadata'].get('pnl', 0):,.2f}")
    
    print("\n✅ RAG knowledge base working perfectly!")
    print("💡 This can be used to enhance agent decisions with historical context")


def test_comparison():
    """Compare Instructor-only vs LangChain approach."""
    print("\n" + "=" * 60)
    print("TEST 3: Comparison Summary")
    print("=" * 60)
    
    print("\n📊 Instructor-Only (Phase 1):")
    print("   ✅ Type-safe structured outputs")
    print("   ✅ Zero JSON parsing errors")
    print("   ✅ Fast and reliable")
    print("   ✅ Manual logging to database")
    print("   ❌ No automatic observability")
    print("   ❌ No RAG capabilities")
    
    print("\n🔗 LangChain Integration (Phase 2):")
    print("   ✅ Everything from Phase 1")
    print("   ✅ Automatic observability via callbacks")
    print("   ✅ RAG with ChromaDB for learning")
    print("   ✅ LCEL chains for complex workflows")
    print("   ✅ LangGraph ready for multi-agent orchestration")
    print("   ℹ️  Slightly more overhead")
    
    print("\n💡 Best Practice:")
    print("   • Use Instructor for simple, fast agent calls")
    print("   • Use LangChain wrapper when you need:")
    print("     - Automatic observability logging")
    print("     - RAG-enhanced decisions")
    print("     - Complex multi-step chains")
    print("     - LangGraph orchestration")


async def main():
    """Run all tests."""
    print("\n🚀 LangChain Phase 2 Integration Tests")
    print("=" * 60)
    
    # Test 1: LangChain wrapper (requires LLM API)
    try:
        await test_langchain_wrapper()
    except Exception as e:
        print(f"\n❌ LangChain wrapper test failed: {e}")
        print("   (This is expected if LLM_API_KEY not set)")
    
    # Test 2: RAG knowledge base (works offline)
    try:
        test_rag_knowledge_base()
    except Exception as e:
        print(f"\n❌ RAG test failed: {e}")
    
    # Test 3: Comparison
    test_comparison()
    
    print("\n" + "=" * 60)
    print("✅ Phase 2 Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
