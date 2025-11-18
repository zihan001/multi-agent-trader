'use client';

import { useState } from 'react';
import { runBacktest } from '@/lib/api';
import type { BacktestResponse } from '@/types/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';
import { PlayCircle, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

export default function Backtest() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-11-17');
  const [timeframe, setTimeframe] = useState('1h');
  const [maxDecisions, setMaxDecisions] = useState('50');
  
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT'];
  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await runBacktest({
        symbol,
        start_date: startDate,
        end_date: endDate,
        timeframe,
        max_decisions: parseInt(maxDecisions),
      });
      setResult(data);
    } catch (err) {
      setError('Failed to run backtest. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Backtest</h1>
        <p className="text-gray-400">Test your trading strategy on historical data</p>
      </div>

      {/* Backtest Form */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
        <form onSubmit={handleRunBacktest} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                  <option key={s} value={s}>
                    {s}
                  </option>
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
                  <option key={tf} value={tf}>
                    {tf}
                  </option>
                ))}
              </select>
            </div>

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

            {/* Max Decisions */}
            <div>
              <label htmlFor="max-decisions" className="block text-sm font-medium text-gray-300 mb-2">
                Max Decisions (to control LLM cost)
              </label>
              <input
                type="number"
                id="max-decisions"
                value={maxDecisions}
                onChange={(e) => setMaxDecisions(e.target.value)}
                min="1"
                max="200"
                className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                required
              />
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
          <p className="text-gray-400 text-lg">Running backtest...</p>
          <p className="text-gray-500 text-sm mt-2">This may take 1-3 minutes</p>
        </div>
      )}

      {/* Results */}
      {!loading && result && (
        <div className="space-y-8">
          {/* Metrics Grid */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-4">Performance Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Total Return */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-gray-400 text-sm font-medium">Total Return</p>
                  {result.metrics.total_return >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-green-500" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-red-500" />
                  )}
                </div>
                <p className={`text-2xl font-bold ${result.metrics.total_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatCurrency(result.metrics.total_return)}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {formatPercent(result.metrics.total_return_pct)}
                </p>
              </div>

              {/* Max Drawdown */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-gray-400 text-sm font-medium">Max Drawdown</p>
                  <TrendingDown className="w-5 h-5 text-red-500" />
                </div>
                <p className="text-2xl font-bold text-red-400">
                  {formatCurrency(result.metrics.max_drawdown)}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {formatPercent(result.metrics.max_drawdown_pct)}
                </p>
              </div>

              {/* Number of Trades */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-gray-400 text-sm font-medium">Total Trades</p>
                  <DollarSign className="w-5 h-5 text-blue-500" />
                </div>
                <p className="text-2xl font-bold text-white">
                  {result.metrics.num_trades}
                </p>
              </div>

              {/* Win Rate */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-gray-400 text-sm font-medium">Win Rate</p>
                  <TrendingUp className="w-5 h-5 text-purple-500" />
                </div>
                <p className="text-2xl font-bold text-white">
                  {(result.metrics.win_rate * 100).toFixed(1)}%
                </p>
              </div>

              {/* Sharpe Ratio */}
              {result.metrics.sharpe_ratio !== undefined && (
                <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-gray-400 text-sm font-medium">Sharpe Ratio</p>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {result.metrics.sharpe_ratio.toFixed(2)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Equity Curve Chart */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-4">Equity Curve</h2>
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart
                  data={result.equity_curve.map(point => ({
                    timestamp: new Date(point.timestamp).getTime(),
                    equity: point.equity,
                  }))}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="timestamp"
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                    stroke="#9CA3AF"
                  />
                  <YAxis
                    domain={['auto', 'auto']}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
                    stroke="#9CA3AF"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '0.5rem',
                      color: '#F3F4F6',
                    }}
                    labelFormatter={(value) => format(new Date(value), 'MMM dd, yyyy HH:mm')}
                    formatter={(value: number) => [formatCurrency(value), 'Equity']}
                  />
                  <Line
                    type="monotone"
                    dataKey="equity"
                    stroke={result.metrics.total_return >= 0 ? '#10B981' : '#EF4444'}
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trades Table */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-4">Trade History</h2>
            <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Date & Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Symbol
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Side
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Value
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                        PnL
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {result.trades.map((trade) => (
                      <tr key={trade.id} className="hover:bg-gray-700/50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {format(new Date(trade.timestamp), 'MMM dd, yyyy HH:mm')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                          {trade.symbol}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            trade.side === 'BUY'
                              ? 'bg-green-900/30 text-green-400'
                              : 'bg-red-900/30 text-red-400'
                          }`}>
                            {trade.side}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                          {trade.quantity.toFixed(6)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                          {formatCurrency(trade.price)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                          {formatCurrency(trade.quantity * trade.price)}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
                          trade.pnl && trade.pnl >= 0 ? 'text-green-400' : trade.pnl ? 'text-red-400' : 'text-gray-400'
                        }`}>
                          {trade.pnl ? formatCurrency(trade.pnl) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
