# Phase 6 Strategy Guide

## Overview

Phase 6 introduces **dual-mode trading** with two distinct decision engines and backtesting systems. This guide documents the rule-based strategies and provides guidance on choosing between LLM and rule-based modes.

---

## Decision Engines

### LLM Engine (6-Agent Pipeline)

**Cost**: ~$0.02 per decision  
**Speed**: ~15 seconds per decision  
**Best For**: Complex market analysis requiring nuanced reasoning

**Agent Pipeline**:
1. **Technical Analyst**: RSI, MACD, EMAs, Bollinger Bands analysis
2. **Sentiment Analyst**: Market narrative and sentiment extraction
3. **Tokenomics Analyst**: Supply/demand and economic fundamentals
4. **Researcher**: Synthesizes all inputs into investment thesis
5. **Trader**: Proposes specific trade with position sizing
6. **Risk Manager**: Final approval/rejection with risk assessment

**When to Use**:
- Need detailed reasoning for each decision
- Analyzing complex market conditions
- Testing new strategies with human-like decision making
- Small decision count (< 50 decisions)

---

### Rule Engine (Deterministic)

**Cost**: $0.00  
**Speed**: <1ms per decision  
**Best For**: Rapid decision-making with clear technical signals

**Available Strategies**: RSI+MACD, EMA Crossover, Bollinger Bands+Volume

**When to Use**:
- Backtesting long time periods
- Production trading requiring instant decisions
- Cost-sensitive environments
- Clear technical signal-based strategies

---

## Rule-Based Strategies

### 1. RSI + MACD Momentum Strategy

**Strategy ID**: `rsi_macd`

**Philosophy**: Buy oversold conditions with bullish momentum confirmation, sell overbought with bearish momentum.

**Entry Signals (BUY)**:
- RSI(14) < 30 (oversold)
- MACD > MACD Signal (bullish crossover)
- MACD Histogram > 0 (positive momentum)

**Exit Signals (SELL)**:
- RSI(14) > 70 (overbought)
- MACD < MACD Signal (bearish crossover)
- MACD Histogram < 0 (negative momentum)

**Hold Conditions**:
- RSI between 30-70 (neutral zone)
- Mixed MACD signals
- Confidence < 70%

**Configuration** (in `.env` or `docker-compose.yml`):
```bash
RULE_STRATEGY=rsi_macd
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
```

**Best Markets**:
- Ranging/oscillating markets
- High volatility assets (BTC, ETH)
- 1h-4h timeframes

**Strengths**:
- Clear reversal signals
- Good risk/reward at extremes
- Works well in sideways markets

**Weaknesses**:
- Whipsaws in strong trends
- Late entries/exits in trending markets
- Requires volatility to trigger signals

---

### 2. EMA Crossover Trend Strategy

**Strategy ID**: `ema_crossover`

**Philosophy**: Ride medium-term trends using moving average crossovers with trend confirmation.

**Entry Signals (BUY - Golden Cross)**:
- Fast EMA(9) crosses above Slow EMA(21)
- Price > Trend EMA(50) (uptrend confirmation)
- Both fast and slow EMAs > trend EMA

**Exit Signals (SELL - Death Cross)**:
- Fast EMA(9) crosses below Slow EMA(21)
- Price < Trend EMA(50) (downtrend confirmation)
- Both fast and slow EMAs < trend EMA

**Hold Conditions**:
- No clear crossover
- Mixed trend signals
- Price near EMA levels (consolidation)

**Configuration**:
```bash
RULE_STRATEGY=ema_crossover
EMA_FAST=9
EMA_SLOW=21
EMA_TREND=50
```

**Best Markets**:
- Strong trending markets
- Lower volatility assets (BNB, ADA)
- 4h-1d timeframes

**Strengths**:
- Captures sustained trends
- Fewer false signals than oscillators
- Good for "set and forget" trading

**Weaknesses**:
- Lagging indicator (late entries)
- Poor performance in ranging markets
- Requires patience for setups

---

### 3. Bollinger Bands + Volume Strategy

**Strategy ID**: `bb_volume`

**Philosophy**: Trade breakouts from volatility bands confirmed by volume surges.

**Entry Signals (BUY - Lower Band Breakout)**:
- Price touches or breaks below lower Bollinger Band
- Volume > 1.5x average volume (surge confirmation)
- Price rebounds back into bands (mean reversion)

**Exit Signals (SELL - Upper Band Breakout)**:
- Price touches or breaks above upper Bollinger Band
- Volume > 1.5x average volume
- Price pullback from upper band

**Hold Conditions**:
- Price within bands
- Normal volume (no surge)
- Bands contracting (low volatility)

**Configuration**:
```bash
RULE_STRATEGY=bb_volume
BB_PERIOD=20
BB_STD_DEV=2
MIN_VOLUME_RATIO=1.5
```

**Best Markets**:
- High volatility expansion/contraction cycles
- News-driven assets
- 1h-4h timeframes

**Strengths**:
- Catches volatility breakouts
- Volume confirmation reduces false signals
- Adaptive to market conditions (bands expand/contract)

**Weaknesses**:
- Requires significant price movement
- Volume data can be unreliable
- Band squeezes can produce whipsaws

---

## Backtesting Engines

### VectorBT Engine

**Speed**: ~100ms for entire backtest  
**Cost**: $0.00  
**Method**: Vectorized pandas/numpy operations

**Features**:
- Full date range processing
- Professional metrics (Sharpe, Sortino, profit factor)
- Equity curve with cash/positions breakdown
- All 3 rule strategies supported

**Best For**:
- Strategy optimization
- Long historical periods (months/years)
- Parameter tuning
- Production backtests

**Usage**:
```bash
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "start_date": "2024-01-01",
    "end_date": "2024-12-01",
    "timeframe": "1h",
    "initial_capital": 10000,
    "engine_type": "vectorbt",
    "strategy": "rsi_macd"
  }'
```

---

### LLM Engine

**Speed**: ~15s per decision  
**Cost**: ~$0.02 per decision  
**Method**: Sequential 6-agent pipeline

**Features**:
- Detailed reasoning for each trade
- Agent-by-agent decision breakdown
- Simulates human-like trading
- Max decision limit to control costs

**Best For**:
- Understanding decision logic
- Small sample backtests (< 50 decisions)
- Strategy development
- Educational purposes

**Usage**:
```bash
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "start_date": "2024-01-01",
    "end_date": "2024-01-07",
    "timeframe": "1h",
    "initial_capital": 10000,
    "engine_type": "llm",
    "max_decisions": 20
  }'
```

**Cost Control**: Always set `max_decisions` to limit LLM API costs. Recommended max: 50 (~$1.00 cost).

---

## Mode Selection Guide

### Use LLM Mode When:
- Exploring new markets/assets
- Need explainable trading decisions
- Testing complex multi-factor strategies
- Budget allows (~$0.02/decision)
- Small decision count requirements

### Use Rule Mode When:
- Backtesting long periods (weeks/months)
- Production trading requiring speed
- Zero-cost operation required
- Clear technical strategies (RSI, MACD, EMAs)
- High-frequency decision making

---

## Configuration

### Environment Variables

**Trading Mode**:
```bash
TRADING_MODE=rule          # or "llm"
RULE_STRATEGY=rsi_macd     # "ema_crossover" or "bb_volume"
```

**RSI + MACD Strategy**:
```bash
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
```

**EMA Crossover Strategy**:
```bash
EMA_FAST=9
EMA_SLOW=21
EMA_TREND=50
```

**Bollinger Bands + Volume**:
```bash
BB_PERIOD=20
BB_STD_DEV=2
MIN_VOLUME_RATIO=1.5
```

### Switching Modes

**Via Environment**:
```bash
# Edit .env file
TRADING_MODE=rule
RULE_STRATEGY=ema_crossover

# Restart backend
docker-compose restart backend
```

**Check Current Mode**:
```bash
curl http://localhost:8000/config/mode
```

**Response**:
```json
{
  "mode": "rule",
  "engine_info": {
    "type": "rule",
    "name": "Rule-Based Decision Engine",
    "description": "Deterministic technical indicator-based trading",
    "cost_per_decision": 0.0,
    "avg_latency_ms": 0.5
  },
  "rule_strategy": "rsi_macd"
}
```

---

## Performance Comparison

| Metric | LLM Engine | Rule Engine (RSI+MACD) |
|--------|------------|------------------------|
| Speed | 15,000ms | 0.5ms |
| Cost | $0.02 | $0.00 |
| Reasoning | Detailed | None |
| Backtesting | Slow (50 decisions max) | Fast (unlimited) |
| Complexity | High | Low |
| Consistency | Variable | Deterministic |

---

## Best Practices

### Strategy Development
1. Start with LLM mode to explore decision logic
2. Convert insights to rule-based strategy
3. Backtest rule strategy on full dataset with VectorBT
4. Deploy rule engine for production

### Backtesting
1. Use VectorBT for initial strategy validation
2. Test on multiple timeframes (1h, 4h, 1d)
3. Verify across different market conditions (trending, ranging, volatile)
4. Check metrics: Sharpe > 1.0, Win Rate > 45%, Max Drawdown < 20%

### Live Trading
1. Always use rule mode for production (speed + cost)
2. Start with small position sizes (1-2% per trade)
3. Monitor actual vs expected performance
4. Adjust parameters based on live results

### Cost Management
1. Use LLM only for exploration/analysis
2. Set `max_decisions` limit for LLM backtests
3. Use rule mode for all production trading
4. VectorBT backtests are always free

---

## Troubleshooting

### Rule Engine Not Generating Signals
- Check if indicators are calculated (need 50+ candles)
- Verify strategy parameters (RSI thresholds, EMA periods)
- Ensure market has sufficient volatility
- Try different timeframe (1h vs 4h)

### VectorBT Backtest Shows 0 Trades
- Market conditions may not trigger strategy
- Adjust entry thresholds (lower RSI_OVERSOLD, raise RSI_OVERBOUGHT)
- Increase date range for more opportunities
- Check data availability in database

### LLM Backtest Too Slow
- Reduce `max_decisions` to 20-30
- Use shorter date range (1 week max)
- Consider switching to VectorBT for speed

### High Backtest Costs
- Always set `max_decisions` limit
- Use VectorBT instead of LLM
- Rule mode has zero cost

---

## Next Steps

1. **Experiment**: Test all 3 strategies on different symbols
2. **Optimize**: Tune parameters for your preferred assets
3. **Compare**: LLM vs Rule performance on same data
4. **Deploy**: Use rule mode for actual trading
5. **Monitor**: Track live performance vs backtests

For technical implementation details, see `ARCHITECTURE.md` and `.github/copilot-instructions.md`.
