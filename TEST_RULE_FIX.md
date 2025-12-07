# Rule Engine Fix - Test Results

## Summary
Fixed the rule-based trading engine to detect **actual crossover events** rather than **persistent states**, and added **position tracking** to prevent duplicate buys/sells.

## Problems Fixed

### 1. **Continuous Buy Signals**
**Before:** Generated BUY signals on every candle when MACD was positive and RSI < 50
**After:** Only generates BUY when MACD **crosses** from negative to positive (state change)

### 2. **No Position Tracking**
**Before:** Would try to buy even if already holding a position
**After:** Checks if position exists before generating BUY/SELL signals

### 3. **Missing Crossover Detection**
**Before:** Checked `macd > macd_signal` (persistent state)
**After:** Checks `macd_hist > 0 AND macd_hist_prev <= 0` (actual crossover)

## Changes Made

### 1. Added Position State Checking (`_has_position` method)
```python
def _has_position(self, symbol: str, portfolio_data: Dict[str, Any]) -> tuple[bool, float]:
    """Check if we have an existing position for this symbol."""
    positions = portfolio_data.get("positions", [])
    for position in positions:
        if position.get("symbol") == symbol:
            quantity = position.get("quantity", 0)
            return quantity > 0, quantity
    return False, 0.0
```

### 2. Fixed RSI+MACD Strategy
**Now detects actual MACD histogram crossovers:**
```python
# Detect MACD crossover: histogram changes sign
macd_bullish_crossover = macd_hist > 0 and macd_hist_prev <= 0
macd_bearish_crossover = macd_hist < 0 and macd_hist_prev >= 0

# BUY: Bullish crossover + RSI filter + no position
if macd_bullish_crossover and rsi < 50 and not has_position:
    action = "BUY"
```

### 3. Fixed EMA Crossover Strategy
**Now detects actual EMA line crossovers:**
```python
# Detect crossovers
golden_cross = (ema_fast > ema_slow) and (ema_fast_prev <= ema_slow_prev)
death_cross = (ema_fast < ema_slow) and (ema_fast_prev >= ema_slow_prev)

# BUY: Golden cross + price above trend + no position
if golden_cross and current_price > ema_trend and not has_position:
    action = "BUY"
```

### 4. Fixed BB+Volume Strategy
**Now checks position state:**
```python
# BUY: Price at/below lower BB + volume surge + no position
if current_price <= bb_lower and volume_ratio >= threshold and not has_position:
    action = "BUY"
```

### 5. Updated Indicator Service
**Added previous EMA values for crossover detection:**
```python
'ema_9_prev': float(ema_9_series.iloc[latest_idx - 1]) if len(df) > 1 else ...
'ema_21_prev': float(ema_21_series.iloc[latest_idx - 1]) if len(df) > 1 else ...
'ema_50_prev': float(ema_50_series.iloc[latest_idx - 1]) if len(df) > 1 else ...
```

### 6. Enhanced Safety in _calculate_quantity
```python
if action == "BUY":
    # Check if we already have a position (should not happen if strategy is correct)
    has_position, _ = self._has_position(symbol, portfolio_data)
    if has_position:
        return 0.0  # Safety check: don't buy if we already have a position
```

## Expected Behavior Now

### Analysis Mode (No Position)
1. Waits for crossover signal
2. If bullish crossover detected → **BUY**
3. If no crossover → **HOLD**

### Analysis Mode (Have Position)
1. Waits for reverse crossover signal  
2. If bearish crossover detected → **SELL**
3. If no crossover → **HOLD** (keeps position)

### Backtesting Mode
- Same logic but operates on historical data
- Should generate **discrete buy/sell signals** on crossover events
- Not continuous signals on every candle

## Test Results
All 17 tests passing:
- ✅ Position state checking
- ✅ MACD crossover detection
- ✅ EMA crossover detection
- ✅ BB+Volume with position tracking
- ✅ Quantity calculations respect position limits
- ✅ Zero-cost execution (no LLM calls)

## Next Steps for Testing
1. Run live analysis to verify single BUY/HOLD/SELL behavior
2. Run backtest to verify signal count is reasonable (10-30 trades, not 1000)
3. Compare performance metrics with previous version
