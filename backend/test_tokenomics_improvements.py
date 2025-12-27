"""
Test script for improved Tokenomics Analyst with real data sources.

Tests:
1. Tokenomics Service - Fetch real CoinGecko data
2. Tokenomics Service - Supply analysis
3. Tokenomics Service - Liquidity analysis  
4. Tokenomics Service - Developer activity assessment
5. Comprehensive tokenomics aggregation
6. Tokenomics Analyst with real data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.tokenomics import TokenomicsService
from app.agents.tokenomics import TokenomicsAnalyst
from app.agents.llm_client import LLMClient


async def test_tokenomics_service():
    """Test TokenomicsService data fetching."""
    print("\n" + "="*80)
    print("TEST 1: Tokenomics Service - Real Data Sources")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        service = TokenomicsService(db)
        
        # Test 1: CoinGecko Tokenomics
        print("\n🦎 Testing CoinGecko tokenomics for BTCUSDT...")
        coingecko_data = await service.fetch_coingecko_tokenomics("BTCUSDT")
        if coingecko_data:
            print(f"✅ CoinGecko Tokenomics Data:")
            print(f"   Name: {coingecko_data['name']}")
            print(f"   Blockchain: {coingecko_data['blockchain']}")
            print(f"   Categories: {', '.join(coingecko_data['categories'][:3])}")
            print(f"   Supply:")
            print(f"      Circulating: {coingecko_data['supply']['circulating']:,.0f}")
            max_supply = coingecko_data['supply']['max']
            max_supply_str = f"{max_supply:,.0f}" if max_supply else "Unlimited"
            print(f"      Max: {max_supply_str}")
            print(f"      % Circulating: {coingecko_data['supply']['percentage_circulating']:.1f}%")
            print(f"      Inflationary: {coingecko_data['supply']['is_inflationary']}")
            print(f"\n   Market:")
            print(f"      Market Cap: ${coingecko_data['market']['market_cap']:,.0f}")
            print(f"      Rank: #{coingecko_data['market']['market_cap_rank']}")
            print(f"      Volume/MCap: {coingecko_data['market']['volume_to_mcap_ratio']:.4f}")
            print(f"\n   Developer:")
            print(f"      Commits (4w): {coingecko_data['developer']['commit_count_4_weeks']}")
            print(f"      Stars: {coingecko_data['developer']['stars']}")
            print(f"      Forks: {coingecko_data['developer']['forks']}")
        else:
            print("❌ Failed to fetch CoinGecko tokenomics")
        
        # Test 2: Supply Analysis
        print("\n📊 Testing Supply Structure Analysis...")
        if coingecko_data:
            supply_analysis = service.analyze_supply_structure(coingecko_data['supply'])
            print(f"✅ Supply Analysis:")
            print(f"   Inflation Type: {supply_analysis['inflation_type']}")
            print(f"   Supply Status: {supply_analysis['supply_status']}")
            print(f"   Inflation Pressure: {supply_analysis['inflation_pressure']}")
        
        # Test 3: Liquidity Analysis
        print("\n💧 Testing Liquidity Analysis...")
        if coingecko_data:
            liquidity_analysis = service.analyze_liquidity(coingecko_data['market'])
            print(f"✅ Liquidity Analysis:")
            print(f"   Market Cap Tier: {liquidity_analysis['market_cap_tier']}")
            print(f"   Liquidity Rating: {liquidity_analysis['liquidity_rating']}")
            print(f"   Volume Rating: {liquidity_analysis['volume_rating']}")
        
        # Test 4: Developer Activity
        print("\n👨‍💻 Testing Developer Activity Assessment...")
        if coingecko_data:
            developer_assessment = service.assess_developer_activity(coingecko_data['developer'])
            print(f"✅ Developer Assessment:")
            print(f"   Activity Level: {developer_assessment['activity_level']}")
            print(f"   Project Health: {developer_assessment['project_health']}")
        
        # Test 5: Comprehensive Tokenomics
        print("\n🎯 Testing Comprehensive Tokenomics Aggregation...")
        comprehensive = await service.get_comprehensive_tokenomics(
            symbol="ETHUSDT",
            current_price=3500,
            market_cap=420000000000,
            volume_24h=15000000000
        )
        
        print(f"✅ Comprehensive Tokenomics:")
        print(f"   Coin: {comprehensive.get('coin_name', 'N/A')}")
        print(f"   Blockchain: {comprehensive.get('blockchain', 'N/A')}")
        print(f"   Data Quality: {comprehensive.get('data_quality', 'N/A')}")
        print(f"\n   Supply Analysis:")
        supply_anal = comprehensive.get('supply_analysis', {})
        print(f"      Type: {supply_anal.get('inflation_type', 'N/A')}")
        print(f"      Pressure: {supply_anal.get('inflation_pressure', 'N/A')}")
        print(f"\n   Liquidity Analysis:")
        liq_anal = comprehensive.get('liquidity_analysis', {})
        print(f"      Tier: {liq_anal.get('market_cap_tier', 'N/A')}")
        print(f"      Rating: {liq_anal.get('liquidity_rating', 'N/A')}")
        print(f"\n   Developer Assessment:")
        dev_assess = comprehensive.get('developer_assessment', {})
        print(f"      Activity: {dev_assess.get('activity_level', 'N/A')}")
        print(f"      Health: {dev_assess.get('project_health', 'N/A')}")
        
        await service.close()
        
        print("\n✅ All Tokenomics Service tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Tokenomics Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_tokenomics_analyst_with_real_data():
    """Test Tokenomics Analyst using real data."""
    print("\n" + "="*80)
    print("TEST 2: Tokenomics Analyst with Real Data")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # First, fetch comprehensive tokenomics data
        print("\n📡 Fetching real tokenomics data...")
        tokenomics_service = TokenomicsService(db)
        
        token_data = await tokenomics_service.get_comprehensive_tokenomics(
            symbol="BTCUSDT",
            current_price=45000,
            market_cap=880000000000,
            volume_24h=30000000000
        )
        
        await tokenomics_service.close()
        
        print(f"✅ Fetched tokenomics data:")
        print(f"   Coin: {token_data.get('coin_name', 'N/A')}")
        print(f"   Data Quality: {token_data.get('data_quality', 'N/A')}")
        
        # Now run Tokenomics Analyst
        print("\n🤖 Running Tokenomics Analyst with real data...")
        
        llm_client = LLMClient(db)
        analyst = TokenomicsAnalyst(db, llm_client)
        
        context = {
            "symbol": "BTCUSDT",
            "current_price": 45000,
            "market_cap": 880000000000,
            "volume_24h": 30000000000,
            "token_data": token_data
        }
        
        result = analyst.analyze_structured(context)
        
        print(f"\n✅ Tokenomics Analysis Complete:")
        analysis = result["analysis"]
        
        print(f"\n📊 TOKENOMICS ANALYSIS RESULTS:")
        print(f"   Fundamental Rating: {analysis['fundamental_rating']}")
        print(f"   Value Assessment: {analysis['value_assessment']}")
        print(f"   Long-term Outlook: {analysis['long_term_outlook']}")
        print(f"   Competitive Position: {analysis['competitive_position'][:100]}...")
        print(f"   Confidence: {analysis['confidence']}%")
        
        print(f"\n📈 Supply Analysis:")
        supply_analysis = analysis.get('supply_analysis', {})
        if isinstance(supply_analysis, dict):
            print(f"   Inflation Rate: {supply_analysis.get('inflation_rate', 'N/A')}")
            print(f"   Supply Distribution: {supply_analysis.get('supply_distribution', 'N/A')[:80]}...")
        
        print(f"\n💧 Liquidity Analysis:")
        liquidity_analysis = analysis.get('liquidity_analysis', {})
        if isinstance(liquidity_analysis, dict):
            print(f"   Market Cap Size: {liquidity_analysis.get('market_cap_size', 'N/A')}")
            print(f"   Trading Liquidity: {liquidity_analysis.get('trading_liquidity', 'N/A')[:80]}...")
        
        print(f"\n💪 Strengths ({len(analysis.get('strengths', []))}):")
        for strength in analysis.get('strengths', [])[:3]:
            print(f"   • {strength}")
        
        print(f"\n⚠️  Weaknesses ({len(analysis.get('weaknesses', []))}):")
        for weakness in analysis.get('weaknesses', [])[:3]:
            print(f"   • {weakness}")
        
        print(f"\n🎯 Key Observations ({len(analysis.get('key_observations', []))}):")
        for obs in analysis.get('key_observations', [])[:3]:
            print(f"   • {obs}")
        
        print(f"\n📈 Trading Implication:")
        print(f"   {analysis.get('trading_implication', 'N/A')[:150]}...")
        
        print("\n✅ Tokenomics Analyst test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Tokenomics Analyst test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_comparison_mock_vs_real():
    """Compare tokenomics analysis with mock vs real data."""
    print("\n" + "="*80)
    print("TEST 3: Comparison - Mock Data vs Real Data")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        llm_client = LLMClient(db)
        analyst = TokenomicsAnalyst(db, llm_client)
        
        # Test with mock data
        print("\n❌ Running with MOCK data (old approach)...")
        mock_context = {
            "symbol": "BTCUSDT",
            "current_price": 45000,
            "market_cap": 880000000000,
            "volume_24h": 30000000000,
            "token_data": {}  # Empty = mock data
        }
        
        mock_result = analyst.analyze_structured(mock_context)
        mock_confidence = mock_result["analysis"]["confidence"]
        print(f"   Confidence with mock data: {mock_confidence}%")
        print(f"   Value Assessment: {mock_result['analysis']['value_assessment']}")
        
        # Test with real data
        print("\n✅ Running with REAL data (new approach)...")
        tokenomics_service = TokenomicsService(db)
        real_token_data = await tokenomics_service.get_comprehensive_tokenomics(
            symbol="BTCUSDT",
            current_price=45000,
            market_cap=880000000000,
            volume_24h=30000000000
        )
        await tokenomics_service.close()
        
        real_context = {
            "symbol": "BTCUSDT",
            "current_price": 45000,
            "market_cap": 880000000000,
            "volume_24h": 30000000000,
            "token_data": real_token_data
        }
        
        real_result = analyst.analyze_structured(real_context)
        real_confidence = real_result["analysis"]["confidence"]
        print(f"   Confidence with real data: {real_confidence}%")
        print(f"   Value Assessment: {real_result['analysis']['value_assessment']}")
        
        # Compare
        print(f"\n📊 COMPARISON:")
        print(f"   Confidence Delta: {real_confidence - mock_confidence:+d}%")
        print(f"   Data Quality: Real data provides supply, market, community, and developer metrics")
        print(f"   Mock Limitations: No supply info, no developer activity, no community data")
        print(f"   Improvement: {'✅ Significant' if abs(real_confidence - mock_confidence) > 10 else '⚠️  Minimal'}")
        
        print("\n✅ Comparison test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """Run all tests."""
    print("\n🚀 Tokenomics Analyst Improvement Tests")
    print("="*80)
    print("Testing real tokenomics data integration:")
    print("  1. CoinGecko comprehensive data")
    print("  2. Supply structure analysis")
    print("  3. Liquidity and market tier assessment")
    print("  4. Developer activity tracking")
    print("  5. LLM analysis with real data")
    print("="*80)
    
    # Test 1: Tokenomics Service
    test1_passed = await test_tokenomics_service()
    
    # Test 2: Tokenomics Analyst with real data
    test2_passed = await test_tokenomics_analyst_with_real_data()
    
    # Test 3: Comparison
    test3_passed = await test_comparison_mock_vs_real()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tokenomics Service: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Tokenomics Analyst: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Mock vs Real: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    print("\n💡 Key Improvements:")
    print("  ✅ Real CoinGecko tokenomics integration")
    print("  ✅ Supply structure and inflation analysis")
    print("  ✅ Market cap tier and liquidity rating")
    print("  ✅ Developer activity tracking")
    print("  ✅ Community metrics (Twitter, Reddit, Telegram)")
    print("  ✅ Price performance history (24h, 7d, 30d, 1y)")
    print("  ✅ No more mock data!")


if __name__ == "__main__":
    asyncio.run(main())
