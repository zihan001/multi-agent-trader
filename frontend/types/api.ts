// Health check
export interface HealthResponse {
  status: string;
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

export interface AnalysisRequest {
  symbol: string;
  mode?: 'live' | 'backtest_step';
  timestamp?: string;
}

export interface AnalysisResponse {
  run_id: string;
  symbol: string;
  timestamp: string;
  status: string;
  agents: {
    technical?: { analysis: TechnicalAnalysis; metadata?: any };
    sentiment?: { analysis: SentimentAnalysis; metadata?: any };
    tokenomics?: { analysis: TokenomicsAnalysis; metadata?: any };
    researcher?: { analysis: ResearcherThesis; metadata?: any };
    trader?: { analysis: TraderDecision; metadata?: any };
    risk_manager?: { analysis: RiskManagerDecision; metadata?: any };
  };
  final_decision: FinalDecision | null;
  total_cost: number;
  total_tokens: number;
  portfolio_snapshot?: PortfolioSnapshot;
  errors?: Array<{ type: string; message: string }>;
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

// Backtest types
export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  timeframe: string;
  max_decisions?: number;
}

export interface BacktestMetrics {
  total_return: number;
  total_return_pct: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  num_trades: number;
  win_rate: number;
  sharpe_ratio?: number;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
}

export interface BacktestResponse {
  run_id: string;
  symbol: string;
  start_date: string;
  end_date: string;
  timeframe: string;
  metrics: BacktestMetrics;
  equity_curve: EquityPoint[];
  trades: Trade[];
}
