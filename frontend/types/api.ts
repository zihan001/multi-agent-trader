// Health check
export interface HealthResponse {
  status: string;
  trading_mode?: string;
  rule_strategy?: string;
}

// Market data types
export interface MarketSymbolsResponse {
  symbols: string[];
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Indicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  ema_12: number;
  ema_26: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
}

export interface MarketDataResponse {
  symbol: string;
  candles: Candle[];
  indicators: Indicators;
  latest_price: number;
}

// Agent analysis types
export interface TechnicalAnalysis {
  trend: string;
  momentum: string;
  signals: string[];
  reasoning: string;
}

export interface SentimentAnalysis {
  sentiment: string;
  narrative_points: string[];
}

export interface TokenomicsAnalysis {
  outlook: string;
  key_points: string[];
}

export interface ResearcherThesis {
  thesis: string;
  confidence: number;
  top_risks: string[];
  justification: string;
}

export interface TraderDecision {
  action: string;
  position_size_pct: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  reasoning: string[];
}

export interface RiskManagerDecision {
  decision: string;
  adjusted_size_pct?: number;
  explanation: string;
}

export interface FinalDecision {
  action: string;
  symbol: string;
  quantity?: number;
  price?: number;
  approved: boolean;
}

// Unified Decision Types (Phase 6)
export interface SignalData {
  name: string;
  value: number;
  threshold?: number;
  status: string;
}

export interface TradingDecision {
  action: string;
  symbol?: string;
  quantity?: number;
  price?: number;
  confidence: number;
  reasoning: string | string[];  // Can be string (rule mode) or array (LLM mode)
  approved?: boolean;
  stop_loss?: number;
  take_profit?: number;
}

export interface DecisionMetadata {
  engine_type: string;
  model_used?: string;
  strategy_name?: string;
  total_cost: number;
  total_tokens?: number;
  execution_time_ms: number;
}

export interface AgentOutput {
  analysis: any;
  metadata: {
    model: string;
    tokens: number;
    cost: number;
    latency: number;
  };
}

export interface DecisionResult {
  run_id: string;
  symbol: string;
  timestamp: string;
  decision: TradingDecision;
  metadata: DecisionMetadata;
  agents?: {
    technical?: AgentOutput;
    sentiment?: AgentOutput;
    tokenomics?: AgentOutput;
    researcher?: AgentOutput;
    trader?: AgentOutput;
    risk_manager?: AgentOutput;
  };
  signals?: Record<string, SignalData>;
}

export interface AnalysisRequest {
  symbol: string;
  mode?: 'live' | 'backtest_step';
  timestamp?: string;
}

export interface AnalysisResponse {
  result: DecisionResult;
  portfolio_updated: boolean;
  trade_executed?: Trade;
  portfolio_snapshot?: PortfolioSnapshot;
  errors?: Array<{ type: string; message: string }>;
}

// Config Types (Phase 6)
export interface EngineInfo {
  type: string;
  name: string;
  description: string;
  cost_per_decision: number;
  avg_latency_ms: number;
  supports_realtime: boolean;
}

export interface TradingModeResponse {
  mode: string;
  engine_info: EngineInfo;
  rule_strategy?: string;
}

export interface EngineCapabilitiesResponse {
  available_engines: EngineInfo[];
  current_mode: string;
}

// Portfolio types
export interface Position {
  symbol: string;
  quantity: number;
  avg_entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface PortfolioSnapshot {
  cash_balance: number;
  total_equity: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_return_pct: number;
}

export interface PortfolioResponse {
  positions: Position[];
  summary: PortfolioSnapshot;
}

// Trade types
export interface Trade {
  id: number;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  timestamp: string;
  pnl?: number;
  run_id: string;
}

export interface TradesResponse {
  trades: Trade[];
  total: number;
}

// Backtest types (Phase 6 - Unified)
export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  timeframe?: string;
  initial_capital?: number;
  engine_type?: string;  // "llm" | "vectorbt"
  strategy?: string;     // For VectorBT: "rsi_macd" | "ema_crossover" | "bb_volume"
  max_decisions?: number; // For LLM: limit decision count to control costs
}

export interface BacktestMetrics {
  total_return: number;
  total_return_pct: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio?: number | null;
  sortino_ratio?: number | null;
  win_rate: number;
  num_trades: number;
  avg_trade_return: number;
  best_trade: number;
  worst_trade: number;
  profit_factor?: number | null;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  cash: number;
  positions_value: number;
}

export interface BacktestTrade {
  timestamp: string;
  side: string;
  quantity: number;
  price: number;
  pnl: number;
}

export interface BacktestResult {
  run_id: string;
  symbol: string;
  start_date: string;
  end_date: string;
  timeframe: string;
  initial_capital: number;
  final_equity: number;
  metrics: BacktestMetrics;
  equity_curve: EquityPoint[];
  trades: BacktestTrade[];
  engine_type: string;
  strategy_name?: string;
  execution_time_ms: number;
}

export interface BacktestResponse {
  result: BacktestResult;
}
