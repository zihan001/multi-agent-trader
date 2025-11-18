#!/usr/bin/env python3
"""
Test script to verify prompt compression optimizations.

This script runs a single analysis and reports token usage per agent.
"""
import sys
import requests
import json
from datetime import datetime

# API endpoint
BASE_URL = "http://localhost:8000"

def test_analysis(symbol="BTCUSDT"):
    """Run a single analysis and report token usage."""
    print(f"Testing prompt optimization with {symbol}...")
    print("=" * 60)
    
    try:
        # Trigger analysis
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting analysis...")
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"symbol": symbol, "mode": "live"},
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
        
        result = response.json()
        print(f"✅ Analysis completed: {result.get('status')}")
        
        # Extract token usage
        agents = result.get("agents", {})
        total_tokens = 0
        total_cost = 0.0
        
        print("\n" + "=" * 60)
        print("TOKEN USAGE BY AGENT")
        print("=" * 60)
        
        for agent_name, agent_data in agents.items():
            metadata = agent_data.get("metadata", {})
            tokens = metadata.get("tokens", 0)
            cost = metadata.get("cost", 0.0)
            latency = metadata.get("latency", 0.0)
            
            total_tokens += tokens
            total_cost += cost
            
            print(f"\n{agent_name.upper()}")
            print(f"  Tokens:  {tokens:>6,} tokens")
            print(f"  Cost:    ${cost:>8.6f}")
            print(f"  Latency: {latency:>6.2f}s")
        
        print("\n" + "=" * 60)
        print("TOTAL")
        print("=" * 60)
        print(f"Total Tokens: {total_tokens:,}")
        print(f"Total Cost:   ${total_cost:.6f}")
        print(f"\n🎯 Target: 8,175-10,675 tokens (19-23% reduction)")
        
        if total_tokens <= 10675:
            print("✅ Token usage within optimized range!")
        else:
            print(f"⚠️  Token usage higher than expected (baseline: 10,150-13,900)")
        
        # Check final decision
        final_decision = result.get("final_decision")
        if final_decision:
            print(f"\n📊 Final Decision: {final_decision.get('action', 'N/A')}")
            print(f"   Confidence: {final_decision.get('confidence', 0)}%")
        else:
            print("\n⚠️  No final decision produced")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running?")
        print("   Run: docker-compose up backend")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>120s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main entry point."""
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    
    print("PROMPT OPTIMIZATION TEST")
    print("=" * 60)
    print(f"Testing symbol: {symbol}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_analysis(symbol)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run test with multiple symbols: BTC, ETH, SOL")
        print("2. Check agent_logs table for detailed token breakdown")
        print("3. Compare with baseline metrics in OPTIMIZATION_LOG.md")
        print("4. Proceed with Phase 2: Analyst Result Caching")
        sys.exit(0)
    else:
        print("\n❌ Test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
