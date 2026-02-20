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
    
    def get_historical_data(self, symbol: str, days: int, interval: str = '1d', **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance
        
        Args:
            symbol: Stock symbol
            days: Number of days/periods to fetch
            interval: Data interval - valid values: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
                     Note: intraday data (< 1d) is limited to last 60 days by Yahoo Finance
        """
        try:
            # Calculate time period based on interval
            if interval in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h']:
                # Intraday data - Yahoo limits to 60 days max
                actual_days = min(days, 60)
                period_str = f"{actual_days}d"
                logger.info(f"[YFinance] Fetching {actual_days} days of {interval} data for {symbol}")
            else:
                # Daily or longer intervals
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
                period_str = None
                logger.info(f"[YFinance] Fetching {days} days of {interval} data for {symbol} ({start_date} to {end_date})")
            
            ticker = yf.Ticker(symbol)
            if period_str:
                data = ticker.history(period=period_str, interval=interval)
            else:
                data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                logger.error(f"[YFinance] No data received for {symbol}")
                return None
            
            logger.info(f"[YFinance] Fetched {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"[YFinance] Error fetching data for {symbol}: {e}")
            self._available = False
            return None
