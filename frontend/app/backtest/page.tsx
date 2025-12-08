'use client';

import { useState, useEffect } from 'react';
import { runBacktest, getTradingMode, getEngineCapabilities, getHealth } from '@/lib/api';
import type { BacktestResult, TradingModeResponse, EngineCapabilitiesResponse } from '@/types/api';
import BacktestResults from '@/components/BacktestResults';
import { PlayCircle, Info } from 'lucide-react';

export default function Backtest() {
  // Form state
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-01-07');
  const [timeframe, setTimeframe] = useState('1h');
  const [initialCapital, setInitialCapital] = useState('10000');
  const [engineType, setEngineType] = useState<string>('vectorbt');
  const [strategy, setStrategy] = useState('rsi_macd');
  const [maxDecisions, setMaxDecisions] = useState('50');
  
  // Results state
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Config state
  const [tradingMode, setTradingMode] = useState<TradingModeResponse | null>(null);
  const [capabilities, setCapabilities] = useState<EngineCapabilitiesResponse | null>(null);
  const [llmEnabled, setLlmEnabled] = useState<boolean>(false);

  const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT'];
  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
  const strategies = [
    { value: 'rsi_macd', label: 'RSI + MACD Momentum', description: 'Buy on oversold RSI with MACD bullish, sell on overbought' },
    { value: 'ema_crossover', label: 'EMA Crossover Trend', description: 'Golden/death cross with trend confirmation' },
    { value: 'bb_volume', label: 'Bollinger Bands + Volume', description: 'Band touch with volume surge breakouts' },
  ];

  // Load config on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const [healthData, modeData, capData] = await Promise.all([
          getHealth(),
          getTradingMode(),
          getEngineCapabilities(),
        ]);
        const isLlmAvailable = healthData.llm_enabled || false;
        setLlmEnabled(isLlmAvailable);
        setTradingMode(modeData);
        setCapabilities(capData);
        // Default to vectorbt, or LLM if it's available and set as default
        setEngineType(isLlmAvailable && modeData.mode === 'llm' ? 'llm' : 'vectorbt');
      } catch (err) {
        console.error('Failed to load config:', err);
      }
    };
    loadConfig();
  }, []);

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await runBacktest({
        symbol,
        start_date: startDate,
        end_date: endDate,
        timeframe,
        initial_capital: parseFloat(initialCapital),
        engine_type: engineType,
        strategy: engineType === 'vectorbt' ? strategy : undefined,
        max_decisions: engineType === 'llm' ? parseInt(maxDecisions) : undefined,
      });
      setResult(response.result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run backtest. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate estimated cost/time
  const estimatedCost = engineType === 'llm' ? parseInt(maxDecisions) * 0.02 : 0;
  const estimatedTime = engineType === 'llm' 
    ? `${(parseInt(maxDecisions) * 15 / 60).toFixed(1)} min` 
    : '<1 sec';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Backtesting</h1>
        <p className="text-gray-400">Test trading strategies on historical market data</p>
      </div>

      {/* Backtest Form */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
        <form onSubmit={handleRunBacktest} className="space-y-6">
          {/* Engine Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Backtest Engine {!llmEnabled && <span className="text-gray-500 text-xs">(LLM mode not available - API key not configured)</span>}
            </label>
            <div className={`grid grid-cols-1 ${llmEnabled ? 'md:grid-cols-2' : ''} gap-4`}>
              <button
                type="button"
                onClick={() => setEngineType('vectorbt')}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  engineType === 'vectorbt'
                    ? 'border-blue-500 bg-blue-900/20'
                    : 'border-gray-600 bg-gray-700/50 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-white">VectorBT Engine</h3>
                  <span className="px-2 py-1 bg-green-900 text-green-200 text-xs rounded">
                    Fast & Free
                  </span>
                </div>
                <p className="text-sm text-gray-400 mb-2">
                  Vectorized backtesting with professional metrics
                </p>
                <div className="text-xs text-gray-500">
                  <span>• Instant results (~100ms)</span><br />
                  <span>• $0.00 cost</span><br />
                  <span>• Full date range support</span>
                </div>
              </button>

              {llmEnabled && (
                <button
                  type="button"
                  onClick={() => setEngineType('llm')}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    engineType === 'llm'
                      ? 'border-purple-500 bg-purple-900/20'
                      : 'border-gray-600 bg-gray-700/50 hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-white">LLM Engine</h3>
                    <span className="px-2 py-1 bg-yellow-900 text-yellow-200 text-xs rounded">
                      Slow & Costly
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">
                    6-agent pipeline with detailed reasoning
                  </p>
                  <div className="text-xs text-gray-500">
                    <span>• ~15s per decision</span><br />
                    <span>• ~$0.02 per decision</span><br />
                    <span>• Limited decision count</span>
                  </div>
                </button>
              )}
            </div>
          </div>

          {/* Strategy Selection (VectorBT only) */}
          {engineType === 'vectorbt' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Trading Strategy
              </label>
              <div className="space-y-2">
                {strategies.map((strat) => (
                  <label
                    key={strat.value}
                    className={`flex items-start p-3 rounded-lg border cursor-pointer transition-colors ${
                      strategy === strat.value
                        ? 'border-blue-500 bg-blue-900/20'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <input
                      type="radio"
                      name="strategy"
                      value={strat.value}
                      checked={strategy === strat.value}
                      onChange={(e) => setStrategy(e.target.value)}
                      className="mt-1 mr-3"
                    />
                    <div>
                      <div className="font-medium text-white">{strat.label}</div>
                      <div className="text-sm text-gray-400">{strat.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Symbol */}
            <div>
              <label htmlFor="symbol" className="block text-sm font-medium text-gray-300 mb-2">
                Symbol
              </label>
              <select
                id="symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                required
              >
                {symbols.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Timeframe */}
            <div>
              <label htmlFor="timeframe" className="block text-sm font-medium text-gray-300 mb-2">
                Timeframe
              </label>
              <select
                id="timeframe"
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                required
              >
                {timeframes.map((tf) => (
                  <option key={tf} value={tf}>{tf}</option>
                ))}
              </select>
            </div>

            {/* Initial Capital */}
            <div>
              <label htmlFor="capital" className="block text-sm font-medium text-gray-300 mb-2">
                Initial Capital ($)
              </label>
              <input
                type="number"
                id="capital"
                value={initialCapital}
                onChange={(e) => setInitialCapital(e.target.value)}
                min="1000"
                step="1000"
                className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Start Date */}
            <div>
              <label htmlFor="start-date" className="block text-sm font-medium text-gray-300 mb-2">
                Start Date
              </label>
              <input
                type="date"
                id="start-date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                required
              />
            </div>

            {/* End Date */}
            <div>
              <label htmlFor="end-date" className="block text-sm font-medium text-gray-300 mb-2">
                End Date
              </label>
              <input
                type="date"
                id="end-date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                required
              />
            </div>
          </div>

          {/* Max Decisions (LLM only) */}
          {engineType === 'llm' && (
            <div>
              <label htmlFor="max-decisions" className="block text-sm font-medium text-gray-300 mb-2">
                Max Decisions (Cost Control)
              </label>
              <input
                type="number"
                id="max-decisions"
                value={maxDecisions}
                onChange={(e) => setMaxDecisions(e.target.value)}
                min="10"
                max="200"
                step="10"
                className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Recommended: 50 decisions max (~$1.00 cost)
              </p>
            </div>
          )}

          {/* Estimated Cost/Time */}
          <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4 flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-gray-300">
                <span className="font-semibold">Estimated:</span> {estimatedTime} execution time, 
                ${estimatedCost.toFixed(2)} cost
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {engineType === 'vectorbt' 
                  ? 'VectorBT processes entire date range instantly with zero cost.'
                  : 'LLM engine runs sequentially and costs add up. Use VectorBT for full backtests.'}
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center pt-4">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-8 rounded-lg transition-colors flex items-center gap-2"
            >
              <PlayCircle className="w-5 h-5" />
              {loading ? 'Running Backtest...' : 'Run Backtest'}
            </button>
          </div>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-6 py-4 rounded-lg mb-8">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-400 text-lg">Running {engineType} backtest...</p>
          <p className="text-gray-500 text-sm mt-2">
            {engineType === 'llm' ? 'This may take several minutes' : 'Should complete in seconds'}
          </p>
        </div>
      )}

      {/* Results */}
      {!loading && result && (
        <BacktestResults result={result} />
      )}
    </div>
  );
}
