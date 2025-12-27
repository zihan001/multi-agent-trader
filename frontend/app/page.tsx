'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getHealth, getMarketSymbols, getMarketData, runAnalysis, getRecommendations } from '@/lib/api';
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
  const [llmEnabled, setLlmEnabled] = useState<boolean>(false);
  const [engineMode, setEngineMode] = useState<'llm' | 'rule'>('rule');
  const [agentMode, setAgentMode] = useState<'classic' | 'langchain'>('langchain');
  const [newRecommendationId, setNewRecommendationId] = useState<number | null>(null);
  const [showSuccessToast, setShowSuccessToast] = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // Fetch health to check LLM availability
        const health = await getHealth();
        const isLlmEnabled = health.llm_enabled || false;
        setLlmEnabled(isLlmEnabled);
        
        // Set default mode based on availability (LLM if available, otherwise rule)
        const defaultMode = health.default_engine_mode || 'rule';
        setEngineMode(defaultMode as 'llm' | 'rule');
        
        // Fetch symbols
        const data = await getMarketSymbols();
        setSymbols(data.symbols);
        if (data.symbols.length > 0) {
          setSelectedSymbol(data.symbols[0]);
          fetchMarketData(data.symbols[0]);
          fetchRecommendations(data.symbols[0]);
        }
      } catch (err) {
        setError('Failed to fetch initial data');
        console.error(err);
      }
    };

    fetchInitialData();
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
    setNewRecommendationId(null);
    try {
      const result = await runAnalysis({ 
        symbol: selectedSymbol, 
        mode: 'live',
        run_id: 'live',
        timeframe: '1h',
        engine_mode: engineMode,
        use_langchain: agentMode === 'langchain'
      });
      
      // Get the new recommendation ID from result
      const newRecId = result.recommendation?.id;
      
      // Refresh recommendations after analysis
      await fetchRecommendations(selectedSymbol);
      
      // Show success feedback
      if (newRecId) {
        setNewRecommendationId(newRecId);
        setShowSuccessToast(true);
        
        // Auto-hide toast after 3 seconds
        setTimeout(() => setShowSuccessToast(false), 3000);
        
        // Clear highlight after 5 seconds
        setTimeout(() => setNewRecommendationId(null), 5000);
        
        // Scroll to recommendations section
        setTimeout(() => {
          const recSection = document.getElementById('recommendations-section');
          if (recSection) {
            recSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 100);
      }
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

      {/* Selectors Row */}
      <div className="mb-6 flex gap-4 flex-wrap">
        {/* Symbol Selector */}
        <div className="flex-1 min-w-[200px]">
          <label htmlFor="symbol" className="block text-sm font-medium text-gray-300 mb-2">
            Select Symbol
          </label>
          <select
            id="symbol"
            value={selectedSymbol}
            onChange={(e) => handleSymbolChange(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
          >
            {symbols.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </div>

        {/* Engine Mode Selector - only show if LLM is enabled */}
        {llmEnabled && (
          <>
            <div className="flex-1 min-w-[200px]">
              <label htmlFor="engine-mode" className="block text-sm font-medium text-gray-300 mb-2">
                Analysis Engine
              </label>
              <select
                id="engine-mode"
                value={engineMode}
                onChange={(e) => setEngineMode(e.target.value as 'llm' | 'rule')}
                className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
              >
                <option value="rule">📊 Rule-Based (Free)</option>
                <option value="llm">🤖 AI Agents (LLM)</option>
              </select>
            </div>
            
            {/* Agent Mode Selector - only show when LLM mode is selected */}
            {engineMode === 'llm' && (
              <div className="flex-1 min-w-[200px]">
                <label htmlFor="agent-mode" className="block text-sm font-medium text-gray-300 mb-2">
                  Agent Framework
                </label>
                <select
                  id="agent-mode"
                  value={agentMode}
                  onChange={(e) => setAgentMode(e.target.value as 'classic' | 'langchain')}
                  className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                >
                  <option value="langchain">🔗 LangChain Agents (Recommended)</option>
                  <option value="classic">📚 Classic Agents</option>
                </select>
              </div>
            )}
          </>
        )}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {showSuccessToast && (
        <div className="bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded-lg mb-6 flex items-center gap-3 animate-pulse">
          <Sparkles className="w-5 h-5" />
          <span className="font-semibold">New trading idea generated! Check recommendations below.</span>
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
          <div id="recommendations-section" className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Sparkles className="w-6 h-6 text-yellow-500" />
                <h2 className="text-xl font-semibold text-white">AI Trading Ideas</h2>
                {recommendations.length > 0 && (
                  <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-sm font-semibold rounded-full">
                    {recommendations.length}
                  </span>
                )}
              </div>
              <button
                onClick={handleRunAnalysis}
                disabled={analyzing}
                className={`font-semibold py-2 px-6 rounded-lg transition-all flex items-center gap-2 ${
                  analyzing 
                    ? 'bg-gray-600 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-500/50 text-white'
                }`}
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
                    className={`bg-gray-900 rounded-lg p-4 border transition-all duration-500 ${
                      rec.id === newRecommendationId
                        ? 'border-yellow-500 shadow-lg shadow-yellow-500/50 animate-pulse'
                        : rec.action === 'BUY'
                        ? 'border-green-500/30'
                        : rec.action === 'SELL'
                        ? 'border-red-500/30'
                        : 'border-gray-600'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {rec.id === newRecommendationId && (
                            <span className="px-2 py-1 rounded-full text-xs font-bold bg-yellow-500 text-black animate-pulse">
                              NEW
                            </span>
                          )}
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
                          <div className="mb-3">
                            {typeof rec.reasoning === 'string' && rec.reasoning.includes(' | ') ? (
                              <div className="space-y-2">
                                {rec.reasoning.split(' | ').map((part: string, idx: number) => {
                                  const [label, ...rest] = part.split(': ');
                                  const text = rest.join(': ');
                                  
                                  const agentIcons: Record<string, string> = {
                                    'Technical': '📊',
                                    'Sentiment': '💬',
                                    'Tokenomics': '🪙',
                                    'Researcher': '🔍',
                                    'Trader': '💼',
                                    'Risk': '🛡️'
                                  };
                                  
                                  return (
                                    <div key={idx} className="bg-gradient-to-r from-gray-700 to-gray-800 p-3 rounded-lg border border-gray-600 hover:border-gray-500 transition-colors">
                                      <div className="flex items-start gap-2">
                                        <span className="text-base">{agentIcons[label] || '🤖'}</span>
                                        <div className="flex-1">
                                          <span className="text-xs font-bold text-blue-400">{label}</span>
                                          <p className="text-xs text-gray-200 mt-1 leading-relaxed">{text}</p>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            ) : (
                              <p className="text-sm text-gray-300">{rec.reasoning}</p>
                            )}
                          </div>
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

