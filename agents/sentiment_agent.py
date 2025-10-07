"""
Sentiment Analysis Agent
=========================

PURPOSE:
Scrapes news and social media data to determine market sentiment for stocks.

WHY SENTIMENT ANALYSIS:
- Market moves on news and emotions, not just fundamentals
- Early detection of sentiment shifts can predict price movements
- Combines with technical analysis for stronger signals

DATA SOURCES:
- DuckDuckGo news search (no API key needed)
- Aggregates headlines and snippets
- Analyzes using LLM for sentiment scoring
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from utils.logger import setup_logger

logger = setup_logger("sentiment_agent")


class SentimentScore(Enum):
    """
    Sentiment categories
    
    WHY ENUM:
    - Type-safe sentiment values
    - Easy to extend with new categories
    - Clear semantic meaning
    """
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2


@dataclass
class SentimentData:
    """Market sentiment information"""
    symbol: str
    score: SentimentScore
    confidence: float  # 0.0 to 1.0
    headlines: List[str]
    timestamp: datetime
    summary: str


class SentimentAgent:
    """
    Agent for analyzing market sentiment from news sources
    
    WORKFLOW:
    1. Scrape news headlines from DuckDuckGo
    2. Extract relevant articles for each symbol
    3. Use LLM to analyze sentiment
    4. Generate sentiment score and confidence
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize Sentiment Agent
        
        WHY GPT-4O-MINI:
        - Cost-effective for high-frequency analysis
        - Fast inference for real-time decisions
        - Good enough accuracy for sentiment classification
        """
        self.llm = ChatOpenAI(model=model_name, temperature=0.3)
        
        # Prompt template for sentiment analysis
        # WHY STRUCTURED PROMPT: Ensures consistent, comparable outputs
        self.sentiment_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial sentiment analyst. Analyze the following news headlines about {symbol} 
            and provide:
            1. Overall sentiment score (-2 to 2): -2=Very Bearish, -1=Bearish, 0=Neutral, 1=Bullish, 2=Very Bullish
            2. Confidence level (0.0 to 1.0)
            3. Brief summary of key points
            
            Format your response as:
            SCORE: [number]
            CONFIDENCE: [number]
            SUMMARY: [text]"""),
            ("user", "Headlines:\n{headlines}")
        ])
        
    async def scrape_duckduckgo_news(self, symbol: str) -> List[str]:
        """
        Scrape news headlines from DuckDuckGo
        
        WHY DUCKDUCKGO:
        - No API key required
        - Good news aggregation
        - Privacy-focused (no tracking)
        - Works well with web scraping
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            List of news headlines
        """
        try:
            # Build search query for financial news
            search_query = f"{symbol} stock news market"
            url = f"https://duckduckgo.com/html/?q={search_query}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract headlines from search results
                        headlines = []
                        for result in soup.find_all('a', class_='result__a', limit=10):
                            title = result.get_text(strip=True)
                            if title:
                                headlines.append(title)
                        
                        logger.info(f"Scraped {len(headlines)} headlines for {symbol}")
                        return headlines
                    else:
                        logger.error(f"DuckDuckGo scraping failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error scraping DuckDuckGo for {symbol}: {str(e)}")
            
        return []
    
    async def analyze_sentiment(self, symbol: str) -> Optional[SentimentData]:
        """
        Analyze market sentiment for a symbol
        
        PROCESS:
        1. Scrape recent news headlines
        2. Feed to LLM for analysis
        3. Parse LLM output
        4. Return structured sentiment data
        
        Args:
            symbol: Stock ticker
            
        Returns:
            SentimentData object with analysis results
        """
        try:
            # Get headlines
            headlines = await self.scrape_duckduckgo_news(symbol)
            
            if not headlines:
                logger.warning(f"No headlines found for {symbol}")
                return None
            
            # Analyze with LLM
            chain = self.sentiment_prompt | self.llm
            response = await chain.ainvoke({
                "symbol": symbol,
                "headlines": "\n".join(f"- {h}" for h in headlines)
            })
            
            # Parse response
            content = response.content
            lines = content.split('\n')
            
            score = 0
            confidence = 0.5
            summary = ""
            
            for line in lines:
                if line.startswith("SCORE:"):
                    score = int(line.split(':')[1].strip())
                elif line.startswith("CONFIDENCE:"):
                    confidence = float(line.split(':')[1].strip())
                elif line.startswith("SUMMARY:"):
                    summary = line.split(':', 1)[1].strip()
            
            sentiment_data = SentimentData(
                symbol=symbol,
                score=SentimentScore(score),
                confidence=confidence,
                headlines=headlines,
                timestamp=datetime.now(),
                summary=summary
            )
            
            logger.info(f"Sentiment for {symbol}: {sentiment_data.score.name} (confidence: {confidence:.2f})")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
            return None
