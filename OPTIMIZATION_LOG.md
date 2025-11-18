# LLM Call Optimization Log

## Date: November 18, 2025

### Phase 1: Prompt Compression ✅ COMPLETED

**Goal**: Reduce token usage by 19-23% through prompt optimization without quality degradation.

#### Changes Implemented

##### 1. Candle Data Compression (`technical.py`)
- **Before**: 10 candles with verbose format (400-600 tokens)
  ```
  Open: X, High: Y, Low: Z, Close: A, Volume: B
  ```
- **After**: 5 candles with compact CSV format (75-100 tokens)
  ```
  close,volume
  ```
- **Savings**: ~325-525 tokens per Technical analysis call

##### 2. JSON Schema Instruction Compression (All Agents)
Compressed verbose JSON structure examples into concise field lists.

- **Technical Analyst**: ~250 tokens saved
- **Sentiment Analyst**: ~300 tokens saved  
- **Tokenomics Analyst**: ~350 tokens saved
- **Researcher**: ~300 tokens saved
- **Trader**: ~350 tokens saved
- **Risk Manager**: ~350 tokens saved
- **Total**: ~900-1,500 tokens saved per full pipeline run

##### 3. Agent Output Compression (`pipeline.py`)
Added `compress_analyst_output()` utility function to extract only decision-relevant fields.

- **Before**: Full analyst outputs forwarded to Researcher (1,150-1,700 tokens)
- **After**: Compressed outputs with top 2 observations + 150 char reasoning (450-600 tokens)
- **Savings**: ~750-1,200 tokens per Researcher call

#### Total Expected Savings

| Optimization | Tokens Saved | % Reduction |
|-------------|--------------|-------------|
| Candle compression | 325-525 | 3-4% |
| JSON schema compression | 900-1,500 | 9-11% |
| Output compression | 750-1,200 | 7-9% |
| **TOTAL** | **1,975-3,225** | **19-23%** |

**New per-run token count**: 8,175-10,675 tokens (down from 10,150-13,900)

#### Files Modified

1. `/backend/app/agents/technical.py` - Candle data + JSON compression
2. `/backend/app/agents/sentiment.py` - JSON compression
3. `/backend/app/agents/tokenomics.py` - JSON compression
4. `/backend/app/agents/researcher.py` - JSON compression
5. `/backend/app/agents/trader.py` - JSON compression
6. `/backend/app/agents/risk.py` - JSON compression
7. `/backend/app/agents/pipeline.py` - Output compression utility + integration

#### Testing Checklist

- [ ] Run single analysis for BTCUSDT and verify all agents complete
- [ ] Check agent outputs are still structured correctly
- [ ] Verify final trade decision quality matches pre-optimization baseline
- [ ] Monitor token usage in `agent_logs` table to confirm savings
- [ ] Test with multiple symbols (BTC, ETH, SOL)
- [ ] Run short backtest to ensure no regression

#### Monitoring Queries

```sql
-- Check token usage after optimization
SELECT 
    agent_name,
    AVG(tokens_used) as avg_tokens,
    AVG(cost) as avg_cost,
    COUNT(*) as calls
FROM agent_logs
WHERE timestamp >= '2025-11-18'
GROUP BY agent_name
ORDER BY avg_tokens DESC;

-- Compare to baseline (before optimization)
SELECT 
    DATE(timestamp) as date,
    SUM(tokens_used) as total_tokens,
    SUM(cost) as total_cost,
    COUNT(*) as total_calls
FROM agent_logs
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

---

## Next Phases (Planned)

### Phase 2: Analyst Result Caching (TODO)
- **Goal**: 6-12% additional savings via 5-min TTL cache
- **Expected impact**: 560-1,740 tokens/run (average with 40-60% hit rate)
- **Complexity**: Medium
- **Files**: `pipeline.py`

### Phase 3: Model Tier Optimization (TODO)
- **Goal**: Cost reduction without sacrificing quality
- **Action**: Add medium model tier for Risk Manager
- **Expected impact**: 50% cost savings on Risk Manager calls
- **Complexity**: Low
- **Files**: `config.py`, `base.py`, `risk.py`

### Phase 4: Switch to Reliable Paid Models (RECOMMENDED)
- **Goal**: Eliminate rate limiting issues
- **Action**: Update `.env` to use `gpt-4o-mini` + `claude-3-haiku`
- **Cost**: ~$0.01-0.02 per run ($0.50-1.70/day for 100 runs)
- **Benefit**: No upstream throttling, consistent availability

---

## Optimization Guidelines

### DO
✅ Compress prompts while maintaining clarity
✅ Extract only decision-relevant data between agents
✅ Use compact formats (CSV vs verbose text)
✅ Cache non-critical analyst outputs
✅ Monitor token usage and quality metrics

### DON'T
❌ Compress prompts to the point of ambiguity
❌ Cache decision agent outputs (Researcher, Trader, Risk)
❌ Remove context needed for quality decisions
❌ Batch agents with different model requirements
❌ Sacrifice safety checks for token savings

---

## Results & Metrics (To be filled after testing)

### Token Usage Comparison

| Agent | Before (avg) | After (avg) | Savings | % Reduction |
|-------|--------------|-------------|---------|-------------|
| Technical | 1,300-1,800 | TBD | TBD | TBD |
| Sentiment | 1,050-1,400 | TBD | TBD | TBD |
| Tokenomics | 1,200-1,600 | TBD | TBD | TBD |
| Researcher | 2,300-3,200 | TBD | TBD | TBD |
| Trader | 2,000-2,700 | TBD | TBD | TBD |
| Risk Manager | 2,300-3,200 | TBD | TBD | TBD |
| **TOTAL** | **10,150-13,900** | **TBD** | **TBD** | **TBD** |

### Quality Metrics (To be measured)

- [ ] Decision accuracy: Target ≥90% of baseline
- [ ] Response completeness: All required fields present
- [ ] Parse success rate: Target ≥95%
- [ ] Final trade quality: Manual review score

### Cost Savings (To be calculated)

- Daily token budget utilization: __%
- Estimated cost per run: $__
- Estimated monthly savings: $__
