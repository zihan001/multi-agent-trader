'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { PaperOrderForm, PaperOrdersTable, PaperAccountDisplay } from '@/components/PaperTrading';
import { getPaperAccount, createPaperOrder, getPaperOrders, getOpenPaperOrders, cancelPaperOrder, syncPaperOrders, getRecommendation, executeRecommendation } from '@/lib/api';
import type { PaperOrder, PaperAccount, AgentRecommendation } from '@/types/api';
import { ArrowLeft, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';

function PaperTradingContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const recommendationId = searchParams.get('recommendation');
  
  const [account, setAccount] = useState<PaperAccount | null>(null);
  const [orders, setOrders] = useState<PaperOrder[]>([]);
  const [openOrders, setOpenOrders] = useState<PaperOrder[]>([]);
  const [recommendation, setRecommendation] = useState<AgentRecommendation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadAccount();
    loadOrders();
    if (recommendationId) {
      loadRecommendation(parseInt(recommendationId));
    }
  }, [recommendationId]);

  const loadRecommendation = async (id: number) => {
    try {
      const data = await getRecommendation(id);
      setRecommendation(data);
    } catch (err: any) {
      setError(`Failed to load recommendation: ${err.message}`);
    }
  };

  const loadAccount = async () => {
    try {
      const data = await getPaperAccount();
      setAccount(data);
    } catch (err: any) {
      setError(`Failed to load account: ${err.message}`);
    }
  };

  const loadOrders = async () => {
    try {
      const [allOrders, open] = await Promise.all([
        getPaperOrders(),
        getOpenPaperOrders(),
      ]);
      setOrders(allOrders);
      setOpenOrders(open);
    } catch (err: any) {
      setError(`Failed to load orders: ${err.message}`);
    }
  };

  const handleCreateOrder = async (order: any) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const created = await createPaperOrder(order);
      setSuccess(`Order created successfully! Order ID: ${created.id}, Binance Order ID: ${created.binance_order_id}`);
      await loadOrders();
      await loadAccount();
    } catch (err: any) {
      setError(`Failed to create order: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelOrder = async (orderId: number) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      await cancelPaperOrder(orderId);
      setSuccess(`Order ${orderId} cancelled successfully!`);
      await loadOrders();
    } catch (err: any) {
      setError(`Failed to cancel order: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSync = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      await syncPaperOrders('BTCUSDT');
      setSuccess('Orders synced from Binance testnet!');
      await loadOrders();
    } catch (err: any) {
      setError(`Failed to sync orders: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteRecommendation = async (orderType: 'MARKET' | 'LIMIT', limitPrice?: number) => {
    if (!recommendation) return;
    
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const result = await executeRecommendation(recommendation.id, orderType, limitPrice);
      setSuccess(`Order executed successfully! Order ID: ${result.order_id}, Binance Order ID: ${result.binance_order_id}`);
      await loadOrders();
      await loadAccount();
      // Go back to dashboard after successful execution
      setTimeout(() => router.push('/'), 2000);
    } catch (err: any) {
      setError(`Failed to execute recommendation: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back Button */}
      {recommendationId && (
        <button
          onClick={() => router.push('/')}
          className="mb-4 text-blue-400 hover:text-blue-300 flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Ideas
        </button>
      )}

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          {recommendationId ? 'Order Ticket' : 'Paper Trading (Binance Testnet)'}
        </h1>
        <p className="text-gray-400 mb-2">
          {recommendationId 
            ? 'Review and execute the AI trading recommendation'
            : 'Trade with real Binance testnet API using simulated funds. No real money involved.'
          }
        </p>
        {!recommendationId && (
          <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3 text-sm text-blue-200">
            <strong>💡 About Testnet:</strong> These are fake balances provided by Binance for testing. 
            Sign up at <a href="https://testnet.binance.vision/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline font-semibold">testnet.binance.vision</a> to get free test tokens (USDT, BTC, ETH, etc.).
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-600 rounded-lg text-red-200">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-900/50 border border-green-600 rounded-lg text-green-200">
          {success}
        </div>
      )}

      {/* Account Balances */}
      {account && (
        <div className="mb-8">
          <PaperAccountDisplay account={account} />
        </div>
      )}

      {/* AI Recommendation Order Ticket */}
      {recommendation && (
        <div className="mb-8 bg-gradient-to-br from-blue-900/30 to-purple-900/30 rounded-lg p-6 border border-blue-500/50">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-6 h-6 text-yellow-500" />
            <h2 className="text-xl font-semibold text-white">AI Trading Recommendation</h2>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-400">Symbol</p>
              <p className="text-xl font-bold text-white">{recommendation.symbol}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Action</p>
              <span className={`inline-block px-4 py-1 rounded-full text-lg font-semibold ${
                recommendation.action === 'BUY'
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {recommendation.action}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-400">Entry Price</p>
              <p className="text-lg font-semibold text-white">${recommendation.price.toFixed(2)}</p>
            </div>
            {recommendation.quantity && (
              <div>
                <p className="text-sm text-gray-400">Quantity</p>
                <p className="text-lg font-semibold text-white">{recommendation.quantity.toFixed(4)}</p>
              </div>
            )}
            {recommendation.position_size_pct && (
              <div>
                <p className="text-sm text-gray-400">Position Size</p>
                <p className="text-lg font-semibold text-white">{(recommendation.position_size_pct * 100).toFixed(1)}%</p>
              </div>
            )}
            {recommendation.time_horizon && (
              <div>
                <p className="text-sm text-gray-400">Time Horizon</p>
                <p className="text-lg font-semibold text-white">{recommendation.time_horizon}</p>
              </div>
            )}
            {recommendation.confidence && (
              <div>
                <p className="text-sm text-gray-400">Confidence</p>
                <p className="text-lg font-semibold text-white">{(recommendation.confidence * 100).toFixed(0)}%</p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-400">Strategy</p>
              <p className="text-lg font-semibold text-white">{recommendation.strategy_name || recommendation.decision_type}</p>
            </div>
          </div>

          {recommendation.reasoning && (
            <div className="mb-4">
              <p className="text-sm text-gray-400 mb-1">Reasoning</p>
              <p className="text-white">{recommendation.reasoning}</p>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => handleExecuteRecommendation('MARKET')}
              disabled={isLoading || recommendation.status !== 'pending'}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {isLoading ? 'Executing...' : 'Execute as Market Order'}
            </button>
            <button
              onClick={() => handleExecuteRecommendation('LIMIT', recommendation.price)}
              disabled={isLoading || recommendation.status !== 'pending'}
              className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {isLoading ? 'Executing...' : 'Execute as Limit Order'}
            </button>
          </div>
        </div>
      )}

      {/* Manual Order Form (shown when no recommendation) */}
      {!recommendation && (
        <div className="mb-8">
          <PaperOrderForm onSubmit={handleCreateOrder} isLoading={isLoading} />
        </div>
      )}

        {/* Orders Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white">Recent Orders</h2>
            <button
              onClick={handleSync}
              disabled={isLoading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded font-semibold transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Syncing...' : 'Sync from Testnet'}
            </button>
          </div>

          <PaperOrdersTable
            orders={orders}
            onCancel={handleCancelOrder}
            isLoading={isLoading}
          />
        </div>

        {/* Info Section */}
        {!recommendation && (
          <div className="bg-gray-800 rounded-lg p-6 text-sm text-gray-300">
            <h3 className="text-lg font-bold text-white mb-3">About Paper Trading</h3>
            <ul className="space-y-2 list-disc list-inside">
              <li>Orders are executed on <strong className="text-blue-400">Binance Spot Testnet</strong> with simulated funds</li>
              <li><strong className="text-green-400">Market orders</strong> are filled immediately at current market price</li>
              <li><strong className="text-yellow-400">Limit orders</strong> are placed and wait for price to reach target</li>
              <li>Use the <strong>Sync</strong> button to pull latest order status from Binance testnet</li>
              <li>Get free testnet funds at <a href="https://testnet.binance.vision/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">testnet.binance.vision</a></li>
            </ul>
          </div>
        )}
      </div>
  );
}

export default function PaperTradingPage() {
  return (
    <Suspense fallback={
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-center items-center py-24">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
        </div>
      </div>
    }>
      <PaperTradingContent />
    </Suspense>
  );
}
