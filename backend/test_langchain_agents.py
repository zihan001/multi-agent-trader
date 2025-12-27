"""
Test script for LangChain agents.

Tests the LangChain-based Researcher, Trader, and Risk Manager agents
with LangChain's ReAct pattern and tool framework.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.langchain.agents import LangChainResearcher, LangChainTrader, LangChainRiskManager


async def test_langchain_researcher():
    """Test LangChain Researcher agent."""
    print("\n" + "="*80)
    print("TEST 1: LangChain Researcher Agent")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        researcher = LangChainResearcher(db, max_iterations=3)
        
        print(f"\n📋 Agent: {researcher.name}")
        print(f"   Tools: {len(researcher.tools)}")
        tool_names = [t.name for t in researcher.tools]
        print(f"   Tool Names: {tool_names}")
        
        # Create test context with conflicting analyst signals
        context = {
            "symbol": "BTCUSDT",
            "current_price": 44500,
            "technical_analysis": {
                "recommendation": "strong_buy",
                "confidence": 85,
                "key_insight": "RSI oversold, MACD bullish crossover",
                "top_signals": ["RSI: 28 (oversold)", "MACD: bullish crossover"]
            },
            "sentiment_analysis": {
                "recommendation": "bearish",
                "confidence": 70,
                "key_insight": "Fear & Greed at 25 (extreme fear)",
                "top_signals": ["Social sentiment: very bearish", "Fear & Greed: 25"]
            },
            "tokenomics_analysis": {
                "recommendation": "hold",
                "confidence": 60,
                "key_insight": "Fairly valued fundamentals",
                "top_signals": ["Supply: 95% circulating", "Market cap: mega"]
            }
        }
        
        print("\n🤖 Running LangChain Researcher with conflicting signals...")
        print("   Technical: STRONG_BUY (85%)")
        print("   Sentiment: BEARISH (70%)")
        print("   Tokenomics: HOLD (60%)")
        
        result = await researcher.analyze(context)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Iterations: {result['metadata'].get('iterations', 0)}")
        print(f"   Tools Used: {result['metadata'].get('tools_used', [])}")
        
        analysis = result.get("analysis", {})
        if isinstance(analysis, dict):
            print(f"\n📊 INVESTMENT THESIS:")
            print(f"   Direction: {analysis.get('direction', 'N/A')}")
            print(f"   Conviction: {analysis.get('conviction', 0)}%")
            print(f"   Thesis: {analysis.get('investment_thesis', 'N/A')}")
            print(f"   Rationale: {analysis.get('primary_rationale', 'N/A')[:100]}...")
        
        print("\n✅ LangChain Researcher test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ LangChain Researcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_langchain_trader():
    """Test LangChain Trader agent."""
    print("\n" + "="*80)
    print("TEST 2: LangChain Trader Agent")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        trader = LangChainTrader(db, max_iterations=3)
        
        print(f"\n📋 Agent: {trader.name}")
        print(f"   Tools: {len(trader.tools)}")
        
        # Create test context
        context = {
            "symbol": "BTCUSDT",
            "current_price": 44500,
            "research_thesis": {
                "direction": "bullish",
                "conviction": 78,
                "investment_thesis": "Technical oversold conditions with contrarian sentiment signal",
                "time_horizon": "short_term"
            },
            "available_cash": 10000
        }
        
        print("\n🤖 Running LangChain Trader with bullish thesis...")
        print(f"   Conviction: 78%")
        print(f"   Available Cash: ${context['available_cash']:,.2f}")
        
        result = await trader.analyze(context)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Iterations: {result['metadata'].get('iterations', 0)}")
        print(f"   Tools Used: {result['metadata'].get('tools_used', [])}")
        
        analysis = result.get("analysis", {})
        if isinstance(analysis, dict):
            print(f"\n📊 TRADE PROPOSAL:")
            print(f"   Action: {analysis.get('action', 'N/A').upper()}")
            print(f"   Size: ${analysis.get('size', 0):,.2f}")
            print(f"   Entry: ${analysis.get('entry_price', 0):,.2f}")
            print(f"   Stop Loss: ${analysis.get('stop_loss', 0):,.2f}")
            print(f"   Take Profit: ${analysis.get('take_profit', 0):,.2f}")
        
        print("\n✅ LangChain Trader test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ LangChain Trader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_langchain_risk_manager():
    """Test LangChain Risk Manager agent."""
    print("\n" + "="*80)
    print("TEST 3: LangChain Risk Manager Agent")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        risk_manager = LangChainRiskManager(db, max_iterations=3)
        
        print(f"\n📋 Agent: {risk_manager.name}")
        print(f"   Tools: {len(risk_manager.tools)}")
        
        # Create test context
        context = {
            "symbol": "BTCUSDT",
            "current_price": 44500,
            "trade_proposal": {
                "action": "buy",
                "size": 2000,
                "entry_price": 44500,
                "stop_loss": 43600,
                "take_profit": 46500
            },
            "available_cash": 10000,
            "total_equity": 15000
        }
        
        print("\n🤖 Running LangChain Risk Manager...")
        print(f"   Proposed Trade: BUY ${context['trade_proposal']['size']:,.2f}")
        
        result = await risk_manager.analyze(context)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Iterations: {result['metadata'].get('iterations', 0)}")
        print(f"   Tools Used: {result['metadata'].get('tools_used', [])}")
        
        analysis = result.get("analysis", {})
        if isinstance(analysis, dict):
            print(f"\n📊 RISK VALIDATION:")
            print(f"   Decision: {analysis.get('decision', 'N/A').upper()}")
            print(f"   Reasoning: {analysis.get('reasoning', 'N/A')[:100]}...")
        
        print("\n✅ LangChain Risk Manager test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ LangChain Risk Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """Run all tests."""
    print("\n🔗 LangChain Agents Test Suite")
    print("="*80)
    print("Testing LangChain's ReAct pattern with tool framework")
    print("="*80)
    
    # Test 1: Researcher
    test1_passed = await test_langchain_researcher()
    
    # Test 2: Trader
    test2_passed = await test_langchain_trader()
    
    # Test 3: Risk Manager
    test3_passed = await test_langchain_risk_manager()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"LangChain Researcher: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"LangChain Trader: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"LangChain Risk Manager: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    print("\n💡 Key Features:")
    print("  ✅ LangChain's create_react_agent for ReAct pattern")
    print("  ✅ LangChain StructuredTool for type-safe tool calling")
    print("  ✅ DatabaseCallbackHandler for observability")
    print("  ✅ AgentExecutor with max_iterations control")
    print("  ✅ Full integration with existing services (Binance, Portfolio)")
    print("  ✅ Maintains reasoning trace and tool usage")


if __name__ == "__main__":
    asyncio.run(main())
