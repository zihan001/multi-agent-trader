"use client";

import React from 'react';
import { BacktestResult } from '@/types/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface BacktestResultsProps {
  result: BacktestResult;
}

export default function BacktestResults({ result }: BacktestResultsProps) {
  const { metrics, equity_curve, trades, engine_type, strategy_name, execution_time_ms } = result;

  // Format equity curve data for chart
  const chartData = equity_curve.map(point => ({
    timestamp: new Date(point.timestamp).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: point.timestamp.includes('T') ? 'numeric' : undefined
    }),
    equity: point.equity,
    cash: point.cash,
    positions: point.positions_value,
  }));

  // Calculate additional metrics
  const totalTrades = trades.length;
  const winningTrades = trades.filter(t => t.pnl > 0).length;
  const losingTrades = trades.filter(t => t.pnl < 0).length;
  const avgWinningTrade = winningTrades > 0 
    ? trades.filter(t => t.pnl > 0).reduce((sum, t) => sum + t.pnl, 0) / winningTrades 
    : 0;
  const avgLosingTrade = losingTrades > 0
    ? trades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0) / losingTrades
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">
              {result.symbol} Backtest Results
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              {new Date(result.start_date).toLocaleDateString()} - {new Date(result.end_date).toLocaleDateString()}
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                engine_type === 'llm' 
                  ? 'bg-purple-900 text-purple-200' 
                  : 'bg-blue-900 text-blue-200'
              }`}>
                {engine_type === 'llm' ? 'LLM Engine' : 'VectorBT Engine'}
              </span>
              {strategy_name && (
                <span className="px-3 py-1 rounded-full text-sm bg-gray-700 text-gray-300">
                  {strategy_name.replace('_', ' ').toUpperCase()}
                </span>
              )}
            </div>
            <p className="text-gray-400 text-sm mt-2">
              Completed in {(execution_time_ms / 1000).toFixed(2)}s
            </p>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Return"
          value={`${metrics.total_return_pct.toFixed(2)}%`}
          subValue={`$${metrics.total_return.toFixed(2)}`}
          trend={metrics.total_return_pct >= 0 ? 'up' : 'down'}
        />
        <MetricCard
          label="Max Drawdown"
          value={`${metrics.max_drawdown_pct.toFixed(2)}%`}
          subValue={`$${metrics.max_drawdown.toFixed(2)}`}
          trend="neutral"
        />
        <MetricCard
          label="Win Rate"
          value={`${metrics.win_rate.toFixed(1)}%`}
          subValue={`${winningTrades}/${totalTrades} trades`}
          trend="neutral"
        />
        <MetricCard
          label="Total Trades"
          value={metrics.num_trades.toString()}
          subValue={`${winningTrades}W / ${losingTrades}L`}
          trend="neutral"
        />
      </div>

      {/* Advanced Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Sharpe Ratio"
          value={metrics.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : 'N/A'}
          trend="neutral"
        />
        <MetricCard
          label="Sortino Ratio"
          value={metrics.sortino_ratio != null ? metrics.sortino_ratio.toFixed(2) : 'N/A'}
          trend="neutral"
        />
        <MetricCard
          label="Profit Factor"
          value={metrics.profit_factor != null ? metrics.profit_factor.toFixed(2) : 'N/A'}
          trend="neutral"
        />
        <MetricCard
          label="Avg Trade Return"
          value={`${metrics.avg_trade_return.toFixed(2)}%`}
          trend={metrics.avg_trade_return >= 0 ? 'up' : 'down'}
        />
      </div>

      {/* Equity Curve Chart */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Equity Curve</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="timestamp" 
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF' }}
            />
            <YAxis 
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF' }}
              tickFormatter={(value) => `$${value.toLocaleString()}`}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F3F4F6'
              }}
              formatter={(value: number) => `$${value.toFixed(2)}`}
            />
            <Legend 
              wrapperStyle={{ color: '#9CA3AF' }}
            />
            <Line 
              type="monotone" 
              dataKey="equity" 
              stroke="#10B981" 
              strokeWidth={2}
              dot={false}
              name="Total Equity"
            />
            <Line 
              type="monotone" 
              dataKey="cash" 
              stroke="#3B82F6" 
              strokeWidth={1}
              dot={false}
              name="Cash"
            />
            <Line 
              type="monotone" 
              dataKey="positions" 
              stroke="#F59E0B" 
              strokeWidth={1}
              dot={false}
              name="Positions Value"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Trade History */}
      {trades.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Trade History ({trades.length} trades)
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Side
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    P&L
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {trades.map((trade, idx) => (
                  <tr key={idx} className="hover:bg-gray-700 transition-colors">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                      {new Date(trade.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${
                        trade.side === 'BUY' 
                          ? 'bg-green-900 text-green-200' 
                          : 'bg-red-900 text-red-200'
                      }`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-300">
                      {trade.quantity.toFixed(6)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-300">
                      ${trade.price.toFixed(2)}
                    </td>
                    <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-semibold ${
                      trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No Trades Message */}
      {trades.length === 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
          <p className="text-gray-400 text-lg">
            No trades executed during this backtest period.
          </p>
          <p className="text-gray-500 text-sm mt-2">
            The strategy may not have found suitable entry conditions.
          </p>
        </div>
      )}
    </div>
  );
}

// Metric Card Component
interface MetricCardProps {
  label: string;
  value: string;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
}

function MetricCard({ label, value, subValue, trend = 'neutral' }: MetricCardProps) {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-white',
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className={`text-2xl font-bold ${trendColors[trend]}`}>
        {value}
      </p>
      {subValue && (
        <p className="text-gray-500 text-xs mt-1">{subValue}</p>
      )}
    </div>
  );
}
