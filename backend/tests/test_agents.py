"""
Unit tests for agent system.

Tests all agents with mocked LLM responses.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

from app.agents.llm_client import LLMClient, BudgetExceededError
from app.agents.technical import TechnicalAnalyst
from app.agents.sentiment import SentimentAnalyst
from app.agents.tokenomics import TokenomicsAnalyst
from app.agents.researcher import Researcher
from app.agents.trader import Trader
from app.agents.risk import RiskManager
from app.agents.pipeline import AgentPipeline


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.add = Mock()
    db.commit = Mock()
    return db


@pytest.fixture
def mock_llm_response():
    """Mock successful LLM response."""
    return {
        "content": '{"test": "response"}',
        "finish_reason": "stop",
        "model": "gpt-4o-mini",
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "cost": 0.001,
        "latency": 1.5
    }


class TestLLMClient:
    """Tests for LLM client."""
    
    def test_count_tokens(self, mock_db):
        """Test token counting."""
        client = LLMClient(mock_db)
        text = "This is a test string for token counting."
        tokens = client.count_tokens(text)
        assert isinstance(tokens, int)
        assert tokens > 0
    
    def test_get_today_usage_empty(self, mock_db):
        """Test usage calculation with no logs."""
        client = LLMClient(mock_db)
        usage = client.get_today_usage()
        assert usage["total_tokens"] == 0
        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0
    
    def test_check_budget_within_limit(self, mock_db):
        """Test budget check when within limit."""
        client = LLMClient(mock_db)
        assert client.check_budget(1000) is True
    
    def test_calculate_cost(self, mock_db):
        """Test cost calculation."""
        client = LLMClient(mock_db)
        cost = client.calculate_cost("gpt-4o-mini", 1000, 500)
        assert isinstance(cost, Decimal)
        assert cost > 0
    
    @patch('app.agents.llm_client.OpenAI')
    def test_call_success(self, mock_openai_class, mock_db, mock_llm_response):
        """Test successful LLM call."""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"test": "response"}'
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = LLMClient(mock_db)
        
        messages = [{"role": "user", "content": "Test message"}]
        result = client.call(messages, agent_name="test_agent")
        
        assert result["content"] == '{"test": "response"}'
        assert result["total_tokens"] == 150
        assert "cost" in result
        assert mock_db.add.called
        assert mock_db.commit.called
    
    @patch('app.agents.llm_client.OpenAI')
    def test_call_budget_exceeded(self, mock_openai_class, mock_db):
        """Test LLM call when budget exceeded."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock usage that exceeds budget
        mock_db.query.return_value.filter.return_value.all.return_value = [
            Mock(tokens_used=99000, input_tokens=50000, output_tokens=49000)
        ]
        
        client = LLMClient(mock_db)
        
        messages = [{"role": "user", "content": "Test message"}]
        
        with pytest.raises(BudgetExceededError):
            client.call(messages, agent_name="test_agent")


class TestTechnicalAnalyst:
    """Tests for Technical Analyst agent."""
    
    def test_build_prompt(self, mock_db):
        """Test prompt building."""
        analyst = TechnicalAnalyst(mock_db)
        context = {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "current_price": 50000,
            "candles": [
                {"open": 49000, "high": 50500, "low": 48900, "close": 50000, "volume": 1000}
            ],
            "indicators": {"rsi": 55, "macd": 100}
        }
        
        messages = analyst.build_prompt(context)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "BTCUSDT" in messages[1]["content"]
        assert "50000" in messages[1]["content"]
    
    def test_parse_response_valid(self, mock_db):
        """Test parsing valid JSON response."""
        analyst = TechnicalAnalyst(mock_db)
        response = json.dumps({
            "trend": "bullish",
            "strength": "strong",
            "key_levels": {"support": [49000], "resistance": [51000]},
            "indicators_summary": {"rsi": "neutral", "macd": "bullish", "emas": "above"},
            "momentum": "increasing",
            "volume_analysis": "high volume",
            "key_observations": ["Strong uptrend"],
            "recommendation": "buy",
            "confidence": 75,
            "reasoning": "Strong technical setup"
        })
        
        result = analyst.parse_response(response)
        
        assert result["trend"] == "bullish"
        assert result["confidence"] == 75
        assert "parse_error" not in result
    
    def test_parse_response_invalid(self, mock_db):
        """Test parsing invalid JSON response."""
        analyst = TechnicalAnalyst(mock_db)
        response = "This is not valid JSON"
        
        result = analyst.parse_response(response)
        
        assert result["trend"] == "unknown"
        assert result["confidence"] == 0
        assert result["parse_error"] is True


class TestSentimentAnalyst:
    """Tests for Sentiment Analyst agent."""
    
    def test_build_prompt(self, mock_db):
        """Test prompt building."""
        analyst = SentimentAnalyst(mock_db)
        context = {
            "symbol": "BTCUSDT",
            "current_price": 50000,
            "price_change_24h": 5.2,
            "sentiment_data": {"social_mentions": "high", "news_tone": "positive"}
        }
        
        messages = analyst.build_prompt(context)
        
        assert len(messages) == 2
        assert "BTCUSDT" in messages[1]["content"]
        assert "+5.20%" in messages[1]["content"]
    
    def test_parse_response_valid(self, mock_db):
        """Test parsing valid sentiment response."""
        analyst = SentimentAnalyst(mock_db)
        response = json.dumps({
            "overall_sentiment": "bullish",
            "sentiment_score": 60,
            "sentiment_strength": "moderate",
            "key_factors": {},
            "contrarian_signals": [],
            "crowd_psychology": "optimistic",
            "sentiment_trend": "improving",
            "key_observations": ["Positive news"],
            "trading_implication": "buy",
            "confidence": 70,
            "reasoning": "Strong positive sentiment"
        })
        
        result = analyst.parse_response(response)
        
        assert result["overall_sentiment"] == "bullish"
        assert result["sentiment_score"] == 60
        assert "parse_error" not in result


class TestTokenomicsAnalyst:
    """Tests for Tokenomics Analyst agent."""
    
    def test_build_prompt(self, mock_db):
        """Test prompt building."""
        analyst = TokenomicsAnalyst(mock_db)
        context = {
            "symbol": "BTCUSDT",
            "current_price": 50000,
            "market_cap": 1000000000,
            "volume_24h": 50000000,
            "token_data": {"total_supply": "21M", "circulating_supply": "19M"}
        }
        
        messages = analyst.build_prompt(context)
        
        assert len(messages) == 2
        assert "1,000,000,000" in messages[1]["content"]
        assert "5.00%" in messages[1]["content"]  # volume/mcap ratio
    
    def test_parse_response_valid(self, mock_db):
        """Test parsing valid tokenomics response."""
        analyst = TokenomicsAnalyst(mock_db)
        response = json.dumps({
            "fundamental_rating": "good",
            "value_assessment": "fairly_valued",
            "supply_analysis": {},
            "liquidity_analysis": {},
            "utility_assessment": {},
            "competitive_position": "strong",
            "strengths": ["Limited supply"],
            "weaknesses": ["High volatility"],
            "key_risks": ["Regulatory risk"],
            "key_observations": ["Strong fundamentals"],
            "long_term_outlook": "bullish",
            "trading_implication": "buy",
            "confidence": 80,
            "reasoning": "Solid fundamentals"
        })
        
        result = analyst.parse_response(response)
        
        assert result["fundamental_rating"] == "good"
        assert result["confidence"] == 80


class TestResearcher:
    """Tests for Researcher agent."""
    
    def test_build_prompt(self, mock_db):
        """Test prompt building."""
        researcher = Researcher(mock_db)
        context = {
            "symbol": "BTCUSDT",
            "current_price": 50000,
            "technical_analysis": {"trend": "bullish", "confidence": 75},
            "sentiment_analysis": {"overall_sentiment": "bullish", "confidence": 70},
            "tokenomics_analysis": {"fundamental_rating": "good", "confidence": 80}
        }
        
        messages = researcher.build_prompt(context)
        
        assert len(messages) == 2
        assert "bullish" in messages[1]["content"]
    
    def test_parse_response_valid(self, mock_db):
        """Test parsing valid research response."""
        researcher = Researcher(mock_db)
        response = json.dumps({
            "thesis_summary": "Strong buy thesis",
            "market_view": "bullish",
            "conviction_level": "high",
            "time_horizon": "medium_term",
            "analysis_synthesis": {},
            "key_bull_cases": ["Strong technicals"],
            "key_bear_cases": ["High volatility"],
            "signal_conflicts": "None",
            "catalyst_watch": ["Breakout"],
            "risk_factors": ["Market correction"],
            "opportunity_assessment": {},
            "recommended_action": "buy",
            "confidence": 85,
            "reasoning": "All signals align"
        })
        
        result = researcher.parse_response(response)
        
        assert result["market_view"] == "bullish"
        assert result["confidence"] == 85


class TestTrader:
    """Tests for Trader agent."""
    
    def test_build_prompt(self, mock_db):
        """Test prompt building."""
        trader = Trader(mock_db)
        context = {
            "symbol": "BTCUSDT",
            "current_price": 50000,
            "research_thesis": {"recommended_action": "buy", "confidence": 85},
            "portfolio_info": {},
            "available_cash": 10000
        }
        
        messages = trader.build_prompt(context)
        
        assert len(messages) == 2
        assert "10,000" in messages[1]["content"]
    
    def test_parse_response_valid(self, mock_db):
        """Test parsing valid trade proposal."""
        trader = Trader(mock_db)
        response = json.dumps({
            "action": "buy",
            "urgency": "soon",
            "trade_rationale": "Strong setup",
            "entry_strategy": {},
            "position_sizing": {},
            "exit_strategy": {},
            "risk_assessment": {},
            "execution_notes": "Market order",
            "time_horizon": "swing",
            "confidence": 80,
            "reasoning": "Good risk-reward"
        })
        
        result = trader.parse_response(response)
        
        assert result["action"] == "buy"
        assert result["confidence"] == 80
    
    def test_parse_response_invalid_action(self, mock_db):
        """Test parsing with invalid action defaults to hold."""
        trader = Trader(mock_db)
        response = json.dumps({
            "action": "invalid_action",
            "urgency": "soon",
            "trade_rationale": "Test",
            "entry_strategy": {},
            "position_sizing": {},
            "exit_strategy": {},
            "risk_assessment": {},
            "execution_notes": "Test",
            "time_horizon": "swing",
            "confidence": 50,
            "reasoning": "Test"
        })
        
        result = trader.parse_response(response)
        
        assert result["action"] == "hold"


class TestRiskManager:
    """Tests for Risk Manager agent."""
    
    def test_build_prompt(self, mock_db):
        """Test prompt building."""
        risk_mgr = RiskManager(mock_db)
        context = {
            "symbol": "BTCUSDT",
            "current_price": 50000,
            "trade_proposal": {"action": "buy", "position_sizing": {"recommended_size_usd": 1000}},
            "portfolio_info": {},
            "available_cash": 10000,
            "total_equity": 12000,
            "current_positions": []
        }
        
        messages = risk_mgr.build_prompt(context)
        
        assert len(messages) == 2
        assert "10.0%" in messages[0]["content"]  # max position size
        assert "80.0%" in messages[0]["content"]  # max exposure
    
    def test_parse_response_valid(self, mock_db):
        """Test parsing valid risk assessment."""
        risk_mgr = RiskManager(mock_db)
        response = json.dumps({
            "decision": "approved",
            "risk_assessment": {},
            "modifications": {},
            "final_trade": {"action": "buy", "size_usd": 1000},
            "risk_metrics": {},
            "concerns": [],
            "recommendations": [],
            "rejection_reason": None,
            "confidence": 90,
            "reasoning": "Trade meets all criteria"
        })
        
        result = risk_mgr.parse_response(response)
        
        assert result["decision"] == "approved"
        assert result["final_trade"]["action"] == "buy"
    
    def test_parse_response_rejected(self, mock_db):
        """Test parsing rejected trade."""
        risk_mgr = RiskManager(mock_db)
        response = json.dumps({
            "decision": "rejected",
            "risk_assessment": {},
            "modifications": {},
            "final_trade": {"action": "hold", "size_usd": 0},
            "risk_metrics": {},
            "concerns": ["Position too large"],
            "recommendations": ["Reduce size"],
            "rejection_reason": "Exceeds position limit",
            "confidence": 95,
            "reasoning": "Risk limits violated"
        })
        
        result = risk_mgr.parse_response(response)
        
        assert result["decision"] == "rejected"
        assert result["final_trade"]["action"] == "hold"
    
    def test_parse_response_error_defaults_to_reject(self, mock_db):
        """Test parsing error defaults to rejection for safety."""
        risk_mgr = RiskManager(mock_db)
        response = "Invalid JSON"
        
        result = risk_mgr.parse_response(response)
        
        assert result["decision"] == "rejected"
        assert result["final_trade"]["action"] == "hold"
        assert result["parse_error"] is True


class TestAgentPipeline:
    """Tests for Agent Pipeline orchestrator."""
    
    def test_initialization(self, mock_db):
        """Test pipeline initialization."""
        pipeline = AgentPipeline(mock_db)
        
        assert pipeline.technical_analyst is not None
        assert pipeline.sentiment_analyst is not None
        assert pipeline.tokenomics_analyst is not None
        assert pipeline.researcher is not None
        assert pipeline.trader is not None
        assert pipeline.risk_manager is not None
    
    @patch.object(TechnicalAnalyst, 'analyze')
    @patch.object(SentimentAnalyst, 'analyze')
    @patch.object(TokenomicsAnalyst, 'analyze')
    @patch.object(Researcher, 'analyze')
    @patch.object(Trader, 'analyze')
    @patch.object(RiskManager, 'analyze')
    def test_run_success(
        self,
        mock_risk,
        mock_trader,
        mock_researcher,
        mock_tokenomics,
        mock_sentiment,
        mock_technical,
        mock_db
    ):
        """Test successful pipeline run."""
        # Mock all agent responses
        mock_technical.return_value = {
            "agent": "technical",
            "analysis": {"trend": "bullish"},
            "metadata": {"cost": 0.001, "tokens": 100}
        }
        mock_sentiment.return_value = {
            "agent": "sentiment",
            "analysis": {"sentiment_score": 60},
            "metadata": {"cost": 0.001, "tokens": 100}
        }
        mock_tokenomics.return_value = {
            "agent": "tokenomics",
            "analysis": {"fundamental_rating": "good"},
            "metadata": {"cost": 0.001, "tokens": 100}
        }
        mock_researcher.return_value = {
            "agent": "researcher",
            "analysis": {"market_view": "bullish"},
            "metadata": {"cost": 0.002, "tokens": 200}
        }
        mock_trader.return_value = {
            "agent": "trader",
            "analysis": {"action": "buy"},
            "metadata": {"cost": 0.002, "tokens": 200}
        }
        mock_risk.return_value = {
            "agent": "risk_manager",
            "analysis": {
                "decision": "approved",
                "final_trade": {"action": "buy", "size_usd": 1000}
            },
            "metadata": {"cost": 0.002, "tokens": 200}
        }
        
        pipeline = AgentPipeline(mock_db)
        
        market_data = {
            "current_price": 50000,
            "timeframe": "1h",
            "candles": [],
            "indicators": {}
        }
        portfolio_data = {
            "cash_balance": 10000,
            "total_equity": 12000,
            "positions": []
        }
        
        result = pipeline.run("BTCUSDT", market_data, portfolio_data)
        
        assert result["status"] == "completed"
        assert result["symbol"] == "BTCUSDT"
        assert "agents" in result
        assert len(result["agents"]) == 6
        assert result["final_decision"]["action"] == "buy"
        assert abs(result["total_cost"] - 0.009) < 0.0001  # Handle floating point precision
        assert result["total_tokens"] == 900
    
    @patch.object(TechnicalAnalyst, 'analyze')
    def test_run_budget_exceeded(self, mock_technical, mock_db):
        """Test pipeline with budget exceeded."""
        mock_technical.side_effect = BudgetExceededError("Budget exceeded")
        
        pipeline = AgentPipeline(mock_db)
        
        result = pipeline.run("BTCUSDT", {}, {})
        
        assert result["status"] == "failed"
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "budget_exceeded"
