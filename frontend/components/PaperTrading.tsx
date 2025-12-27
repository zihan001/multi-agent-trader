'use client';

import React, { useState } from 'react';
import type { PaperOrder } from '@/types/api';

interface PaperOrderFormProps {
  onSubmit: (order: {
    symbol: string;
    side: 'BUY' | 'SELL';
    order_type: 'MARKET' | 'LIMIT' | 'STOP_LOSS' | 'TAKE_PROFIT';
    quantity: number;
    price?: number;
    stop_price?: number;
    time_in_force?: 'GTC' | 'IOC' | 'FOK';
  }) => Promise<void>;
  isLoading?: boolean;
}

export function PaperOrderForm({ onSubmit, isLoading }: PaperOrderFormProps) {
  const SUPPORTED_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT'];
  
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [quantity, setQuantity] = useState('0.001');
  const [price, setPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [timeInForce, setTimeInForce] = useState<'GTC' | 'IOC' | 'FOK'>('GTC');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const order: any = {
      symbol,
      side,
      order_type: orderType,
      quantity: parseFloat(quantity),
      time_in_force: timeInForce,
    };

    if (orderType === 'LIMIT' && price) {
      order.price = parseFloat(price);
    }

    await onSubmit(order);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-gray-800 p-6 rounded-lg">
      <h3 className="text-xl font-bold text-white mb-4">Create Paper Trading Order</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Symbol</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            required
          >
            {SUPPORTED_SYMBOLS.map(sym => (
              <option key={sym} value={sym}>{sym}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Side</label>
          <select
            value={side}
            onChange={(e) => setSide(e.target.value as 'BUY' | 'SELL')}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
          >
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Order Type</label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as any)}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
          >
            <option value="MARKET">MARKET</option>
            <option value="LIMIT">LIMIT</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Quantity</label>
          <input
            type="number"
            step="0.000001"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            placeholder="0.001"
            required
          />
        </div>
      </div>

      {orderType === 'LIMIT' && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Limit Price</label>
          <input
            type="number"
            step="0.01"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            placeholder="50000.00"
            required={orderType === 'LIMIT'}
          />
        </div>
      )}

      {orderType !== 'MARKET' && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Time in Force</label>
          <select
            value={timeInForce}
            onChange={(e) => setTimeInForce(e.target.value as any)}
            className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
          >
            <option value="GTC">Good Till Cancel (GTC)</option>
            <option value="IOC">Immediate or Cancel (IOC)</option>
            <option value="FOK">Fill or Kill (FOK)</option>
          </select>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className={`w-full py-3 rounded font-semibold transition-colors ${
          side === 'BUY'
            ? 'bg-green-600 hover:bg-green-700 text-white'
            : 'bg-red-600 hover:bg-red-700 text-white'
        } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {isLoading ? 'Creating Order...' : `${side} ${symbol}`}
      </button>
    </form>
  );
}

interface PaperOrdersTableProps {
  orders: PaperOrder[];
  onCancel?: (orderId: number) => Promise<void>;
  isLoading?: boolean;
}

export function PaperOrdersTable({ orders, onCancel, isLoading }: PaperOrdersTableProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'FILLED': return 'text-green-400';
      case 'PENDING': return 'text-yellow-400';
      case 'CANCELLED': return 'text-gray-400';
      case 'REJECTED': return 'text-red-400';
      default: return 'text-gray-300';
    }
  };

  const getSideColor = (side: string) => {
    return side === 'BUY' ? 'text-green-400' : 'text-red-400';
  };

  if (orders.length === 0) {
    return (
      <div className="bg-gray-800 p-6 rounded-lg text-center text-gray-400">
        No orders found
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Symbol</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Side</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Type</th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-gray-300">Quantity</th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-gray-300">Price</th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-gray-300">Filled</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Status</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Time</th>
              {onCancel && <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300">Action</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-gray-750">
                <td className="px-4 py-3 text-sm text-white font-medium">{order.symbol}</td>
                <td className={`px-4 py-3 text-sm font-semibold ${getSideColor(order.side)}`}>
                  {order.side}
                </td>
                <td className="px-4 py-3 text-sm text-gray-300">{order.order_type}</td>
                <td className="px-4 py-3 text-sm text-gray-300 text-right">{order.quantity}</td>
                <td className="px-4 py-3 text-sm text-gray-300 text-right">
                  {order.price ? `$${order.price.toFixed(2)}` : 'MARKET'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-300 text-right">
                  {order.filled_quantity.toFixed(6)}
                </td>
                <td className={`px-4 py-3 text-sm font-semibold ${getStatusColor(order.status)}`}>
                  {order.status}
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">
                  {new Date(order.created_at).toLocaleString()}
                </td>
                {onCancel && (
                  <td className="px-4 py-3 text-center">
                    {order.status === 'PENDING' && (
                      <button
                        onClick={() => onCancel(order.id)}
                        disabled={isLoading}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface PaperAccountDisplayProps {
  account: {
    balances: Array<{
      asset: string;
      free: string;
      locked: string;
    }>;
  };
}

export function PaperAccountDisplay({ account }: PaperAccountDisplayProps) {
  // Crypto assets to display (exclude fiat currencies)
  const cryptoAssets = ['BTC', 'ETH', 'BNB', 'USDT', 'USDC', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK'];
  
  // Filter to show only crypto balances with non-zero amounts
  const relevantBalances = account.balances
    .filter(b => {
      const hasBalance = parseFloat(b.free) > 0 || parseFloat(b.locked) > 0;
      const isCrypto = cryptoAssets.includes(b.asset);
      return hasBalance && isCrypto;
    })
    .sort((a, b) => {
      const aTotal = parseFloat(a.free) + parseFloat(a.locked);
      const bTotal = parseFloat(b.free) + parseFloat(b.locked);
      return bTotal - aTotal;
    });

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-xl font-bold text-white mb-2">Testnet Crypto Balances</h3>
      <p className="text-sm text-gray-400 mb-4">
        Showing only crypto assets. Your testnet account may also have fiat balances (USD, EUR, etc.) which are hidden here.
      </p>
      
      {relevantBalances.length === 0 ? (
        <p className="text-gray-400">No balances available</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {relevantBalances.map((balance) => {
            const total = parseFloat(balance.free) + parseFloat(balance.locked);
            return (
              <div key={balance.asset} className="bg-gray-700 rounded-lg p-4">
                <div className="text-lg font-bold text-white mb-2">{balance.asset}</div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Free:</span>
                    <span className="text-green-400 font-medium">{parseFloat(balance.free).toFixed(8)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Locked:</span>
                    <span className="text-yellow-400 font-medium">{parseFloat(balance.locked).toFixed(8)}</span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-gray-600">
                    <span className="text-gray-300 font-semibold">Total:</span>
                    <span className="text-white font-bold">{total.toFixed(8)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
