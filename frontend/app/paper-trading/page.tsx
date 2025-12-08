'use client';

import { useState, useEffect } from 'react';
import { PaperOrderForm, PaperOrdersTable, PaperAccountDisplay } from '@/components/PaperTrading';
import { getPaperAccount, createPaperOrder, getPaperOrders, getOpenPaperOrders, cancelPaperOrder, syncPaperOrders } from '@/lib/api';
import type { PaperOrder, PaperAccount } from '@/types/api';

export default function PaperTradingPage() {
  const [account, setAccount] = useState<PaperAccount | null>(null);
  const [orders, setOrders] = useState<PaperOrder[]>([]);
  const [openOrders, setOpenOrders] = useState<PaperOrder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'open' | 'all'>('open');

  useEffect(() => {
    loadAccount();
    loadOrders();
  }, []);

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

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Paper Trading (Binance Testnet)</h1>
        <p className="text-gray-400 mb-2">
          Trade with real Binance testnet API using simulated funds. No real money involved.
        </p>
        <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3 text-sm text-blue-200">
          <strong>💡 About Testnet:</strong> These are fake balances provided by Binance for testing. 
          Sign up at <a href="https://testnet.binance.vision/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline font-semibold">testnet.binance.vision</a> to get free test tokens (USDT, BTC, ETH, etc.).
        </div>
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

        {/* Order Form */}
        <div className="mb-8">
          <PaperOrderForm onSubmit={handleCreateOrder} isLoading={isLoading} />
        </div>

        {/* Orders Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveTab('open')}
                className={`px-4 py-2 rounded font-semibold transition-colors ${
                  activeTab === 'open'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Open Orders ({openOrders.length})
              </button>
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-2 rounded font-semibold transition-colors ${
                  activeTab === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                All Orders ({orders.length})
              </button>
            </div>

            <button
              onClick={handleSync}
              disabled={isLoading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded font-semibold transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Syncing...' : 'Sync from Testnet'}
            </button>
          </div>

          {activeTab === 'open' ? (
            <PaperOrdersTable
              orders={openOrders}
              onCancel={handleCancelOrder}
              isLoading={isLoading}
            />
          ) : (
            <PaperOrdersTable orders={orders} />
          )}
        </div>

        {/* Info Section */}
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
      </div>
  );
}
