# AI Multi-Agent Crypto Trading Simulator — Architecture

## System Overview

This is a portfolio demonstration project that simulates a crypto trading firm powered by multiple AI agents. The system fetches real market data from Binance, analyzes it through specialized LLM agents, and executes simulated trades.

## Architecture Components

### Backend (FastAPI + Python)

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core configuration and database
│   │   ├── config.py        # Settings management
│   │   └── database.py      # SQLAlchemy setup
│   ├── models/              # Database models
│   │   └── database.py      # Candles, Trades, Positions, etc.
│   ├── routes/              # API endpoints (to be implemented)
│   │   ├── market.py        # Market data endpoints
│   │   ├── portfolio.py     # Portfolio management
│   │   ├── analysis.py      # Trading analysis
│   │   └── backtest.py      # Backtesting
│   ├── services/            # Business logic (to be implemented)
│   │   ├── binance.py       # Binance API client
│   │   ├── portfolio.py     # Portfolio management
│   │   └── indicators.py    # Technical indicators
│   └── agents/              # LLM agents (to be implemented)
│       ├── llm_client.py    # LLM integration wrapper
│       ├── technical.py     # Technical analyst
│       ├── sentiment.py     # Sentiment analyst
│       ├── tokenomics.py    # Tokenomics analyst
│       ├── researcher.py    # Researcher synthesizer
│       ├── trader.py        # Trading decision maker
│       └── risk.py          # Risk manager
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── Dockerfile               # Backend container
└── alembic.ini             # Alembic configuration
```

### Database (PostgreSQL)

Tables:
- `candles` - OHLCV market data
- `trades` - Executed trades (simulated)
- `positions` - Current open positions
- `portfolio_snapshots` - Portfolio state over time
- `agent_logs` - LLM call logs and costs

### Multi-Agent Decision Pipeline

```
Market Data → Technical Analyst ─┐
             Sentiment Analyst   ├─→ Researcher → Trader → Risk Manager → Decision
             Tokenomics Analyst ─┘
```

**Agent Roles:**
1. **Technical Analyst** - Analyzes price action, indicators (RSI, MACD, EMAs)
2. **Sentiment Analyst** - Evaluates market sentiment (mock data initially)
3. **Tokenomics Analyst** - Assesses fundamental token metrics
4. **Researcher** - Synthesizes all analysis into unified thesis
5. **Trader** - Proposes trades based on thesis
6. **Risk Manager** - Validates and adjusts trades per risk rules

**Model Strategy:**
- Cheap model (GPT-3.5) for analysts
- Strong model (GPT-4) for researcher, trader, risk manager
- Cost tracking and daily budget enforcement

### External Services

- **Binance Public API** - Real-time and historical market data (no authentication required)
- **OpenAI/OpenRouter API** - LLM providers for agent reasoning

## Deployment Architecture (AWS)

```
┌─────────────────┐
│   CloudFront    │  (Optional: Frontend CDN)
└────────┬────────┘
         │
┌────────▼────────┐
│   S3 Bucket     │  Frontend (React/Next.js)
└─────────────────┘
         │
         │ API Calls
         │
┌────────▼────────┐
│      ALB        │  Application Load Balancer
└────────┬────────┘
         │
┌────────▼────────┐
│  ECS Fargate    │  Backend (FastAPI container)
│  or EC2         │
└────────┬────────┘
         │
┌────────▼────────┐
│  RDS Postgres   │  Database
└─────────────────┘
         │
┌────────▼────────┐
│ Secrets Manager │  API Keys, DB Credentials
└─────────────────┘
```

### Security
- Environment variables stored in AWS Systems Manager Parameter Store
- No secrets in code or git
- CORS configured for frontend domain
- Private subnets for backend and database

## Data Flow

### Live Analysis
1. User selects symbol and triggers analysis
2. Backend fetches latest OHLCV from Binance
3. Calculates technical indicators
4. Runs agent pipeline
5. Executes approved trade (simulated)
6. Updates portfolio and returns results

### Backtesting
1. User specifies symbol, date range, timeframe
2. Backend loads historical candles from DB (or fetches if missing)
3. Iterates through candles, running agent pipeline
4. Simulates trade execution
5. Calculates performance metrics
6. Returns equity curve and trade history

## Cost Management

- Token usage logged per LLM call
- Daily budget enforced in `LLMClient`
- Concise prompts with structured outputs
- Limited backtest iterations to control costs

## Development Phases

**Phase 1 (Current):** Foundation
- Project structure
- Database models
- Basic FastAPI app
- Docker setup

**Phase 2:** Core Services
- Binance integration
- Portfolio simulation
- Indicator calculations

**Phase 3:** Agent System
- LLM client wrapper
- All six agents
- Decision pipeline orchestration

**Phase 4:** API Completion
- All REST endpoints
- Backtest engine
- Error handling

**Phase 5:** Frontend
- React/Next.js UI
- Dashboard, analysis, portfolio views
- Backtest interface

**Phase 6:** Deployment
- AWS infrastructure
- CI/CD pipeline
- Monitoring and logging
