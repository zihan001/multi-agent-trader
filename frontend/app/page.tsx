'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getMarketSymbols, getMarketData, runAnalysis, getRecommendations } from '@/lib/api';
import type { MarketDataResponse, AgentRecommendation } from '@/types/api';
import { TrendingUp, TrendingDown, Activity, DollarSign, Sparkles, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [recommendations, setRecommendations] = useState<AgentRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const data = await getMarketSymbols();
        setSymbols(data.symbols);
        if (data.symbols.length > 0) {
          setSelectedSymbol(data.symbols[0]);
          fetchMarketData(data.symbols[0]);
          fetchRecommendations(data.symbols[0]);
        }
      } catch (err) {
        setError('Failed to fetch symbols');
        console.error(err);
      }
    };

    fetchSymbols();
  }, []);

  const fetchMarketData = async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMarketData(symbol);
      setMarketData(data);
    } catch (err) {
      setError('Failed to fetch market data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async (symbol: string) => {
    try {
      const data = await getRecommendations({ symbol, limit: 5 });
      setRecommendations(data);
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
    }
  };

  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
    fetchMarketData(symbol);
    fetchRecommendations(symbol);
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      await runAnalysis({ symbol: selectedSymbol, mode: 'live' });
      // Refresh recommendations after analysis
      await fetchRecommendations(selectedSymbol);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run analysis');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleOpenOrderTicket = (rec: AgentRecommendation) => {
    router.push(`/paper-trading?recommendation=${rec.id}`);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Market Dashboard</h1>
        <p className="text-gray-400">Select a cryptocurrency to analyze</p>
      </div>

      {/* Symbol Selector */}
      <div className="mb-6">
        <label htmlFor="symbol" className="block text-sm font-medium text-gray-300 mb-2">
          Select Symbol
        </label>
        <select
          id="symbol"
          value={selectedSymbol}
          onChange={(e) => handleSymbolChange(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full max-w-xs p-2.5"
        >
          {symbols.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      )}

      {!loading && marketData && (
        <>
          {/* Market Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Current Price */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-400 text-sm font-medium">Current Price</p>
                <DollarSign className="w-5 h-5 text-blue-500" />
              </div>
              <p className="text-2xl font-bold text-white">
                {formatPrice(marketData.latest_price)}
              </p>
            </div>

            {/* RSI */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-400 text-sm font-medium">RSI (14)</p>
                <Activity className="w-5 h-5 text-purple-500" />
              </div>
              <p className="text-2xl font-bold text-white">
                {marketData.indicators.rsi.toFixed(2)}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {marketData.indicators.rsi > 70
                  ? 'Overbought'
                  : marketData.indicators.rsi < 30
                  ? 'Oversold'
                  : 'Neutral'}
              </p>
            </div>

            {/* MACD */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-400 text-sm font-medium">MACD</p>
                {marketData.indicators.macd_hist > 0 ? (
                  <TrendingUp className="w-5 h-5 text-green-500" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-red-500" />
                )}
              </div>
              <p className="text-2xl font-bold text-white">
                {marketData.indicators.macd.toFixed(2)}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Signal: {marketData.indicators.macd_signal.toFixed(2)}
              </p>
            </div>

            {/* Volume */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-400 text-sm font-medium">24h Volume</p>
                <Activity className="w-5 h-5 text-yellow-500" />
              </div>
              <p className="text-2xl font-bold text-white">
                {marketData.candles[marketData.candles.length - 1]?.volume.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                }) || 'N/A'}
              </p>
            </div>
          </div>

          {/* Bollinger Bands */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Bollinger Bands</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-gray-400 text-sm">Upper Band</p>
                <p className="text-white font-semibold">
                  {formatPrice(marketData.indicators.bb_upper)}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Middle Band</p>
                <p className="text-white font-semibold">
                  {formatPrice(marketData.indicators.bb_middle)}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Lower Band</p>
                <p className="text-white font-semibold">
                  {formatPrice(marketData.indicators.bb_lower)}
                </p>
              </div>
            </div>
          </div>

          {/* AI Agent Ideas Panel */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-yellow-500" />
                <h2 className="text-xl font-semibold text-white">AI Trading Ideas</h2>
              </div>
              <button
                onClick={handleRunAnalysis}
                disabled={analyzing}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold py-2 px-6 rounded-lg transition-colors flex items-center gap-2"
              >
                {analyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-4 h-4" />
                    Get New Ideas
                  </>
                )}
              </button>
            </div>

            {recommendations.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 mb-4">No trading ideas yet. Click "Get New Ideas" to run AI analysis.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className={`bg-gray-900 rounded-lg p-4 border ${
                      rec.action === 'BUY'
                        ? 'border-green-500/30'
                        : rec.action === 'SELL'
                        ? 'border-red-500/30'
                        : 'border-gray-600'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-semibold ${
                              rec.action === 'BUY'
                                ? 'bg-green-500/20 text-green-400'
                                : rec.action === 'SELL'
                                ? 'bg-red-500/20 text-red-400'
                                : 'bg-gray-500/20 text-gray-400'
                            }`}
                          >
                            {rec.action}
                          </span>
                          <span className="text-white font-semibold">{rec.symbol}</span>
                          {rec.confidence && (
                            <span className="text-sm text-gray-400">
                              Confidence: {(rec.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-3 gap-3 mb-3">
                          <div>
                            <p className="text-xs text-gray-400">Entry Price</p>
                            <p className="text-white font-semibold">{formatPrice(rec.price)}</p>
                          </div>
                          {rec.stop_loss && (
                            <div>
                              <p className="text-xs text-gray-400">Stop Loss</p>
                              <p className="text-red-400 font-semibold">{formatPrice(rec.stop_loss)}</p>
                            </div>
                          )}
                          {rec.take_profit && (
                            <div>
                              <p className="text-xs text-gray-400">Take Profit</p>
                              <p className="text-green-400 font-semibold">{formatPrice(rec.take_profit)}</p>
                            </div>
                          )}
                          {rec.quantity && (
                            <div>
                              <p className="text-xs text-gray-400">Quantity</p>
                              <p className="text-white font-semibold">{rec.quantity.toFixed(4)}</p>
                            </div>
                          )}
                          {rec.position_size_pct && (
                            <div>
                              <p className="text-xs text-gray-400">Position Size</p>
                              <p className="text-white font-semibold">{(rec.position_size_pct * 100).toFixed(1)}%</p>
                            </div>
                          )}
                          {rec.time_horizon && (
                            <div>
                              <p className="text-xs text-gray-400">Time Horizon</p>
                              <p className="text-white font-semibold">{rec.time_horizon}</p>
                            </div>
                          )}
                        </div>

                        {rec.reasoning && (
                          <p className="text-sm text-gray-300 mb-3">{rec.reasoning}</p>
                        )}

                        <div className="flex items-center gap-2 text-xs text-gray-400">
                          <span>Strategy: {rec.strategy_name || rec.decision_type}</span>
                          {rec.action !== 'HOLD' && (
                            <>
                              <span>•</span>
                              <span>Status: {rec.status}</span>
                            </>
                          )}
                        </div>
                      </div>

                      {rec.action !== 'HOLD' && (
                        <button
                          onClick={() => handleOpenOrderTicket(rec)}
                          disabled={rec.status !== 'pending'}
                          className="ml-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
                        >
                          Open Order
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

