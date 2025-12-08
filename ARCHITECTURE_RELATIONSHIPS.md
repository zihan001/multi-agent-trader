# System Architecture: Portfolio, Paper Trading, Analysis & Backtest

## Overview

This document clarifies how the four main features relate to each other and when to use each one.

---

## Feature Relationships

### 1. **Analysis** → **Portfolio** (Primary Flow)

```
User → /analysis → Agent Pipeline → Trading Decision → Portfolio Manager → Trade Executed → Portfolio Updated
```

**What it does:**
- Runs 6 LLM agents (or rule-based strategy) to analyze market
- Makes BUY/SELL/HOLD decision
- **Automatically executes** approved trades
- Updates portfolio with positions and PnL

**When paper trading is enabled:**
```
Decision → Portfolio Manager (use_paper_trading=True) → 
    1. Creates Trade record (portfolio tracking)
    2. Creates PaperOrder + Binance testnet API call (actual execution)
```

**Key Point:** Analysis is the **automated trading system** that uses AI agents to make decisions.

---

### 2. **Paper Trading** (Manual Trading Interface)

```
User → /paper-trading → Manual Order Form → Binance Testnet API → Order Placed
```

**What it does:**
- Provides UI for **manual** order placement
- Uses real Binance testnet API
- Independent of agent pipeline
- For testing strategies or manual execution

**Relationship to Portfolio:**
- Initially **disconnected** - paper orders tracked separately
- **Now integrated** - Portfolio page shows both:
  - "Agent Trades" tab: Automated trades from /analysis
  - "Paper Orders" tab: Manual orders from /paper-trading

**Key Point:** Paper Trading is for **manual control** and testing real API integration.

---

### 3. **Portfolio** (Unified View)

```
User → /portfolio → Shows:
    - Summary (equity, cash, PnL)
    - Open positions
    - Agent Trades (from /analysis)
    - Paper Orders (from /paper-trading)
```

**What it does:**
- Central dashboard for all trading activity
- Tracks performance metrics
- Shows both automated and manual trading

**Data Sources:**
- `trades` table → Agent-executed trades
- `positions` table → Current holdings
- `paper_orders` table → Manual paper trading orders
- `portfolio_snapshots` table → Historical equity

**Key Point:** Portfolio is the **read-only dashboard** showing results from both automated and manual trading.

---

### 4. **Backtest** (Historical Simulation)

```
User → /backtest → Select date range + strategy → Run simulation → Backtest Results
```

**What it does:**
- Tests strategies on **past data**
- Simulates trades without real execution
- Uses `run_id` to isolate backtest data
- Shows performance metrics (Sharpe ratio, max drawdown, etc.)

**Relationship to other features:**
- **Isolated** - Uses separate `run_id` to avoid mixing with live data
- **Never uses Paper Trading** - No API calls on historical data
- Can test both LLM agents and rule-based strategies

**Key Point:** Backtest is for **strategy validation** using historical data, completely separate from live trading.

---

## Configuration Flow

### When Paper Trading is **DISABLED** (Default)
```
.env:
PAPER_TRADING_ENABLED=false

Flow:
/analysis → Agent Decision → PortfolioManager (local simulation) → Trade record created
```
- Trades are **purely simulated** in database
- No real API calls
- Fast and cheap (no network latency)

### When Paper Trading is **ENABLED** (Testnet Mode)
```
.env:
PAPER_TRADING_ENABLED=true
PAPER_TRADING_MODE=testnet
BINANCE_TESTNET_API_KEY=your_key
BINANCE_TESTNET_API_SECRET=your_secret

Flow:
/analysis → Agent Decision → PortfolioManager (use_paper_trading=True) →
    1. Trade record (portfolio tracking)
    2. Binance testnet API order (actual execution)
```
- Trades execute on **real Binance testnet**
- Full order book matching
- Validates API integration
- Slightly slower (network calls)

---

## Data Models

### Simulation Mode (Paper Trading OFF)
```
Database Tables Used:
- trades: All executed trades
- positions: Current open positions
- portfolio_snapshots: Historical equity
- agent_logs: LLM usage tracking
```

### Testnet Mode (Paper Trading ON)
```
Database Tables Used:
- trades: Portfolio tracking (same as above)
- positions: Current open positions (same)
- portfolio_snapshots: Historical equity (same)
- agent_logs: LLM usage (same)
+ paper_orders: Binance testnet orders with order IDs
```

**Why both?**
- `trades` = **Local record** for portfolio calculations
- `paper_orders` = **Testnet order** with Binance order ID for validation

---

## Use Cases

### Use Case 1: Testing Agent Strategy (Analysis + Portfolio)
1. Go to `/analysis`
2. Select symbol (e.g., BTCUSDT)
3. Click "Analyze"
4. Agents make decision → Trade executes → Portfolio updates
5. View results on `/portfolio`

**Paper trading:** Can be ON or OFF depending on if you want real API validation

---

### Use Case 2: Manual Trading Practice (Paper Trading)
1. Go to `/paper-trading`
2. Fill order form (symbol, side, quantity)
3. Submit → Order sent to Binance testnet
4. View order status in real-time
5. Cancel open orders if needed
6. Check `/portfolio` → "Paper Orders" tab

**Purpose:** Learn API behavior, test manual strategies

---

### Use Case 3: Strategy Validation (Backtest)
1. Go to `/backtest`
2. Select date range (e.g., last 3 months)
3. Choose strategy (LLM agents or rule-based)
4. Run backtest → See historical performance
5. Compare metrics (Sharpe, drawdown, win rate)

**Paper trading:** Not used (historical data only)

---

### Use Case 4: Compare Manual vs Automated (Portfolio)
1. Execute some trades via `/analysis` (automated)
2. Execute some trades via `/paper-trading` (manual)
3. Go to `/portfolio`
4. Switch tabs: "Agent Trades" vs "Paper Orders"
5. Compare which performs better

**Purpose:** Evaluate if agents beat manual trading

---

## Decision Tree: Which Feature to Use?

```
Do you want to make a trading decision?
├─ Yes, but let AI decide
│  └─ Use /analysis (Agent Pipeline)
│     ├─ Paper Trading ON → Real testnet execution
│     └─ Paper Trading OFF → Local simulation
│
├─ Yes, I want manual control
│  └─ Use /paper-trading (Manual Orders)
│     └─ Always uses testnet API
│
├─ No, just view results
│  └─ Use /portfolio (Dashboard)
│     ├─ View Agent Trades tab
│     └─ View Paper Orders tab
│
└─ No, test historical strategy
   └─ Use /backtest (Simulation)
      └─ Never uses paper trading
```

---

## Frontend Navigation Flow

```
Dashboard (/) 
    ↓ Select Symbol → Analyze
    
Analysis (/analysis)
    → Run Agent Pipeline
    → Auto-execute trade
    → Redirects to Portfolio
    
Portfolio (/portfolio)
    → View performance
    → Tabs: Agent Trades | Paper Orders
    → Link to Paper Trading page
    
Paper Trading (/paper-trading)
    → Manual order form
    → View testnet balance
    → Manage open orders
    → Link back to Portfolio
    
Backtest (/backtest)
    → Historical analysis
    → Strategy comparison
    → No connection to Portfolio (isolated run_id)
```

---

## Technical Implementation

### PortfolioManager Integration
```python
# backend/app/services/portfolio.py
class PortfolioManager:
    def __init__(self, db: Session, run_id: str = "live", use_paper_trading: bool = False):
        self.paper_trading_service = PaperTradingService(db) if use_paper_trading else None
    
    def execute_trade(self, symbol, side, quantity, price):
        # If paper trading enabled, execute on testnet
        if self.use_paper_trading:
            self.paper_trading_service.create_order(symbol, side, "MARKET", quantity)
        
        # Always create local Trade record for portfolio tracking
        trade = Trade(symbol=symbol, side=side, ...)
        self.db.add(trade)
```

### Analysis Route Activation
```python
# backend/app/routes/analysis.py
use_paper_trading = settings.paper_trading_enabled and settings.paper_trading_mode == "testnet"
portfolio_manager = PortfolioManager(db, use_paper_trading=use_paper_trading)
```

### Frontend Data Flow
```typescript
// frontend/app/portfolio/page.tsx
const [trades, setTrades] = useState<Trade[]>([]);        // From /portfolio/trades
const [paperOrders, setPaperOrders] = useState<Order[]>([]); // From /paper-trading/orders/history

// Show both in tabbed interface
{activeTab === 'agent' && <TradesTable trades={trades} />}
{activeTab === 'paper' && <OrdersTable orders={paperOrders} />}
```

---

## Summary

| Feature | Purpose | Data Source | Paper Trading? |
|---------|---------|-------------|----------------|
| **Analysis** | Automated trading via AI agents | `trades`, `positions` | Optional (testnet execution) |
| **Paper Trading** | Manual trading interface | `paper_orders` | Always (testnet API) |
| **Portfolio** | Unified performance dashboard | Both above | N/A (read-only view) |
| **Backtest** | Historical strategy testing | Isolated `run_id` | Never (historical data) |

**Key Insight:** Analysis and Paper Trading are **independent execution methods** (automated vs manual), and Portfolio **combines both** into a unified view.
