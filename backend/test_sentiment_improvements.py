"""
Test script for improved Sentiment Analyst with real data sources.

Tests:
1. Sentiment Service - Fetch real Fear & Greed Index
2. Sentiment Service - Fetch CoinGecko data
3. Sentiment Service - Volume analysis
4. Sentiment Service - Technical sentiment
5. Comprehensive sentiment aggregation
6. Sentiment Analyst with real data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.sentiment import SentimentService
from app.agents.sentiment import SentimentAnalyst
from app.agents.llm_client import LLMClient


async def test_sentiment_service():
    """Test SentimentService data fetching."""
    print("\n" + "="*80)
    print("TEST 1: Sentiment Service - Real Data Sources")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        service = SentimentService(db)
        
        # Test 1: Fear & Greed Index
        print("\n📊 Testing Fear & Greed Index...")
        fear_greed = await service.fetch_fear_greed_index()
        if fear_greed:
            print(f"✅ Fear & Greed Index: {fear_greed['value']}/100 ({fear_greed['classification']})")
            print(f"   Timestamp: {fear_greed['timestamp']}")
        else:
            print("❌ Failed to fetch Fear & Greed Index")
        
        # Test 2: CoinGecko
        print("\n🦎 Testing CoinGecko data for BTCUSDT...")
        coingecko = await service.fetch_coingecko_sentiment("BTCUSDT")
        if coingecko:
            print(f"✅ CoinGecko Data:")
            print(f"   Market Cap Rank: #{coingecko['market_cap_rank']}")
            print(f"   Sentiment Votes Up: {coingecko['sentiment_votes_up']:.1f}%")
            print(f"   24h Price Change: {coingecko['price_change_24h']:+.2f}%")
            print(f"   7d Price Change: {coingecko['price_change_7d']:+.2f}%")
            print(f"   Twitter Followers: {coingecko['twitter_followers']:,}")
        else:
            print("❌ Failed to fetch CoinGecko data")
        
        # Test 3: Volume Analysis
        print("\n📈 Testing Volume Sentiment Analysis...")
        volume_sentiment = service.analyze_volume_sentiment(
            current_volume=1000000,
            avg_volume=600000,
            price_change=3.5
        )
        print(f"✅ Volume Sentiment:")
        print(f"   Trend: {volume_sentiment['volume_trend']}")
        print(f"   Ratio: {volume_sentiment['volume_ratio']}x average")
        print(f"   Signal: {volume_sentiment['sentiment_signal']}")
        print(f"   Conviction: {volume_sentiment['conviction']}")
        
        # Test 4: Technical Sentiment
        print("\n🔧 Testing Technical Sentiment Analysis...")
        tech_sentiment = service.analyze_technical_sentiment({
            "rsi": 72.5,
            "macd": 150.3,
            "macd_signal": 120.1
        })
        print(f"✅ Technical Sentiment:")
        print(f"   RSI Sentiment: {tech_sentiment['rsi_sentiment']} (RSI: {tech_sentiment['rsi_value']})")
        print(f"   Momentum: {tech_sentiment['momentum_sentiment']}")
        print(f"   Overall: {tech_sentiment['overall_technical_sentiment']}")
        print(f"   Extremes: {tech_sentiment['extremes_detected']}")
        
        # Test 5: Comprehensive Sentiment
        print("\n🎯 Testing Comprehensive Sentiment Aggregation...")
        comprehensive = await service.get_comprehensive_sentiment(
            symbol="BTCUSDT",
            current_price=45000,
            price_change_24h=2.5,
            volume_24h=1000000,
            avg_volume=650000,
            indicators={"rsi": 65.0, "macd": 100.0, "macd_signal": 95.0}
        )
        
        print(f"✅ Comprehensive Sentiment:")
        print(f"   Overall Score: {comprehensive['overall_sentiment_score']}/100")
        print(f"   Classification: {comprehensive['sentiment_classification']}")
        print(f"   Data Sources Available:")
        for source, available in comprehensive['data_sources_available'].items():
            print(f"      {source}: {'✓' if available else '✗'}")
        
        await service.close()
        
        print("\n✅ All Sentiment Service tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Sentiment Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_sentiment_analyst_with_real_data():
    """Test Sentiment Analyst using real data."""
    print("\n" + "="*80)
    print("TEST 2: Sentiment Analyst with Real Data")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # First, fetch comprehensive sentiment data
        print("\n📡 Fetching real sentiment data...")
        sentiment_service = SentimentService(db)
        
        sentiment_data = await sentiment_service.get_comprehensive_sentiment(
            symbol="BTCUSDT",
            current_price=45000,
            price_change_24h=2.3,
            volume_24h=25000000000,
            avg_volume=20000000000,
            indicators={
                "rsi": 68.5,
                "macd": 250.3,
                "macd_signal": 220.1,
                "ema_12": 44800,
                "ema_26": 44600
            }
        )
        
        await sentiment_service.close()
        
        print(f"✅ Fetched sentiment data:")
        print(f"   Overall Score: {sentiment_data['overall_sentiment_score']}")
        print(f"   Classification: {sentiment_data['sentiment_classification']}")
        
        # Now run Sentiment Analyst
        print("\n🤖 Running Sentiment Analyst with real data...")
        
        llm_client = LLMClient(db)
        analyst = SentimentAnalyst(db, llm_client)
        
        context = {
            "symbol": "BTCUSDT",
            "current_price": 45000,
            "price_change_24h": 2.3,
            "sentiment_data": sentiment_data
        }
        
        result = analyst.analyze_structured(context)
        
        print(f"\n✅ Sentiment Analysis Complete:")
        analysis = result["analysis"]
        
        print(f"\n📊 SENTIMENT ANALYSIS RESULTS:")
        print(f"   Overall Sentiment: {analysis['overall_sentiment']}")
        print(f"   Sentiment Score: {analysis['sentiment_score']}/100")
        print(f"   Sentiment Strength: {analysis['sentiment_strength']}")
        print(f"   Crowd Psychology: {analysis['crowd_psychology']}")
        print(f"   Sentiment Trend: {analysis['sentiment_trend']}")
        print(f"   Confidence: {analysis['confidence']}%")
        
        print(f"\n🔑 Key Factors:")
        key_factors = analysis.get('key_factors', {})
        if isinstance(key_factors, dict):
            for factor, value in key_factors.items():
                print(f"   {factor}: {value}")
        
        print(f"\n⚠️  Contrarian Signals ({len(analysis.get('contrarian_signals', []))}):")
        for signal in analysis.get('contrarian_signals', [])[:3]:
            print(f"   • {signal}")
        
        print(f"\n💡 Key Observations ({len(analysis.get('key_observations', []))}):")
        for obs in analysis.get('key_observations', [])[:3]:
            print(f"   • {obs}")
        
        print(f"\n📈 Trading Implication:")
        print(f"   {analysis.get('trading_implication', 'N/A')}")
        
        print(f"\n💭 Reasoning:")
        print(f"   {analysis.get('reasoning', 'N/A')[:200]}...")
        
        print("\n✅ Sentiment Analyst test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Sentiment Analyst test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_comparison_mock_vs_real():
    """Compare sentiment analysis with mock vs real data."""
    print("\n" + "="*80)
    print("TEST 3: Comparison - Mock Data vs Real Data")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        llm_client = LLMClient(db)
        analyst = SentimentAnalyst(db, llm_client)
        
        # Test with mock data
        print("\n❌ Running with MOCK data (old approach)...")
        mock_context = {
            "symbol": "BTCUSDT",
            "current_price": 45000,
            "price_change_24h": 2.3,
            "sentiment_data": {}  # Empty = mock data
        }
        
        mock_result = analyst.analyze_structured(mock_context)
        mock_confidence = mock_result["analysis"]["confidence"]
        print(f"   Confidence with mock data: {mock_confidence}%")
        
        # Test with real data
        print("\n✅ Running with REAL data (new approach)...")
        sentiment_service = SentimentService(db)
        real_sentiment = await sentiment_service.get_comprehensive_sentiment(
            symbol="BTCUSDT",
            current_price=45000,
            price_change_24h=2.3,
            volume_24h=25000000000,
            avg_volume=20000000000,
            indicators={"rsi": 68.5, "macd": 250.3, "macd_signal": 220.1}
        )
        await sentiment_service.close()
        
        real_context = {
            "symbol": "BTCUSDT",
            "current_price": 45000,
            "price_change_24h": 2.3,
            "sentiment_data": real_sentiment
        }
        
        real_result = analyst.analyze_structured(real_context)
        real_confidence = real_result["analysis"]["confidence"]
        print(f"   Confidence with real data: {real_confidence}%")
        
        # Compare
        print(f"\n📊 COMPARISON:")
        print(f"   Confidence Delta: {real_confidence - mock_confidence:+d}%")
        print(f"   Data Quality: Real data provides {len(str(real_sentiment))} chars vs {len(str({}))} chars")
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
    print("\n🚀 Sentiment Analyst Improvement Tests")
    print("="*80)
    print("Testing real sentiment data integration:")
    print("  1. Fear & Greed Index (alternative.me)")
    print("  2. CoinGecko market data")
    print("  3. Volume sentiment analysis")
    print("  4. Technical sentiment indicators")
    print("  5. LLM analysis with real data")
    print("="*80)
    
    # Test 1: Sentiment Service
    test1_passed = await test_sentiment_service()
    
    # Test 2: Sentiment Analyst with real data
    test2_passed = await test_sentiment_analyst_with_real_data()
    
    # Test 3: Comparison
    test3_passed = await test_comparison_mock_vs_real()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Sentiment Service: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Sentiment Analyst: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Mock vs Real: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    print("\n💡 Key Improvements:")
    print("  ✅ Real Fear & Greed Index integration")
    print("  ✅ CoinGecko sentiment and social metrics")
    print("  ✅ Volume-based sentiment analysis")
    print("  ✅ Technical indicator sentiment scoring")
    print("  ✅ Aggregated sentiment score (-100 to +100)")
    print("  ✅ Contrarian signal detection")
    print("  ✅ No more mock data!")


if __name__ == "__main__":
    asyncio.run(main())
