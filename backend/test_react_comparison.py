"""
Comparison test: Classic Instructor agents vs ReAct agents.

Runs the same analysis request through both pipelines and compares results.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.agents.pipeline import AgentPipeline
from app.agents.llm_client import LLMClient


async def run_classic_analysis(symbol="BTCUSDT"):
    """Run analysis with classic Instructor agents."""
    print("\n" + "="*80)
    print("🎯 CLASSIC ANALYSIS (Instructor-based agents)")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        llm_client = LLMClient(db)
        pipeline = AgentPipeline(db, llm_client, use_react=False)
        
        market_data = {
            "current_price": 44500,
            "timeframe": "1h",
            "candles": [],
            "indicators": {},
            "sentiment_data": {},
            "token_data": {}
        }
        
        portfolio_data = {
            "cash": 10000,
            "equity": 10000,
            "positions": []
        }
        
        print(f"\n📊 Market: {symbol} @ ${market_data['current_price']:,.2f}")
        print(f"🤖 Mode: Classic (Instructor + Pydantic)")
        
        start_time = datetime.now()
        result = await pipeline.arun(symbol, market_data, portfolio_data)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n⏱️  Execution Time: {duration:.2f}s")
        
        # Show results
        print(f"\n📈 Technical: {result['technical']['recommendation'].upper()} ({result['technical']['confidence']}%)")
        print(f"💬 Sentiment: {result['sentiment']['recommendation'].upper()} ({result['sentiment']['confidence']}%)")
        print(f"💎 Tokenomics: {result['tokenomics']['recommendation'].upper()} ({result['tokenomics']['confidence']}%)")
        
        research = result.get('research', {})
        print(f"\n🔍 Research: {research.get('direction', 'N/A').upper()} ({research.get('conviction', 0)}%)")
        print(f"   Thesis: {research.get('investment_thesis', 'N/A')[:80]}...")
        
        trade = result.get('trade', {})
        print(f"\n💰 Trade: {trade.get('action', 'N/A').upper()} ${trade.get('size', 0):,.2f}")
        print(f"   Entry: ${trade.get('entry_price', 0):,.2f} | Stop: ${trade.get('stop_loss', 0):,.2f} | Target: ${trade.get('take_profit', 0):,.2f}")
        
        risk = result.get('risk', {})
        print(f"\n🛡️  Risk: {risk.get('decision', 'N/A').upper()}")
        print(f"   Reasoning: {risk.get('reasoning', 'N/A')[:80]}...")
        
        return {
            "duration": duration,
            "result": result
        }
        
    except Exception as e:
        print(f"\n❌ Classic analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


async def run_react_analysis(symbol="BTCUSDT"):
    """Run analysis with ReAct agents."""
    print("\n" + "="*80)
    print("🚀 REACT ANALYSIS (Reasoning + Acting agents)")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        llm_client = LLMClient(db)
        pipeline = AgentPipeline(db, llm_client, use_react=True)
        
        market_data = {
            "current_price": 44500,
            "timeframe": "1h",
            "candles": [],
            "indicators": {},
            "sentiment_data": {},
            "token_data": {}
        }
        
        portfolio_data = {
            "cash": 10000,
            "equity": 10000,
            "positions": []
        }
        
        print(f"\n📊 Market: {symbol} @ ${market_data['current_price']:,.2f}")
        print(f"🤖 Mode: ReAct (Thought → Action → Observation)")
        
        start_time = datetime.now()
        result = await pipeline.arun(symbol, market_data, portfolio_data)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n⏱️  Execution Time: {duration:.2f}s")
        
        # Show results
        print(f"\n📈 Technical: {result['technical']['recommendation'].upper()} ({result['technical']['confidence']}%)")
        print(f"💬 Sentiment: {result['sentiment']['recommendation'].upper()} ({result['sentiment']['confidence']}%)")
        print(f"💎 Tokenomics: {result['tokenomics']['recommendation'].upper()} ({result['tokenomics']['confidence']}%)")
        
        research = result.get('research', {})
        research_analysis = research.get('analysis', {}) if isinstance(research.get('analysis'), dict) else {}
        research_meta = research.get('metadata', {})
        
        print(f"\n🔍 Research (ReAct): {research_analysis.get('direction', 'N/A').upper()} ({research_analysis.get('conviction', 0)}%)")
        print(f"   Iterations: {research_meta.get('iterations', 0)}")
        print(f"   Thesis: {research_analysis.get('investment_thesis', 'N/A')[:80]}...")
        
        if research_analysis.get('additional_research_conducted'):
            print(f"   🔧 Research Tools Used: {research_analysis['additional_research_conducted'][:60]}...")
        
        trade = result.get('trade', {})
        trade_analysis = trade.get('analysis', {}) if isinstance(trade.get('analysis'), dict) else {}
        trade_meta = trade.get('metadata', {})
        
        print(f"\n💰 Trade (ReAct): {trade_analysis.get('action', 'N/A').upper()} ${trade_analysis.get('size', 0):,.2f}")
        print(f"   Iterations: {trade_meta.get('iterations', 0)}")
        print(f"   Entry: ${trade_analysis.get('entry_price', 0):,.2f} | Stop: ${trade_analysis.get('stop_loss', 0):,.2f} | Target: ${trade_analysis.get('take_profit', 0):,.2f}")
        
        if trade_analysis.get('tools_used'):
            print(f"   🔧 Trading Tools Used: {', '.join(trade_analysis['tools_used'])}")
        
        risk = result.get('risk', {})
        risk_analysis = risk.get('analysis', {}) if isinstance(risk.get('analysis'), dict) else {}
        risk_meta = risk.get('metadata', {})
        
        print(f"\n🛡️  Risk (ReAct): {risk_analysis.get('decision', 'N/A').upper()}")
        print(f"   Iterations: {risk_meta.get('iterations', 0)}")
        print(f"   Reasoning: {risk_analysis.get('reasoning', 'N/A')[:80]}...")
        
        if risk_analysis.get('risk_checks_performed'):
            print(f"   ✓ Checks: {', '.join(risk_analysis['risk_checks_performed'])}")
        
        return {
            "duration": duration,
            "result": result
        }
        
    except Exception as e:
        print(f"\n❌ ReAct analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


async def main():
    """Run comparison test."""
    print("\n" + "="*80)
    print("🔬 CLASSIC vs REACT COMPARISON TEST")
    print("="*80)
    print("Comparing decision quality, execution time, and tool usage")
    print("="*80)
    
    # Run classic analysis
    classic_result = await run_classic_analysis()
    
    # Run ReAct analysis
    react_result = await run_react_analysis()
    
    # Comparison summary
    print("\n" + "="*80)
    print("📊 COMPARISON SUMMARY")
    print("="*80)
    
    if classic_result and react_result:
        print(f"\n⏱️  Execution Time:")
        print(f"   Classic: {classic_result['duration']:.2f}s")
        print(f"   ReAct: {react_result['duration']:.2f}s")
        print(f"   Difference: {react_result['duration'] - classic_result['duration']:+.2f}s ({((react_result['duration'] / classic_result['duration'] - 1) * 100):+.1f}%)")
        
        print(f"\n🤖 Agent Behavior:")
        print(f"   Classic: Static prompts, single LLM call per agent")
        print(f"   ReAct: Dynamic tool usage, iterative reasoning (max 3 iterations)")
        
        print(f"\n💡 Key Differences:")
        print(f"   ✅ ReAct agents can fetch live order book data")
        print(f"   ✅ ReAct agents can query portfolio exposure dynamically")
        print(f"   ✅ ReAct agents can resolve analyst conflicts with news/indicators")
        print(f"   ✅ ReAct agents maintain reasoning trace for explainability")
        print(f"   ⚠️  ReAct agents use more tokens (multiple LLM calls per iteration)")
        
        print(f"\n🎯 Use Cases:")
        print(f"   Classic: Fast, cost-effective for straightforward analysis")
        print(f"   ReAct: Better for complex scenarios requiring dynamic data access")
        
        print("\n✅ Both pipelines completed successfully!")
    else:
        print("\n❌ One or both pipelines failed")


if __name__ == "__main__":
    asyncio.run(main())
