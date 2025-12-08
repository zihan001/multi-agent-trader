# Configuration Simplification Summary

## Overview
Simplified the trading system configuration by removing the redundant `TRADING_MODE` environment variable. Engine mode (LLM vs rule-based) is now automatically determined based on the presence of an LLM API key.

## Changes Made

### 1. Backend Configuration (`backend/app/core/config.py`)
**Before:**
```python
llm_api_key: str  # Required field
trading_mode: str = "llm"  # Redundant variable
```

**After:**
```python
llm_api_key: Optional[str] = None  # Optional - determines LLM availability
# trading_mode removed

@property
def llm_enabled(self) -> bool:
    """Check if LLM mode is available based on API key presence."""
    return bool(self.llm_api_key and self.llm_api_key.strip())

@property
def default_engine_mode(self) -> str:
    """Return default engine mode: 'llm' if available, otherwise 'rule'."""
    return "llm" if self.llm_enabled else "rule"
```

### 2. Decision Engine Factory (`backend/app/engines/factory.py`)
**Updated:**
- `create()` method now uses `settings.default_engine_mode` instead of `settings.trading_mode`
- Added validation to prevent LLM mode when API key not configured
- `get_current_engine_info()` updated to use new property

### 3. API Endpoints

#### Health Endpoint (`backend/app/main.py`)
**Before:**
```json
{
  "status": "ok",
  "trading_mode": "llm",
  "llm_enabled": true
}
```

**After:**
```json
{
  "status": "ok",
  "default_engine_mode": "llm",
  "llm_enabled": true,
  "environment": "development",
  "rule_strategy": "rsi_macd",
  "paper_trading_enabled": true,
  "paper_trading_mode": "testnet"
}
```

#### Config Mode Endpoint (`backend/app/routes/config.py`)
**Updated:**
- Removed `trading_mode` from response
- Uses `settings.llm_enabled` property
- Returns `available_modes` array based on LLM availability

### 4. Analysis Routes
**Updated files:**
- `backend/app/routes/analysis.py` - Uses `settings.default_engine_mode`
- `backend/app/routes/backtest.py` - Uses `settings.default_engine_mode`
- `backend/app/models/decisions.py` - Updated docstrings

### 5. Frontend Updates

#### Dashboard (`frontend/app/page.tsx`)
**Before:**
```typescript
if (health.trading_mode === 'llm' && isLlmEnabled) {
  setEngineMode('llm');
}
```

**After:**
```typescript
const defaultMode = health.default_engine_mode || 'rule';
setEngineMode(defaultMode as 'llm' | 'rule');
```

#### Type Definitions (`frontend/types/api.ts`)
**Before:**
```typescript
export interface HealthResponse {
  trading_mode?: string;
  llm_enabled?: boolean;
}
```

**After:**
```typescript
export interface HealthResponse {
  default_engine_mode?: string;
  llm_enabled?: boolean;
  environment?: string;
  paper_trading_enabled?: boolean;
  paper_trading_mode?: string;
}
```

### 6. Environment Files

#### `.env`
**Removed:**
```bash
# Phase 6: Trading Mode Configuration
TRADING_MODE=llm  # Options: "llm" or "rule"
```

**Added comment:**
```bash
# Note: Engine mode (llm/rule) is automatic - LLM enabled if LLM_API_KEY is set, otherwise rule-based
```

#### `.env.example`
**Updated:**
```bash
# LLM Configuration (Optional - if not set, only rule-based mode will be available)
# To enable LLM mode: provide an API key from OpenAI or OpenRouter
# To use only rule-based mode: leave LLM_API_KEY empty or unset
LLM_API_KEY=your_api_key_here
```

Removed `TRADING_MODE` variable entirely.

## How It Works Now

### Automatic Mode Detection
1. **LLM API key present** → Both LLM and rule-based modes available, defaults to LLM
2. **No LLM API key** → Only rule-based mode available, defaults to rule

### Frontend Behavior
- Dashboard fetches health endpoint on load
- Checks `llm_enabled` flag to show/hide mode selector
- Sets default mode from `default_engine_mode`
- Users can still manually select mode if both available

### Backend Validation
- `DecisionEngineFactory.create()` validates LLM requests
- Raises `ValueError` if LLM mode requested but key not configured
- Falls back to rule-based if no mode specified and LLM unavailable

## Testing Results

### With LLM API Key Set
```bash
$ curl http://localhost:8000/health
{
  "status": "ok",
  "default_engine_mode": "llm",
  "llm_enabled": true,
  ...
}

$ curl -X POST http://localhost:8000/analyze -d '{"symbol": "BTCUSDT", "engine_mode": "llm"}'
# ✅ Works - uses LLM multi-agent pipeline

$ curl -X POST http://localhost:8000/analyze -d '{"symbol": "BTCUSDT", "engine_mode": "rule"}'
# ✅ Works - uses rule-based strategy

$ curl -X POST http://localhost:8000/analyze -d '{"symbol": "BTCUSDT"}'
# ✅ Works - defaults to LLM
```

### Without LLM API Key (if key removed)
```bash
$ curl http://localhost:8000/health
{
  "status": "ok",
  "default_engine_mode": "rule",
  "llm_enabled": false,
  ...
}

$ curl -X POST http://localhost:8000/analyze -d '{"symbol": "BTCUSDT", "engine_mode": "llm"}'
# ❌ Error: "LLM mode requested but LLM API key not configured"

$ curl -X POST http://localhost:8000/analyze -d '{"symbol": "BTCUSDT"}'
# ✅ Works - defaults to rule-based
```

## Database Verification
```sql
SELECT id, symbol, action, decision_type, created_at 
FROM agent_recommendations 
ORDER BY id DESC LIMIT 5;

 id | symbol  | action | decision_type |          created_at           
----+---------+--------+---------------+-------------------------------
 11 | ETHUSDT | HOLD   | llm           | 2025-12-08 03:02:50.28351+00
 10 | BTCUSDT | HOLD   | rule          | 2025-12-08 03:01:30.712886+00
```
✅ Both engine types storing correctly with proper decision_type tracking

## Benefits

### 1. **Simpler Configuration**
- One less environment variable to manage
- Clearer relationship between API key and LLM availability
- No confusion about which setting controls what

### 2. **More Intuitive**
- Presence of API key = LLM available (obvious)
- No API key = rule-based only (obvious)
- No need to synchronize multiple config variables

### 3. **Better Developer Experience**
- Quick setup: just provide API key to enable LLM
- Easy to disable LLM: remove or comment out API key
- Less prone to configuration errors

### 4. **Maintains Flexibility**
- Users can still choose mode at runtime via `engine_mode` parameter
- Frontend mode selector still works when both modes available
- Backward compatible with existing API usage patterns

## Migration Guide

### For Existing Users
1. **Remove `TRADING_MODE` from your `.env` file**
2. **Keep or remove `LLM_API_KEY`:**
   - Keep it to use LLM mode (automatically enabled)
   - Remove/comment it to use only rule-based mode
3. **No code changes needed** - API still accepts `engine_mode` parameter

### For New Users
1. Copy `.env.example` to `.env`
2. If you want LLM mode:
   - Set `LLM_API_KEY=your_actual_key`
3. If you only want rule-based:
   - Leave `LLM_API_KEY` empty or remove the line
4. That's it!

## Files Modified

### Backend
- `backend/app/core/config.py` - Removed trading_mode, added properties
- `backend/app/main.py` - Updated health endpoint
- `backend/app/routes/config.py` - Updated config endpoint
- `backend/app/routes/analysis.py` - Uses default_engine_mode
- `backend/app/routes/backtest.py` - Uses default_engine_mode
- `backend/app/models/decisions.py` - Updated docstrings
- `backend/app/engines/factory.py` - Uses default_engine_mode, added validation

### Frontend
- `frontend/app/page.tsx` - Uses default_engine_mode from health
- `frontend/types/api.ts` - Updated HealthResponse interface

### Configuration
- `.env` - Removed TRADING_MODE
- `.env.example` - Removed TRADING_MODE, added clarifying comments

## Deployment Notes

### Docker
- Rebuild backend container: `docker-compose up -d --build backend`
- No database migration needed (schema unchanged)
- Existing recommendations preserved

### Environment Variables
- Remove `TRADING_MODE` from production environment
- Keep `LLM_API_KEY` if LLM mode desired
- Update CI/CD pipelines to remove TRADING_MODE references

## Conclusion

The configuration is now cleaner and more intuitive. The presence of an LLM API key automatically enables LLM mode as an option, while its absence restricts the system to rule-based mode. This aligns with the principle of least surprise - users naturally expect that providing an API key enables the associated feature.

The change eliminates a common source of configuration errors where TRADING_MODE and LLM_API_KEY could be out of sync, making the system more robust and easier to use.
