"""
Base Market Data Provider

Abstract base class for all market data providers.
"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    def get_historical_data(self, symbol: str, days: int, interval: str = '1d', **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical market data for a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days/periods of historical data
            interval: Data interval/timeframe (e.g., '1m', '5m', '1h', '1d')
                     Format varies by provider but common values:
                     - Minutes: '1m', '5m', '15m', '30m'
                     - Hours: '1h', '2h', '4h'
                     - Days: '1d' (default)
                     - Weeks: '1w'
            **kwargs: Additional provider-specific parameters
            
        Returns:
            DataFrame with OHLCV data or None
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
