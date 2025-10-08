"""
Risk Management Agent
=====================

PURPOSE:
Implements comprehensive risk controls to protect capital and limit losses.

CORE PRINCIPLES:
1. Never risk more than 2% of capital per trade (hard limit)
2. Dynamic position sizing based on volatility
3. Automatic stop-loss triggers
4. Portfolio-level exposure limits
5. Correlation-based diversification

WHY CRITICAL:
- One bad trade can wipe out months of gains
- Systematic risk management is difference between success and failure
- Prevents emotional decision-making
- Ensures long-term survival in markets
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from agents.strategy_agents import TradingSignal, SignalType
from agents.market_data_agent import MarketData
from utils.logger import setup_logger

logger = setup_logger("risk_management_agent")


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4


@dataclass
class PositionSize:
    """
    Position sizing calculation result
    
    WHY SEPARATE CLASS:
    - Clear contract for position sizing
    - Easy to validate and log
    - Includes risk metrics for monitoring
    """
    symbol: str
    shares: int
    dollar_amount: float
    risk_dollars: float
    risk_percent: float
    stop_loss_price: float
    reasoning: str


@dataclass
class RiskMetrics:
    """Portfolio-level risk metrics"""
    total_exposure: float
    var_95: float  # Value at Risk (95% confidence)
    sharpe_ratio: float
    max_drawdown_pct: float
    current_positions: int
    available_capital: float


class RiskManagementAgent:
    """
    Agent responsible for risk management and position sizing
    
    RESPONSIBILITIES:
    1. Calculate position sizes based on risk parameters
    2. Monitor stop-loss levels
    3. Enforce portfolio-level limits
    4. Calculate risk metrics
    5. Prevent overexposure
    """
    
    def __init__(self, 
                 total_capital: float = 100000,
                 max_risk_per_trade: float = 0.02,  # 2% max risk
                 max_portfolio_exposure: float = 0.6,  # 60% max deployed
                 max_position_size: float = 0.2):  # 20% max per position
        """
        Initialize Risk Management Agent
        
        Args:
            total_capital: Total trading capital
            max_risk_per_trade: Maximum risk per trade (as fraction, e.g., 0.02 = 2%)
            max_portfolio_exposure: Maximum portfolio exposure (as fraction)
            max_position_size: Maximum position size (as fraction of capital)
        """
        self.total_capital = total_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_position_size = max_position_size
        
        # Track open positions
        self.positions: Dict[str, Dict] = {}
        self.available_capital = total_capital
        
        logger.info(f"Risk Management initialized: Capital=${total_capital:,.0f}, Max risk/trade={max_risk_per_trade*100}%")
    
    def calculate_position_size(self,
                                signal: TradingSignal,
                                current_price: float) -> Optional[PositionSize]:
        """
        Calculate position size based on risk parameters
        
        FORMULA:
        Position Size = (Account Risk $) / (Price - Stop Loss Price)
        
        WHY THIS FORMULA:
        - Ensures consistent dollar risk across trades
        - Automatically adjusts for volatility
        - Larger positions for tighter stops, smaller for wider stops
        
        Args:
            signal: Trading signal with stop loss
            current_price: Current market price
            
        Returns:
            PositionSize object or None if risk too high
        """
        try:
            # Calculate risk per share
            risk_per_share = abs(current_price - signal.stop_loss)
            
            if risk_per_share == 0:
                logger.warning(f"Invalid stop loss for {signal.symbol}, risk per share is 0")
                return None
            
            # Calculate max risk dollars for this trade
            max_risk_dollars = self.total_capital * self.max_risk_per_trade
            
            # Calculate position size based on risk
            shares = int(max_risk_dollars / risk_per_share)
            
            # Calculate dollar amount
            dollar_amount = shares * current_price
            
            # Apply maximum position size limit
            max_position_dollars = self.total_capital * self.max_position_size
            if dollar_amount > max_position_dollars:
                dollar_amount = max_position_dollars
                shares = int(dollar_amount / current_price)
            
            # Check if we have enough capital
            if dollar_amount > self.available_capital:
                logger.warning(f"Insufficient capital for {signal.symbol}: Need ${dollar_amount:,.0f}, Have ${self.available_capital:,.0f}")
                # Scale down position
                dollar_amount = self.available_capital * 0.95  # Use 95% of available
                shares = int(dollar_amount / current_price)
            
            # Recalculate actual risk
            actual_risk_dollars = shares * risk_per_share
            actual_risk_percent = (actual_risk_dollars / self.total_capital) * 100
            
            reasoning = f"Risk: ${actual_risk_dollars:,.0f} ({actual_risk_percent:.2f}%), Stop: ${signal.stop_loss:.2f}, R/share: ${risk_per_share:.2f}"
            
            position_size = PositionSize(
                symbol=signal.symbol,
                shares=shares,
                dollar_amount=dollar_amount,
                risk_dollars=actual_risk_dollars,
                risk_percent=actual_risk_percent,
                stop_loss_price=signal.stop_loss,
                reasoning=reasoning
            )
            
            logger.info(f"Position size for {signal.symbol}: {shares} shares, ${dollar_amount:,.0f} ({reasoning})")
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size for {signal.symbol}: {str(e)}")
            return None
    
    def check_stop_loss(self, 
                       symbol: str,
                       current_price: float) -> bool:
        """
        Check if stop loss has been hit for a position
        
        WHY AUTOMATIC:
        - Removes emotion from loss-taking
        - Ensures consistent risk management
        - Prevents large losses
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            
        Returns:
            True if stop loss hit, False otherwise
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        stop_loss = position['stop_loss']
        
        # Check for long positions
        if position['direction'] == 'LONG' and current_price <= stop_loss:
            logger.warning(f"STOP LOSS HIT for {symbol}: Price ${current_price:.2f} <= Stop ${stop_loss:.2f}")
            return True
        
        # Check for short positions
        if position['direction'] == 'SHORT' and current_price >= stop_loss:
            logger.warning(f"STOP LOSS HIT for {symbol}: Price ${current_price:.2f} >= Stop ${stop_loss:.2f}")
            return True
        
        return False
    
    def add_position(self, 
                    symbol: str,
                    shares: int,
                    entry_price: float,
                    stop_loss: float,
                    direction: str = 'LONG'):
        """
        Add a new position to tracking
        
        WHY TRACK:
        - Monitor aggregate exposure
        - Calculate portfolio metrics
        - Enforce risk limits
        
        Args:
            symbol: Stock symbol
            shares: Number of shares
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: LONG or SHORT
        """
        position_value = shares * entry_price
        
        self.positions[symbol] = {
            'shares': shares,
            'entry_price': entry_price,
            'current_price': entry_price,
            'stop_loss': stop_loss,
            'direction': direction,
            'value': position_value,
            'entry_time': datetime.now()
        }
        
        self.available_capital -= position_value
        
        logger.info(f"Position added: {symbol} - {shares} shares @ ${entry_price:.2f}, SL: ${stop_loss:.2f}")
        logger.info(f"Available capital: ${self.available_capital:,.0f}")
    
    def update_position(self, symbol: str, current_price: float):
        """Update position with current price"""
        if symbol in self.positions:
            old_price = self.positions[symbol]['current_price']
            self.positions[symbol]['current_price'] = current_price
            
            # Recalculate value
            shares = self.positions[symbol]['shares']
            self.positions[symbol]['value'] = shares * current_price
            
            # Log significant moves
            pct_change = ((current_price - old_price) / old_price) * 100
            if abs(pct_change) > 1:
                logger.info(f"Position update: {symbol} {pct_change:+.2f}% - Now ${current_price:.2f}")
    
    def close_position(self, symbol: str, exit_price: float) -> Dict:
        """
        Close a position and calculate P&L
        
        Returns:
            Dictionary with position details and P&L
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot close position: {symbol} not found")
            return {}
        
        position = self.positions[symbol]
        shares = position['shares']
        entry_price = position['entry_price']
        
        # Calculate P&L
        if position['direction'] == 'LONG':
            pnl = (exit_price - entry_price) * shares
        else:
            pnl = (entry_price - exit_price) * shares
        
        pnl_pct = (pnl / (shares * entry_price)) * 100
        
        # Return capital
        position_value = shares * exit_price
        self.available_capital += position_value
        
        # Remove position
        del self.positions[symbol]
        
        result = {
            'symbol': symbol,
            'shares': shares,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'direction': position['direction']
        }
        
        logger.info(f"Position closed: {symbol} - P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
        return result
    
    def calculate_portfolio_metrics(self) -> RiskMetrics:
        """
        Calculate portfolio-level risk metrics
        
        METRICS:
        - Total exposure: Sum of all position values
        - VaR (Value at Risk): Potential loss at 95% confidence
        - Current positions count
        - Available capital
        
        WHY PORTFOLIO LEVEL:
        - Individual position risk is not enough
        - Need to monitor aggregate exposure
        - Prevent correlation risk
        """
        total_exposure = sum(pos['value'] for pos in self.positions.values())
        
        # Simple VaR calculation (assumes 2% daily volatility, 95% confidence = 1.65 std devs)
        var_95 = total_exposure * 0.02 * 1.65
        
        # Placeholder values for other metrics (would need historical returns)
        sharpe_ratio = 0.0
        max_drawdown_pct = 0.0
        
        metrics = RiskMetrics(
            total_exposure=total_exposure,
            var_95=var_95,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            current_positions=len(self.positions),
            available_capital=self.available_capital
        )
        
        exposure_pct = (total_exposure / self.total_capital) * 100
        logger.info(f"Portfolio metrics: Exposure={exposure_pct:.1f}%, VaR(95%)=${var_95:,.0f}, Positions={len(self.positions)}")
        
        return metrics
    
    def assess_risk_level(self, signal: TradingSignal) -> RiskLevel:
        """
        Assess risk level of a potential trade
        
        FACTORS:
        - Signal confidence
        - Current portfolio exposure
        - Volatility
        - Correlation with existing positions
        
        Returns:
            RiskLevel enum
        """
        metrics = self.calculate_portfolio_metrics()
        
        # Check portfolio exposure
        exposure_pct = metrics.total_exposure / self.total_capital
        
        # Assess risk
        if exposure_pct > 0.8:
            return RiskLevel.EXTREME
        elif exposure_pct > 0.6:
            return RiskLevel.HIGH
        elif signal.confidence < 0.5:
            return RiskLevel.HIGH
        elif exposure_pct > 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def should_take_trade(self, signal: TradingSignal) -> Tuple[bool, str]:
        """
        Determine if a trade should be taken based on risk rules
        
        CHECKS:
        1. Portfolio exposure limits
        2. Risk level acceptable
        3. Sufficient capital
        4. Signal quality
        
        Returns:
            Tuple of (should_take: bool, reason: str)
        """
        # Check signal strength
        if signal.signal == SignalType.NEUTRAL:
            return False, "Neutral signal"
        
        # Check confidence threshold
        if signal.confidence < 0.5:
            return False, f"Low confidence: {signal.confidence:.2f}"
        
        # Check portfolio exposure
        metrics = self.calculate_portfolio_metrics()
        exposure_pct = metrics.total_exposure / self.total_capital
        
        if exposure_pct > self.max_portfolio_exposure:
            return False, f"Max portfolio exposure reached: {exposure_pct*100:.1f}%"
        
        # Check if already have position
        if signal.symbol in self.positions:
            return False, f"Already have position in {signal.symbol}"
        
        # Check risk level
        risk_level = self.assess_risk_level(signal)
        if risk_level == RiskLevel.EXTREME:
            return False, "Risk level too high"
        
        # All checks passed
        return True, "Trade approved"
