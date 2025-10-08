"""
Multi-Agent Trading System with LangGraph
==========================================

This is the main entry point for the real-time multi-agent trading system.

COMPONENTS:
- Market Data Agent: Fetches real-time data from Polygon.io
- Sentiment Agent: Scrapes news and analyzes sentiment from DuckDuckGo
- Fundamental Analysis Agent: Parses earnings reports using LLM
- Strategy Agents: Momentum and Mean Reversion strategies
- Risk Management Agent: Implements stop-loss and position sizing
- Orchestrator: Coordinates all agents using LangGraph

WHY THIS ARCHITECTURE:
- Modular design allows independent testing and deployment of each agent
- LangGraph provides state management and orchestration between agents
- Real-time data processing enables quick reaction to market changes
- Multiple strategies increase diversification and reduce risk
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

from agents.orchestrator import TradingOrchestrator
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging for monitoring system performance
logger = setup_logger("main")

# Stock symbols to track
TRACKED_SYMBOLS = ["NVDA", "SPY", "GLD", "GOOGL"]


async def main():
    """
    Main execution function
    
    WHY ASYNC:
    - Multiple agents need to run concurrently
    - Real-time data fetching requires non-blocking operations
    - Allows efficient handling of multiple stock symbols simultaneously
    """
    logger.info("=" * 50)
    logger.info("Starting Multi-Agent Trading System")
    logger.info(f"Tracked Symbols: {', '.join(TRACKED_SYMBOLS)}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 50)
    
    try:
        # Initialize the orchestrator
        # The orchestrator manages the LangGraph workflow and coordinates all agents
        orchestrator = TradingOrchestrator(symbols=TRACKED_SYMBOLS)
        
        # Start the trading system
        # This runs in a continuous loop, processing market data and executing trades
        await orchestrator.run()
        
    except KeyboardInterrupt:
        logger.info("Shutting down trading system gracefully...")
    except Exception as e:
        logger.error(f"Critical error in main execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # Entry point - ensures proper async execution
    asyncio.run(main())
