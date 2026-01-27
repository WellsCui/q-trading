"""
Base classes for trading strategies
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Tuple, Any
import pandas as pd


class Signal(Enum):
    """Trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


class TradingStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy with configuration
        
        Args:
            config: Strategy-specific configuration parameters
        """
        self.config = config
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"Strategy.{self.name}")
        
    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict[str, Any]]:
        """
        Calculate trading signals based on market data
        
        Args:
            data: Market data DataFrame with OHLCV columns
            symbol: Stock symbol
            
        Returns:
            Tuple of (Signal, signal_details)
        """
        pass
    
    @abstractmethod
    def get_required_data_period(self) -> int:
        """
        Get the minimum number of days of historical data required
        
        Returns:
            Number of days needed for strategy calculations
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate that data contains required columns and sufficient history
        
        Args:
            data: Market data DataFrame
            
        Returns:
            True if data is valid, False otherwise
        """
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        if data is None or data.empty:
            self.logger.error("Data is empty")
            return False
            
        missing_cols = [col for col in required_columns if col not in data.columns]
        if missing_cols:
            self.logger.error(f"Missing required columns: {missing_cols}")
            return False
            
        if len(data) < self.get_required_data_period():
            self.logger.error(f"Insufficient data: {len(data)} days, need {self.get_required_data_period()}")
            return False
            
        return True
