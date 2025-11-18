"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_get_supported_symbols(client):
    """Test getting supported symbols."""
    response = client.get("/market/symbols")
    assert response.status_code == 200
    symbols = response.json()
    assert isinstance(symbols, list)
    assert "BTCUSDT" in symbols
    assert "ETHUSDT" in symbols


def test_get_supported_timeframes(client):
    """Test getting supported timeframes."""
    response = client.get("/market/timeframes")
    assert response.status_code == 200
    timeframes = response.json()
    assert isinstance(timeframes, list)
    assert "1h" in timeframes
    assert "1d" in timeframes


def test_initialize_portfolio(client):
    """Test portfolio initialization."""
    response = client.post("/portfolio/initialize?run_id=test")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "test"
    assert "initialized successfully" in data["message"]


def test_get_portfolio(client):
    """Test getting portfolio state."""
    # Initialize first
    client.post("/portfolio/initialize?run_id=test")
    
    response = client.get("/portfolio?run_id=test")
    assert response.status_code == 200
    data = response.json()
    
    assert data["run_id"] == "test"
    assert "cash_balance" in data
    assert "total_equity" in data
    assert "positions" in data
    assert data["num_positions"] == 0


def test_execute_trade(client):
    """Test executing a trade."""
    # Initialize portfolio
    client.post("/portfolio/initialize?run_id=test")
    
    # Execute buy trade
    trade_data = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.01,
        "price": 50000.0
    }
    
    response = client.post("/portfolio/trade?run_id=test", json=trade_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "trade" in data
    assert "portfolio" in data
    assert data["trade"]["symbol"] == "BTCUSDT"
    assert data["trade"]["side"] == "BUY"
    assert data["portfolio"]["num_positions"] == 1


def test_get_positions(client):
    """Test getting positions."""
    # Initialize and execute a trade
    client.post("/portfolio/initialize?run_id=test")
    trade_data = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.01,
        "price": 50000.0
    }
    client.post("/portfolio/trade?run_id=test", json=trade_data)
    
    response = client.get("/portfolio/positions?run_id=test")
    assert response.status_code == 200
    positions = response.json()
    
    assert len(positions) == 1
    assert positions[0]["symbol"] == "BTCUSDT"
    assert positions[0]["quantity"] == 0.01


def test_get_trades(client):
    """Test getting trade history."""
    # Initialize and execute trades
    client.post("/portfolio/initialize?run_id=test")
    client.post("/portfolio/trade?run_id=test", json={
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.01,
        "price": 50000.0
    })
    
    response = client.get("/portfolio/trades?run_id=test")
    assert response.status_code == 200
    trades = response.json()
    
    assert len(trades) >= 1
    assert trades[0]["symbol"] == "BTCUSDT"


def test_invalid_trade_side(client):
    """Test that invalid trade side is rejected."""
    client.post("/portfolio/initialize?run_id=test")
    
    trade_data = {
        "symbol": "BTCUSDT",
        "side": "INVALID",
        "quantity": 0.01,
        "price": 50000.0
    }
    
    response = client.post("/portfolio/trade?run_id=test", json=trade_data)
    assert response.status_code == 400


def test_risk_limit_rejection(client):
    """Test that trades violating risk limits are rejected."""
    client.post("/portfolio/initialize?run_id=test")
    
    # Try to buy too much (exceeds position size limit)
    trade_data = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.5,  # Way too much for 10k portfolio
        "price": 50000.0
    }
    
    response = client.post("/portfolio/trade?run_id=test", json=trade_data)
    assert response.status_code == 400
    assert "rejected" in response.json()["detail"].lower()


def test_openapi_schema(client):
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
