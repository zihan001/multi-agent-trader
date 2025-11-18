"""
Tests for API routes (analysis and backtest endpoints).
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import AgentLog, BacktestRun, Trade


client = TestClient(app)


@pytest.fixture
def mock_binance_client():
    """Mock Binance service responses."""
    with patch('app.routes.analysis.BinanceService') as mock:
        mock_instance = Mock()
        mock_instance.fetch_klines = AsyncMock(return_value=[
            [1704067200000, "50000", "50100", "49900", "50050", "100"],
            [1704070800000, "50050", "50200", "50000", "50150", "105"],
        ])
        mock_instance.fetch_24h_ticker = AsyncMock(return_value={
            "priceChangePercent": "2.5",
            "volume": "1000000"
        })
        mock_instance.close = AsyncMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_pipeline():
    """Mock AgentPipeline responses."""
    with patch('app.routes.analysis.AgentPipeline') as mock:
        mock_instance = Mock()
        mock_instance.arun = AsyncMock(return_value={
            "run_id": "test_run_123",
            "symbol": "BTCUSDT",
            "timestamp": "2024-01-01T00:00:00",
            "status": "completed",
            "agents": {
                "technical": {"analysis": {"trend": "uptrend"}},
                "sentiment": {"analysis": {"sentiment": "bullish"}},
                "tokenomics": {"analysis": {"outlook": "positive"}},
                "researcher": {"analysis": {"thesis": "bullish"}},
                "trader": {"analysis": {"action": "BUY"}},
                "risk_manager": {"analysis": {"decision": "APPROVE"}},
            },
            "final_decision": {
                "action": "BUY",
                "quantity": 0.01,
                "size_pct": 0.05,
            },
            "total_cost": 0.05,
            "total_tokens": 5000,
            "errors": [],
        })
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_portfolio_manager():
    """Mock PortfolioManager responses."""
    with patch('app.routes.analysis.PortfolioManager') as mock:
        mock_instance = Mock()
        mock_instance.get_portfolio_state.return_value = {
            "cash_balance": 10000.0,
            "total_equity": 10000.0,
            "positions": [],
        }
        mock_instance.execute_trade = Mock()
        mock.return_value = mock_instance
        yield mock


class TestAnalyzeEndpoint:
    """Tests for POST /analyze endpoint."""
    
    def test_analyze_success(self, mock_binance_client, mock_pipeline, mock_portfolio_manager):
        """Test successful analysis request."""
        with patch('app.routes.analysis.get_latest_candles', return_value=[]):
            with patch('app.routes.analysis.IndicatorService') as mock_indicator:
                mock_indicator.return_value.calculate_all_indicators.return_value = {
                    "rsi_14": 55.0,
                    "ema_21": 49900.0,
                }
                
                response = client.post("/analyze", json={
                    "symbol": "BTCUSDT",
                    "mode": "live",
                    "timeframe": "1h"
                })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "BTCUSDT"
        assert data["status"] == "completed"
        assert "agents" in data
        assert "final_decision" in data
        assert data["final_decision"]["action"] == "BUY"
        assert "portfolio_snapshot" in data
    
    def test_analyze_invalid_symbol(self):
        """Test analysis with missing symbol."""
        response = client.post("/analyze", json={
            "mode": "live"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_hold_decision(self, mock_binance_client, mock_portfolio_manager):
        """Test analysis when decision is HOLD (no trade execution)."""
        with patch('app.routes.analysis.get_latest_candles', return_value=[]):
            with patch('app.routes.analysis.IndicatorService'):
                with patch('app.routes.analysis.AgentPipeline') as mock_pipeline:
                    mock_instance = Mock()
                    mock_instance.arun = AsyncMock(return_value={
                        "run_id": "test_run_123",
                        "symbol": "BTCUSDT",
                        "timestamp": "2024-01-01T00:00:00",
                        "status": "completed",
                        "agents": {},
                        "final_decision": {"action": "HOLD"},
                        "total_cost": 0.02,
                        "total_tokens": 3000,
                        "errors": [],
                    })
                    mock_pipeline.return_value = mock_instance
                    
                    response = client.post("/analyze", json={
                        "symbol": "BTCUSDT"
                    })
        
        assert response.status_code == 200
        data = response.json()
        assert data["final_decision"]["action"] == "HOLD"
    
    def test_analyze_trade_execution_error(self, mock_binance_client, mock_pipeline):
        """Test analysis when trade execution fails."""
        with patch('app.routes.analysis.get_latest_candles', return_value=[]):
            with patch('app.routes.analysis.IndicatorService'):
                with patch('app.routes.analysis.PortfolioManager') as mock_pm:
                    mock_instance = Mock()
                    mock_instance.get_portfolio_state.return_value = {
                        "cash_balance": 10000.0,
                        "total_equity": 10000.0,
                        "positions": [],
                    }
                    mock_instance.execute_trade.side_effect = Exception("Insufficient funds")
                    mock_pm.return_value = mock_instance
                    
                    response = client.post("/analyze", json={
                        "symbol": "BTCUSDT"
                    })
        
        assert response.status_code == 200
        data = response.json()
        # Should still return results but with error recorded
        assert len(data["errors"]) > 0
        assert any(e["type"] == "trade_execution_error" for e in data["errors"])


class TestBacktestEndpoint:
    """Tests for backtest endpoints."""
    
    @patch('app.routes.backtest.BacktestEngine')
    def test_backtest_success(self, mock_engine):
        """Test successful backtest request."""
        mock_instance = Mock()
        mock_instance.run_backtest.return_value = {
            "run_id": "backtest_BTCUSDT_2024-01-01_2024-01-05_123",
            "symbol": "BTCUSDT",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-05T00:00:00",
            "metrics": {
                "total_return_pct": 15.5,
                "max_drawdown_pct": -5.2,
                "sharpe_ratio": 1.8,
                "win_rate_pct": 65.0,
                "num_trades": 10,
                "avg_trade_pnl": 150.0,
                "final_equity": 11550.0,
            },
            "equity_curve": [
                {"timestamp": "2024-01-01T00:00:00", "equity": 10000.0},
                {"timestamp": "2024-01-05T00:00:00", "equity": 11550.0},
            ],
            "trades": [],
            "final_portfolio": {
                "cash": 11550.0,
                "positions": {},
                "equity": 11550.0,
            },
        }
        mock_engine.return_value = mock_instance
        
        response = client.post("/backtest", json={
            "symbol": "BTCUSDT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-05",
            "timeframe": "1h",
            "initial_cash": 10000.0,
            "decision_frequency": 4,
            "max_decisions": 50
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "BTCUSDT"
        assert data["metrics"]["total_return_pct"] == 15.5
        assert data["metrics"]["num_trades"] == 10
        assert len(data["equity_curve"]) == 2
    
    def test_backtest_invalid_dates(self):
        """Test backtest with invalid date range."""
        response = client.post("/backtest", json={
            "symbol": "BTCUSDT",
            "start_date": "2024-01-05",
            "end_date": "2024-01-01",  # End before start
        })
        
        assert response.status_code == 400
        assert "start_date must be before end_date" in response.json()["detail"]
    
    def test_backtest_missing_required_fields(self):
        """Test backtest with missing required fields."""
        response = client.post("/backtest", json={
            "symbol": "BTCUSDT",
            # Missing start_date and end_date
        })
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.routes.backtest.BacktestEngine')
    def test_backtest_with_max_decisions(self, mock_engine):
        """Test backtest respects max_decisions limit."""
        mock_instance = Mock()
        mock_instance.run_backtest.return_value = {
            "run_id": "test_run",
            "symbol": "BTCUSDT",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-31T00:00:00",
            "metrics": {
                "total_return_pct": 5.0,
                "max_drawdown_pct": -2.0,
                "sharpe_ratio": 1.2,
                "win_rate_pct": 55.0,
                "num_trades": 5,  # Should stop at max_decisions
                "avg_trade_pnl": 100.0,
                "final_equity": 10500.0,
            },
            "equity_curve": [],
            "trades": [],
            "final_portfolio": {},
        }
        mock_engine.return_value = mock_instance
        
        response = client.post("/backtest", json={
            "symbol": "BTCUSDT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "max_decisions": 5
        })
        
        assert response.status_code == 200
        # Verify max_decisions was passed to engine
        mock_instance.run_backtest.assert_called_once()
        call_kwargs = mock_instance.run_backtest.call_args.kwargs
        assert call_kwargs["max_decisions"] == 5


class TestBacktestListEndpoint:
    """Tests for GET /backtest/runs endpoint."""
    
    @patch('app.routes.backtest.BacktestRun')
    def test_list_backtest_runs(self, mock_run_model):
        """Test listing backtest runs."""
        # This would need database fixtures for proper testing
        # Placeholder for now
        pass


class TestGetAnalysisStatus:
    """Tests for GET /analyze/status/{run_id} endpoint."""
    
    @patch('app.models.database.AgentLog')
    def test_get_analysis_status_success(self, mock_log_model):
        """Test getting status of an analysis run."""
        # Mock database query
        mock_log1 = Mock()
        mock_log1.agent_name = "technical"
        mock_log1.tokens_used = 1000
        mock_log1.cost = 0.01
        mock_log1.timestamp = datetime(2024, 1, 1)
        mock_log1.model = "gpt-4o-mini"
        
        with patch('app.core.database.get_db'):
            # Would need proper database mocking
            pass


class TestIndicatorService:
    """Tests for IndicatorService."""
    
    def test_calculate_all_indicators(self):
        """Test indicator calculation with valid DataFrame."""
        import pandas as pd
        from app.services.indicators import IndicatorService
        
        # Create sample data
        df = pd.DataFrame({
            'open': [50000 + i * 10 for i in range(100)],
            'high': [50100 + i * 10 for i in range(100)],
            'low': [49900 + i * 10 for i in range(100)],
            'close': [50050 + i * 10 for i in range(100)],
            'volume': [1000 + i for i in range(100)],
        })
        
        service = IndicatorService()
        indicators = service.calculate_all_indicators(df)
        
        # Check required indicators are present
        assert 'current_price' in indicators
        assert 'rsi_14' in indicators
        assert 'ema_21' in indicators
        assert 'macd' in indicators
        assert 'trend' in indicators
        assert 'momentum' in indicators
        
        # Check values are reasonable
        assert isinstance(indicators['rsi_14'], (float, type(None)))
        assert indicators['trend'] in ['uptrend', 'downtrend', 'sideways']
        assert indicators['momentum'] in ['strong', 'moderate', 'weak']
    
    def test_calculate_indicators_insufficient_data(self):
        """Test indicator calculation with insufficient data."""
        import pandas as pd
        from app.services.indicators import IndicatorService
        
        # Create minimal data (15 rows - just enough for ATR but not ideal for all indicators)
        df = pd.DataFrame({
            'open': [50000 + i * 10 for i in range(15)],
            'high': [50100 + i * 10 for i in range(15)],
            'low': [49900 + i * 10 for i in range(15)],
            'close': [50050 + i * 10 for i in range(15)],
            'volume': [1000 + i for i in range(15)],
        })
        
        service = IndicatorService()
        indicators = service.calculate_all_indicators(df)
        
        # Should still return structure but with None values where needed
        assert 'current_price' in indicators
        assert indicators['current_price'] is not None


class TestBinanceServiceEnhancements:
    """Tests for BinanceService new methods."""
    
    def test_fetch_klines_sync(self):
        """Test synchronous kline fetching."""
        from app.services.binance import BinanceService
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = [
            [1704067200000, "50000", "50100", "49900", "50050", "100"],
        ]
        mock_response.raise_for_status = Mock()
        
        # Create mock clients
        mock_sync_client = Mock()
        mock_sync_client.get.return_value = mock_response
        mock_async_client = Mock()
        
        # Test the actual service with mocked HTTP layer
        service = BinanceService(async_client=mock_async_client, sync_client=mock_sync_client)
        result = service.fetch_klines_sync("BTCUSDT", "1h", 10)
        
        # Verify the service called the client correctly
        mock_sync_client.get.assert_called_once()
        call_args = mock_sync_client.get.call_args
        assert call_args[0][0].endswith("/api/v3/klines")
        assert call_args[1]["params"]["symbol"] == "BTCUSDT"
        
        # Verify the result
        assert len(result) == 1
        assert result[0][1] == "50000"  # Open price
    
    def test_binance_service_get_historical_klines(self):
        """Test BinanceService historical klines fetching."""
        from app.services.binance import BinanceService
        from datetime import datetime
        
        # Mock response - timestamp must be AFTER end_date to break the loop
        # Jan 1, 2024 00:00:00 to Jan 2, 2024 00:00:00
        # end_ms = 1704153600000 (Jan 2, 2024)
        # So we return a timestamp >= end_ms to terminate the while loop
        mock_response = Mock()
        mock_response.json.return_value = [
            [1704153600000, "50000", "50100", "49900", "50050", "100"],  # Jan 2, 2024 - at end_date
        ]
        mock_response.raise_for_status = Mock()
        
        # Create mock clients
        mock_sync_client = Mock()
        mock_sync_client.get.return_value = mock_response
        mock_async_client = Mock()
        
        # Test the actual service logic
        service = BinanceService(async_client=mock_async_client, sync_client=mock_sync_client)
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 2)
        
        result = service.get_historical_klines("BTCUSDT", "1h", start, end)
        
        # Verify the service called fetch_klines_sync internally
        assert mock_sync_client.get.called
        
        # Verify the result is properly formatted
        assert len(result) > 0
        assert "timestamp" in result[0]
        assert "open" in result[0]
        assert "close" in result[0]
        assert result[0]["open"] == 50000.0
        assert result[0]["close"] == 50050.0
