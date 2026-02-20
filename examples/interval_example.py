"""
Example: Using Different Time Intervals with Data Providers

This example demonstrates how to fetch market data at different intervals
(minutes, hours, days) using the enhanced get_historical_data method.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_providers.yfinance_provider import YFinanceProvider
from data_providers.multi_provider import MultiProviderDataSource

def test_intervals():
    """Test fetching data at different intervals"""
    
    provider = YFinanceProvider()
    symbol = 'AAPL'
    
    print("=" * 60)
    print("Testing Different Time Intervals")
    print("=" * 60)
    
    # Test 1: Daily data (default)
    print("\n1. Fetching 30 days of daily data:")
    data_daily = provider.get_historical_data(symbol, days=30, interval='1d')
    if data_daily is not None:
        print(f"   ✓ Fetched {len(data_daily)} daily data points")
        print(f"   Date range: {data_daily.index[0]} to {data_daily.index[-1]}")
    
    # Test 2: Hourly data
    print("\n2. Fetching 5 days of hourly data:")
    data_hourly = provider.get_historical_data(symbol, days=5, interval='1h')
    if data_hourly is not None:
        print(f"   ✓ Fetched {len(data_hourly)} hourly data points")
        print(f"   Date range: {data_hourly.index[0]} to {data_hourly.index[-1]}")
    
    # Test 3: 15-minute data
    print("\n3. Fetching 2 days of 15-minute data:")
    data_15min = provider.get_historical_data(symbol, days=2, interval='15m')
    if data_15min is not None:
        print(f"   ✓ Fetched {len(data_15min)} 15-minute data points")
        print(f"   Date range: {data_15min.index[0]} to {data_15min.index[-1]}")
    
    # Test 4: 5-minute data
    print("\n4. Fetching 1 day of 5-minute data:")
    data_5min = provider.get_historical_data(symbol, days=1, interval='5m')
    if data_5min is not None:
        print(f"   ✓ Fetched {len(data_5min)} 5-minute data points")
        print(f"   Date range: {data_5min.index[0]} to {data_5min.index[-1]}")
        print(f"\n   Sample data (last 5 bars):")
        print(data_5min.tail()[['Open', 'High', 'Low', 'Close', 'Volume']])
    
    # Test 5: 1-minute data
    print("\n5. Fetching intraday 1-minute data (last trading day):")
    data_1min = provider.get_historical_data(symbol, days=1, interval='1m')
    if data_1min is not None:
        print(f"   ✓ Fetched {len(data_1min)} 1-minute data points")
        print(f"   Date range: {data_1min.index[0]} to {data_1min.index[-1]}")
    
    print("\n" + "=" * 60)
    print("Interval Support:")
    print("  • Minutes: 1m, 2m, 5m, 15m, 30m")
    print("  • Hours:   1h, 2h, 4h")
    print("  • Days:    1d (default), 5d")
    print("  • Weeks:   1w")
    print("  • Months:  1M")
    print("\nNote: Intraday data (< 1d) limited to last 60 days")
    print("=" * 60)

def test_with_multi_provider():
    """Test using MultiProviderDataSource with intervals"""
    
    print("\n\n" + "=" * 60)
    print("Testing with MultiProviderDataSource")
    print("=" * 60)
    
    # Create multi-provider with YFinance
    providers = [YFinanceProvider()]
    data_source = MultiProviderDataSource(providers)
    
    symbol = 'QQQ'
    
    # Fetch 5-minute data for the last 3 days
    print(f"\nFetching 3 days of 5-minute data for {symbol}:")
    data = data_source.get_historical_data(symbol, days=3, interval='5m')
    
    if data is not None:
        print(f"✓ Successfully fetched {len(data)} data points")
        print(f"  Date range: {data.index[0]} to {data.index[-1]}")
        print(f"\n  Latest prices:")
        print(data.tail()[['Open', 'High', 'Low', 'Close', 'Volume']])
    else:
        print("✗ Failed to fetch data")

if __name__ == '__main__':
    test_intervals()
    test_with_multi_provider()
