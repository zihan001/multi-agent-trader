'use client';

import { useEffect, useState } from 'react';
import { getPortfolio, getTrades, getPaperOrders, getPaperAccount, getRecommendations } from '@/lib/api';
import type { PortfolioResponse, TradesResponse, PaperOrder, PaperAccount, AgentRecommendation } from '@/types/api';
import { TrendingUp, TrendingDown, DollarSign, Target, BarChart3 } from 'lucide-react';
import { format } from 'date-fns';

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [trades, setTrades] = useState<TradesResponse | null>(null);
  const [paperOrders, setPaperOrders] = useState<PaperOrder[]>([]);
  const [paperAccount, setPaperAccount] = useState<PaperAccount | null>(null);
  const [recommendations, setRecommendations] = useState<AgentRecommendation[]>([]);
  const [activeTab, setActiveTab] = useState<'agent' | 'paper' | 'recommendations' | 'all'>('agent');
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
        
        // Try to load paper trading data and recommendations
        try {
          const [orders, account, recs] = await Promise.all([
            getPaperOrders({ limit: 50 }),
            getPaperAccount(),
            getRecommendations({ limit: 50 }),
          ]);
          setPaperOrders(orders);
          setPaperAccount(account);
          setRecommendations(recs);
        } catch (paperErr) {
          console.log('Paper trading not available:', paperErr);
        }
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
        <p className="text-gray-400">Your simulated trading portfolio and testnet account</p>
      </div>

      {/* Paper Trading Account Summary (if available) */}
      {paperAccount && (
        <div className="mb-8 bg-blue-900/20 border border-blue-500/50 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
            <h2 className="text-xl font-bold text-white">Binance Testnet Account</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {paperAccount.balances
              .filter(b => {
                const total = parseFloat(b.free) + parseFloat(b.locked);
                const cryptoAssets = ['BTC', 'ETH', 'BNB', 'USDT', 'USDC', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK'];
                return total > 0 && cryptoAssets.includes(b.asset);
              })
              .sort((a, b) => {
                const aTotal = parseFloat(a.free) + parseFloat(a.locked);
                const bTotal = parseFloat(b.free) + parseFloat(b.locked);
                return bTotal - aTotal;
              })
              .slice(0, 4)
              .map(balance => {
                const total = parseFloat(balance.free) + parseFloat(balance.locked);
                return (
                  <div key={balance.asset} className="bg-gray-800 rounded p-3">
                    <p className="text-gray-400 text-xs mb-1">{balance.asset}</p>
                    <p className="text-white font-bold text-lg">{total.toFixed(8)}</p>
                  </div>
                );
              })}
          </div>
          <p className="text-sm text-blue-400 mt-4">
            This shows your real Binance testnet balances from paper trading orders. See full details on the Paper Trading page.
          </p>
        </div>
      )}

      {/* Summary Cards */}
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white mb-2">Agent Simulation Portfolio</h2>
        <p className="text-sm text-gray-400 mb-4">AI agent decisions tracked in local database (not on Binance testnet)</p>
      </div>
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

      {/* Trade History / Orders */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white">Activity History</h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'recommendations'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              AI Recommendations ({recommendations.length})
            </button>
            <button
              onClick={() => setActiveTab('agent')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'agent'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Agent Trades ({trades?.trades.length || 0})
            </button>
            {paperOrders.length > 0 && (
              <button
                onClick={() => setActiveTab('paper')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'paper'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Paper Orders ({paperOrders.length})
              </button>
            )}
          </div>
        </div>

        {/* AI Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <>
            {recommendations.length === 0 ? (
              <div className="bg-gray-800 rounded-lg p-8 border border-gray-700 text-center">
                <p className="text-gray-400">No AI recommendations yet. Run an analysis to get started!</p>
              </div>
            ) : (
              <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-900">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Symbol
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Action
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Quantity
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Price
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Confidence
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                          Engine
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                      {recommendations.map((rec) => (
                        <tr key={rec.id} className="hover:bg-gray-700/50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            {format(new Date(rec.created_at), 'MMM dd, HH:mm')}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                            {rec.symbol}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`font-semibold ${rec.action === 'BUY' ? 'text-green-400' : rec.action === 'SELL' ? 'text-red-400' : 'text-gray-400'}`}>
                              {rec.action}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                            {rec.quantity ? rec.quantity.toFixed(6) : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                            ${rec.price.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                            {rec.confidence ? (
                              <span className="text-blue-400 font-medium">{(rec.confidence * 100).toFixed(0)}%</span>
                            ) : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              rec.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
                              rec.status === 'executed' ? 'bg-green-500/20 text-green-400' :
                              rec.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              {rec.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                            {rec.decision_type === 'llm' ? '🤖 AI Agents' : '📊 Rule-Based'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {/* Agent Trades Tab */}
        {activeTab === 'agent' && (
          <>
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
        </>
        )}

        {/* Paper Trading Orders Tab */}
        {activeTab === 'paper' && paperOrders.length > 0 && (
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Filled
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Binance ID
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {paperOrders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {format(new Date(order.created_at), 'MMM dd, yyyy HH:mm')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {order.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          order.side === 'BUY'
                            ? 'bg-green-900/30 text-green-400'
                            : 'bg-red-900/30 text-red-400'
                        }`}>
                          {order.side}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {order.order_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                        {order.quantity.toFixed(6)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                        {order.price ? formatCurrency(order.price) : 'MARKET'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-300">
                        {order.filled_quantity.toFixed(6)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          order.status === 'FILLED'
                            ? 'bg-green-900/30 text-green-400'
                            : order.status === 'PENDING'
                            ? 'bg-yellow-900/30 text-yellow-400'
                            : order.status === 'CANCELLED'
                            ? 'bg-gray-700 text-gray-400'
                            : 'bg-red-900/30 text-red-400'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-400">
                        {order.binance_order_id || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-gray-900 px-6 py-3 text-center">
              <a 
                href="/paper-trading" 
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                Go to Paper Trading page for order management →
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
