"""
LangGraph Trading Orchestrator
===============================

PURPOSE:
Coordinates all trading agents using LangGraph's state machine framework.

WHY LANGGRAPH:
- Provides structured workflow for agent coordination
- State management for complex multi-agent systems
- Built-in error handling and recovery
- Visual representation of agent flow
- Scalable architecture for adding new agents

WORKFLOW:
1. Market Data Collection
2. Sentiment Analysis
3. Fundamental Analysis
4. Strategy Signal Generation
5. Risk Assessment
6. Trade Execution
7. Position Monitoring
"""

import asyncio
from typing import Dict, List, Any, TypedDict, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from agents.market_data_agent import MarketDataAgent, MarketData
from agents.sentiment_agent import SentimentAgent
from agents.fundamental_agent import FundamentalAgent
from agents.strategy_agents import MomentumStrategy, MeanReversionStrategy, StrategyOrchestrator
from agents.risk_management_agent import RiskManagementAgent
from utils.logger import setup_logger

logger = setup_logger("orchestrator")


class TradingState(TypedDict):
    """
    State object that flows through the LangGraph workflow
    
    WHY TYPED DICT:
    - Type safety for state management
    - Clear contract for agent communication
    - Easy to validate and debug
    
    STATE COMPONENTS:
    - symbols: List of tickers to trade
    - market_data: Real-time price data
    - sentiment_data: News sentiment analysis
    - fundamental_data: Earnings and financials
    - signals: Trading signals from strategies
    - risk_assessment: Risk management decisions
    - trades: Executed trades
    - messages: Communication between agents
    """
    symbols: List[str]
    market_data: Dict[str, Any]
    sentiment_data: Dict[str, Any]
    fundamental_data: Dict[str, Any]
    signals: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    trades: Annotated[List[Dict], operator.add]  # Accumulate trades
    messages: Annotated[List, operator.add]  # Accumulate messages
    iteration: int


class TradingOrchestrator:
    """
    Main orchestrator that coordinates all trading agents
    
    ARCHITECTURE:
    - LangGraph state machine manages agent flow
    - Each agent processes state and returns updates
    - State flows through: Data -> Analysis -> Strategy -> Risk -> Execution
    - Continuous loop for real-time trading
    """
    
    def __init__(self, symbols: List[str]):
        """
        Initialize Trading Orchestrator
        
        Args:
            symbols: List of stock symbols to trade
        """
        self.symbols = symbols
        
        # Initialize all agents
        logger.info("Initializing trading agents...")
        self.market_agent = MarketDataAgent()
        self.sentiment_agent = SentimentAgent()
        self.fundamental_agent = FundamentalAgent()
        self.strategy_orchestrator = StrategyOrchestrator()
        self.risk_agent = RiskManagementAgent(total_capital=100000)
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        
        logger.info(f"Trading orchestrator initialized for symbols: {', '.join(symbols)}")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow
        
        WORKFLOW DESIGN:
        1. collect_market_data: Fetch real-time prices
        2. analyze_sentiment: Get news sentiment
        3. analyze_fundamentals: LLM-powered analysis
        4. generate_signals: Strategy signals
        5. assess_risk: Risk management check
        6. execute_trades: Place orders
        7. monitor_positions: Check stop losses
        
        WHY THIS FLOW:
        - Data collection before analysis
        - Multiple analysis types run in parallel (could optimize)
        - Risk assessment before execution (prevents bad trades)
        - Continuous monitoring for exits
        """
        # Create workflow graph
        workflow = StateGraph(TradingState)
        
        # Add nodes (agents)
        workflow.add_node("collect_market_data", self._collect_market_data)
        workflow.add_node("analyze_sentiment", self._analyze_sentiment)
        workflow.add_node("analyze_fundamentals", self._analyze_fundamentals)
        workflow.add_node("generate_signals", self._generate_signals)
        workflow.add_node("assess_risk", self._assess_risk)
        workflow.add_node("execute_trades", self._execute_trades)
        workflow.add_node("monitor_positions", self._monitor_positions)
        
        # Define edges (flow)
        workflow.set_entry_point("collect_market_data")
        workflow.add_edge("collect_market_data", "analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "analyze_fundamentals")
        workflow.add_edge("analyze_fundamentals", "generate_signals")
        workflow.add_edge("generate_signals", "assess_risk")
        workflow.add_edge("assess_risk", "execute_trades")
        workflow.add_edge("execute_trades", "monitor_positions")
        workflow.add_edge("monitor_positions", END)
        
        return workflow.compile()
    
    async def _collect_market_data(self, state: TradingState) -> TradingState:
        """
        Node: Collect real-time market data
        
        WHY FIRST:
        - Foundation for all other analysis
        - Ensures we have latest prices
        - Parallel collection for efficiency
        """
        logger.info("=" * 50)
        logger.info("STEP 1: Collecting Market Data")
        logger.info("=" * 50)
        
        market_data = {}
        
        # Fetch data for all symbols
        for symbol in state['symbols']:
            data = await self.market_agent.fetch_real_time_data(symbol)
            if data:
                market_data[symbol] = {
                    'current': data,
                    'historical': await self.market_agent.get_historical_data(symbol, days=30)
                }
        
        state['market_data'] = market_data
        state['messages'].append(HumanMessage(content=f"Collected market data for {len(market_data)} symbols"))
        
        return state
    
    async def _analyze_sentiment(self, state: TradingState) -> TradingState:
        """
        Node: Analyze market sentiment
        
        WHY IMPORTANT:
        - News drives short-term price action
        - Early sentiment detection provides edge
        - Complements technical analysis
        """
        logger.info("=" * 50)
        logger.info("STEP 2: Analyzing Sentiment")
        logger.info("=" * 50)
        
        sentiment_data = {}
        
        # Analyze sentiment for each symbol
        for symbol in state['symbols']:
            sentiment = await self.sentiment_agent.analyze_sentiment(symbol)
            if sentiment:
                sentiment_data[symbol] = sentiment
        
        state['sentiment_data'] = sentiment_data
        state['messages'].append(AIMessage(content=f"Sentiment analysis complete for {len(sentiment_data)} symbols"))
        
        return state
    
    async def _analyze_fundamentals(self, state: TradingState) -> TradingState:
        """
        Node: Perform fundamental analysis
        
        WHY LLM-POWERED:
        - Automates earnings report parsing
        - Identifies key metrics quickly
        - Scales to multiple stocks
        """
        logger.info("=" * 50)
        logger.info("STEP 3: Analyzing Fundamentals")
        logger.info("=" * 50)
        
        fundamental_data = {}
        
        # Analyze fundamentals for each symbol
        for symbol in state['symbols']:
            # Get mock earnings data (in production, fetch from API)
            earnings_data = await self.fundamental_agent.get_mock_earnings_data(symbol)
            
            analysis = await self.fundamental_agent.analyze_fundamentals(symbol, earnings_data)
            if analysis:
                fundamental_data[symbol] = analysis
        
        state['fundamental_data'] = fundamental_data
        state['messages'].append(AIMessage(content=f"Fundamental analysis complete for {len(fundamental_data)} symbols"))
        
        return state
    
    async def _generate_signals(self, state: TradingState) -> TradingState:
        """
        Node: Generate trading signals from strategies
        
        WHY MULTIPLE STRATEGIES:
        - Momentum for trending markets
        - Mean reversion for ranging markets
        - Combined signals reduce false positives
        """
        logger.info("=" * 50)
        logger.info("STEP 4: Generating Trading Signals")
        logger.info("=" * 50)
        
        signals = {}
        
        for symbol in state['symbols']:
            if symbol not in state['market_data']:
                continue
            
            market_data = state['market_data'][symbol]
            current_data = market_data['current']
            historical_data = market_data['historical']
            
            # Generate signals from both strategies
            momentum_signal = self.strategy_orchestrator.momentum.generate_signal(
                symbol, current_data, historical_data
            )
            
            mean_reversion_signal = self.strategy_orchestrator.mean_reversion.generate_signal(
                symbol, current_data, historical_data
            )
            
            # Combine signals
            strategy_signals = [s for s in [momentum_signal, mean_reversion_signal] if s]
            
            if strategy_signals:
                combined = self.strategy_orchestrator.combine_signals(strategy_signals)
                if combined:
                    signals[symbol] = {
                        'combined': combined,
                        'momentum': momentum_signal,
                        'mean_reversion': mean_reversion_signal
                    }
        
        state['signals'] = signals
        state['messages'].append(AIMessage(content=f"Generated signals for {len(signals)} symbols"))
        
        return state
    
    async def _assess_risk(self, state: TradingState) -> TradingState:
        """
        Node: Assess risk and validate trades
        
        WHY CRITICAL:
        - Prevents overexposure
        - Enforces 2% max loss per trade
        - Protects capital
        """
        logger.info("=" * 50)
        logger.info("STEP 5: Risk Assessment")
        logger.info("=" * 50)
        
        risk_assessment = {}
        
        for symbol, signal_data in state['signals'].items():
            combined_signal = signal_data['combined']
            
            # Check if trade should be taken
            should_take, reason = self.risk_agent.should_take_trade(combined_signal)
            
            if should_take:
                # Calculate position size
                current_price = state['market_data'][symbol]['current'].price
                position_size = self.risk_agent.calculate_position_size(combined_signal, current_price)
                
                risk_assessment[symbol] = {
                    'approved': True,
                    'signal': combined_signal,
                    'position_size': position_size,
                    'reason': reason
                }
                
                logger.info(f"✓ Trade APPROVED for {symbol}: {position_size.shares} shares, Risk: ${position_size.risk_dollars:,.0f}")
            else:
                risk_assessment[symbol] = {
                    'approved': False,
                    'signal': combined_signal,
                    'reason': reason
                }
                
                logger.info(f"✗ Trade REJECTED for {symbol}: {reason}")
        
        state['risk_assessment'] = risk_assessment
        state['messages'].append(AIMessage(content=f"Risk assessment complete"))
        
        return state
    
    async def _execute_trades(self, state: TradingState) -> TradingState:
        """
        Node: Execute approved trades
        
        WHY SIMULATED:
        - Demonstrates trade execution flow
        - In production, would connect to broker API
        - Logs all trade details for audit
        """
        logger.info("=" * 50)
        logger.info("STEP 6: Executing Trades")
        logger.info("=" * 50)
        
        trades = []
        
        for symbol, assessment in state['risk_assessment'].items():
            if assessment['approved']:
                signal = assessment['signal']
                position_size = assessment['position_size']
                
                # Execute trade (simulated)
                direction = 'LONG' if signal.signal.value > 0 else 'SHORT'
                
                trade = {
                    'symbol': symbol,
                    'direction': direction,
                    'shares': position_size.shares,
                    'entry_price': signal.entry_price,
                    'stop_loss': position_size.stop_loss_price,
                    'take_profit': signal.take_profit,
                    'risk_dollars': position_size.risk_dollars,
                    'timestamp': datetime.now(),
                    'strategy': signal.strategy_name,
                    'reasoning': signal.reasoning
                }
                
                # Add to risk agent tracking
                self.risk_agent.add_position(
                    symbol=symbol,
                    shares=position_size.shares,
                    entry_price=signal.entry_price,
                    stop_loss=position_size.stop_loss_price,
                    direction=direction
                )
                
                trades.append(trade)
                
                logger.info(f"📈 EXECUTED: {direction} {position_size.shares} {symbol} @ ${signal.entry_price:.2f}")
                logger.info(f"   Stop Loss: ${position_size.stop_loss_price:.2f}, Take Profit: ${signal.take_profit:.2f}")
                logger.info(f"   Reasoning: {signal.reasoning}")
        
        state['trades'].extend(trades)
        state['messages'].append(AIMessage(content=f"Executed {len(trades)} trades"))
        
        return state
    
    async def _monitor_positions(self, state: TradingState) -> TradingState:
        """
        Node: Monitor open positions and check stop losses
        
        WHY CONTINUOUS:
        - Markets move quickly
        - Stop losses protect capital
        - Auto-exit on adverse moves
        """
        logger.info("=" * 50)
        logger.info("STEP 7: Monitoring Positions")
        logger.info("=" * 50)
        
        # Update positions with current prices
        for symbol in state['symbols']:
            if symbol in state['market_data']:
                current_price = state['market_data'][symbol]['current'].price
                self.risk_agent.update_position(symbol, current_price)
                
                # Check stop loss
                if self.risk_agent.check_stop_loss(symbol, current_price):
                    # Close position
                    result = self.risk_agent.close_position(symbol, current_price)
                    logger.warning(f"🛑 STOP LOSS: Closed {symbol} - P&L: ${result.get('pnl', 0):+,.2f}")
        
        # Calculate and log portfolio metrics
        metrics = self.risk_agent.calculate_portfolio_metrics()
        logger.info(f"Portfolio: {metrics.current_positions} positions, ${metrics.total_exposure:,.0f} exposure, ${metrics.available_capital:,.0f} available")
        
        state['messages'].append(AIMessage(content="Position monitoring complete"))
        
        return state
    
    async def run(self):
        """
        Main execution loop
        
        FLOW:
        1. Initialize state
        2. Run LangGraph workflow
        3. Sleep for interval
        4. Repeat
        
        WHY LOOP:
        - Real-time trading requires continuous monitoring
        - Markets change constantly
        - New opportunities appear frequently
        """
        iteration = 0
        
        while True:
            try:
                iteration += 1
                logger.info(f"\n{'='*70}")
                logger.info(f"TRADING CYCLE #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*70}\n")
                
                # Initialize state
                initial_state: TradingState = {
                    'symbols': self.symbols,
                    'market_data': {},
                    'sentiment_data': {},
                    'fundamental_data': {},
                    'signals': {},
                    'risk_assessment': {},
                    'trades': [],
                    'messages': [],
                    'iteration': iteration
                }
                
                # Run workflow
                final_state = await self.workflow.ainvoke(initial_state)
                
                # Log summary
                logger.info(f"\n{'='*70}")
                logger.info(f"CYCLE #{iteration} COMPLETE")
                logger.info(f"Trades executed: {len(final_state.get('trades', []))}")
                logger.info(f"Messages: {len(final_state.get('messages', []))}")
                logger.info(f"{'='*70}\n")
                
                # Sleep before next cycle (in production, would be much shorter)
                await asyncio.sleep(60)  # Run every 60 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in trading cycle: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Brief pause before retry
