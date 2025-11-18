'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { runAnalysis } from '@/lib/api';
import type { AnalysisResponse } from '@/types/api';
import { CheckCircle, XCircle, AlertCircle, TrendingUp, TrendingDown, ArrowLeft } from 'lucide-react';

function AnalysisContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const symbol = searchParams.get('symbol') || 'BTCUSDT';
  
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const performAnalysis = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await runAnalysis({ symbol, mode: 'live' });
        setAnalysis(data);
      } catch (err) {
        setError('Failed to run analysis. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    performAnalysis();
  }, [symbol]);

  const getActionColor = (action: string) => {
    switch (action.toUpperCase()) {
      case 'BUY':
        return 'text-green-400 bg-green-900/20 border-green-500';
      case 'SELL':
        return 'text-red-400 bg-red-900/20 border-red-500';
      case 'HOLD':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-500';
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-500';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action.toUpperCase()) {
      case 'BUY':
        return <TrendingUp className="w-6 h-6" />;
      case 'SELL':
        return <TrendingDown className="w-6 h-6" />;
      default:
        return <AlertCircle className="w-6 h-6" />;
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col items-center justify-center py-24">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-400 text-lg">Analyzing {symbol}...</p>
          <p className="text-gray-500 text-sm mt-2">This may take 10-15 seconds</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-6 py-4 rounded-lg">
          <p className="font-semibold mb-2">Error</p>
          <p>{error}</p>
        </div>
        <button
          onClick={() => router.push('/')}
          className="mt-4 text-blue-400 hover:text-blue-300 flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.push('/')}
          className="text-blue-400 hover:text-blue-300 flex items-center gap-2 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
        <h1 className="text-3xl font-bold text-white mb-2">AI Analysis Results</h1>
        <p className="text-gray-400">{symbol}</p>
      </div>

      {/* Final Decision - Prominent Display */}
      <div className={`rounded-lg p-6 border-2 mb-8 ${getActionColor(analysis.final_decision.action)}`}>
        <div className="flex items-center gap-4 mb-4">
          {getActionIcon(analysis.final_decision.action)}
          <div>
            <h2 className="text-2xl font-bold">Final Decision: {analysis.final_decision.action}</h2>
            <p className="text-sm opacity-80">
              {analysis.final_decision.approved ? 'Approved by Risk Manager' : 'Not Approved'}
            </p>
          </div>
        </div>
        {analysis.final_decision.quantity && (
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm opacity-80">Quantity</p>
              <p className="font-semibold">{analysis.final_decision.quantity.toFixed(6)}</p>
            </div>
            <div>
              <p className="text-sm opacity-80">Price</p>
              <p className="font-semibold">${analysis.final_decision.price?.toFixed(2)}</p>
            </div>
          </div>
        )}
      </div>

      {/* Agent Analysis Cards */}
      <div className="space-y-6">
        {/* Technical Analyst */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">📊 Technical Analyst</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-gray-400 text-sm">Trend</p>
              <p className="text-white font-medium">{analysis.technical.trend}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Momentum</p>
              <p className="text-white font-medium">{analysis.technical.momentum}</p>
            </div>
          </div>
          {analysis.technical.signals && analysis.technical.signals.length > 0 && (
            <div className="mb-4">
              <p className="text-gray-400 text-sm mb-2">Signals</p>
              <ul className="list-disc list-inside text-gray-300 space-y-1">
                {analysis.technical.signals.map((signal, idx) => (
                  <li key={idx}>{signal}</li>
                ))}
              </ul>
            </div>
          )}
          <div>
            <p className="text-gray-400 text-sm mb-2">Reasoning</p>
            <p className="text-gray-300">{analysis.technical.reasoning}</p>
          </div>
        </div>

        {/* Sentiment Analyst */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">📰 Sentiment Analyst</h3>
          <div className="mb-4">
            <p className="text-gray-400 text-sm">Sentiment</p>
            <p className="text-white font-medium capitalize">{analysis.sentiment.sentiment}</p>
          </div>
          {analysis.sentiment.narrative_points && analysis.sentiment.narrative_points.length > 0 && (
            <div>
              <p className="text-gray-400 text-sm mb-2">Key Points</p>
              <ul className="list-disc list-inside text-gray-300 space-y-1">
                {analysis.sentiment.narrative_points.map((point, idx) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Tokenomics Analyst */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">🪙 Tokenomics Analyst</h3>
          <div className="mb-4">
            <p className="text-gray-400 text-sm">Outlook</p>
            <p className="text-white font-medium capitalize">{analysis.tokenomics.outlook}</p>
          </div>
          {analysis.tokenomics.key_points && analysis.tokenomics.key_points.length > 0 && (
            <div>
              <p className="text-gray-400 text-sm mb-2">Key Points</p>
              <ul className="list-disc list-inside text-gray-300 space-y-1">
                {analysis.tokenomics.key_points.map((point, idx) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Researcher */}
        <div className="bg-gray-800 rounded-lg p-6 border border-blue-700">
          <h3 className="text-xl font-semibold text-white mb-4">🔬 Researcher Synthesis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-gray-400 text-sm">Thesis</p>
              <p className="text-white font-medium capitalize">{analysis.researcher.thesis}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Confidence</p>
              <p className="text-white font-medium">{(analysis.researcher.confidence * 100).toFixed(0)}%</p>
            </div>
          </div>
          <div className="mb-4">
            <p className="text-gray-400 text-sm mb-2">Top Risks</p>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              {analysis.researcher.top_risks.map((risk, idx) => (
                <li key={idx}>{risk}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Justification</p>
            <p className="text-gray-300">{analysis.researcher.justification}</p>
          </div>
        </div>

        {/* Trader */}
        <div className="bg-gray-800 rounded-lg p-6 border border-green-700">
          <h3 className="text-xl font-semibold text-white mb-4">💼 Trader Decision</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-gray-400 text-sm">Action</p>
              <p className="text-white font-medium">{analysis.trader.action}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Position Size</p>
              <p className="text-white font-medium">{analysis.trader.position_size_pct}%</p>
            </div>
            {analysis.trader.stop_loss_pct && (
              <div>
                <p className="text-gray-400 text-sm">Stop Loss</p>
                <p className="text-white font-medium">{analysis.trader.stop_loss_pct}%</p>
              </div>
            )}
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Reasoning</p>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              {analysis.trader.reasoning.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Risk Manager */}
        <div className="bg-gray-800 rounded-lg p-6 border border-yellow-700">
          <h3 className="text-xl font-semibold text-white mb-4">🛡️ Risk Manager</h3>
          <div className="mb-4">
            <p className="text-gray-400 text-sm">Decision</p>
            <div className="flex items-center gap-2 mt-1">
              {analysis.risk_manager.decision === 'APPROVE' ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : analysis.risk_manager.decision === 'REJECT' ? (
                <XCircle className="w-5 h-5 text-red-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-500" />
              )}
              <p className="text-white font-medium">{analysis.risk_manager.decision}</p>
            </div>
          </div>
          {analysis.risk_manager.adjusted_size_pct && (
            <div className="mb-4">
              <p className="text-gray-400 text-sm">Adjusted Size</p>
              <p className="text-white font-medium">{analysis.risk_manager.adjusted_size_pct}%</p>
            </div>
          )}
          <div>
            <p className="text-gray-400 text-sm mb-2">Explanation</p>
            <p className="text-gray-300">{analysis.risk_manager.explanation}</p>
          </div>
        </div>
      </div>

      {/* Portfolio Snapshot */}
      <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Portfolio Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Cash Balance</p>
            <p className="text-white font-semibold">
              ${analysis.portfolio_snapshot.cash_balance.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Total Equity</p>
            <p className="text-white font-semibold">
              ${analysis.portfolio_snapshot.total_equity.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Unrealized PnL</p>
            <p className={`font-semibold ${analysis.portfolio_snapshot.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${analysis.portfolio_snapshot.unrealized_pnl.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Total Return</p>
            <p className={`font-semibold ${analysis.portfolio_snapshot.total_return_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {analysis.portfolio_snapshot.total_return_pct.toFixed(2)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center py-24">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
        </div>
      </div>
    }>
      <AnalysisContent />
    </Suspense>
  );
}
