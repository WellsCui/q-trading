"""
Broker Data Provider

Provides market data from broker connections (e.g., Interactive Brokers).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from .base import MarketDataProvider

logger = logging.getLogger("QuantTradingAgent.BrokerProvider")


class BrokerDataProvider(MarketDataProvider):
    """Broker-based data provider (e.g., Interactive Brokers)"""
    
    def __init__(self, broker):
        """
        Initialize broker data provider
        
        Args:
            broker: BrokerInterface instance
        """
        self.broker = broker
    
    @property
    def name(self) -> str:
        return f"Broker ({type(self.broker).__name__ if self.broker else 'None'})"
    
    def is_available(self) -> bool:
        return self.broker is not None and self.broker.is_connected()
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from broker"""
        if not self.is_available():
            logger.warning(f"[Broker] Not connected, cannot fetch data for {symbol}")
            return None
        
        try:
            duration = kwargs.get('duration', f"{days} D")
            bar_size = kwargs.get('bar_size', "1 D")
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"[Broker] Fetching {days} days of data for {symbol} ({start_date} to {end_date})")
            
            data = self.broker.get_historical_data(symbol, duration=duration, bar_size=bar_size)
            
            if data is not None and not data.empty:
                logger.info(f"[Broker] Fetched {len(data)} data points for {symbol}")
                return data
            else:
                logger.warning(f"[Broker] No data received for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"[Broker] Error fetching data for {symbol}: {e}")
            return None
