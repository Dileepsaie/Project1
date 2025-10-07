"""
Strategy Agents
===============

PURPOSE:
Implements different trading strategies as modular agents:
1. Momentum Strategy - Trades in direction of strong price movements
2. Mean Reversion Strategy - Trades against extreme price moves expecting reversal

WHY MULTIPLE STRATEGIES:
- Diversification reduces risk
- Different strategies perform better in different market conditions
- Momentum works in trending markets, mean reversion in ranging markets
- Can be deployed/disabled independently based on market regime
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from agents.market_data_agent import MarketData
from utils.logger import setup_logger

logger = setup_logger("strategy_agents")


class SignalType(Enum):
    """Trading signal types"""
    STRONG_BUY = 2
    BUY = 1
    NEUTRAL = 0
    SELL = -1
    STRONG_SELL = -2


@dataclass
class TradingSignal:
    """
    Trading signal output from strategies
    
    COMPONENTS:
    - signal: Direction and strength
    - confidence: How confident is the strategy (0-1)
    - entry_price: Suggested entry price
    - stop_loss: Suggested stop loss price
    - take_profit: Suggested take profit price
    - reasoning: Why this signal was generated
    """
    symbol: str
    signal: SignalType
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    reasoning: str
    strategy_name: str


class MomentumStrategy:
    """
    Momentum Trading Strategy
    
    CONCEPT:
    - "The trend is your friend"
    - Buy when price shows strong upward momentum
    - Sell when momentum reverses
    
    INDICATORS USED:
    - Rate of Change (ROC)
    - Moving Average Crossovers
    - Volume confirmation
    - Relative Strength
    
    BEST FOR:
    - Trending markets
    - Breakout scenarios
    - News-driven moves
    """
    
    def __init__(self, 
                 short_window: int = 10,
                 long_window: int = 30,
                 roc_period: int = 14):
        """
        Initialize Momentum Strategy
        
        Args:
            short_window: Short-term moving average period
            long_window: Long-term moving average period
            roc_period: Rate of change lookback period
        """
        self.short_window = short_window
        self.long_window = long_window
        self.roc_period = roc_period
        self.name = "Momentum"
        
    def generate_signal(self, 
                        symbol: str,
                        current_data: MarketData,
                        historical_data: List[MarketData]) -> Optional[TradingSignal]:
        """
        Generate momentum-based trading signal
        
        LOGIC:
        1. Calculate short and long moving averages
        2. Calculate rate of change
        3. Check volume confirmation
        4. Generate signal if momentum is strong
        
        Args:
            symbol: Stock ticker
            current_data: Latest market data
            historical_data: Historical price data
            
        Returns:
            TradingSignal if conditions met, else None
        """
        try:
            if len(historical_data) < self.long_window:
                logger.warning(f"Insufficient data for momentum strategy on {symbol}")
                return None
            
            # Extract prices
            prices = np.array([d.close for d in historical_data])
            volumes = np.array([d.volume for d in historical_data])
            
            # Calculate moving averages
            sma_short = np.mean(prices[-self.short_window:])
            sma_long = np.mean(prices[-self.long_window:])
            
            # Calculate rate of change
            if len(prices) > self.roc_period:
                roc = ((prices[-1] - prices[-self.roc_period]) / prices[-self.roc_period]) * 100
            else:
                roc = 0
            
            # Volume confirmation (current volume vs average)
            avg_volume = np.mean(volumes[-20:])
            volume_ratio = current_data.volume / avg_volume if avg_volume > 0 else 1
            
            # Generate signal
            signal = SignalType.NEUTRAL
            confidence = 0.5
            reasoning = ""
            
            # Bullish momentum conditions
            if sma_short > sma_long and roc > 2:
                if volume_ratio > 1.5:
                    signal = SignalType.STRONG_BUY
                    confidence = 0.8
                    reasoning = f"Strong upward momentum: ROC={roc:.1f}%, MA crossover bullish, high volume"
                else:
                    signal = SignalType.BUY
                    confidence = 0.6
                    reasoning = f"Moderate upward momentum: ROC={roc:.1f}%, MA crossover bullish"
            
            # Bearish momentum conditions
            elif sma_short < sma_long and roc < -2:
                if volume_ratio > 1.5:
                    signal = SignalType.STRONG_SELL
                    confidence = 0.8
                    reasoning = f"Strong downward momentum: ROC={roc:.1f}%, MA crossover bearish, high volume"
                else:
                    signal = SignalType.SELL
                    confidence = 0.6
                    reasoning = f"Moderate downward momentum: ROC={roc:.1f}%, MA crossover bearish"
            
            else:
                reasoning = f"No clear momentum: ROC={roc:.1f}%, MA diff={((sma_short-sma_long)/sma_long*100):.1f}%"
            
            # Calculate stop loss and take profit
            # WHY THESE LEVELS: 2% risk, 1.5:1 reward-to-risk ratio
            if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                stop_loss = current_data.price * 0.98  # 2% stop loss
                take_profit = current_data.price * 1.03  # 3% take profit (1.5:1 R:R)
            elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
                stop_loss = current_data.price * 1.02
                take_profit = current_data.price * 0.97
            else:
                stop_loss = current_data.price
                take_profit = current_data.price
            
            trading_signal = TradingSignal(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                entry_price=current_data.price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                timestamp=datetime.now(),
                reasoning=reasoning,
                strategy_name=self.name
            )
            
            logger.info(f"Momentum signal for {symbol}: {signal.name} ({reasoning})")
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating momentum signal for {symbol}: {str(e)}")
            return None


class MeanReversionStrategy:
    """
    Mean Reversion Trading Strategy
    
    CONCEPT:
    - "What goes up must come down (and vice versa)"
    - Buy when price is oversold (below statistical mean)
    - Sell when price is overbought (above statistical mean)
    
    INDICATORS USED:
    - Bollinger Bands
    - RSI (Relative Strength Index)
    - Z-Score
    
    BEST FOR:
    - Range-bound markets
    - Low volatility periods
    - Counter-trend opportunities
    """
    
    def __init__(self,
                 bb_period: int = 20,
                 bb_std: float = 2.0,
                 rsi_period: int = 14):
        """
        Initialize Mean Reversion Strategy
        
        Args:
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation
            rsi_period: RSI calculation period
        """
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.name = "Mean Reversion"
        
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """
        Calculate Relative Strength Index
        
        WHY RSI:
        - Identifies overbought (>70) and oversold (<30) conditions
        - Leading indicator for reversals
        - Widely used and reliable
        """
        if len(prices) < period + 1:
            return 50  # Neutral
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signal(self,
                        symbol: str,
                        current_data: MarketData,
                        historical_data: List[MarketData]) -> Optional[TradingSignal]:
        """
        Generate mean reversion trading signal
        
        LOGIC:
        1. Calculate Bollinger Bands
        2. Calculate RSI
        3. Look for price at extremes
        4. Generate reversal signal
        
        Args:
            symbol: Stock ticker
            current_data: Latest market data
            historical_data: Historical price data
            
        Returns:
            TradingSignal if conditions met, else None
        """
        try:
            if len(historical_data) < self.bb_period:
                logger.warning(f"Insufficient data for mean reversion strategy on {symbol}")
                return None
            
            # Extract prices
            prices = np.array([d.close for d in historical_data])
            
            # Calculate Bollinger Bands
            sma = np.mean(prices[-self.bb_period:])
            std = np.std(prices[-self.bb_period:])
            upper_band = sma + (self.bb_std * std)
            lower_band = sma - (self.bb_std * std)
            
            # Calculate RSI
            rsi = self.calculate_rsi(prices, self.rsi_period)
            
            # Calculate Z-Score (how many std devs from mean)
            z_score = (current_data.price - sma) / std if std > 0 else 0
            
            # Generate signal
            signal = SignalType.NEUTRAL
            confidence = 0.5
            reasoning = ""
            
            # Oversold conditions (potential buy)
            if current_data.price <= lower_band and rsi < 30:
                signal = SignalType.STRONG_BUY
                confidence = 0.85
                reasoning = f"Oversold: Price at lower BB, RSI={rsi:.1f}, Z-score={z_score:.2f}"
            elif current_data.price <= lower_band or rsi < 35:
                signal = SignalType.BUY
                confidence = 0.65
                reasoning = f"Near oversold: Price={current_data.price:.2f}, RSI={rsi:.1f}"
            
            # Overbought conditions (potential sell)
            elif current_data.price >= upper_band and rsi > 70:
                signal = SignalType.STRONG_SELL
                confidence = 0.85
                reasoning = f"Overbought: Price at upper BB, RSI={rsi:.1f}, Z-score={z_score:.2f}"
            elif current_data.price >= upper_band or rsi > 65:
                signal = SignalType.SELL
                confidence = 0.65
                reasoning = f"Near overbought: Price={current_data.price:.2f}, RSI={rsi:.1f}"
            
            else:
                reasoning = f"In range: SMA={sma:.2f}, RSI={rsi:.1f}, Z-score={z_score:.2f}"
            
            # Calculate stop loss and take profit for mean reversion
            # WHY TIGHTER STOPS: Mean reversion trades expect quick moves
            if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                stop_loss = current_data.price * 0.985  # 1.5% stop
                take_profit = min(sma * 1.005, current_data.price * 1.025)  # Revert to mean or 2.5%
            elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
                stop_loss = current_data.price * 1.015
                take_profit = max(sma * 0.995, current_data.price * 0.975)
            else:
                stop_loss = current_data.price
                take_profit = current_data.price
            
            trading_signal = TradingSignal(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                entry_price=current_data.price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                timestamp=datetime.now(),
                reasoning=reasoning,
                strategy_name=self.name
            )
            
            logger.info(f"Mean reversion signal for {symbol}: {signal.name} ({reasoning})")
            return trading_signal
            
        except Exception as e:
            logger.error(f"Error generating mean reversion signal for {symbol}: {str(e)}")
            return None


class StrategyOrchestrator:
    """
    Orchestrates multiple strategies and combines their signals
    
    WHY ORCHESTRATION:
    - Multiple strategies provide confirmation
    - Reduces false signals
    - Adapts to different market conditions
    - Can weight strategies based on performance
    """
    
    def __init__(self):
        self.momentum = MomentumStrategy()
        self.mean_reversion = MeanReversionStrategy()
        
    def combine_signals(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """
        Combine multiple strategy signals into one consensus signal
        
        APPROACH:
        - Weight signals by confidence
        - Require agreement for strong signals
        - Use highest confidence signal as base
        
        Args:
            signals: List of signals from different strategies
            
        Returns:
            Combined trading signal
        """
        if not signals:
            return None
        
        # Filter out neutral signals
        active_signals = [s for s in signals if s.signal != SignalType.NEUTRAL]
        
        if not active_signals:
            # All neutral, return first
            return signals[0]
        
        # Check for consensus
        buy_signals = [s for s in active_signals if s.signal.value > 0]
        sell_signals = [s for s in active_signals if s.signal.value < 0]
        
        if len(buy_signals) > len(sell_signals):
            # Bullish consensus
            best_signal = max(buy_signals, key=lambda x: x.confidence)
            combined_confidence = np.mean([s.confidence for s in buy_signals])
        elif len(sell_signals) > len(buy_signals):
            # Bearish consensus
            best_signal = max(sell_signals, key=lambda x: x.confidence)
            combined_confidence = np.mean([s.confidence for s in sell_signals])
        else:
            # Conflicting signals, use highest confidence
            best_signal = max(active_signals, key=lambda x: x.confidence)
            combined_confidence = best_signal.confidence * 0.7  # Reduce confidence for conflict
        
        # Create combined signal
        reasoning = f"Combined: {', '.join([f'{s.strategy_name}={s.signal.name}' for s in signals])}"
        
        combined = TradingSignal(
            symbol=best_signal.symbol,
            signal=best_signal.signal,
            confidence=combined_confidence,
            entry_price=best_signal.entry_price,
            stop_loss=best_signal.stop_loss,
            take_profit=best_signal.take_profit,
            timestamp=datetime.now(),
            reasoning=reasoning,
            strategy_name="Combined"
        )
        
        logger.info(f"Combined signal for {best_signal.symbol}: {combined.signal.name} (confidence: {combined_confidence:.2f})")
        return combined
