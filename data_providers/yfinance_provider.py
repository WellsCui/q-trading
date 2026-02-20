"""
Yahoo Finance Data Provider

Provides market data from Yahoo Finance using yfinance library.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import yfinance as yf

from .base import MarketDataProvider

logger = logging.getLogger("QuantTradingAgent.YFinance")


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance data provider"""
    
    def __init__(self):
        self._available = True
    
    @property
    def name(self) -> str:
        return "YFinance"
    
    def is_available(self) -> bool:
        return self._available
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"[YFinance] Fetching {days} days of data for {symbol} ({start_date} to {end_date})")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.error(f"[YFinance] No data received for {symbol}")
                return None
            
            logger.info(f"[YFinance] Fetched {len(data)} days of data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"[YFinance] Error fetching data for {symbol}: {e}")
            self._available = False
            return None
