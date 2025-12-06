# AI Multi-Agent Crypto Trading Simulator

> A portfolio demonstration project showcasing a simulated crypto trading firm powered by multiple LLM agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This system simulates a crypto trading firm where specialized AI agents analyze market data, debate trading decisions, and execute simulated trades. The project demonstrates:
- Multi-agent LLM orchestration (primary focus)
- Real-time market data integration (Binance API)
- Portfolio simulation and backtesting
- Full-stack web application
- AWS cloud deployment with dual-mode operation

**Deployment Strategy:**
- **Development/Local Demo**: LLM-based agents (showcase AI capabilities locally)
- **AWS Production Deployment**: Rule-based mode ONLY (zero LLM costs for public access)
- **Capability**: Full LLM system available locally, rule-based deployed to cloud
- **Future**: Optional ML models to enhance rule-based strategies

**⚠️ Note:** This is a **simulation only**. No real trading occurs.

## Features

### Phase 1-6: LLM-Based System (PRIMARY - For Portfolio Demonstration)
- 🤖 **Six Specialized LLM Agents** - Technical, Sentiment, Tokenomics Analysts + Researcher, Trader, Risk Manager
- 🧠 **Natural Language Reasoning** - Agents provide human-readable explanations for every decision
- 📊 **Live Market Data** - Real-time OHLCV from Binance public API
- 💰 **Portfolio Simulation** - Track positions, PnL, and equity over time
- ⏮️ **LLM Agent Backtesting** - Test AI decision-making on historical data
- 🌐 **Web Interface** - Interactive dashboard showing agent reasoning and decisions
- ☁️ **AWS Deployment** - Production-ready cloud infrastructure
- 💵 **Cost-Conscious** - Token budgets, tiered LLM models, and daily spending limits

### Phase 6+: Production Deployment Optimization (Cost-Effective for Live Demos)
- 🎯 **Rule-Based Trading Engine** - Deterministic decisions based on technical indicators (no LLM costs)
- ⚡ **VectorBT Backtesting** - Vectorized backtesting for 100x speed improvement
- 📈 **TA-Lib Integration** - 150+ professional technical indicators
- 🔄 **Dual-Mode Operation** - Switch between LLM and rule modes via environment variable
- 🔮 **Future: ML Enhancement** - Optional ML models to work alongside rule-based strategies

### Phase 6.5+: Advanced LLM Features (When Budget Allows)
- 🤝 **LangChain Integration** - Enhanced agent orchestration with tools, memory, and advanced reasoning
- 🧠 **Agent Memory** - Context retention across decisions for improved learning
- 📝 **Paper Trading** - Real-time trading simulation via Binance testnet (spot & futures)
- 🔍 **ReAct Agents** - Iterative reasoning and tool usage for complex analysis

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+ (for frontend development)
- LLM API key (OpenAI or OpenRouter)
- Binance testnet account (optional, for paper trading features)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd multi-agent-trader
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env and add your LLM_API_KEY
   ```

3. **Start all services (backend + frontend + database)**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Development Setup (Local)

#### Backend

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run the development server
uvicorn app.main:app --reload
```

#### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Copy environment file
cp .env.example .env.local

# Run development server
npm run dev
```

## Project Structure

```
multi-agent-trader/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py      # App entry point
│   │   ├── core/        # Config & database
│   │   ├── models/      # Database models
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   └── agents/      # LLM agents
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Next.js application
│   ├── app/            # Next.js pages (Dashboard, Analysis, Portfolio, Backtest)
│   ├── components/     # React components
│   ├── lib/            # API client & utilities
│   ├── types/          # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml   # Production Docker setup
├── docker-compose.dev.yml  # Development setup with hot-reload
├── .env.example        # Environment template
└── ARCHITECTURE.md     # Detailed architecture docs
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

### Agent Pipeline

```
Market Data → [Technical, Sentiment, Tokenomics Analysts] 
           → Researcher → Trader → Risk Manager → Decision
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check (includes current TRADING_MODE)
- `GET /market/symbols` - Available trading symbols
- `GET /market/{symbol}/latest` - Latest market data
- `POST /analyze` - Run analysis (LLM agents OR rule-based engine based on TRADING_MODE)
- `GET /portfolio` - Current portfolio state
- `GET /trades` - Trade history
- `GET /config/mode` - Get current trading mode and capabilities
- `POST /config/mode` - Switch trading mode (llm/rule) - admin only

### Backtesting Endpoints

#### Phase 1-6: LLM Agent Backtesting
- `POST /backtest/agents` - Run LLM agent-based historical backtest
  - Returns agent reasoning, decisions, and performance
  - Costs LLM tokens (monitored against budget)
  
#### Phase 6+: Technical Strategy Backtesting  
- `POST /backtest/technical` - Run VectorBT technical strategy backtest
  - Pure indicator-based strategies (RSI, MACD, EMA, etc.)
  - 100x faster than LLM backtest
  - Zero LLM costs
  
- `GET /backtest/runs` - List all backtest runs
- `GET /backtest/{run_id}` - Get detailed backtest results

### Paper Trading Endpoints (Phase 6.5+)
- `POST /paper/order` - Place paper trade order on Binance testnet
- `GET /paper/positions` - Get current paper trading positions
- `GET /paper/balance` - Get paper trading account balance
- `DELETE /paper/position/{symbol}` - Close paper trading position

## Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_db

# Trading Mode (Primary Configuration)
TRADING_MODE=llm  # Options: llm (Phase 1-6), rule (Phase 6+)

# LLM Configuration (for TRADING_MODE=llm)
LLM_API_KEY=your_api_key_here
CHEAP_MODEL=gpt-3.5-turbo
STRONG_MODEL=gpt-4-turbo-preview
DAILY_TOKEN_BUDGET=100000

# Rule-Based Configuration (for TRADING_MODE=rule - Phase 6+)
RULE_STRATEGY=RSI_MACD  # Options: RSI_MACD, EMA_CROSSOVER, BOLLINGER_BANDS
# Future: ML_MODEL_PATH for optional ML enhancements

# Trading Simulation
INITIAL_CASH=10000.0
MAX_POSITION_SIZE_PCT=0.10

# Binance Testnet (for paper trading - Phase 6.5+)
BINANCE_TESTNET_ENABLED=false
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_SECRET=your_testnet_secret
```

## Development Roadmap

### ✅ Completed Phases (LLM-Based System - Local Development)
- [x] Phase 1: Project foundation and structure
- [x] Phase 2: Core services (Binance, portfolio, indicators)
- [x] Phase 3: LLM agent system implementation
- [x] Phase 4: API endpoints and LLM backtest engine
- [x] Phase 5: Frontend application with agent reasoning visualization

**🎯 Deliverable**: Fully functional LLM agent trading system for local portfolio demonstrations

---

### 🚧 Phase 6: Rule-Based Trading Engine (IN PROGRESS)

#### A. Deterministic Rule Engine
- [ ] Implement rule-based decision logic
  - RSI + MACD strategy
  - EMA crossover strategy
  - Bollinger Bands + Volume strategy
- [ ] Rule-based portfolio management
- [ ] Environment variable to switch: `TRADING_MODE=rule`
- [ ] Frontend displays rule-based signals (no agent reasoning)

#### B. VectorBT Integration
- [ ] VectorBT backtesting engine
  - Vectorized operations for 100x speed
  - Professional metrics (Sharpe, Sortino, Calmar ratios)
  - Portfolio optimization
- [ ] TA-Lib integration (150+ indicators)

**🎯 Deliverable**: Production-ready rule-based system with zero LLM costs

---

### 📦 Phase 7: AWS Deployment (Rule-Based Mode ONLY)
- [ ] Deploy **rule-based system only** to AWS
- [ ] ECS/EC2 deployment (no LLM API keys needed)
- [ ] RDS PostgreSQL for portfolio data and trade history
- [ ] ALB configuration
- [ ] CloudWatch logging
- [ ] Environment: `TRADING_MODE=rule` (hardcoded in production)
- [ ] Public demo accessible without ongoing costs

**🎯 Deliverable**: Live public demo running rule-based strategies at zero LLM cost

**Note**: LLM system remains available for local demonstrations and portfolio presentations

---

### 💡 Future Enhancements (Post-Deployment)

---

### 🚀 Future Enhancements (Post-Deployment)

#### Advanced LLM Features (Local Development Only)
- [ ] LangChain/CrewAI integration for enhanced orchestration
- [ ] Tool-using agents (dynamic data fetching)
- [ ] Agent memory for context retention
- [ ] ReAct reasoning loops

#### Paper Trading
- [ ] Binance testnet integration (spot & futures)
- [ ] Real-time paper trading mode
- [ ] Live order placement simulation

#### ML Enhancements (Optional)
- [ ] ML models to work alongside rule-based strategies
- [ ] Not trained on LLM outputs
- [ ] Can be deployed to AWS if desired

**🎯 Note**: Advanced LLM features for local portfolio demonstrations only

## Technology Stack

**Frontend:**
- Next.js 14 (React framework with App Router)
- TypeScript (type safety)
- TailwindCSS (styling)
- Recharts (data visualization)
- Axios (HTTP client)

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy + PostgreSQL (database)

**Phase 1-6: LLM-Based (Primary)**
- OpenAI/OpenRouter (LLM providers)
- Custom multi-agent pipeline (6 specialized agents)
- Token budget enforcement and cost tracking

**Phase 6+: Production Optimization**
- VectorBT (vectorized backtesting - 100x faster)
- TA-Lib (150+ professional technical indicators)
- Custom rule engine (deterministic trading logic)
- Future: scikit-learn / XGBoost (optional ML enhancements)

**Phase 6.5+: Advanced Features**
- LangChain/CrewAI (enhanced agent orchestration)
- python-binance (Binance testnet integration)

**Shared Infrastructure:**
- HTTPX (Binance API client)
- Pandas / NumPy (data processing)

**Infrastructure:**
- Docker & Docker Compose
- AWS ECS/EC2 (compute)
- AWS RDS (database)
- AWS ALB (load balancer)
- AWS Secrets Manager (secrets)

## Contributing

This is a portfolio project, but suggestions and feedback are welcome! Please open an issue to discuss major changes.

## License

MIT License - see LICENSE file for details

## Disclaimer

This project is for **educational and demonstration purposes only**. It does not execute real trades or handle real funds. Past performance of backtests does not guarantee future results. Not financial advice.

---

## Full Requirements Specification

The complete requirements document follows below:

---

# AI Multi-Agent Crypto Trading Simulator — Requirements Specification

## 1. Project Overview

**Name**  
AI Multi-Agent Crypto Trading Simulator

**Purpose**  
A web-based portfolio project that simulates a crypto trading “firm” composed of multiple LLM-powered agents.  
The system analyzes real-time or recent crypto market data (via Binance’s public API), generates trading decisions, and simulates execution — **no real trading**, purely for demonstration.

**Deployment Target**  
- Backend & DB: **AWS**
- Frontend: AWS (S3 + CloudFront) or external (e.g. Vercel)

**Key Characteristics**
- Multi-agent decision-making (analysts → researcher → trader → risk)
- Fully simulated trading
- Live or historical crypto data
- LLM-cost-conscious architecture
- Clean full-stack demo suitable for portfolio

---

## 2. Scope

### 2.1 In Scope

#### Phase 1-5: LLM-Based System (LOCAL - Portfolio Demonstration)
- Live data ingestion from Binance public API
- **Six specialized LLM agents** with natural language reasoning:
  - Technical, Sentiment, Tokenomics Analysts
  - Researcher, Trader, Risk Manager
- Multi-agent orchestration (analysts → researcher → trader → risk)
- LLM cost tracking and daily budget enforcement
- Simulated order execution with explainable decisions
- Portfolio PnL tracking
- LLM agent backtesting with historical data
- Web UI showing agent reasoning and decision-making process
- **Runs locally only** for portfolio presentations

**Goal**: Demonstrate advanced AI/ML engineering skills and multi-agent system design

---

#### Phase 6: Rule-Based System Development

**A. Rule-Based Trading Engine** (Zero LLM costs)
- Deterministic decision logic based on technical indicators
- Strategies: RSI+MACD, EMA Crossover, Bollinger Bands
- Environment variable to switch modes: `TRADING_MODE=rule`
- Same UI, same API, zero ongoing costs

**B. VectorBT + TA-Lib Integration** (Professional Backtesting)
- Vectorized backtesting (100x speed improvement over LLM backtest)
- 150+ TA-Lib indicators for institutional-grade analysis
- Metrics: Sharpe ratio, Sortino ratio, Calmar ratio, max drawdown

**Goal**: Build production-ready rule-based system for AWS deployment

---

#### Phase 7: AWS Deployment (Rule-Based ONLY)
- Deploy rule-based system to AWS (ECS/EC2, RDS, ALB)
- Public demo accessible without LLM costs
- No LLM API keys in production environment
- Cost-effective 24/7 operation

**Goal**: Live public portfolio demo running at zero LLM cost

**Future Enhancement**: Optional ML models (not LLM-trained) to work alongside rule-based strategies

---

#### Phase 6.5+: Advanced LLM Features (Budget Permitting)
- **LangChain/CrewAI**: Enhanced agent orchestration with tools and memory
- **Paper Trading**: Binance testnet integration for spot and futures
- **Agent Memory**: Context retention across trading sessions
- **ReAct Agents**: Iterative reasoning and tool usage

**Goal**: State-of-the-art agentic AI when LLM budget allows

### 2.2 Out of Scope

- Real money trading
- Binance private API keys / authenticated trading (use testnet during development)
- High-frequency trading
- Multi-user auth (single demo user only)
- Complex order types / order book microstructure
- Dedicated paper trading infrastructure (MVP uses Binance testnet endpoints)

---

## 3. User Role

**Demo User (You / Recruiters)**

- Trigger new analyses
- Run backtests
- Review agent reasoning
- View simulated trades & PnL

---

## 4. Functional Requirements

### 4.1 Market Data Ingestion

- **FR-1**: Fetch live OHLCV data for selected symbols (e.g. `BTCUSDT`, `ETHUSDT`, `SOLUSDT`) from Binance **public REST API**.
- **FR-2**: Cache OHLCV data in the database for reuse and backtesting.
- **FR-3**: Support fetching historical OHLCV for specified date ranges and timeframes.
- **FR-4**: Allow mocked or static data for:
  - News / narrative
  - Tokenomics
  - Sentiment  
  (to simplify initial version and control cost).

---

### 4.2 Multi-Agent Decision Engine

The engine shall include these logical agents:

#### 4.2.1 Technical Analyst Agent

- **Inputs**: symbol, timeframe, OHLCV data + derived indicators (RSI, MACD, EMAs, volatility, etc.)
- **Output**: concise structured analysis:
  - trend (up/down/sideways)
  - momentum (strong/weak)
  - overbought/oversold assessment
  - short bullet-point reasoning

#### 4.2.2 Sentiment / News Analyst Agent

- **Inputs**: simplified/mock news & sentiment signals for the symbol
- **Output**:
  - sentiment (`bullish` / `neutral` / `bearish`)
  - key narrative points (bullets)

#### 4.2.3 Tokenomics Analyst Agent

- **Inputs**: basic token metadata from JSON (category, supply schedule, major risks)
- **Output**:
  - long-term outlook (positive/neutral/negative)
  - 2–4 key structural risks or strengths

#### 4.2.4 Researcher Agent

- **Inputs**: outputs from all analysts
- **Output**:
  - unified thesis: `bullish` / `neutral` / `bearish`
  - confidence score (0–1)
  - top 3 risks
  - short justification

#### 4.2.5 Trader Agent

- **Inputs**: researcher thesis, symbol, current position, recent price action summary
- **Output**:
  - action: `BUY` / `SELL` / `HOLD`
  - position size: % of portfolio to allocate or reduce
  - optional: suggested stop-loss and take-profit (as %)
  - reasoning bullets

#### 4.2.6 Risk Manager Agent

- **Inputs**: trader proposal + portfolio state + risk rules
- **Risk rules examples**:
  - max position per asset (e.g. 10% of equity)
  - max total exposure to crypto (e.g. 80%)
  - optional volatility thresholds
- **Output**:
  - decision: `APPROVE` / `ADJUST` / `REJECT`
  - adjusted size (if applicable)
  - explanation

#### 4.2.7 Orchestration

- **FR-5**: The decision pipeline must orchestrate agents in this order:

  > Data → Analysts → Researcher → Trader → Risk Manager → Final Decision

- **FR-6**: LLM usage must be cost-aware:
  - analysts use **cheap models**
  - researcher, trader, risk manager use **stronger model**
  - max one reasoning round per agent (no extended debates)

---

### 4.3 Simulated Execution & Portfolio

- **FR-7**: Maintain a simulated portfolio with:
  - initial cash (e.g. 10,000 USDT)
  - open positions per symbol
  - realized PnL
  - unrealized PnL
- **FR-8**: When a final decision is approved:
  - compute quantity based on:
    - portfolio value
    - allocation % from trader / risk manager
  - “execute”:
    - in live mode: at latest available price
    - in backtest: at next candle’s open or close
  - update:
    - cash
    - open/closed positions
    - trade history
- **FR-9**: Backtesting:
  - **LLM Agent Backtest**:
    - input: symbol, start date, end date, timeframe
    - iterate over candles, optionally only every N candles to save LLM calls
    - simulate trades and portfolio evolution
    - compute metrics: total return, max drawdown, number of trades
    - return time series equity curve
  - **VectorBT Technical Backtest** (Phase 6.5+):
    - vectorized backtesting for 100x speed improvement
    - support for pure technical indicator strategies
    - professional metrics: Sharpe, Sortino, Calmar ratios
    - portfolio optimization and walk-forward analysis
  - **TA-Lib Integration** (Phase 6.5+):
    - 150+ professional technical indicators
    - pattern recognition (candlestick patterns, chart patterns)
    - statistical functions and volatility indicators
    - cycle indicators and volume analysis

---

### 4.4 Backend API (FastAPI)

Backend must expose:

1. `GET /health`  
   - Returns `{ "status": "ok" }`.

2. `GET /market/symbols`  
   - Returns list of supported symbols.

3. `GET /market/{symbol}/latest`  
   - Returns recent OHLCV data and computed indicators for a symbol.

4. `POST /analyze`  
   - **Request body**:
     - `symbol`: string
     - `mode`: `"live"` or `"backtest_step"`
     - optional `timestamp` for backtest
   - **Response**:
     - per-agent summaries (technical, sentiment, tokenomics)
     - researcher thesis
     - trader decision
     - risk manager decision
     - final approved decision
     - updated portfolio snapshot (if trade executed)

5. `GET /portfolio`  
   - Returns current:
     - cash
     - positions
     - unrealized/realized PnL
     - total equity

6. `GET /trades`  
   - Returns trade history (paginated if needed).

7. `POST /backtest/agents` (LLM Agent Backtest)
   - **Request body**:
     - `symbol`
     - `start_date`
     - `end_date`
     - `timeframe` (e.g. `1h`, `4h`)
     - `max_decisions` (to cap LLM calls)
   - **Response**:
     - summary metrics
     - equity curve (list of `{timestamp, equity}`)
     - list of trades taken in backtest

8. `POST /backtest/technical` (VectorBT Technical Backtest - Phase 6.5+)
   - **Request body**:
     - `symbol`
     - `start_date`
     - `end_date`
     - `strategy` (e.g. `RSI_MACD`, `EMA_CROSSOVER`)
     - `parameters` (strategy-specific params)
   - **Response**:
     - comprehensive metrics (Sharpe, Sortino, Calmar, max drawdown, win rate)
     - equity curve
     - trade list
     - comparison with buy-and-hold

9. `POST /paper/order` (Paper Trading - Phase 6.5+)
   - **Request body**:
     - `symbol`
     - `side` (BUY/SELL)
     - `type` (MARKET/LIMIT)
     - `quantity`
     - `price` (for LIMIT orders)
     - `leverage` (for futures)
   - **Response**:
     - order confirmation
     - execution details
     - updated position

10. `GET /paper/positions` (Paper Trading - Phase 6.5+)
    - Returns all active paper trading positions

11. `GET /paper/balance` (Paper Trading - Phase 6.5+)
    - Returns paper trading account balance and equity

---

### 4.5 Frontend Requirements

- **FR-10**: Provide a simple web UI with the following views:

#### 4.5.1 Dashboard

- Dropdown for symbol selection
- Display:
  - latest price
  - basic stats/indicators
- Button: **"Run Analysis"**
- Shows loading and then navigates to Analysis view

#### 4.5.2 Analysis View

- Show each agent’s output clearly:
  - Technical Analyst
  - Sentiment/News Analyst
  - Tokenomics Analyst
  - Researcher Thesis
  - Trader Decision
  - Risk Manager Verdict
- Emphasize final decision (color, card, etc.)
- Optionally show a small price chart with trade marker

#### 4.5.3 Portfolio View

- Table of open positions with:
  - symbol
  - quantity
  - avg entry price
  - current price
  - unrealized PnL
- Summary:
  - cash balance
  - total equity
  - total return
- Trade history table

#### 4.5.4 Backtest View

- Form:
  - symbol select
  - start date, end date
  - timeframe
  - `Run Backtest` button
- Results:
  - stats (return, drawdown, win rate)
  - equity curve chart
  - trades list

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **NFR-1**: `/analyze` target response time: **5–15 seconds**.
- **NFR-2**: Backtests limited by `max_decisions` to constrain LLM calls and runtime.

### 5.2 LLM Cost Control

- **NFR-3**: Define at least two model tiers:
  - `cheap` for analysts
  - `strong` for researcher, trader, risk
- **NFR-4**: Implement a central `LLMClient` that:
  - routes calls based on agent role
  - enforces per-call token limits
  - enforces a daily token budget (from config)
  - logs model, tokens, and estimated cost
- **NFR-5**: Prompts must:
  - use numeric and summarized inputs where possible
  - request concise, structured outputs (prefer JSON)

### 5.3 Security

- **NFR-6**: No secrets in source control.
- **NFR-7**: Use **AWS Systems Manager Parameter Store** or **Secrets Manager** for:
  - LLM API keys (e.g. OpenRouter/OpenAI)
  - DB credentials
  - any future Binance-related keys (if ever used in read-only mode)
- **NFR-8**: Public endpoints should be REQ/RESP JSON only. Optionally add simple rate limiting.

### 5.4 Reliability & Logging

- **NFR-9**: Log every LLM call:
  - timestamp
  - agent name
  - model
  - tokens in/out
  - symbol
- **NFR-10**: Graceful failure behavior:
  - if an analyst fails, mark data as unavailable and continue with others
  - if researcher/trader fails, respond with “no trade” and a clear error in logs
- **NFR-11**: Backend errors return JSON with error message and HTTP status.

---

## 6. AWS Architecture Requirements

### 6.1 Core Components

- **Compute**:
  - Option A: ECS Fargate service running backend Docker image
  - Option B: Single EC2 instance with Docker (simpler/cheaper to operate)
- **Database**:
  - RDS PostgreSQL (small instance) recommended
  - For strict budget, Postgres on EC2 is acceptable
- **Load Balancer**:
  - Application Load Balancer (ALB) for backend HTTP(S) traffic
- **Config & Secrets**:
  - SSM Parameter Store / Secrets Manager for:
    - API keys
    - DB credentials
    - daily budget config
- **Logging**:
  - CloudWatch Logs for backend container logs

### 6.2 Networking

- VPC with public + private subnets
- ALB in public subnets
- Backend tasks/instance + DB in private subnets
- Security groups:
  - ALB → Backend (80/443)
  - Backend → DB (5432)

### 6.3 Frontend Hosting

- Option A: React app built & hosted as static site on:
  - S3 + CloudFront
- Option B: Host frontend on Vercel/Netlify and call AWS backend API

---

## 7. Data Model (Initial Schema)

### 7.1 `candles`

- `id` (PK)
- `symbol` (text)
- `timestamp` (datetime)
- `timeframe` (text)
- `open` (float)
- `high` (float)
- `low` (float)
- `close` (float)
- `volume` (float)

Unique index on (`symbol`, `timestamp`, `timeframe`).

### 7.2 `trades`

- `id` (PK)
- `symbol` (text)
- `side` (text: `BUY` / `SELL`)
- `quantity` (float)
- `price` (float)
- `timestamp` (datetime)
- `pnl` (float, nullable until closed)
- `run_id` (text or UUID for grouping backtests vs live sim)

### 7.3 `positions`

- `id` (PK)
- `symbol` (text)
- `quantity` (float)
- `avg_entry_price` (float)
- `unrealized_pnl` (float)
- `updated_at` (datetime)

### 7.4 `portfolio_snapshots`

- `id` (PK)
- `timestamp` (datetime)
- `total_equity` (float)
- `cash_balance` (float)
- `run_id` (text/UUID)

### 7.5 `agent_logs`

- `id` (PK)
- `timestamp` (datetime)
- `run_id` or `decision_id` (text/UUID)
- `agent_name` (text)
- `symbol` (text)
- `model_name` (text)
- `tokens_input` (int)
- `tokens_output` (int)
- `cost_estimate` (float, approximate)
- `input_summary` (json/text)
- `output_summary` (json/text)

---

## 8. LLM Strategy

- Two main model tiers:
  - **Cheap model** (e.g., OpenRouter cheap model) for:
    - Technical Analyst
    - Sentiment/News Analyst
    - Tokenomics Analyst
  - **Strong model** for:
    - Researcher
    - Trader
    - Risk Manager
- Use a shared `LLMClient` that:
  - abstracts provider (OpenRouter vs OpenAI)
  - maps `agent_name` → `model_tier`
  - enforces max tokens per call
  - tracks cumulative daily token usage against budget

---

## 9. Development Environment

### 9.1 Local

- Use Docker Compose to run:
  - FastAPI backend
  - Postgres DB
- `.env` file (gitignored) for:
  - DB URL
  - LLM API key
  - daily token budget

### 9.2 AWS Demo Environment

- Deployed backend container on ECS or EC2
- Connected RDS Postgres
- ALB in front of backend
- CloudWatch for logs/metrics

---

## 10. Project Timeline (Rough)

Assume ~5–6 weeks part-time. Adjust pacing as needed.

### Week 1 — Foundations & Data

- Initialize Git repo and base project structure.
- Set up FastAPI skeleton.
- Set up Docker + Docker Compose for:
  - backend
  - Postgres
- Implement Binance OHLCV fetcher and DB schema for `candles`.
- Build simple script/endpoint to:
  - fetch + store recent candles for a symbol
  - read them back from DB.

### Week 2 — Simulation Core & Portfolio

- Implement portfolio model:
  - positions
  - trades
  - portfolio snapshots
- Implement core simulation logic:
  - “execute_trade” function
  - open/close positions
  - update PnL
- Add `/portfolio` and `/trades` endpoints.
- Unit test trade + portfolio mechanics with fake signals (no LLM yet).

### Week 3 — LLM Integration & Agents (Backend Only)

- Implement `LLMClient` wrapper with:
  - role → model mapping
  - token limit per call
  - cost logging
- Implement first pass of agents:
  - Technical Analyst (using real indicators)
  - Mock Sentiment/News Analyst
  - Mock Tokenomics Analyst
- Implement Researcher, Trader, Risk Manager agents using LLM.
- Implement `/analyze` endpoint that:
  - runs full pipeline
  - returns agent outputs + final decision
  - optionally executes trade in “live simulation” mode.

### Week 4 — Backtest & Cost Controls

- Implement backtest engine:
  - iterate over historical candles
  - call pipeline at configured intervals (`N` candles)
  - simulate trades and PnL
- Add `/backtest` endpoint that:
  - returns metrics and equity curve
- Wire in daily token budget in `LLMClient`.
- Add logging to `agent_logs` table.

### Week 5 — Frontend & AWS Deployment

- Build minimal frontend (React or Next.js):
  - Dashboard view
  - Analysis view
  - Portfolio view
  - Backtest view
- Deploy backend to AWS:
  - ECS Fargate or EC2
  - RDS Postgres
  - ALB
- Host frontend:
  - S3 + CloudFront or Vercel
- Ensure environment variables & secrets come from AWS (Parameter Store / Secrets Manager).

### Week 6 — Polish & Documentation

- Improve UI styling and UX (loading states, error messages).
- Polish prompts for agents for clearer reasoning outputs.
- Add basic tests (unit + a couple of integration flows).
- Write:
  - README with architecture diagram
  - short “How It Works” overview
  - deployment notes
- Capture screenshots / GIFs for portfolio.

---
