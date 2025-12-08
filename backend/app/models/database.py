"""
Database models for the trading simulator.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Candle(Base):
    """OHLCV candlestick data."""
    __tablename__ = "candles"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('idx_symbol_timestamp_timeframe', 'symbol', 'timestamp', 'timeframe', unique=True),
    )


class Trade(Base):
    """Executed trades."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    pnl = Column(Float, nullable=True)  # Realized PnL, null until position closed
    run_id = Column(String(50), nullable=False, index=True)  # For grouping backtest vs live


class Position(Base):
    """Current open positions."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    quantity = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PortfolioSnapshot(Base):
    """Portfolio state snapshots over time."""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    total_equity = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    run_id = Column(String(50), nullable=False, index=True)


class AgentLog(Base):
    """Logs of agent LLM calls and decisions."""
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    agent_name = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=True)  # Model name (null for rule-based)
    input_data = Column(Text, nullable=True)  # Full input (JSON string)
    output_data = Column(Text, nullable=True)  # Full output or error message
    tokens_used = Column(Integer, default=0)  # Total tokens (0 for rule-based)
    input_tokens = Column(Integer, nullable=True)  # Input tokens
    output_tokens = Column(Integer, nullable=True)  # Output tokens
    cost = Column(Float, default=0.0)  # Cost in USD (0 for rule-based)
    latency_seconds = Column(Float, nullable=True)  # API call latency
    run_id = Column(String(50), nullable=True, index=True)  # Optional grouping
    symbol = Column(String(20), nullable=True, index=True)  # Optional symbol context
    
    # Phase 6: Engine type tracking
    decision_type = Column(String(20), nullable=True, index=True)  # "llm", "rule", "hybrid", etc.
    strategy_name = Column(String(50), nullable=True)  # Strategy name for rule-based engines


class BacktestRun(Base):
    """Backtest execution metadata and results."""
    __tablename__ = "backtest_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), nullable=False, unique=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    timeframe = Column(String(10), nullable=False)
    initial_cash = Column(Float, nullable=False)
    decision_frequency = Column(Integer, nullable=False)  # Run pipeline every N candles
    max_decisions = Column(Integer, nullable=True)  # Optional cap on decisions
    status = Column(String(20), nullable=False, index=True)  # running, completed, failed
    final_equity = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)  # Return percentage
    max_drawdown = Column(Float, nullable=True)  # Max drawdown percentage
    num_trades = Column(Integer, nullable=True)
    num_decisions = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class PaperOrder(Base):
    """Paper trading orders with realistic execution simulation."""
    __tablename__ = "paper_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY or SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # Limit price (for LIMIT orders)
    stop_price = Column(Float, nullable=True)  # Stop price (for STOP_LOSS/TAKE_PROFIT)
    filled_quantity = Column(Float, default=0.0)
    avg_fill_price = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # PENDING, FILLED, CANCELLED, etc.
    time_in_force = Column(String(10), default="GTC")  # GTC, IOC, FOK
    run_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    binance_order_id = Column(Integer, nullable=True)  # Binance Testnet order ID (if using testnet)
    
    __table_args__ = (
        Index('idx_paper_orders_status_symbol', 'status', 'symbol'),
        Index('idx_paper_orders_run_created', 'run_id', 'created_at'),
    )


class AgentRecommendation(Base):
    """AI agent trading recommendations (not auto-executed)."""
    __tablename__ = "agent_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    quantity = Column(Float, nullable=True)  # Recommended quantity
    price = Column(Float, nullable=False)  # Market price at recommendation time
    confidence = Column(Float, nullable=True)  # Agent confidence score
    reasoning = Column(Text, nullable=True)  # Combined agent reasoning
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, executed, rejected, expired
    decision_type = Column(String(20), nullable=False)  # llm or rule
    strategy_name = Column(String(50), nullable=True)  # For rule-based strategies
    executed_order_id = Column(Integer, nullable=True)  # Link to PaperOrder if executed
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    __table_args__ = (
        Index('idx_recommendations_status_symbol', 'status', 'symbol'),
        Index('idx_recommendations_run_created', 'run_id', 'created_at'),
    )
