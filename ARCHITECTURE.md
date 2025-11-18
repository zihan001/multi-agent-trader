# AI Multi-Agent Crypto Trading Simulator — Architecture

## System Overview

This is a portfolio demonstration project that simulates a crypto trading firm powered by multiple AI agents. The system fetches real market data from Binance, analyzes it through specialized LLM agents, and executes simulated trades. **All components are fully implemented and operational.**

## Architecture Components

### Backend (FastAPI + Python)

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point with CORS
│   ├── core/                # Core configuration and database
│   │   ├── config.py        # Pydantic settings from environment
│   │   └── database.py      # SQLAlchemy engine and session factory
│   ├── models/              # Database models
│   │   └── database.py      # Candles, Trades, Positions, AgentLogs, etc.
│   ├── routes/              # API endpoints (✅ IMPLEMENTED)
│   │   ├── market.py        # Market data and indicators
│   │   ├── portfolio.py     # Portfolio state and trade history
│   │   ├── analysis.py      # Run agent pipeline for trading decisions
│   │   └── backtest.py      # Historical strategy backtesting
│   ├── services/            # Business logic (✅ IMPLEMENTED)
│   │   ├── binance.py       # Binance API client with caching
│   │   ├── portfolio.py     # Trade execution and position management
│   │   ├── indicators.py    # Technical indicators (RSI, MACD, EMAs)
│   │   └── backtest.py      # Backtesting engine
│   └── agents/              # LLM agents (✅ IMPLEMENTED)
│       ├── base.py          # BaseAgent, AnalystAgent, DecisionAgent
│       ├── llm_client.py    # LLM integration with budget enforcement
│       ├── pipeline.py      # Agent orchestration logic
│       ├── technical.py     # Technical analyst (cheap model)
│       ├── sentiment.py     # Sentiment analyst (cheap model)
│       ├── tokenomics.py    # Tokenomics analyst (cheap model)
│       ├── researcher.py    # Researcher synthesizer (strong model)
│       ├── trader.py        # Trading decision maker (strong model)
│       └── risk.py          # Risk manager (strong model)
├── alembic/                 # Database migrations
│   └── versions/            # Migration scripts
├── tests/                   # Comprehensive test suite
├── requirements.txt         # Python dependencies
├── Dockerfile               # Production container
└── alembic.ini             # Alembic configuration
```

### Frontend (Next.js + TypeScript)

```
frontend/
├── app/
│   ├── page.tsx             # Dashboard with live market data
│   ├── layout.tsx           # Root layout with navigation
│   ├── analysis/
│   │   └── page.tsx         # Agent analysis results viewer
│   ├── portfolio/
│   │   └── page.tsx         # Portfolio positions and trades
│   └── backtest/
│       └── page.tsx         # Backtest interface with charts
├── components/
│   └── Navigation.tsx       # Navigation bar
├── lib/
│   └── api.ts               # Backend API client
├── types/
│   └── api.ts               # TypeScript type definitions
├── Dockerfile               # Production container
└── package.json             # Dependencies (React, Recharts, Tailwind)
```

### Database (PostgreSQL)

**Tables:**
- `candles` - OHLCV market data with symbol/timeframe/timestamp indexes
- `trades` - Executed trades (simulated) with run_id grouping
- `positions` - Current open positions by symbol
- `portfolio_snapshots` - Portfolio state snapshots over time
- `agent_logs` - LLM call logs with tokens, cost, latency tracking
- `backtest_runs` - Backtest metadata and performance metrics

**Key Features:**
- Alembic migrations for schema versioning
- Composite indexes for fast queries (symbol + timestamp)
- Run ID isolation for backtests vs live simulation
- Foreign key constraints for data integrity

### Multi-Agent Decision Pipeline

```
Market Data → [Technical Analyst]   ─┐
              [Sentiment Analyst]    ├─→ Researcher → Trader → Risk Manager → Final Decision
              [Tokenomics Analyst]   ─┘
              (parallel, cheap model)    (sequential, strong model)
```

**Agent Roles:**
1. **Technical Analyst** (`AnalystAgent`) - Analyzes price action, RSI, MACD, EMAs, Bollinger Bands
2. **Sentiment Analyst** (`AnalystAgent`) - Evaluates market sentiment (currently mock data)
3. **Tokenomics Analyst** (`AnalystAgent`) - Assesses fundamental token metrics (mock data)
4. **Researcher** (`DecisionAgent`) - Synthesizes all analyst outputs into unified investment thesis
5. **Trader** (`DecisionAgent`) - Proposes specific trades (symbol, side, quantity) based on thesis
6. **Risk Manager** (`DecisionAgent`) - Validates trades against risk rules, adjusts or rejects

**Execution Strategy:**
- **Phase 1 (Parallel):** All analysts run concurrently with cheap model (`deepseek-chat-v3-0324:free`)
- **Phase 2 (Sequential):** Decision agents run one-by-one with strong model (`kimi-k2-thinking`)
- **Cost Optimization:** Cheap models for high-volume analysis, strong models for critical decisions
- **Budget Enforcement:** Daily token budget checked before every LLM call via `LLMClient`

**Agent Class Hierarchy:**
```python
BaseAgent (abstract)
├── AnalystAgent (uses settings.cheap_model)
│   ├── TechnicalAnalyst
│   ├── SentimentAnalyst
│   └── TokenomicsAnalyst
└── DecisionAgent (uses settings.strong_model)
    ├── Researcher
    ├── Trader
    └── RiskManager
```

**Model Configuration:**
- Cheap model: `deepseek-chat-v3-0324:free` (via OpenRouter)
- Strong model: `kimi-k2-thinking` (via OpenRouter)
- Cost tracking per call with token counts
- All LLM interactions logged to `agent_logs` table

### External Services

- **Binance Public API** - Real-time and historical OHLCV data (no authentication required)
  - Supported symbols: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, ADAUSDT
  - Supported timeframes: 1m, 5m, 15m, 1h, 4h, 1d
  - Cached in database to minimize API calls
  - Rate limiting handled with exponential backoff
  
- **OpenRouter API** - LLM providers for agent reasoning
  - Primary provider for both cheap and strong models
  - Alternative: Direct OpenAI API support
  - Configured via `LLM_PROVIDER` environment variable

## Deployment Architecture

### Current State: Docker Compose (Local/Development)

```
┌─────────────────────────────────────────────────────┐
│                  Docker Network                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   Frontend   │  │   Backend    │  │ Postgres │ │
│  │  (Next.js)   │  │  (FastAPI)   │  │  (DB)    │ │
│  │ Port: 3000   │←─│ Port: 8000   │←─│ Port:    │ │
│  │              │  │              │  │  5432    │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
          ↓                    ↓
    User Browser         Binance API
                         OpenRouter API
```

**Services:**
- `frontend`: Next.js 15 with hot-reload (development) or production build
- `backend`: FastAPI with Uvicorn, auto-reload in dev mode
- `db`: PostgreSQL 16 with persistent volume
- Environment: `.env` file for all configuration
- Networks: Shared Docker network for inter-service communication

### Target State: AWS (Phase 6 - Not Yet Implemented)

```
         Internet
            │
    ┌───────▼────────┐
    │   CloudFront   │  Frontend CDN (optional)
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │   S3 Bucket    │  Static site hosting (Next.js export)
    └────────────────┘
            │
            │ API Calls
            │
    ┌───────▼────────┐
    │      ALB       │  Application Load Balancer
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │  ECS Fargate   │  Backend container (or EC2)
    │  or EC2        │  Auto-scaling based on load
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │  RDS Postgres  │  Managed database (Multi-AZ)
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │Secrets Manager │  API Keys, DB credentials
    └────────────────┘
```

**Planned AWS Components:**
- **Compute:** ECS Fargate for containerized backend (serverless compute)
- **Database:** RDS PostgreSQL with automated backups and Multi-AZ
- **Frontend:** S3 + CloudFront for static Next.js site
- **Networking:** VPC with public/private subnets, security groups
- **Secrets:** AWS Secrets Manager for API keys and credentials
- **Monitoring:** CloudWatch logs and metrics
- **CI/CD:** GitHub Actions → ECR → ECS deployment pipeline

### Security Considerations

**Current Implementation:**
- Environment variables for all secrets (`.env` file, not committed to git)
- CORS configured for frontend origin (`http://localhost:3000`)
- No authentication/authorization (single-user demo)
- Database password in environment config
- API keys for LLM providers stored in environment

**Production Requirements (Phase 6):**
- AWS Secrets Manager for sensitive credentials
- Private subnets for backend and database
- Security groups restricting inbound traffic
- HTTPS/TLS for all external communication
- IAM roles with least-privilege access
- Environment-specific configuration management

## Data Flow

### Live Analysis Flow (Implemented)

1. **User triggers analysis** via frontend (`/analysis` page) or API (`POST /api/analysis/run`)
2. **Backend fetches latest candles** from Binance API (configurable timeframe and lookback)
3. **Technical indicators calculated** using `IndicatorService` (RSI, MACD, EMAs, Bollinger Bands)
4. **Agent pipeline executes:**
   - **Phase 1 (Parallel):** Technical, Sentiment, Tokenomics analysts analyze concurrently
   - **Phase 2 (Sequential):** Researcher synthesizes → Trader proposes → Risk Manager validates
5. **Trade execution** (simulated):
   - If approved, `PortfolioManager` executes trade at current market price
   - Updates `trades`, `positions`, and `portfolio_snapshots` tables
6. **Response returned** with all agent outputs, trade details, and portfolio state
7. **Frontend displays** agent reasoning, trade decision, and updated portfolio

**Key Implementation Details:**
- Async execution for parallel analyst phase
- Context passed through pipeline with market data, indicators, portfolio state
- LLM responses parsed into structured JSON
- Budget checked before each LLM call
- All agent interactions logged to `agent_logs` table

### Backtesting Flow (Implemented)

1. **User specifies parameters** via frontend (`/backtest` page) or API:
   - Symbol (e.g., BTCUSDT)
   - Date range (start_date, end_date)
   - Timeframe (1h, 4h, 1d, etc.)
   - Initial cash amount
2. **Backend loads historical candles:**
   - Fetches from database cache if available
   - Otherwise fetches from Binance API and caches
3. **Backtest engine iterates** through candles sequentially:
   - For each candle, runs full agent pipeline
   - Executes approved trades at candle's close price
   - Updates simulated portfolio state
4. **Performance metrics calculated:**
   - Total return, max drawdown, Sharpe ratio
   - Win rate, average win/loss
   - Equity curve over time
5. **Results stored** in `backtest_runs` table with unique `run_id`
6. **Frontend displays:**
   - Equity curve chart (using Recharts)
   - Trade history table
   - Performance metrics summary
   - Individual candle-by-candle decisions

**Optimization Notes:**
- Backtests can be expensive (many LLM calls)
- Budget enforcement prevents runaway costs
- Results cached by parameters for re-display
- Configurable candle limits to control duration

## API Endpoints (All Implemented)

### Market Data (`/api/market`)
- `GET /candles` - Fetch OHLCV data for symbol/timeframe
- `GET /indicators` - Calculate technical indicators for latest data
- `GET /price` - Current market price for symbol

### Portfolio (`/api/portfolio`)
- `GET /summary` - Current portfolio state (cash, positions, equity)
- `GET /positions` - All open positions
- `GET /trades` - Trade history with optional filtering
- `POST /reset` - Reset portfolio to initial state

### Analysis (`/api/analysis`)
- `POST /run` - Execute agent pipeline and get trading decision
- `GET /logs` - Agent execution logs with token/cost tracking

### Backtest (`/api/backtest`)
- `POST /run` - Run historical backtest with parameters
- `GET /runs` - List all backtest runs
- `GET /runs/{run_id}` - Detailed backtest results with equity curve

**Response Format:**
All endpoints return JSON with consistent error handling:
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-11-17T10:30:00Z"
}
```

Errors return appropriate HTTP status codes (400, 404, 500) with descriptive messages.

## Cost Management and Budget Control

**LLM Budget Enforcement (Implemented):**
- Daily token budget configured via `DAILY_TOKEN_BUDGET` environment variable
- `LLMClient` tracks cumulative tokens/cost per day in `agent_logs` table
- Raises `BudgetExceededError` if budget exceeded (pipeline catches gracefully)
- Per-model cost calculation using `LLMClient.COSTS` dictionary

**Cost Optimization Strategies:**
- **Tiered models:** Cheap models for high-volume analysts, strong models for critical decisions
- **Structured outputs:** Request JSON responses for easier parsing (fewer retries)
- **Concise prompts:** Minimize input tokens while maintaining clarity
- **Backtest limits:** Configurable max candles to prevent runaway costs
- **Caching:** Binance data cached in database to reduce API calls

**Cost Tracking:**
Every LLM call logged with:
- Agent name and run ID
- Model name (e.g., `deepseek-chat-v3-0324:free`)
- Prompt/completion tokens
- Estimated cost in USD
- Latency (response time)
- Timestamp

**Example Budget Configuration:**
```env
DAILY_TOKEN_BUDGET=1000000  # 1M tokens/day
CHEAP_MODEL=deepseek-chat-v3-0324:free  # ~$0 per 1M tokens
STRONG_MODEL=kimi-k2-thinking  # ~$0.30 per 1M tokens (approx)
```

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (REST API framework)
- SQLAlchemy (ORM)
- Alembic (database migrations)
- Pydantic (data validation)
- Pandas + TA-Lib (technical indicators)
- httpx (async HTTP client for Binance)
- pytest (testing framework)

**Frontend:**
- Next.js 15 (React framework)
- TypeScript (type safety)
- Tailwind CSS (styling)
- Recharts (data visualization)
- React Hooks (state management)

**Infrastructure:**
- Docker + Docker Compose (containerization)
- PostgreSQL 16 (database)
- Uvicorn (ASGI server)

**External APIs:**
- Binance Public API (market data)
- OpenRouter API (LLM access)

## Development Phases

**Phase 1:** ✅ **Foundation (Completed)**
- Project structure and documentation
- Database models with Alembic migrations
- FastAPI application skeleton
- Docker Compose setup

**Phase 2:** ✅ **Core Services (Completed)**
- Binance API integration with caching
- Portfolio simulation and trade execution
- Technical indicator calculations (RSI, MACD, EMAs, etc.)

**Phase 3:** ✅ **Agent System (Completed)**
- LLM client wrapper with budget enforcement
- All six agents implemented (Technical, Sentiment, Tokenomics, Researcher, Trader, Risk Manager)
- Agent pipeline orchestration (parallel + sequential)

**Phase 4:** ✅ **API Completion (Completed)**
- All REST endpoints functional
- Backtest engine with performance metrics
- Comprehensive error handling and logging

**Phase 5:** ✅ **Frontend (Completed)**
- Next.js UI with Tailwind CSS
- Dashboard with live market data and indicators
- Analysis page showing all agent outputs
- Portfolio page with positions and trade history
- Backtest interface with equity curve charts

**Phase 6:** 🚧 **Deployment (Planned)**
- AWS infrastructure (ECS Fargate, RDS, S3, CloudFront)
- CI/CD pipeline (GitHub Actions)
- CloudWatch monitoring and logging
- Production environment configuration

## Current Status

**✅ Fully Operational (Phase 5 Complete):**
- All backend services and APIs working
- All six agents integrated and tested
- Complete frontend with all views
- Docker Compose deployment for local/development
- Comprehensive test coverage

**🚧 Planned (Phase 6):**
- AWS cloud deployment
- Production-grade monitoring
- CI/CD automation

**Project Purpose:**
This is a **portfolio demonstration project** showcasing:
- Multi-agent AI orchestration
- Cost-conscious LLM usage
- Real-time data integration
- Full-stack development (FastAPI + Next.js)
- Clean architecture and testing
- Modern DevOps practices

**⚠️ Not Production-Ready:**
- Simulated trades only (no real money)
- No authentication/authorization
- Single-user design
- Minimal security hardening
