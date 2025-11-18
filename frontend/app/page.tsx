'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getMarketSymbols, getMarketData } from '@/lib/api';
import type { MarketDataResponse } from '@/types/api';
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const data = await getMarketSymbols();
        setSymbols(data.symbols);
        if (data.symbols.length > 0) {
          setSelectedSymbol(data.symbols[0]);
          fetchMarketData(data.symbols[0]);
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

  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
    fetchMarketData(symbol);
  };

  const handleRunAnalysis = () => {
    router.push(`/analysis?symbol=${selectedSymbol}`);
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

          {/* Run Analysis Button */}
          <div className="flex justify-center">
            <button
              onClick={handleRunAnalysis}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors flex items-center gap-2"
            >
              <TrendingUp className="w-5 h-5" />
              Run AI Analysis
            </button>
          </div>
        </>
      )}
    </div>
  );
}

