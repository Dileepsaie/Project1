# 🏗️ System Architecture

Detailed architecture documentation for the Multi-Agent Trading System.

---

## Overview

The system follows a **multi-agent architecture** where specialized agents collaborate through a centralized state machine (LangGraph) to make trading decisions.

### Core Principles

1. **Modularity**: Each agent is independent and replaceable
2. **State Management**: LangGraph manages shared state between agents
3. **Asynchronous Processing**: Non-blocking operations for real-time data
4. **Risk-First Design**: Multiple layers of risk protection
5. **Observability**: Comprehensive logging at every step

---

## Agent Architecture

### 1. Market Data Agent

```
┌─────────────────────────────────┐
│     Market Data Agent           │
│                                 │
│  ┌─────────────────────────┐   │
│  │  Polygon.io API Client  │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │   Data Cache (Dict)     │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │  MarketData Objects     │   │
│  │  - Price                │   │
│  │  - Volume               │   │
│  │  - VWAP                 │   │
│  │  - OHLC                 │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

**Responsibilities**:
- Fetch real-time price data
- Retrieve historical data (30 days)
- Calculate VWAP
- Cache data for other agents

**Why Polygon.io**:
- Tick-level data (essential for scalping)
- <100ms latency
- Professional-grade reliability
- Multiple asset classes

---

### 2. Sentiment Analysis Agent

```
┌─────────────────────────────────┐
│    Sentiment Analysis Agent     │
│                                 │
│  ┌─────────────────────────┐   │
│  │  DuckDuckGo Scraper     │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │  News Headlines         │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │  LLM (GPT-4o-mini)      │   │
│  │  Sentiment Analysis     │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │  SentimentData          │   │
│  │  - Score (-2 to +2)     │   │
│  │  - Confidence (0-1)     │   │
│  │  - Summary              │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

**Responsibilities**:
- Scrape news headlines
- Analyze sentiment using LLM
- Generate confidence scores
- Provide actionable summary

**Why DuckDuckGo**:
- No API key required (free)
- Aggregates multiple news sources
- No rate limits
- Privacy-focused

---

### 3. Fundamental Analysis Agent

```
┌─────────────────────────────────┐
│   Fundamental Analysis Agent    │
│                                 │
│  ┌─────────────────────────┐   │
│  │  Earnings Data Source   │   │
│  │  (Mock/API)             │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │  LLM (GPT-4o)           │   │
│  │  Financial Analysis     │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │  Pydantic Parser        │   │
│  │  Structured Output      │   │
│  └─────────────────────────┘   │
│              │                  │
│              ▼                  │
│  ┌─────────────────────────┐   │
│  │  FundamentalMetrics     │   │
│  │  - Earnings surprise    │   │
│  │  - Revenue growth       │   │
│  │  - Profit margin        │   │
│  │  - Guidance sentiment   │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

**Responsibilities**:
- Parse earnings reports
- Extract key financial metrics
- Analyze growth trends
- Generate trading signals from fundamentals

**Why GPT-4o**:
- Superior reasoning for complex analysis
- Better structured outputs
- More accurate metric extraction

---

### 4. Strategy Agents

```
┌─────────────────────────────────────────────┐
│         Strategy Orchestrator               │
│                                             │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Momentum Strategy│  │ Mean Reversion  │ │
│  │                  │  │   Strategy      │ │
│  │ - MA Crossover   │  │ - Bollinger     │ │
│  │ - ROC            │  │   Bands         │ │
│  │ - Volume         │  │ - RSI           │ │
│  │                  │  │ - Z-Score       │ │
│  └──────────────────┘  └─────────────────┘ │
│           │                     │           │
│           └──────────┬──────────┘           │
│                      ▼                      │
│          ┌─────────────────────┐            │
│          │ Signal Combiner     │            │
│          │ - Weighted average  │            │
│          │ - Consensus logic   │            │
│          └─────────────────────┘            │
│                      │                      │
│                      ▼                      │
│          ┌─────────────────────┐            │
│          │  TradingSignal      │            │
│          │  - Direction        │            │
│          │  - Confidence       │            │
│          │  - Entry/SL/TP      │            │
│          └─────────────────────┘            │
└─────────────────────────────────────────────┘
```

**Momentum Strategy**:
- Trend-following approach
- Uses MA crossovers, ROC
- Best for trending markets
- 2% stop, 3% target

**Mean Reversion Strategy**:
- Counter-trend approach
- Uses Bollinger Bands, RSI
- Best for range-bound markets
- 1.5% stop, 2.5% target

**Signal Combination**:
- Requires consensus for strong signals
- Weights by confidence
- Reduces false positives

---

### 5. Risk Management Agent

```
┌─────────────────────────────────────────────┐
│        Risk Management Agent                │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Position Size Calculator           │   │
│  │                                     │   │
│  │  Formula:                           │   │
│  │  Size = Risk$ / (Entry - StopLoss)  │   │
│  └─────────────────────────────────────┘   │
│                    │                        │
│                    ▼                        │
│  ┌─────────────────────────────────────┐   │
│  │  Risk Validation                    │   │
│  │  - Max 2% per trade                 │   │
│  │  - Max 60% portfolio exposure       │   │
│  │  - Max 20% per position             │   │
│  └─────────────────────────────────────┘   │
│                    │                        │
│                    ▼                        │
│  ┌─────────────────────────────────────┐   │
│  │  Position Tracking                  │   │
│  │  - Entry price                      │   │
│  │  - Current P&L                      │   │
│  │  - Stop loss monitoring             │   │
│  └─────────────────────────────────────┘   │
│                    │                        │
│                    ▼                        │
│  ┌─────────────────────────────────────┐   │
│  │  Portfolio Metrics                  │   │
│  │  - Total exposure                   │   │
│  │  - VaR (95%)                        │   │
│  │  - Available capital                │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Risk Layers**:

1. **Trade Level**: 2% max loss per trade
2. **Portfolio Level**: 60% max exposure
3. **Position Level**: 20% max per stock

**Position Sizing Example**:
```
Capital: $100,000
Risk: 2% = $2,000
Entry: $100
Stop: $98
Risk/share: $2
Shares: $2,000 / $2 = 1,000

But capped at 20% of capital:
Max Position: $20,000
Actual Shares: 200
```

---

### 6. LangGraph Orchestrator

```
┌─────────────────────────────────────────────┐
│          LangGraph Orchestrator             │
│                                             │
│              Trading State                  │
│  ┌─────────────────────────────────────┐   │
│  │  symbols: [NVDA, SPY, GLD, GOOGL]   │   │
│  │  market_data: {...}                 │   │
│  │  sentiment_data: {...}              │   │
│  │  fundamental_data: {...}            │   │
│  │  signals: {...}                     │   │
│  │  risk_assessment: {...}             │   │
│  │  trades: [...]                      │   │
│  │  messages: [...]                    │   │
│  └─────────────────────────────────────┘   │
│                    │                        │
│                    ▼                        │
│         ┌──────────────────────┐            │
│         │   State Machine      │            │
│         │                      │            │
│         │  1. Market Data      │            │
│         │  2. Sentiment        │            │
│         │  3. Fundamentals     │            │
│         │  4. Signals          │            │
│         │  5. Risk             │            │
│         │  6. Execute          │            │
│         │  7. Monitor          │            │
│         └──────────────────────┘            │
└─────────────────────────────────────────────┘
```

**Workflow Steps**:

1. **collect_market_data**: Fetch prices from Polygon.io
2. **analyze_sentiment**: Scrape news and analyze
3. **analyze_fundamentals**: LLM parsing of earnings
4. **generate_signals**: Run strategies
5. **assess_risk**: Validate and size positions
6. **execute_trades**: Place orders (simulated)
7. **monitor_positions**: Check stop losses

**State Flow**:
```
Initial → Market Data → Sentiment → Fundamentals → 
Signals → Risk → Execute → Monitor → Final
```

---

## Data Flow Diagram

```
┌─────────────┐
│ Polygon.io  │──────┐
└─────────────┘      │
                     ▼
┌─────────────┐   ┌──────────────┐
│ DuckDuckGo  │──→│ LangGraph    │
└─────────────┘   │ Orchestrator │
                  │              │
┌─────────────┐   │  (State)     │
│ OpenAI LLM  │──→│              │
└─────────────┘   └──────────────┘
                        │
                        ▼
                  ┌──────────────┐
                  │   Trading    │
                  │   Signals    │
                  └──────────────┘
                        │
                        ▼
                  ┌──────────────┐
                  │     Risk     │
                  │  Management  │
                  └──────────────┘
                        │
                        ▼
                  ┌──────────────┐
                  │   Execute    │
                  │   (Simulated)│
                  └──────────────┘
```

---

## Technology Stack

### Core Framework
- **LangGraph 0.2.59**: State machine orchestration
- **LangChain 0.3.20**: LLM framework
- **LangChain-OpenAI 0.2.14**: OpenAI integration

### Data Processing
- **NumPy 1.26.4**: Numerical computing
- **Pandas 2.2.0**: Data manipulation

### Web & API
- **aiohttp 3.9.3**: Async HTTP client
- **BeautifulSoup4 4.12.3**: Web scraping
- **requests 2.31.0**: HTTP library

### Utilities
- **python-dotenv 1.0.1**: Environment variables
- **Pydantic 2.10.5**: Data validation

---

## Design Patterns

### 1. Agent Pattern
Each agent is self-contained with:
- Initialization
- Processing logic
- Error handling
- Logging

### 2. State Machine Pattern
LangGraph manages state transitions:
- Nodes = Agents
- Edges = Data flow
- State = Shared data structure

### 3. Strategy Pattern
Multiple trading strategies:
- Common interface (TradingSignal)
- Pluggable implementations
- Easy to add new strategies

### 4. Observer Pattern
Risk management observes:
- Portfolio state
- Position updates
- Stop loss triggers

---

## Scalability Considerations

### Horizontal Scaling
- Each symbol can be processed independently
- Parallel data fetching with asyncio
- Multiple strategy instances

### Vertical Scaling
- In-memory caching reduces API calls
- Efficient NumPy computations
- Optimized LLM prompts

### Extension Points
1. **New Data Sources**: Implement MarketDataAgent interface
2. **New Strategies**: Extend Strategy base class
3. **New Agents**: Add to LangGraph workflow
4. **New Risk Rules**: Modify RiskManagementAgent

---

## Error Handling

### Agent-Level
```python
try:
    # Agent logic
except Exception as e:
    logger.error(f"Error: {e}")
    return None  # Graceful degradation
```

### Workflow-Level
- LangGraph handles node failures
- State is preserved
- Retry logic available

### System-Level
- Continuous loop with error recovery
- Logs all errors for debugging
- Graceful shutdown on critical errors

---

## Performance Metrics

### Latency
- Market data fetch: <500ms
- Sentiment analysis: 2-3 seconds
- Fundamental analysis: 3-5 seconds
- Total cycle time: ~10-15 seconds

### Throughput
- 4 symbols per cycle
- 60-second cycle time
- ~240 analysis operations/hour

### Resource Usage
- Memory: ~500MB
- CPU: Low (mostly I/O bound)
- Network: Moderate (API calls)

---

## Security Considerations

### API Keys
- Stored in `.env` (never committed)
- Loaded via python-dotenv
- Never logged or exposed

### Data Privacy
- No PII collected
- News scraping is anonymous
- Trade data stored locally only

### Rate Limiting
- Respects API rate limits
- Exponential backoff on errors
- Configurable delays

---

## Future Enhancements

### Planned Features
1. **WebSocket Integration**: Real-time streaming data
2. **Backtesting Engine**: Historical strategy validation
3. **Paper Trading Mode**: Real broker API without real money
4. **Advanced Strategies**: ML-based signal generation
5. **Web Dashboard**: Real-time monitoring UI
6. **Alert System**: Email/SMS notifications

### Architecture Evolution
1. **Microservices**: Separate agents into services
2. **Message Queue**: Redis/RabbitMQ for communication
3. **Database**: PostgreSQL for trade history
4. **Caching Layer**: Redis for market data
5. **API Gateway**: FastAPI for external access

---

## Monitoring & Observability

### Logging
- Multi-level logging (DEBUG, INFO, WARNING, ERROR)
- File-based persistence
- Console output for real-time monitoring

### Metrics (Future)
- Prometheus metrics export
- Grafana dashboards
- Alert manager integration

### Tracing (Future)
- OpenTelemetry integration
- Distributed tracing
- Performance profiling

---

This architecture provides a solid foundation for algorithmic trading while maintaining flexibility for future enhancements.
