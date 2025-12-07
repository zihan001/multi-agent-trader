'use client';

import type { DecisionResult } from '@/types/api';

interface DecisionDisplayProps {
  result: DecisionResult;
}

export default function DecisionDisplay({ result }: DecisionDisplayProps) {
  const { decision, metadata, agents, signals } = result;

  return (
    <div className="space-y-6">
      {/* Decision Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Trading Decision</h2>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              metadata.engine_type === 'llm' 
                ? 'bg-purple-100 text-purple-800' 
                : 'bg-blue-100 text-blue-800'
            }`}>
              {metadata.engine_type.toUpperCase()} Mode
            </span>
            {metadata.strategy_name && (
              <span className="px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                {metadata.strategy_name.replace('_', ' ').toUpperCase()}
              </span>
            )}
          </div>
        </div>

        {/* Action Badge */}
        <div className="mb-4">
          <span className={`inline-block px-4 py-2 rounded-lg text-lg font-bold ${
            decision.action === 'BUY' 
              ? 'bg-green-500 text-white' 
              : decision.action === 'SELL' 
              ? 'bg-red-500 text-white' 
              : 'bg-gray-500 text-white'
          }`}>
            {decision.action}
          </span>
        </div>

        {/* Decision Details */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600">Symbol</p>
            <p className="text-lg font-semibold">{decision.symbol}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Confidence</p>
            <p className="text-lg font-semibold">{(decision.confidence * 100).toFixed(1)}%</p>
          </div>
          {decision.quantity && (
            <div>
              <p className="text-sm text-gray-600">Quantity</p>
              <p className="text-lg font-semibold">{decision.quantity.toFixed(4)}</p>
            </div>
          )}
          {decision.price && (
            <div>
              <p className="text-sm text-gray-600">Price</p>
              <p className="text-lg font-semibold">${decision.price.toFixed(2)}</p>
            </div>
          )}
        </div>

        {/* Reasoning */}
        <div>
          <p className="text-sm text-gray-600 mb-2">Reasoning</p>
          <ul className="list-disc list-inside space-y-1">
            {decision.reasoning.map((reason, idx) => (
              <li key={idx} className="text-sm">{reason}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Metadata */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Execution Metrics</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Cost</p>
            <p className="text-lg font-semibold">
              ${metadata.total_cost.toFixed(4)}
            </p>
          </div>
          {metadata.total_tokens && (
            <div>
              <p className="text-sm text-gray-600">Tokens</p>
              <p className="text-lg font-semibold">{metadata.total_tokens.toLocaleString()}</p>
            </div>
          )}
          <div>
            <p className="text-sm text-gray-600">Execution Time</p>
            <p className="text-lg font-semibold">{metadata.execution_time_ms.toFixed(0)}ms</p>
          </div>
        </div>
      </div>

      {/* LLM Mode: Agent Outputs */}
      {metadata.engine_type === 'llm' && agents && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Agent Analysis</h3>
          
          {/* Technical Analyst */}
          {agents.technical && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold">Technical Analyst</h4>
                <div className="text-xs text-gray-500">
                  {agents.technical.metadata.tokens} tokens • ${agents.technical.metadata.cost.toFixed(4)}
                </div>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Trend:</span>
                  <span className="ml-2 text-sm">{agents.technical.analysis.trend}</span>
                </div>
                <div>
                  <span className="text-sm font-medium">Momentum:</span>
                  <span className="ml-2 text-sm">{agents.technical.analysis.momentum}</span>
                </div>
                <div>
                  <span className="text-sm font-medium">Signals:</span>
                  <ul className="list-disc list-inside ml-4 mt-1">
                    {agents.technical.analysis.signals.map((signal: string, idx: number) => (
                      <li key={idx} className="text-sm">{signal}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <span className="text-sm font-medium">Reasoning:</span>
                  <p className="text-sm text-gray-700 mt-1">{agents.technical.analysis.reasoning}</p>
                </div>
              </div>
            </div>
          )}

          {/* Sentiment Analyst */}
          {agents.sentiment && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold">Sentiment Analyst</h4>
                <div className="text-xs text-gray-500">
                  {agents.sentiment.metadata.tokens} tokens • ${agents.sentiment.metadata.cost.toFixed(4)}
                </div>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Sentiment:</span>
                  <span className="ml-2 text-sm">{agents.sentiment.analysis.sentiment}</span>
                </div>
                <div>
                  <span className="text-sm font-medium">Narrative Points:</span>
                  <ul className="list-disc list-inside ml-4 mt-1">
                    {agents.sentiment.analysis.narrative_points.map((point: string, idx: number) => (
                      <li key={idx} className="text-sm">{point}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Tokenomics Analyst */}
          {agents.tokenomics && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold">Tokenomics Analyst</h4>
                <div className="text-xs text-gray-500">
                  {agents.tokenomics.metadata.tokens} tokens • ${agents.tokenomics.metadata.cost.toFixed(4)}
                </div>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Outlook:</span>
                  <span className="ml-2 text-sm">{agents.tokenomics.analysis.outlook}</span>
                </div>
                <div>
                  <span className="text-sm font-medium">Key Points:</span>
                  <ul className="list-disc list-inside ml-4 mt-1">
                    {agents.tokenomics.analysis.key_points.map((point: string, idx: number) => (
                      <li key={idx} className="text-sm">{point}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Researcher */}
          {agents.researcher && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold">Researcher</h4>
                <div className="text-xs text-gray-500">
                  {agents.researcher.metadata.tokens} tokens • ${agents.researcher.metadata.cost.toFixed(4)}
                </div>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Thesis:</span>
                  <p className="text-sm text-gray-700 mt-1">{agents.researcher.analysis.thesis}</p>
                </div>
                <div>
                  <span className="text-sm font-medium">Confidence:</span>
                  <span className="ml-2 text-sm">{(agents.researcher.analysis.confidence * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-sm font-medium">Top Risks:</span>
                  <ul className="list-disc list-inside ml-4 mt-1">
                    {agents.researcher.analysis.top_risks.map((risk: string, idx: number) => (
                      <li key={idx} className="text-sm">{risk}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Trader */}
          {agents.trader && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold">Trader</h4>
                <div className="text-xs text-gray-500">
                  {agents.trader.metadata.tokens} tokens • ${agents.trader.metadata.cost.toFixed(4)}
                </div>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Action:</span>
                  <span className="ml-2 text-sm">{agents.trader.analysis.action}</span>
                </div>
                <div>
                  <span className="text-sm font-medium">Position Size:</span>
                  <span className="ml-2 text-sm">{(agents.trader.analysis.position_size_pct * 100).toFixed(1)}%</span>
                </div>
                {agents.trader.analysis.stop_loss_pct && (
                  <div>
                    <span className="text-sm font-medium">Stop Loss:</span>
                    <span className="ml-2 text-sm">{(agents.trader.analysis.stop_loss_pct * 100).toFixed(1)}%</span>
                  </div>
                )}
                {agents.trader.analysis.take_profit_pct && (
                  <div>
                    <span className="text-sm font-medium">Take Profit:</span>
                    <span className="ml-2 text-sm">{(agents.trader.analysis.take_profit_pct * 100).toFixed(1)}%</span>
                  </div>
                )}
                <div>
                  <span className="text-sm font-medium">Reasoning:</span>
                  <ul className="list-disc list-inside ml-4 mt-1">
                    {agents.trader.analysis.reasoning.map((reason: string, idx: number) => (
                      <li key={idx} className="text-sm">{reason}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Risk Manager */}
          {agents.risk_manager && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold">Risk Manager</h4>
                <div className="text-xs text-gray-500">
                  {agents.risk_manager.metadata.tokens} tokens • ${agents.risk_manager.metadata.cost.toFixed(4)}
                </div>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Decision:</span>
                  <span className="ml-2 text-sm">{agents.risk_manager.analysis.decision}</span>
                </div>
                {agents.risk_manager.analysis.adjusted_size_pct && (
                  <div>
                    <span className="text-sm font-medium">Adjusted Size:</span>
                    <span className="ml-2 text-sm">{(agents.risk_manager.analysis.adjusted_size_pct * 100).toFixed(1)}%</span>
                  </div>
                )}
                <div>
                  <span className="text-sm font-medium">Explanation:</span>
                  <p className="text-sm text-gray-700 mt-1">{agents.risk_manager.analysis.explanation}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Rule Mode: Signal Analysis */}
      {metadata.engine_type === 'rule' && signals && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Technical Signals</h3>
          <div className="space-y-3">
            {Object.entries(signals).map(([key, signal]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex-1">
                  <p className="text-sm font-medium">{signal.indicator}</p>
                  <p className="text-xs text-gray-600">
                    Value: {signal.value.toFixed(2)}
                    {signal.threshold !== undefined && ` | Threshold: ${signal.threshold.toFixed(2)}`}
                  </p>
                </div>
                <div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    signal.signal === 'BUY' 
                      ? 'bg-green-100 text-green-800' 
                      : signal.signal === 'SELL' 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {signal.signal}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
