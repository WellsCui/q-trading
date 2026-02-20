"""
Twelve Data API Provider

Provides market data from Twelve Data API service.
Get free API key at https://twelvedata.com/
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import requests

from .base import MarketDataProvider

logger = logging.getLogger("QuantTradingAgent.TwelveData")


class TwelveDataProvider(MarketDataProvider):
    """Twelve Data API provider for market data"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('TWELVEDATA_API_KEY')
        self._available = self.api_key is not None
        self.base_url = "https://api.twelvedata.com"
        
        if not self._available:
            logger.warning("[TwelveData] No API key provided. Set 'twelvedata_api_key' in config or TWELVEDATA_API_KEY environment variable.")
    
    @property
    def name(self) -> str:
        return "TwelveData"
    
    def is_available(self) -> bool:
        return self._available
    
    def get_historical_data(self, symbol: str, days: int, interval: str = '1d', **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from Twelve Data API
        
        Args:
            symbol: Stock symbol
            days: Number of days/periods to fetch
            interval: Data interval - valid values: 1min, 5min, 15min, 30min, 45min, 
                     1h, 2h, 4h, 1day, 1week, 1month
        """
        if not self.is_available():
            logger.warning(f"[TwelveData] API key not available, cannot fetch data for {symbol}")
            return None
        
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Map common interval formats to TwelveData format
            interval_map = {
                '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
                '1h': '1h', '2h': '2h', '4h': '4h',
                '1d': '1day', '1w': '1week', '1M': '1month'
            }
            twelvedata_interval = interval_map.get(interval, interval)
            
            logger.info(f"[TwelveData] Fetching {days} days of {twelvedata_interval} data for {symbol} ({start_date} to {end_date})")
            
            # Calculate outputsize based on interval and days
            outputsize = min(days * (1440 // self._interval_to_minutes(twelvedata_interval)), 5000)
            
            params = {
                'symbol': symbol,
                'interval': twelvedata_interval,
                'outputsize': outputsize,
                'apikey': self.api_key,
                'format': 'JSON',
                'start_date': start_date,
                'end_date': end_date
            }
            
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"[TwelveData] API request failed with status {response.status_code}: {response.text}")
                return None
            
            data_json = response.json()
            
            # Check for API errors
            if 'status' in data_json and data_json['status'] == 'error':
                logger.error(f"[TwelveData] API error: {data_json.get('message', 'Unknown error')}")
                return None
            
            if 'values' not in data_json or not data_json['values']:
                logger.error(f"[TwelveData] No data received for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data_json['values'])
            
            # Convert column names to match yfinance format
            df = df.rename(columns={
                'datetime': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            
            # Convert types
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df = df.sort_index()  # Sort by date ascending
            
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if 'Volume' in df.columns:
                df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype(int)
            
            logger.info(f"[TwelveData] Fetched {len(df)} data points for {symbol}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TwelveData] Network error fetching data for {symbol}: {e}")
            self._available = False
            return None
        except Exception as e:
            logger.error(f"[TwelveData] Error fetching data for {symbol}: {e}")
            return None
    
    def _interval_to_minutes(self, interval: str) -> int:
        """Convert interval string to approximate minutes"""
        interval_minutes = {
            '1min': 1, '5min': 5, '15min': 15, '30min': 30, '45min': 45,
            '1h': 60, '2h': 120, '4h': 240,
            '1day': 1440, '1week': 10080, '1month': 43200
        }
        return interval_minutes.get(interval, 1440)
