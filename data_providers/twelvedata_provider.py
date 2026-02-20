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
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from Twelve Data API"""
        if not self.is_available():
            logger.warning(f"[TwelveData] API key not available, cannot fetch data for {symbol}")
            return None
        
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"[TwelveData] Fetching {days} days of data for {symbol} ({start_date} to {end_date})")
            
            # Determine interval based on days requested
            if days <= 30:
                interval = "1day"
                outputsize = days
            elif days <= 365:
                interval = "1day"
                outputsize = min(days, 5000)  # API limit
            else:
                interval = "1week"
                outputsize = min(days // 7, 5000)
            
            params = {
                'symbol': symbol,
                'interval': interval,
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
            
            logger.info(f"[TwelveData] Fetched {len(df)} days of data for {symbol}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TwelveData] Network error fetching data for {symbol}: {e}")
            self._available = False
            return None
        except Exception as e:
            logger.error(f"[TwelveData] Error fetching data for {symbol}: {e}")
            return None
