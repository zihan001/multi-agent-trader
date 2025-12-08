# **AI Trading System – Architecture & Flow Recommendations**

This document provides recommended structure, flow, and features for an AI-driven trading simulator where LLM agents act as advisors and all trading is executed manually through a paper-trading engine. It is designed for both **spot (Binance Testnet)** and future support of **futures trading**.

---

# **1. System Overview**

Your trading system should consist of **three distinct layers**:

## **1. Agents (Advisors)**

* Receive market data and portfolio state.
* Produce **trade ideas**, not executable orders.
* Output includes:

  * **BUY / SELL / HOLD**
  * Suggested entry price
  * Stop-loss (SL)
  * Take-profit (TP)
  * Position size %
  * Confidence level
  * Time horizon
  * Reason summary

Agents should **not** decide order types (market/limit/etc.).
Their job is strategic: *What should we do?*

---

## **2. Execution Planner (Your App Logic)**

* Converts agent *ideas* into proposed order plans.
* Example:

  * Entry: Limit order at 60,000
  * SL: Stop order at 58,500
  * TP: Limit sell at 63,000
* User can edit these through an **Order Ticket UI**.
* After user confirmation, orders are sent to the paper trading engine.

---

## **3. Paper Trading Engine**

Simulates order placement, order filling, positions, PnL, and portfolio equity.

Capabilities include:

* MARKET orders (instant fill)
* LIMIT orders (filled when market crosses price)
* STOP LOSS & TAKE PROFIT logic
* Performance tracking
* Order status: OPEN → FILLED → CLOSED

This layer simulates real exchanges but does not require connectivity to order endpoints.

---

# **2. Agent Output Format (Recommended Schema)**

Agents should output structured JSON with enriched metadata:

```json
{
  "symbol": "BTCUSDT",
  "action": "BUY",
  "confidence": 0.82,
  "time_horizon": "4h",
  "suggested_entry": 60000,
  "stop_loss": 58500,
  "take_profit": 63000,
  "position_size_pct": 0.03,
  "reason_summary": "Momentum up, strong support at 60k..."
}
```

Why this matters:

* Agents focus on “what” and “why”.
* Execution engine handles the “how”.

---

# **3. Paper Trading Capabilities**

## **Level 1 — Core Features**

* MARKET & LIMIT orders
* Position tracking:

  * Quantity
  * Average entry price
  * Unrealized PnL
  * Realized PnL
* Simulated fills based on price feed
* No slippage, no partial fills initially
* Basic fees (e.g., 0.1%)

## **Level 2 — Advanced**

* Stop-loss orders
* Take-profit orders
* OCO logic (SL cancels TP & vice versa)
* Slippage simulation (optional)

## **Level 3 — Futures Support**

* Leverage
* Margin + maintenance margin
* Liquidation price
* Funding payments (optional)

---

# **4. Suggested Data Models**

## **Trade Idea**

```python
class TradeIdea:
    id: str
    timestamp: datetime
    symbol: str
    action: "BUY" | "SELL" | "HOLD"
    confidence: float
    time_horizon: str
    suggested_entry: float | None
    stop_loss: float | None
    take_profit: float | None
    position_size_pct: float | None
    reasoning: str
```

## **Order**

```python
class Order:
    id: str
    symbol: str
    side: "BUY" | "SELL"
    quantity: float
    type: "MARKET" | "LIMIT" | "STOP_MARKET" | "STOP_LIMIT"
    price: float | None
    stop_price: float | None
    status: "OPEN" | "FILLED" | "CANCELLED"
    linked_idea_id: str | None
```

## **Position**

```python
class Position:
    symbol: str
    quantity: float
    avg_entry_price: float
    unrealized_pnl: float
    realized_pnl: float
```

---

# **5. Recommended Dashboard Layout**

A usable UI should display three core areas:

---

## **A. Agent Ideas Panel**

Shows strategic suggestions:

* Symbol
* Action (Buy / Sell / Hold)
* Suggested entry, SL, TP
* Confidence (bar or %)
* Time horizon
* Reason summary
* **“Open Order Ticket”** button

This is where users decide whether to act on agent advice.

---

## **B. Order Ticket Modal**

User edits and confirms:

* Order type (Market / Limit)
* Price (auto-filled from agent)
* Position size (auto-converted from %)
* SL/TP toggles
* Confirm → Sends to paper trading engine

---

## **C. Portfolio & Orders Dashboard**

### **Positions Table**

* Symbol
* Quantity
* Avg Entry
* Current Price
* Unrealized PnL
* Realized PnL
* SL/TP levels
* Close Position button

### **Orders Table**

* Order ID
* Type
* Side
* Price / Stop Price
* Status
* Linked Agent Idea

### **Performance Panel**

* Equity curve
* Total PnL
* Win rate
* Drawdown

### **Charts**

* Candlestick chart
* Markers for agent suggestions
* Markers for filled trades

---

# **6. Example End-to-End Flow**

1. Fetch latest market data.
2. Send data + portfolio to LLM agents.
3. Agents output trade ideas.
4. Ideas appear in the “AI Advisor” panel.
5. User opens an order ticket for a BUY idea.
6. User edits fields → confirms.
7. Paper trading engine simulates the order.
8. If filled, a new position is created.
9. Dashboard updates (PnL, positions, equity).

This creates a full trading loop while keeping LLMs in a safe advisory role.

---

# **7. Should You Change BUY/SELL/HOLD?**

**No.**
Just **enrich it** with metadata:

* Entry
* SL / TP
* Position size
* Confidence
* Time horizon

This keeps your system clean and modular:

* Agents = strategic intent
* Paper trading engine = execution logic
* User = final decision maker

---

# **8. Summary**

Your system should stay simple for agents and sophisticated for trading logic.

**Agents decide:**
→ What to do (Buy / Sell / Hold), at what level, and why.

**Your system decides:**
→ How to execute it (order type, fill simulation, SL/TP, margin).

**User decides:**
→ Whether to follow the advice.

This creates a realistic but manageable trading simulator.
