# 🚀 Quick Start Guide

Get your multi-agent trading system running in 5 minutes!

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Get API Keys

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Copy the key (starts with `sk-...`)

#### Polygon.io API Key
1. Go to https://polygon.io/dashboard/signup
2. Sign up for free account
3. Copy API key from dashboard

### 3. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

Add your API keys:
```
OPENAI_API_KEY=sk-your-key-here
POLYGON_API_KEY=your-polygon-key-here
```

### 4. Run the System

```bash
python main.py
```

## What Happens Next?

The system will:

1. ✅ Initialize all agents
2. ✅ Fetch real-time data for NVDA, SPY, GLD, GOOGL
3. ✅ Analyze sentiment from news
4. ✅ Parse fundamentals with LLM
5. ✅ Generate trading signals
6. ✅ Assess risk
7. ✅ Execute trades (simulated)
8. ✅ Monitor positions

## Expected Output

```
==================================================
Starting Multi-Agent Trading System
Tracked Symbols: NVDA, SPY, GLD, GOOGL
==================================================

STEP 1: Collecting Market Data
INFO | Fetched data for NVDA: $875.50
INFO | Fetched data for SPY: $450.20
INFO | Fetched data for GLD: $195.30
INFO | Fetched data for GOOGL: $140.80

STEP 2: Analyzing Sentiment
INFO | Sentiment for NVDA: BULLISH (0.75)
INFO | Sentiment for SPY: NEUTRAL (0.50)
INFO | Sentiment for GLD: BULLISH (0.68)
INFO | Sentiment for GOOGL: BEARISH (0.45)

STEP 3: Analyzing Fundamentals
INFO | Fundamental analysis for NVDA: BUY (0.82)
INFO | Fundamental analysis for SPY: HOLD (0.60)
INFO | Fundamental analysis for GLD: BUY (0.71)
INFO | Fundamental analysis for GOOGL: HOLD (0.55)

STEP 4: Generating Trading Signals
INFO | Momentum signal for NVDA: STRONG_BUY
INFO | Mean reversion signal for NVDA: BUY
INFO | Combined signal for NVDA: STRONG_BUY (0.85)

STEP 5: Risk Assessment
INFO | ✓ Trade APPROVED for NVDA: 228 shares, Risk: $1,996
INFO | ✗ Trade REJECTED for SPY: Neutral signal
INFO | ✓ Trade APPROVED for GLD: 512 shares, Risk: $1,998

STEP 6: Executing Trades
INFO | 📈 EXECUTED: LONG 228 NVDA @ $875.50
INFO |    Stop Loss: $857.59, Take Profit: $901.97
INFO | 📈 EXECUTED: LONG 512 GLD @ $195.30
INFO |    Stop Loss: $191.36, Take Profit: $200.70

STEP 7: Monitoring Positions
INFO | Portfolio: 2 positions, $299,450 exposure, $100,550 available
```

## Customization

### Change Tracked Symbols

Edit `main.py`:
```python
TRACKED_SYMBOLS = ["AAPL", "MSFT", "TSLA", "AMD"]  # Your choices
```

### Adjust Risk Parameters

Edit `.env`:
```
MAX_RISK_PER_TRADE=0.01  # 1% instead of 2%
MAX_PORTFOLIO_EXPOSURE=0.50  # 50% instead of 60%
```

### Change Update Frequency

Edit `agents/orchestrator.py`:
```python
await asyncio.sleep(30)  # Run every 30 seconds instead of 60
```

## Troubleshooting

### Issue: Import Error

```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: API Rate Limiting

```
Error: 429 Too Many Requests
```

**Solution**: 
- Polygon.io free tier: 5 requests/minute
- Increase sleep time in orchestrator
- Or upgrade to paid plan

### Issue: No News Headlines

```
WARNING | No headlines found for NVDA
```

**Solution**: 
- This is normal if DuckDuckGo is busy
- System continues with other analysis
- Not critical for operation

### Issue: OpenAI Timeout

```
Error: Request timed out
```

**Solution**: 
- Increase timeout in agents (default: 60s)
- Check internet connection
- Verify API key is valid

## Next Steps

1. **Run for a few cycles** to see the system in action
2. **Check logs** in `logs/trading_YYYYMMDD.log`
3. **Modify strategies** in `agents/strategy_agents.py`
4. **Add new agents** following the modular pattern
5. **Connect to broker API** for live trading (advanced)

## Learning Resources

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Polygon.io Docs**: https://polygon.io/docs
- **Trading Strategies**: Read comments in `agents/strategy_agents.py`

## Need Help?

- 📖 Full documentation: See `README.md`
- 🐛 Issues: Create GitHub issue
- 💬 Questions: Check code comments (every function explained)

---

**Happy Trading!** 🚀📈
