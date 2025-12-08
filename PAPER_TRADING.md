# Binance Paper Trading Setup

This application now supports **real Binance paper trading** using Binance's Spot Testnet API!

## Two Paper Trading Modes

### 1. Testnet Mode (Recommended) 🌐
Uses Binance's **real testnet API** - authentic order execution with fake money.

**Features:**
- Real Binance API behavior
- Actual order matching engine
- Real market prices and fills
- Multiple order types (Market, Limit, Stop Loss, Take Profit)
- Account balances tracked by Binance
- No local simulation needed

**Setup:**

1. **Get Testnet API Credentials**
   - Visit: https://testnet.binance.vision/
   - Sign in with GitHub
   - Click "Generate HMAC_SHA256 Key"
   - Save your API Key and Secret Key

2. **Configure Environment Variables**
   
   Add to your `.env` file:
   ```bash
   # Binance Testnet Configuration
   BINANCE_TESTNET_ENABLED=true
   BINANCE_TESTNET_API_KEY=your_api_key_here
   BINANCE_TESTNET_API_SECRET=your_secret_key_here
   PAPER_TRADING_MODE=testnet
   ```

3. **Fund Your Testnet Account**
   - Testnet accounts come with fake USDT
   - No real money involved!

### 2. Simulation Mode (Local) 💻
Pure local simulation - all order management in PostgreSQL.

**Features:**
- No API credentials needed
- Order fills simulated based on real market prices
- Configurable slippage and fees
- Fully offline operation

**Setup:**

Add to your `.env` file:
```bash
PAPER_TRADING_MODE=simulation
```

## API Endpoints

All endpoints available at `/paper-trading`:

### Create Order
```bash
POST /paper-trading/orders
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "MARKET",
  "quantity": 0.001
}
```

### Get Open Orders
```bash
GET /paper-trading/orders/open?symbol=BTCUSDT
```

### Get Order History
```bash
GET /paper-trading/orders/history?limit=50
```

### Cancel Order
```bash
DELETE /paper-trading/orders/{order_id}
```

### Sync Testnet Orders (Testnet Mode Only)
```bash
POST /paper-trading/orders/sync
```

### Get Account Info
```bash
GET /paper-trading/account
```

## Order Types Supported

### Market Orders
Executed immediately at current market price (with slippage in simulation mode).

```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "MARKET",
  "quantity": 0.001
}
```

### Limit Orders
Executed when market reaches specified price.

```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "LIMIT",
  "quantity": 0.001,
  "price": 95000.00,
  "time_in_force": "GTC"
}
```

### Stop Loss Orders
Triggered when price crosses stop price (sell to limit losses).

```json
{
  "symbol": "BTCUSDT",
  "side": "SELL",
  "order_type": "STOP_LOSS",
  "quantity": 0.001,
  "stop_price": 90000.00
}
```

### Take Profit Orders
Triggered when price reaches profit target.

```json
{
  "symbol": "BTCUSDT",
  "side": "SELL",
  "order_type": "TAKE_PROFIT",
  "quantity": 0.001,
  "stop_price": 105000.00
}
```

## Architecture

### Testnet Mode Flow
```
Your App → BinanceTestnetClient → Binance Testnet API
              ↓
         PostgreSQL (order records)
```

### Simulation Mode Flow
```
Your App → PaperTradingService → PostgreSQL
              ↓
         Simulated fills based on real prices
```

## Security Notes

🔒 **Important:**
- Testnet API keys are for testnet only - no real money access
- Never commit API keys to version control
- Use `.env` file for credentials
- Testnet keys cannot access real Binance accounts

## Testing

### Test Testnet Connection
```bash
curl -X GET http://localhost:8000/paper-trading/account
```

Should return:
```json
{
  "mode": "testnet",
  "testnet_connected": true,
  "balances": [...],
  "can_trade": true
}
```

### Test Order Creation
```bash
curl -X POST http://localhost:8000/paper-trading/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "order_type": "MARKET",
    "quantity": 0.001
  }'
```

## Troubleshooting

### "API credentials not configured"
- Make sure `BINANCE_TESTNET_API_KEY` and `BINANCE_TESTNET_API_SECRET` are set in `.env`
- Restart backend container after adding credentials

### Orders not filling (Simulation Mode)
- Call `POST /paper-trading/orders/process` to manually trigger fill checks
- Market orders fill immediately; limit orders wait for price

### Testnet orders not syncing
- Call `POST /paper-trading/orders/sync` to fetch latest status from Binance
- Check API key permissions

## Advantages of Testnet Mode

✅ **Real API behavior** - matches production exactly  
✅ **Actual order book** - realistic fills and slippage  
✅ **No maintenance** - Binance handles execution  
✅ **Free forever** - unlimited fake money  
✅ **Best practice** - test before using real API  

## Next Steps

1. Get testnet credentials from https://testnet.binance.vision/
2. Configure `.env` with API keys
3. Test with small orders
4. Build trading strategies
5. Ready for production (with real API keys)!

---

**Note:** This is paper trading with fake money. Perfect for testing strategies before risking real funds!
