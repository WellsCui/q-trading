#!/usr/bin/env python3
"""
Example: Using Twelve Data as a Market Data Provider

This example demonstrates how to configure and use Twelve Data API
for fetching market data in the Quantitative Trading Agent.

Get your free API key at: https://twelvedata.com/
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_trading_agent import TwelveDataProvider

# Example 1: Using API key from environment variable
print("Example 1: Initialize with environment variable")
print("-" * 50)
# Set the API key (replace with your actual key)
api_key = os.environ.get('TWELVEDATA_API_KEY', 'fake_api_key')

provider = TwelveDataProvider()
print(f"Provider: {provider.name}")
print(f"Available: {provider.is_available()}")
print()

# Example 2: Using API key directly
print("Example 2: Initialize with API key directly")
print("-" * 50)
provider = TwelveDataProvider(api_key=api_key)

# Example 3: Fetch historical data (uncomment when you have an API key)

print("Example 3: Fetch historical data")
print("-" * 50)
data = provider.get_historical_data('AAPL', days=30)
if data is not None:
    print(f"Fetched {len(data)} days of data")
    print(data.head())
else:
    print("Failed to fetch data")
print()


# Configuration example in quant_config.yaml:
print("Configuration in quant_config.yaml:")
print("-" * 50)
print("""
data_provider: auto
data_provider_priority:
  - twelvedata
  - broker
  - yfinance
twelvedata_api_key: your_api_key_here
""")

print("\nOR set environment variable:")
print("export TWELVEDATA_API_KEY='your_api_key_here'")
print("\nOR use only Twelve Data:")
print("""
data_provider: twelvedata
twelvedata_api_key: your_api_key_here
""")
