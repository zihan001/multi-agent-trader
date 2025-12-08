"""
Test script for ReAct agents.

Tests the new Researcher, Trader, and Risk Manager ReAct agents
with tool-calling capabilities.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.agents.researcher_react import ResearcherReAct
from app.agents.trader_react import TraderReAct
from app.agents.risk_manager_react import RiskManagerReAct
from app.agents.llm_client import LLMClient


async def test_researcher_react():
    """Test Researcher ReAct agent."""
    print("\n" + "="*80)
    print("TEST 1: Researcher ReAct Agent")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        llm_client = LLMClient(db)
        researcher = ResearcherReAct(db, llm_client, max_iterations=3)
        
        print(f"\n📋 Agent: {researcher.name}")
        print(f"   Role: {researcher.role}")
        print(f"   Available Tools: {list(researcher.tools.keys())}")
        
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
        
        print("\n🤖 Running Researcher with conflicting signals...")
        print("   Technical: STRONG_BUY (85%)")
        print("   Sentiment: BEARISH (70%)")
        print("   Tokenomics: HOLD (60%)")
        
        result = await researcher.analyze(context)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Iterations: {result['metadata'].get('iterations', 0)}")
        
        analysis = result.get("analysis", {})
        if isinstance(analysis, dict):
            print(f"\n📊 INVESTMENT THESIS:")
            print(f"   Direction: {analysis.get('direction', 'N/A')}")
            print(f"   Conviction: {analysis.get('conviction', 0)}%")
            print(f"   Thesis: {analysis.get('investment_thesis', 'N/A')}")
            print(f"   Primary Rationale: {analysis.get('primary_rationale', 'N/A')}")
            print(f"   Time Horizon: {analysis.get('time_horizon', 'N/A')}")
            
            if analysis.get('key_conflicts_resolved'):
                print(f"\n🔍 Conflicts Resolved:")
                print(f"   {analysis['key_conflicts_resolved']}")
            
            if analysis.get('additional_research_conducted'):
                print(f"\n🔧 Additional Research:")
                print(f"   {analysis['additional_research_conducted']}")
        
        # Show ReAct history
        history = result['metadata'].get('history', [])
        if history:
            print(f"\n📝 ReAct Trace ({len(history)} steps):")
            for i, step in enumerate(history[:6], 1):  # Show first 6 steps
                step_type = step.get('type', 'unknown')
                content = step.get('content', '')
                if step_type == "thought":
                    print(f"   {i}. Thought: {content[:80]}...")
                elif step_type == "action":
                    print(f"   {i}. Action: {content}")
                elif step_type == "observation":
                    print(f"   {i}. Observation: {content[:60]}...")
        
        print("\n✅ Researcher ReAct test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Researcher ReAct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_trader_react():
    """Test Trader ReAct agent."""
    print("\n" + "="*80)
    print("TEST 2: Trader ReAct Agent")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        llm_client = LLMClient(db)
        trader = TraderReAct(db, llm_client, max_iterations=3)
        
        print(f"\n📋 Agent: {trader.name}")
        print(f"   Role: {trader.role}")
        print(f"   Available Tools: {list(trader.tools.keys())}")
        
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
        
        print("\n🤖 Running Trader with bullish thesis...")
        print(f"   Conviction: 78%")
        print(f"   Available Cash: ${context['available_cash']:,.2f}")
        
        result = await trader.analyze(context)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Iterations: {result['metadata'].get('iterations', 0)}")
        
        analysis = result.get("analysis", {})
        if isinstance(analysis, dict):
            print(f"\n📊 TRADE PROPOSAL:")
            print(f"   Action: {analysis.get('action', 'N/A').upper()}")
            print(f"   Size: ${analysis.get('size', 0):,.2f}")
            print(f"   Entry Price: ${analysis.get('entry_price', 0):,.2f}")
            print(f"   Stop Loss: ${analysis.get('stop_loss', 0):,.2f}")
            print(f"   Take Profit: ${analysis.get('take_profit', 0):,.2f}")
            print(f"   Risk-Reward: {analysis.get('risk_reward_ratio', 0):.2f}")
            print(f"   Execution: {analysis.get('execution_strategy', 'N/A')}")
            print(f"   Conviction: {analysis.get('conviction', 0)}%")
            
            if analysis.get('market_conditions'):
                print(f"\n💹 Market Conditions:")
                print(f"   {analysis['market_conditions'][:150]}...")
            
            if analysis.get('tools_used'):
                print(f"\n🔧 Tools Used: {', '.join(analysis['tools_used'])}")
        
        print("\n✅ Trader ReAct test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Trader ReAct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_risk_manager_react():
    """Test Risk Manager ReAct agent."""
    print("\n" + "="*80)
    print("TEST 3: Risk Manager ReAct Agent")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        llm_client = LLMClient(db)
        risk_manager = RiskManagerReAct(db, llm_client, max_iterations=3)
        
        print(f"\n📋 Agent: {risk_manager.name}")
        print(f"   Role: {risk_manager.role}")
        print(f"   Available Tools: {list(risk_manager.tools.keys())}")
        
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
            "total_equity": 15000,
            "current_positions": []
        }
        
        print("\n🤖 Running Risk Manager...")
        print(f"   Proposed Trade: BUY ${context['trade_proposal']['size']:,.2f}")
        print(f"   Entry: ${context['trade_proposal']['entry_price']:,.2f}")
        print(f"   Stop Loss: ${context['trade_proposal']['stop_loss']:,.2f}")
        print(f"   Take Profit: ${context['trade_proposal']['take_profit']:,.2f}")
        
        result = await risk_manager.analyze(context)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Iterations: {result['metadata'].get('iterations', 0)}")
        
        analysis = result.get("analysis", {})
        if isinstance(analysis, dict):
            print(f"\n📊 RISK VALIDATION:")
            print(f"   Decision: {analysis.get('decision', 'N/A').upper()}")
            print(f"   Reasoning: {analysis.get('reasoning', 'N/A')[:150]}...")
            
            checks = analysis.get('risk_checks_performed', [])
            if checks:
                print(f"\n✓ Risk Checks: {', '.join(checks)}")
            
            violations = analysis.get('violations_found', [])
            if violations:
                print(f"\n⚠️  Violations: {', '.join(violations)}")
            
            final_trade = analysis.get('final_trade', {})
            if final_trade:
                print(f"\n💼 Final Trade:")
                print(f"   Action: {final_trade.get('action', 'N/A').upper()}")
                print(f"   Size: ${final_trade.get('size', 0):,.2f}")
                if final_trade.get('modifications_made'):
                    print(f"   Modifications: {final_trade['modifications_made']}")
            
            risk_metrics = analysis.get('risk_metrics', {})
            if risk_metrics:
                print(f"\n📈 Risk Metrics:")
                print(f"   Max Loss: ${risk_metrics.get('max_loss_dollars', 0):,.2f} ({risk_metrics.get('max_loss_portfolio_pct', 0):.1f}% of portfolio)")
                print(f"   Risk-Reward: {risk_metrics.get('risk_reward_ratio', 0):.2f}")
                print(f"   Position Size: {risk_metrics.get('position_size_pct', 0):.1f}%")
        
        print("\n✅ Risk Manager ReAct test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Risk Manager ReAct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """Run all tests."""
    print("\n🚀 ReAct Agents Test Suite")
    print("="*80)
    print("Testing Researcher, Trader, and Risk Manager with tool-calling capabilities")
    print("="*80)
    
    # Test 1: Researcher
    test1_passed = await test_researcher_react()
    
    # Test 2: Trader
    test2_passed = await test_trader_react()
    
    # Test 3: Risk Manager
    test3_passed = await test_risk_manager_react()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Researcher ReAct: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Trader ReAct: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Risk Manager ReAct: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    print("\n💡 Key Features:")
    print("  ✅ ReAct pattern: Thought → Action → Observation → Repeat")
    print("  ✅ Dynamic tool calling based on reasoning")
    print("  ✅ Researcher can fetch news, query analysts, get order book")
    print("  ✅ Trader can analyze order book, check fills, optimize entry")
    print("  ✅ Risk Manager can query portfolio, calculate VaR, simulate impact")
    print("  ✅ Max 3 iterations per agent to control costs")
    print("  ✅ Maintains full trace of reasoning and tool usage")


if __name__ == "__main__":
    asyncio.run(main())
