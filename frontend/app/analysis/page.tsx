'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { runAnalysis, getTradingMode } from '@/lib/api';
import type { AnalysisResponse, TradingModeResponse } from '@/types/api';
import { ArrowLeft } from 'lucide-react';
import DecisionDisplay from '@/components/DecisionDisplay';

function AnalysisContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const symbol = searchParams.get('symbol') || 'BTCUSDT';
  
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [modeInfo, setModeInfo] = useState<TradingModeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModeInfo = async () => {
      try {
        const mode = await getTradingMode();
        setModeInfo(mode);
      } catch (err) {
        console.error('[Analysis] Failed to fetch trading mode:', err);
      }
    };

    const performAnalysis = async () => {
      setLoading(true);
      setError(null);
      try {
        console.log(`[Analysis] Starting analysis for ${symbol}`);
        const data = await runAnalysis({ symbol, mode: 'live' });
        console.log('[Analysis] Response received:', data);
        setAnalysis(data);
      } catch (err: any) {
        console.error('[Analysis] Error caught:', err);
        
        // Handle specific error types based on HTTP status or message
        if (err.response) {
          const status = err.response.status;
          const detail = err.response.data?.detail || 'Unknown error';
          
          if (status === 429) {
            if (detail.includes('budget')) {
              setError('⚠️ Daily LLM budget exceeded. The system has reached its token usage limit. Please try again tomorrow.');
            } else {
              setError('⏳ Rate limit exceeded. The AI service is receiving too many requests. Please wait a moment and try again.');
            }
          } else if (status === 504) {
            setError('⏱️ Analysis timed out. The AI service may be experiencing high load. Please try again in a few moments.');
          } else if (status === 503) {
            setError('🔧 AI service unavailable. Please contact support if this persists.');
          } else {
            setError(`❌ Analysis failed: ${detail}`);
          }
        } else if (err.message) {
          setError(`❌ Network error: ${err.message}. Please check your connection.`);
        } else {
          setError('❌ Failed to run analysis. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchModeInfo();
    performAnalysis();
  }, [symbol]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col items-center justify-center py-24">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-400 text-lg">Analyzing {symbol}...</p>
          <p className="text-gray-500 text-sm mt-2">
            {modeInfo?.engine_info.type === 'rule' 
              ? 'Processing technical signals...' 
              : 'Running AI agents... (10-15 seconds)'}
          </p>
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

  const hasErrors = analysis.errors && analysis.errors.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.push('/')}
          className="text-blue-400 hover:text-blue-300 flex items-center gap-2 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Trading Analysis Results</h1>
            <p className="text-gray-400">{symbol}</p>
          </div>
          {modeInfo && (
            <div className="text-right">
              <div className="text-sm text-gray-400 mb-1">Engine Mode</div>
              <div className="text-lg font-semibold text-white">
                {modeInfo.engine_info.name}
              </div>
              <div className="text-xs text-gray-500">
                ~${modeInfo.engine_info.cost_per_decision.toFixed(4)} per decision
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {hasErrors && (
        <div className="bg-red-900/20 border border-red-500 text-red-400 px-6 py-4 rounded-lg mb-8">
          <p className="font-semibold mb-2">⚠️ Analysis Completed with Errors</p>
          <ul className="list-disc list-inside space-y-1">
            {analysis.errors && Array.isArray(analysis.errors) && analysis.errors.map((error: any, idx: number) => (
              <li key={idx}>
                <span className="font-medium">{error.type}:</span> {error.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Unified Decision Display */}
      <DecisionDisplay result={analysis.result} />

      {/* Agent Recommendation Card */}
      {analysis.recommendation && (
        <div className="mt-8 bg-gradient-to-br from-blue-900/30 to-purple-900/30 border-2 border-blue-500/50 rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-semibold text-white mb-2">🤖 AI Recommendation</h3>
              <p className="text-sm text-gray-400">
                The agents recommend <span className="font-semibold text-white">{analysis.recommendation.action}</span>
                {analysis.recommendation.action !== 'HOLD' && (
                  <span> {analysis.recommendation.quantity} {symbol} at ${analysis.recommendation.price.toFixed(2)}</span>
                )}
              </p>
            </div>
            <div className={`px-3 py-1 rounded text-xs font-semibold ${
              analysis.recommendation.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
              analysis.recommendation.status === 'executed' ? 'bg-green-500/20 text-green-400' :
              analysis.recommendation.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {analysis.recommendation.status.toUpperCase()}
            </div>
          </div>
          
          {analysis.recommendation.confidence && (
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Confidence</span>
                <span className="text-white font-medium">{(analysis.recommendation.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${analysis.recommendation.confidence * 100}%` }}
                ></div>
              </div>
            </div>
          )}
          
          {analysis.recommendation.reasoning && (
            <div className="mb-4 p-4 bg-gray-800/50 rounded">
              <p className="text-sm text-gray-300 leading-relaxed">{analysis.recommendation.reasoning}</p>
            </div>
          )}
          
          {analysis.recommendation?.status === 'pending' && analysis.recommendation?.action !== 'HOLD' && (
            <div className="flex gap-3">
              <button
                onClick={() => router.push(`/paper-trading?recommendation=${analysis.recommendation?.id}`)}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded font-medium transition-colors"
              >
                Execute on Testnet
              </button>
              <button
                onClick={async () => {
                  if (confirm('Reject this recommendation?')) {
                    try {
                      await fetch(`http://localhost:8000/recommendations/${analysis.recommendation?.id}/reject`, {
                        method: 'POST',
                      });
                      window.location.reload();
                    } catch (err) {
                      alert('Failed to reject recommendation');
                    }
                  }
                }}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded font-medium transition-colors"
              >
                Reject
              </button>
            </div>
          )}
          
          {analysis.recommendation?.status === 'executed' && analysis.recommendation?.executed_order_id && (
            <div className="text-sm text-green-400">
              ✓ Executed as order #{analysis.recommendation?.executed_order_id}. View on <a href="/paper-trading" className="underline">Paper Trading</a> page.
            </div>
          )}
        </div>
      )}

      {/* Portfolio Snapshot */}
      {analysis.portfolio_snapshot && (
      <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Portfolio Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Cash Balance</p>
            <p className="text-white font-semibold">
              ${analysis.portfolio_snapshot.cash_balance?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Total Equity</p>
            <p className="text-white font-semibold">
              ${analysis.portfolio_snapshot.total_equity?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Unrealized PnL</p>
            <p className={`font-semibold ${(analysis.portfolio_snapshot.unrealized_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${analysis.portfolio_snapshot.unrealized_pnl?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Total Return</p>
            <p className={`font-semibold ${(analysis.portfolio_snapshot.total_return_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {analysis.portfolio_snapshot.total_return_pct?.toFixed(2) || '0.00'}%
            </p>
          </div>
        </div>
      </div>
      )}
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
