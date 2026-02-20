# Data Provider Interval Support

## Overview

The `get_historical_data()` method now supports fetching market data at different time intervals, including intraday data (minutes, hours) in addition to daily data.

## Method Signature

```python
def get_historical_data(
    self, 
    symbol: str, 
    days: int, 
    interval: str = '1d', 
    **kwargs
) -> Optional[pd.DataFrame]:
```

## Parameters

- **symbol** (str): Stock symbol (e.g., 'AAPL', 'QQQ')
- **days** (int): Number of days/periods to fetch
- **interval** (str): Data interval/timeframe (default: '1d')
  - Minutes: `'1m'`, `'2m'`, `'5m'`, `'15m'`, `'30m'`
  - Hours: `'1h'`, `'2h'`, `'4h'`
  - Days: `'1d'` (default), `'5d'`
  - Weeks: `'1w'`
  - Months: `'1M'`

## Supported Intervals by Provider

### YFinanceProvider
- **Minute intervals**: 1m, 2m, 5m, 15m, 30m, 60m, 90m
- **Hour intervals**: 1h
- **Day intervals**: 1d, 5d
- **Week intervals**: 1wk
- **Month intervals**: 1mo, 3mo
- **Limitation**: Intraday data (< 1d) limited to last 60 days

### TwelveDataProvider
- **Minute intervals**: 1min, 5min, 15min, 30min, 45min
- **Hour intervals**: 1h, 2h, 4h
- **Day intervals**: 1day
- **Week intervals**: 1week
- **Month intervals**: 1month
- **Note**: Accepts both formats (e.g., '1m' or '1min')

### BrokerDataProvider (Interactive Brokers)
- **Minute intervals**: 1 min, 5 mins, 15 mins, 30 mins
- **Hour intervals**: 1 hour, 2 hours, 4 hours
- **Day intervals**: 1 day
- **Week intervals**: 1 week
- **Month intervals**: 1 month

## Usage Examples

### Basic Usage

```python
from data_providers.yfinance_provider import YFinanceProvider

provider = YFinanceProvider()

# Fetch daily data (default)
daily_data = provider.get_historical_data('AAPL', days=30)

# Fetch 5-minute intraday data
intraday_5m = provider.get_historical_data('AAPL', days=2, interval='5m')

# Fetch hourly data
hourly_data = provider.get_historical_data('AAPL', days=5, interval='1h')

# Fetch 15-minute data
data_15m = provider.get_historical_data('AAPL', days=3, interval='15m')
```

### Using with QuantTradingAgent

```python
from quant_trading_agent import QuantTradingAgent

agent = QuantTradingAgent(config_path='quant_config.yaml')

# Fetch daily data (default behavior)
daily_data = agent.fetch_market_data('QQQ')

# Fetch 5-minute intraday data for last 3 days
intraday_data = agent.fetch_market_data('QQQ', days=3, interval='5m')

# Fetch hourly data for last week
hourly_data = agent.fetch_market_data('QQQ', days=7, interval='1h')
```

### Using with MultiProviderDataSource

```python
from data_providers.multi_provider import MultiProviderDataSource
from data_providers.yfinance_provider import YFinanceProvider
from data_providers.twelvedata_provider import TwelveDataProvider

# Create multi-provider data source
providers = [
    YFinanceProvider(),
    TwelveDataProvider(api_key='your_api_key')
]
data_source = MultiProviderDataSource(providers)

# Fetch with automatic fallback
data = data_source.get_historical_data('TSLA', days=5, interval='15m')
```

## Important Notes

1. **Intraday Data Limitations**:
   - Yahoo Finance limits intraday data to the last 60 days
   - Requesting more than 60 days of intraday data will be automatically capped

2. **Data Availability**:
   - Not all symbols may have intraday data available
   - Market hours apply for intraday data (typically 9:30 AM - 4:00 PM ET)

3. **Backward Compatibility**:
   - The `interval` parameter defaults to `'1d'` (daily)
   - Existing code without the interval parameter will continue to work

4. **Interval Format Variations**:
   - The code handles common interval format variations
   - Example: '1m' and '1min' are both supported and mapped appropriately

## Return Value

Returns a pandas DataFrame with the following columns:
- **Date/Datetime**: Index (timestamp of the bar)
- **Open**: Opening price
- **High**: Highest price
- **Low**: Lowest price
- **Close**: Closing price
- **Volume**: Trading volume

For intraday data, the index includes time information (e.g., `2026-02-20 09:30:00-05:00`).

## Error Handling

The method returns `None` if:
- The provider is not available
- The symbol is invalid
- No data is available for the requested period/interval
- Network errors occur

Check the logs for detailed error messages.

## Complete Example

See [examples/interval_example.py](../examples/interval_example.py) for a complete working example demonstrating all interval types.
