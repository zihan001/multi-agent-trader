# Quick Start Guide - AI Multi-Agent Trading Simulator

This guide will help you get the full-stack application running quickly.

## Prerequisites

- Docker and Docker Compose installed
- LLM API key (OpenAI or OpenRouter)
- 8GB+ RAM recommended

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd multi-agent-trader
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your LLM API key
# Required:
LLM_API_KEY=your_api_key_here

# Optional (defaults provided):
# DAILY_TOKEN_BUDGET=100000
# CHEAP_MODEL=openai/gpt-3.5-turbo
# STRONG_MODEL=openai/gpt-4-turbo-preview
```

### 3. Start All Services

```bash
# Start backend, frontend, and database
docker-compose up -d

# Check logs
docker-compose logs -f
```

Wait for all services to be healthy (about 30-60 seconds).

### 4. Run Database Migrations

```bash
# Apply database schema
docker-compose exec backend alembic upgrade head
```

### 5. Access the Application

- **Frontend (Web UI)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Using the Application

### Dashboard (Home Page)

1. Select a cryptocurrency symbol (e.g., BTCUSDT)
2. View real-time market data and technical indicators
3. Click **"Run AI Analysis"** to trigger the multi-agent pipeline

### Analysis View

- See detailed outputs from all 6 AI agents:
  - 📊 Technical Analyst
  - 📰 Sentiment Analyst
  - 🪙 Tokenomics Analyst
  - 🔬 Researcher (Synthesizer)
  - 💼 Trader (Decision Maker)
  - 🛡️ Risk Manager (Validator)
- Final decision shown prominently at top
- Portfolio summary updated after trade execution

### Portfolio View

- View all open positions with real-time PnL
- Track cash balance and total equity
- Review complete trade history

### Backtest View

1. Select symbol, date range, and timeframe
2. Set max decisions (to control LLM costs)
3. Click **"Run Backtest"**
4. View performance metrics, equity curve, and all trades

## Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

## Development Mode (with Hot Reload)

For development with automatic code reloading:

```bash
# Use the development compose file
docker-compose -f docker-compose.dev.yml up

# Backend reloads on Python file changes
# Frontend reloads on TypeScript/React file changes
```

## Troubleshooting

### Backend won't start
- Check `docker-compose logs backend`
- Verify `LLM_API_KEY` is set in `.env`
- Ensure port 8000 is not in use

### Frontend won't start
- Check `docker-compose logs frontend`
- Ensure port 3000 is not in use
- Verify `NEXT_PUBLIC_API_URL` points to backend

### Database connection errors
- Wait for database to be fully initialized (check `docker-compose logs db`)
- Run migrations: `docker-compose exec backend alembic upgrade head`

### LLM API errors
- Verify API key is correct
- Check you have credits/balance with your LLM provider
- Try using a different model (edit `CHEAP_MODEL` or `STRONG_MODEL` in `.env`)

### Port conflicts
If ports 3000, 8000, or 5432 are in use, you can change them in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change 3001 to any free port
```

## Testing Without LLM Calls

For testing the UI without making expensive LLM calls:

1. Reduce `DAILY_TOKEN_BUDGET` in `.env` to a small number (e.g., 1000)
2. Use cheaper models if available
3. Limit backtest `max_decisions` to 5-10

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system design details
- Review [backend/README.md](./backend/README.md) for API documentation
- Check [frontend/README.md](./frontend/README.md) for UI development guide
- For production deployment, see Phase 6 documentation (coming soon)

## Getting Help

- Check API documentation: http://localhost:8000/docs
- Review agent logs: `docker-compose logs backend | grep "agent"`
- See full logs: `docker-compose logs -f`

## Cost Management

⚠️ **Important**: This system makes real LLM API calls which cost money.

- Set `DAILY_TOKEN_BUDGET` to limit spending
- Start with small backtests (max_decisions=10)
- Use cheaper models for analysts
- Monitor usage in `agent_logs` table

Estimated costs (using OpenAI):
- Single analysis: $0.10 - $0.50
- Backtest (50 decisions): $5 - $25

Using cheaper providers like OpenRouter can reduce costs significantly.

---

**Happy Trading (Simulation)!** 🚀
