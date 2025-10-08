"""
Market Data Agent
=================

PURPOSE:
Fetches real-time market data from Polygon.io API for price discovery and technical analysis.

WHY POLYGON.IO:
- Provides tick-level data for scalping strategies
- Real-time updates with minimal latency
- Professional-grade market data
- Supports multiple asset classes
"""

import os
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass

from utils.logger import setup_logger

logger = setup_logger("market_data_agent")


@dataclass
class MarketData:
    """
    Data structure for market information
    
    WHY DATACLASS:
    - Type safety and validation
    - Cleaner serialization
    - Easy to extend with new fields
    """
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    vwap: Optional[float] = None  # Volume Weighted Average Price for better entry/exit
    

class MarketDataAgent:
    """
    Agent responsible for fetching and processing real-time market data
    
    RESPONSIBILITIES:
    1. Connect to Polygon.io WebSocket/REST API
    2. Stream real-time tick data
    3. Calculate technical indicators
    4. Provide data to strategy agents
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Market Data Agent
        
        Args:
            api_key: Polygon.io API key (falls back to environment variable)
        """
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            logger.warning("POLYGON_API_KEY not found. Using simulated data.")
        
        self.base_url = "https://api.polygon.io"
        self.data_cache: Dict[str, MarketData] = {}
        
    async def fetch_real_time_data(self, symbol: str) -> Optional[MarketData]:
        """
        Fetch real-time market data for a symbol
        
        WHY REAL-TIME:
        - Scalping requires up-to-the-second data
        - Market conditions change rapidly
        - Enables quick reaction to price movements
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            MarketData object or None if fetch fails
        """
        try:
            # Use previous day's close as endpoint for current data
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/prev"
            params = {"apiKey": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("results"):
                            result = data["results"][0]
                            
                            market_data = MarketData(
                                symbol=symbol,
                                price=result["c"],  # Close price
                                volume=result["v"],
                                timestamp=datetime.fromtimestamp(result["t"] / 1000),
                                open=result["o"],
                                high=result["h"],
                                low=result["l"],
                                close=result["c"],
                                vwap=result.get("vw")
                            )
                            
                            # Cache for other agents
                            self.data_cache[symbol] = market_data
                            
                            logger.info(f"Fetched data for {symbol}: ${market_data.price}")
                            return market_data
                    else:
                        logger.error(f"API error for {symbol}: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            
        return None
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> List[MarketData]:
        """
        Fetch historical data for technical analysis
        
        WHY HISTORICAL DATA:
        - Calculate moving averages and indicators
        - Identify support/resistance levels
        - Train/validate trading strategies
        
        Args:
            symbol: Stock ticker
            days: Number of days of history
            
        Returns:
            List of MarketData objects
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {"apiKey": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        historical_data = []
                        for result in data.get("results", []):
                            historical_data.append(MarketData(
                                symbol=symbol,
                                price=result["c"],
                                volume=result["v"],
                                timestamp=datetime.fromtimestamp(result["t"] / 1000),
                                open=result["o"],
                                high=result["h"],
                                low=result["l"],
                                close=result["c"],
                                vwap=result.get("vw")
                            ))
                        
                        logger.info(f"Fetched {len(historical_data)} days of historical data for {symbol}")
                        return historical_data
                        
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            
        return []
    
    def get_cached_data(self, symbol: str) -> Optional[MarketData]:
        """Get cached market data without API call"""
        return self.data_cache.get(symbol)
