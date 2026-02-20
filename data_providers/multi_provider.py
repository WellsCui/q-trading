"""
Multi-Provider Data Source

Manages multiple data providers with automatic fallback support.
"""

import logging
from typing import List, Optional
import pandas as pd

from .base import MarketDataProvider

logger = logging.getLogger("QuantTradingAgent.MultiProvider")


class MultiProviderDataSource:
    """Manages multiple data providers with fallback support"""
    
    def __init__(self, providers: List[MarketDataProvider]):
        self.providers = providers
        logger.info(f"Initialized data source with {len(providers)} providers: {[p.name for p in providers]}")
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch data from first available provider"""
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Provider {provider.name} not available, trying next...")
                continue
            
            logger.info(f"Attempting to fetch {symbol} data from {provider.name}")
            data = provider.get_historical_data(symbol, days, **kwargs)
            
            if data is not None and not data.empty:
                logger.info(f"Successfully fetched {symbol} data from {provider.name}")
                return data
            else:
                logger.warning(f"Failed to fetch {symbol} data from {provider.name}, trying next provider")
        
        logger.error(f"All providers failed for {symbol}")
        return None
