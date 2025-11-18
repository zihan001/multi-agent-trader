# AI Multi-Agent Crypto Trading Simulator

> A portfolio demonstration project showcasing a simulated crypto trading firm powered by multiple LLM agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This system simulates a crypto trading firm where specialized AI agents analyze market data, debate trading decisions, and execute simulated trades. The project demonstrates:
- Multi-agent LLM orchestration
- Real-time market data integration (Binance API)
- Portfolio simulation and backtesting
- Full-stack web application
- AWS cloud deployment

**⚠️ Note:** This is a **simulation only**. No real trading occurs.

## Features

- 🤖 **Six Specialized AI Agents** - Technical, Sentiment, Tokenomics Analysts + Researcher, Trader, Risk Manager
- 📊 **Live Market Data** - Real-time OHLCV from Binance public API
- 💰 **Portfolio Simulation** - Track positions, PnL, and equity over time
- ⏮️ **Backtesting Engine** - Test strategies on historical data
- 🌐 **Web Interface** - Interactive dashboard for analysis and monitoring
- ☁️ **AWS Deployment** - Production-ready cloud infrastructure
- 💵 **Cost-Conscious** - Token budgets and tiered LLM models

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- LLM API key (OpenAI or OpenRouter)

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

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Development Setup (Local)

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (once implemented)
alembic upgrade head

# Run the development server
uvicorn app.main:app --reload
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
├── docker-compose.yml    # Local development setup
├── .env.example         # Environment template
└── ARCHITECTURE.md      # Detailed architecture docs
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

### Agent Pipeline

```
Market Data → [Technical, Sentiment, Tokenomics Analysts] 
           → Researcher → Trader → Risk Manager → Decision
```

## API Endpoints (Planned)

- `GET /health` - Health check
- `GET /market/symbols` - Available trading symbols
- `GET /market/{symbol}/latest` - Latest market data
- `POST /analyze` - Run agent analysis
- `GET /portfolio` - Current portfolio state
- `GET /trades` - Trade history
- `POST /backtest` - Run historical backtest

## Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_db

# LLM Configuration
LLM_API_KEY=your_api_key_here
CHEAP_MODEL=gpt-3.5-turbo
STRONG_MODEL=gpt-4-turbo-preview
DAILY_TOKEN_BUDGET=100000

# Trading Simulation
INITIAL_CASH=10000.0
MAX_POSITION_SIZE_PCT=0.10
```

## Development Roadmap

- [x] Phase 1: Project foundation and structure
- [x] Phase 2: Core services (Binance, portfolio, indicators)
- [ ] Phase 3: Agent system implementation
- [ ] Phase 4: API endpoints and backtest engine
- [ ] Phase 5: Frontend application
- [ ] Phase 6: AWS deployment

## Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy + PostgreSQL (database)
- OpenAI/OpenRouter (LLM providers)
- TA-Lib (technical indicators)
- HTTPX (Binance API client)

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

- Live data ingestion from Binance public API
- Multi-agent LLM reasoning pipeline
- Trade decision generation
- Risk evaluation & approval/adjustment
- Simulated order execution
- Portfolio PnL tracking
- Backtesting with historical data
- Web UI to visualize markets, decisions, and portfolio
- Deployment on AWS (backend + DB + logging)

### 2.2 Out of Scope

- Real money trading
- Binance private API keys / authenticated trading
- High-frequency trading
- Multi-user auth (single demo user only)
- Complex order types / order book microstructure

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
  - input: symbol, start date, end date, timeframe
  - iterate over candles, optionally only every N candles to save LLM calls
  - simulate trades and portfolio evolution
  - compute metrics:
    - total return
    - max drawdown
    - number of trades
  - return time series equity curve

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

7. `POST /backtest`  
   - **Request body**:
     - `symbol`
     - `start_date`
     - `end_date`
     - `timeframe` (e.g. `1h`, `4h`)
     - `max_decisions` (to cap LLM calls)
   - **Response**:
     - summary metrics
     - equity curve (list of `{timestamp, equity}`
     - list of trades taken in backtest

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
