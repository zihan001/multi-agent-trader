"""
Tests for portfolio management service.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.database import Trade, Position, PortfolioSnapshot
from app.services.portfolio import PortfolioManager, initialize_portfolio
from app.core.config import settings


@pytest.fixture
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def portfolio_manager(db_session):
    """Create a portfolio manager with initialized portfolio."""
    initialize_portfolio(db_session, run_id="test")
    return PortfolioManager(db_session, run_id="test")


def test_initialize_portfolio(db_session):
    """Test portfolio initialization."""
    initialize_portfolio(db_session, run_id="test_init")
    
    snapshot = db_session.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.run_id == "test_init"
    ).first()
    
    assert snapshot is not None
    assert snapshot.cash_balance == settings.initial_cash
    assert snapshot.total_equity == settings.initial_cash


def test_get_cash_balance(portfolio_manager):
    """Test getting cash balance."""
    cash = portfolio_manager.get_cash_balance()
    assert cash == settings.initial_cash


def test_execute_buy_trade(portfolio_manager):
    """Test executing a buy trade."""
    trade = portfolio_manager.execute_trade(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.01,
        price=50000.0
    )
    
    assert trade.symbol == "BTCUSDT"
    assert trade.side == "BUY"
    assert trade.quantity == 0.01
    assert trade.price == 50000.0
    assert trade.pnl == 0.0  # No PnL on entry
    
    # Check cash was deducted
    cash = portfolio_manager.get_cash_balance()
    assert cash == settings.initial_cash - 500.0
    
    # Check position was created
    position = portfolio_manager.get_position("BTCUSDT")
    assert position is not None
    assert position.quantity == 0.01
    assert position.avg_entry_price == 50000.0


def test_execute_sell_trade(portfolio_manager):
    """Test executing a sell trade with PnL."""
    # First buy
    portfolio_manager.execute_trade("BTCUSDT", "BUY", 0.01, 50000.0)
    
    # Then sell at higher price
    trade = portfolio_manager.execute_trade("BTCUSDT", "SELL", 0.005, 52000.0)
    
    assert trade.side == "SELL"
    assert trade.quantity == 0.005
    assert trade.pnl > 0  # Profit
    expected_pnl = (52000.0 - 50000.0) * 0.005
    assert abs(trade.pnl - expected_pnl) < 0.01
    
    # Check position was reduced
    position = portfolio_manager.get_position("BTCUSDT")
    assert position.quantity == 0.005


def test_insufficient_funds(portfolio_manager):
    """Test that trade is rejected with insufficient funds."""
    with pytest.raises(ValueError, match="Insufficient cash"):
        portfolio_manager.execute_trade(
            symbol="BTCUSDT",
            side="BUY",
            quantity=1.0,  # Too much
            price=50000.0
        )


def test_insufficient_position(portfolio_manager):
    """Test that sell is rejected with insufficient position."""
    with pytest.raises(ValueError, match="Insufficient position"):
        portfolio_manager.execute_trade(
            symbol="BTCUSDT",
            side="SELL",
            quantity=0.01,
            price=50000.0
        )


def test_risk_limits_position_size(portfolio_manager):
    """Test max position size limit."""
    is_valid, reason = portfolio_manager.check_risk_limits(
        symbol="BTCUSDT",
        side="BUY",
        proposed_value=2000.0  # 20% of 10000 initial cash
    )
    
    assert not is_valid
    assert "max position size" in reason.lower()


def test_risk_limits_within_limits(portfolio_manager):
    """Test trade within risk limits."""
    is_valid, reason = portfolio_manager.check_risk_limits(
        symbol="BTCUSDT",
        side="BUY",
        proposed_value=500.0  # 5% of equity, within 10% limit
    )
    
    assert is_valid


def test_portfolio_summary(portfolio_manager):
    """Test portfolio summary generation."""
    # Execute some trades
    portfolio_manager.execute_trade("BTCUSDT", "BUY", 0.01, 50000.0)
    portfolio_manager.execute_trade("ETHUSDT", "BUY", 0.1, 3000.0)
    
    summary = portfolio_manager.get_portfolio_summary()
    
    assert summary['run_id'] == "test"
    assert summary['num_positions'] == 2
    assert summary['cash_balance'] < settings.initial_cash
    assert len(summary['positions']) == 2


def test_trade_history(portfolio_manager):
    """Test trade history retrieval."""
    portfolio_manager.execute_trade("BTCUSDT", "BUY", 0.01, 50000.0)
    portfolio_manager.execute_trade("ETHUSDT", "BUY", 0.1, 3000.0)
    
    trades = portfolio_manager.get_trade_history(limit=10)
    
    assert len(trades) == 2
    assert trades[0]['symbol'] in ['BTCUSDT', 'ETHUSDT']


def test_update_unrealized_pnl(portfolio_manager):
    """Test updating unrealized PnL."""
    # Buy at 50000
    portfolio_manager.execute_trade("BTCUSDT", "BUY", 0.01, 50000.0)
    
    # Update price to 55000
    portfolio_manager.update_unrealized_pnl("BTCUSDT", 55000.0)
    
    position = portfolio_manager.get_position("BTCUSDT")
    expected_pnl = (55000.0 - 50000.0) * 0.01
    assert abs(position.unrealized_pnl - expected_pnl) < 0.01


def test_close_position_completely(portfolio_manager):
    """Test closing a position completely."""
    # Buy
    portfolio_manager.execute_trade("BTCUSDT", "BUY", 0.01, 50000.0)
    
    # Sell all
    portfolio_manager.execute_trade("BTCUSDT", "SELL", 0.01, 52000.0)
    
    # Position should be removed
    position = portfolio_manager.get_position("BTCUSDT")
    assert position is None


def test_average_entry_price(portfolio_manager):
    """Test average entry price calculation with multiple buys."""
    # First buy
    portfolio_manager.execute_trade("BTCUSDT", "BUY", 0.01, 50000.0)
    
    # Second buy at different price
    portfolio_manager.execute_trade("BTCUSDT", "BUY", 0.01, 52000.0)
    
    position = portfolio_manager.get_position("BTCUSDT")
    expected_avg = (50000.0 + 52000.0) / 2
    assert abs(position.avg_entry_price - expected_avg) < 0.01
    assert position.quantity == 0.02
