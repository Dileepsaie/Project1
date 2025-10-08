"""
Fundamental Analysis Agent
===========================

PURPOSE:
Uses LLM to parse and analyze earnings reports, financial statements, and company fundamentals.

WHY LLM-POWERED:
- Automatically extracts key metrics from unstructured reports
- Identifies growth trends and red flags
- Reduces manual research time from hours to minutes
- Can process multiple reports simultaneously

ANALYSIS COMPONENTS:
- Earnings surprise (actual vs expected)
- Revenue growth trends
- Profit margin analysis
- Forward guidance sentiment
- Management commentary analysis
"""

import os
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from utils.logger import setup_logger

logger = setup_logger("fundamental_agent")


class FundamentalSignal(Enum):
    """Trading signals based on fundamental analysis"""
    STRONG_BUY = 2
    BUY = 1
    HOLD = 0
    SELL = -1
    STRONG_SELL = -2


class FundamentalMetrics(BaseModel):
    """
    Structured output from LLM fundamental analysis
    
    WHY PYDANTIC:
    - Ensures LLM outputs valid structured data
    - Type validation and parsing
    - Easy integration with other components
    """
    earnings_surprise_pct: float = Field(description="Earnings surprise as percentage")
    revenue_growth_yoy: float = Field(description="Year-over-year revenue growth percentage")
    profit_margin: float = Field(description="Net profit margin percentage")
    guidance_sentiment: str = Field(description="Forward guidance sentiment: positive/neutral/negative")
    key_highlights: List[str] = Field(description="Key highlights from the report")
    risk_factors: List[str] = Field(description="Identified risk factors")
    recommendation: str = Field(description="Investment recommendation")


@dataclass
class FundamentalAnalysis:
    """Results of fundamental analysis"""
    symbol: str
    signal: FundamentalSignal
    confidence: float
    metrics: FundamentalMetrics
    timestamp: datetime
    summary: str


class FundamentalAgent:
    """
    Agent that performs LLM-powered fundamental analysis
    
    WORKFLOW:
    1. Retrieve earnings report or financial data
    2. Feed to LLM with structured prompt
    3. Extract key metrics and insights
    4. Generate trading signal based on analysis
    """
    
    def __init__(self, model_name: str = "gpt-4o"):
        """
        Initialize Fundamental Analysis Agent
        
        WHY GPT-4O:
        - Superior reasoning for complex financial analysis
        - Better at extracting nuanced information
        - More accurate structured outputs
        """
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        # Setup structured output parser
        self.parser = PydanticOutputParser(pydantic_object=FundamentalMetrics)
        
        # Analysis prompt template
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial analyst. Analyze the following earnings report or financial data for {symbol}.
            
            Extract and calculate:
            1. Earnings surprise percentage (actual vs expected)
            2. Year-over-year revenue growth
            3. Net profit margin
            4. Forward guidance sentiment
            5. Key highlights (3-5 points)
            6. Risk factors (2-3 points)
            7. Overall investment recommendation
            
            {format_instructions}"""),
            ("user", "Financial Data:\n{financial_data}")
        ])
        
    async def analyze_fundamentals(self, symbol: str, financial_data: str) -> Optional[FundamentalAnalysis]:
        """
        Perform fundamental analysis on financial data
        
        WHY THIS MATTERS:
        - Earnings reports can move stocks 10-20% in a day
        - Automated analysis enables quick reaction
        - Identifies both opportunities and risks
        
        Args:
            symbol: Stock ticker
            financial_data: Raw financial data or earnings report text
            
        Returns:
            FundamentalAnalysis with trading signal
        """
        try:
            # Format prompt with parser instructions
            format_instructions = self.parser.get_format_instructions()
            
            chain = self.analysis_prompt | self.llm
            response = await chain.ainvoke({
                "symbol": symbol,
                "financial_data": financial_data,
                "format_instructions": format_instructions
            })
            
            # Parse structured output
            metrics = self.parser.parse(response.content)
            
            # Generate trading signal based on metrics
            signal = self._generate_signal(metrics)
            confidence = self._calculate_confidence(metrics)
            
            # Create summary
            summary = f"""
            Earnings surprise: {metrics.earnings_surprise_pct:+.1f}%
            Revenue growth: {metrics.revenue_growth_yoy:+.1f}%
            Profit margin: {metrics.profit_margin:.1f}%
            Guidance: {metrics.guidance_sentiment}
            Recommendation: {metrics.recommendation}
            """.strip()
            
            analysis = FundamentalAnalysis(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                metrics=metrics,
                timestamp=datetime.now(),
                summary=summary
            )
            
            logger.info(f"Fundamental analysis for {symbol}: {signal.name} (confidence: {confidence:.2f})")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in fundamental analysis for {symbol}: {str(e)}")
            return None
    
    def _generate_signal(self, metrics: FundamentalMetrics) -> FundamentalSignal:
        """
        Convert metrics to trading signal
        
        LOGIC:
        - Positive earnings surprise + growth + positive guidance = BUY
        - Negative metrics = SELL
        - Mixed signals = HOLD
        """
        score = 0
        
        # Earnings surprise contribution
        if metrics.earnings_surprise_pct > 10:
            score += 2
        elif metrics.earnings_surprise_pct > 0:
            score += 1
        elif metrics.earnings_surprise_pct < -10:
            score -= 2
        elif metrics.earnings_surprise_pct < 0:
            score -= 1
        
        # Revenue growth contribution
        if metrics.revenue_growth_yoy > 20:
            score += 1
        elif metrics.revenue_growth_yoy < 0:
            score -= 1
        
        # Guidance contribution
        if metrics.guidance_sentiment.lower() == "positive":
            score += 1
        elif metrics.guidance_sentiment.lower() == "negative":
            score -= 1
        
        # Map score to signal
        if score >= 3:
            return FundamentalSignal.STRONG_BUY
        elif score >= 1:
            return FundamentalSignal.BUY
        elif score <= -3:
            return FundamentalSignal.STRONG_SELL
        elif score <= -1:
            return FundamentalSignal.SELL
        else:
            return FundamentalSignal.HOLD
    
    def _calculate_confidence(self, metrics: FundamentalMetrics) -> float:
        """
        Calculate confidence in the analysis
        
        FACTORS:
        - Strong earnings surprise increases confidence
        - Consistent growth trends increase confidence
        - Clear guidance increases confidence
        """
        confidence = 0.5  # Base confidence
        
        # Boost for strong earnings
        if abs(metrics.earnings_surprise_pct) > 15:
            confidence += 0.2
        
        # Boost for strong growth
        if abs(metrics.revenue_growth_yoy) > 20:
            confidence += 0.1
        
        # Boost for clear guidance
        if metrics.guidance_sentiment.lower() in ["positive", "negative"]:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def get_mock_earnings_data(self, symbol: str) -> str:
        """
        Generate mock earnings data for testing
        
        WHY MOCK DATA:
        - Allows testing without API dependencies
        - Demonstrates expected input format
        - Useful for development and demos
        """
        mock_data = {
            "NVDA": """
            NVIDIA Q4 2024 Earnings Report:
            - Revenue: $22.1B (actual) vs $20.4B (expected) - Beat by 8.3%
            - EPS: $5.16 (actual) vs $4.64 (expected) - Beat by 11.2%
            - YoY Revenue Growth: 265%
            - Data Center Revenue: $18.4B (+409% YoY)
            - Gaming Revenue: $2.9B (-8% YoY)
            - Net Income: $12.3B (55.7% margin)
            - Q1 2025 Guidance: $24B (+/- 2%)
            - Management Commentary: Strong AI demand, expanding TAM, supply constraints easing
            """,
            "SPY": """
            S&P 500 (SPY) Market Analysis:
            - Year-to-date return: +12.5%
            - Earnings growth: +8.3% YoY across index
            - Forward P/E: 21.2x (vs 10-year avg of 18.5x)
            - Top sector: Technology (+18.2%)
            - Weakest sector: Financials (+3.1%)
            - Market breadth: 68% of stocks above 200-day MA
            - Economic backdrop: GDP growth 2.8%, inflation 3.2%
            """,
            "GLD": """
            Gold (GLD) Fundamental Analysis:
            - Current price: $195.50 (+15.3% YTD)
            - Global gold demand: +12% YoY
            - Central bank buying: 800 tons (+25% vs prior year)
            - Real rates: -0.8% (supportive for gold)
            - USD Index: 103.5 (-2.1% vs prior quarter)
            - Geopolitical tensions: Elevated (Ukraine, Middle East)
            - Inflation expectations: 3.0% (above Fed target)
            """,
            "GOOGL": """
            Alphabet (GOOGL) Q4 2024 Earnings:
            - Revenue: $86.3B (actual) vs $85.2B (expected) - Beat by 1.3%
            - EPS: $1.64 (actual) vs $1.59 (expected) - Beat by 3.1%
            - YoY Revenue Growth: 13.5%
            - Google Cloud: $9.2B (+25.7% YoY)
            - YouTube Ads: $8.1B (+15.5% YoY)
            - Operating Margin: 32%
            - Q1 2025 Guidance: Mid-teens revenue growth
            - AI investments: $12B capex in AI infrastructure
            """
        }
        
        return mock_data.get(symbol, "No earnings data available for this symbol.")
