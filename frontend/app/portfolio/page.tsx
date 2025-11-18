'use client';

import { useEffect, useState } from 'react';
import { getPortfolio, getTrades } from '@/lib/api';
import type { PortfolioResponse, TradesResponse } from '@/types/api';
import { TrendingUp, TrendingDown, DollarSign, Target, BarChart3 } from 'lucide-react';
import { format } from 'date-fns';

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [trades, setTrades] = useState<TradesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [portfolioData, tradesData] = await Promise.all([
          getPortfolio(),
          getTrades(),
        ]);
        setPortfolio(portfolioData);
        setTrades(tradesData);
      } catch (err) {
        setError('Failed to fetch portfolio data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center py-24">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-6 py-4 rounded-lg">
          {error}
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Portfolio</h1>
        <p className="text-gray-400">Your simulated trading portfolio</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Equity */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm font-medium">Total Equity</p>
            <BarChart3 className="w-5 h-5 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(portfolio.summary.total_equity)}
          </p>
        </div>

        {/* Cash Balance */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm font-medium">Cash Balance</p>
            <DollarSign className="w-5 h-5 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(portfolio.summary.cash_balance)}
          </p>
        </div>

        {/* Unrealized PnL */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm font-medium">Unrealized PnL</p>
            {portfolio.summary.unrealized_pnl >= 0 ? (
              <TrendingUp className="w-5 h-5 text-green-500" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-500" />
            )}
          </div>
          <p className={`text-2xl font-bold ${portfolio.summary.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatCurrency(portfolio.summary.unrealized_pnl)}
          </p>
        </div>

        {/* Total Return */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-sm font-medium">Total Return</p>
            <Target className="w-5 h-5 text-purple-500" />
          </div>
          <p className={`text-2xl font-bold ${portfolio.summary.total_return_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(portfolio.summary.total_return_pct)}
          </p>
        </div>
      </div>

      {/* Open Positions */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-4">Open Positions</h2>
        {portfolio.positions.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 border border-gray-700 text-center">
            <p className="text-gray-400">No open positions</p>
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Entry Price
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Current Price
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Unrealized PnL
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      PnL %
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {portfolio.positions.map((position, idx) => (
                    <tr key={idx} className="hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {position.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                        {position.quantity.toFixed(6)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                        {formatCurrency(position.avg_entry_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                        {formatCurrency(position.current_price)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
                        position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {formatCurrency(position.unrealized_pnl)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
                        position.unrealized_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {formatPercent(position.unrealized_pnl_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Trade History */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-4">Trade History</h2>
        {!trades || trades.trades.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 border border-gray-700 text-center">
            <p className="text-gray-400">No trades yet</p>
          </div>
        ) : (
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
                  {trades.trades.slice(0, 20).map((trade) => (
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
            {trades.total > 20 && (
              <div className="bg-gray-900 px-6 py-3 text-center text-sm text-gray-400">
                Showing 20 of {trades.total} trades
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
