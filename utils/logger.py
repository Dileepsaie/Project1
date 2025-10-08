"""
Logging Utility
===============

PURPOSE:
Centralized logging configuration for the trading system.

WHY LOGGING:
- Track system behavior and performance
- Debug issues in production
- Audit trail for all trades
- Monitor agent decisions
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logger with console and file handlers
    
    WHY BOTH:
    - Console: Real-time monitoring during development
    - File: Permanent record for analysis
    
    Args:
        name: Logger name (usually module name)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s | %(name)s | %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Capture all details in file
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger
