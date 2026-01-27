# Broker Interface Documentation

## Overview

The broker interface provides a standardized API for integrating different brokers (Interactive Brokers, Alpaca, etc.) with the QuantTradingAgent. This abstraction allows you to:

- Switch between different brokers without changing your trading logic
- Test strategies with a MockBroker before going live
- Maintain consistent code across different trading platforms

## Architecture

### Base Interface

[brokers/base_broker.py](brokers/base_broker.py) defines the `BrokerInterface` abstract base class that all brokers must implement.

### Implementations

1. **MockBroker** - A simulated broker for testing and dry-run mode
2. **IBBroker** - Interactive Brokers integration
3. *(Future)* - Alpaca, TD Ameritrade, etc.

## Usage

### Basic Usage with Auto-created Broker

The simplest way is to let the agent create the broker from config:

```python
from quant_trading_agent import QuantTradingAgent

# Agent will create broker based on quant_config.json
agent = QuantTradingAgent(config_path='quant_config.json')

# Run the agent
agent.run()
```

### Explicit Broker Injection

For more control, create and inject the broker yourself:

```python
from brokers.base_broker import MockBroker
from brokers.ib_broker import IBBroker
from quant_trading_agent import QuantTradingAgent

# Option 1: Mock broker for testing
broker = MockBroker({
    'total_capital': 100000,
    'position_size_pct': 20
})
broker.connect()

# Option 2: Interactive Brokers
broker = IBBroker({
    'ib_host': '127.0.0.1',
    'ib_port': 7497,  # Paper trading
    'ib_client_id': 3,
    'total_capital': 100000,
    'position_size_pct': 95
})
broker.connect()

# Create agent with broker
agent = QuantTradingAgent(config_path='quant_config.json', broker=broker)
agent.run()
```

## Configuration

### quant_config.json

```json
{
  "broker": {
    "type": "mock",
    "total_capital": 100000,
    "position_size_pct": 95,
    
    "ib_host": "127.0.0.1",
    "ib_port": 7497,
    "ib_client_id": 3,
    "ib_account": ""
  }
}
```

**Broker Types:**
- `"mock"` - Use MockBroker for testing
- `"ib"` or `"interactive_brokers"` - Use Interactive Brokers

**Interactive Brokers Ports:**
- `7497` - Paper trading account
- `7496` - Live trading account

## Broker Interface Methods

### Connection Management

- `connect() -> bool` - Connect to broker
- `disconnect()` - Disconnect from broker
- `is_connected() -> bool` - Check connection status

### Market Data

- `get_market_data(symbol: str) -> Dict` - Current market data
- `get_historical_data(symbol: str, duration: str, bar_size: str) -> DataFrame` - Historical bars
- `get_tick_data(symbol: str) -> DataFrame` - Real-time tick data
- `get_order_book(symbol: str) -> Dict` - Level 2 order book

### Account Information

- `get_account_balance() -> float` - Cash balance
- `get_buying_power() -> float` - Available buying power
- `get_portfolio_value() -> float` - Total portfolio value
- `get_account_value() -> float` - Total account value

### Position Management

- `get_position(symbol: str) -> float` - Position quantity
- `get_all_positions() -> Dict` - All positions
- `get_position_details(symbol: str) -> Dict` - Detailed position info
- `close_position(symbol: str) -> bool` - Close a position

### Order Management

- `place_order(symbol, action, quantity, order_type, ...) -> int` - Place order
- `place_bracket_order(symbol, action, quantity, ...) -> List[int]` - Bracket order
- `cancel_order(order_id: int) -> bool` - Cancel order
- `modify_order(order_id, ...) -> bool` - Modify order
- `get_order_status(order_id: int) -> str` - Order status
- `get_all_orders() -> Dict` - All orders
- `get_open_orders() -> Dict` - Open orders only
- `get_executions(symbol: str) -> List` - Execution history

### Risk Management

- `validate_order(symbol, action, quantity, ...) -> Tuple[bool, str]` - Validate before placing
- `calculate_shares(symbol: str, price: float) -> int` - Position sizing

### Performance Tracking

- `get_performance_metrics() -> Dict` - Sharpe ratio, returns, etc.
- `get_risk_metrics() -> Dict` - Risk metrics
- `export_trade_history(filepath: str)` - Export trades to CSV
- `export_equity_curve(filepath: str)` - Export equity curve to CSV

## Integration with QuantTradingAgent

The QuantTradingAgent integrates with the broker in several ways:

### 1. Market Data Fetching

The agent will try to fetch market data from the broker first, falling back to yfinance:

```python
def fetch_market_data(self, symbol: str):
    # Try broker first
    if self.broker and self.broker.is_connected():
        data = self.broker.get_historical_data(symbol)
        if data is not None:
            return data
    
    # Fall back to yfinance
    return yf.download(symbol)
```

### 2. Position Opening

When opening a position, the agent uses the broker API:

```python
def _open_position(self, symbol: str, details: Dict):
    # Calculate position size
    quantity = self.broker.calculate_shares(symbol, current_price)
    
    # Validate order
    is_valid, error = self.broker.validate_order(symbol, 'BUY', quantity)
    
    # Place order
    order_id = self.broker.place_order(symbol, 'BUY', quantity)
```

### 3. Position Closing

Similarly for closing:

```python
def _close_position(self, symbol: str, details: Dict):
    # Validate and close
    is_valid, error = self.broker.validate_order(symbol, 'SELL', quantity)
    success = self.broker.close_position(symbol)
```

### 4. Status Monitoring

The agent's `get_status()` method includes broker information:

```python
status = agent.get_status()
# {
#   'broker': {
#     'type': 'IBBroker',
#     'connected': True,
#     'portfolio_value': 105000.0,
#     'buying_power': 420000.0,
#     'positions': {...}
#   }
# }
```

## Testing

### Running Tests

```bash
# Test the broker integration
python test_broker_integration_v2.py
```

This will test:
1. MockBroker functionality
2. IBBroker connection (if configured)
3. Agent with auto-created broker

### Unit Testing Your Own Broker

To implement a new broker, create a class that inherits from `BrokerInterface` and implements all abstract methods:

```python
from brokers.base_broker import BrokerInterface

class MyBroker(BrokerInterface):
    def __init__(self, config: Dict):
        self.config = config
        self.connected = False
    
    def connect(self) -> bool:
        # Your connection logic
        self.connected = True
        return True
    
    # Implement all other abstract methods...
```

## Example: Complete Trading Flow

```python
from brokers.ib_broker import IBBroker
from quant_trading_agent import QuantTradingAgent

# 1. Create and connect broker
broker = IBBroker({
    'ib_host': '127.0.0.1',
    'ib_port': 7497,
    'ib_client_id': 3,
    'total_capital': 100000
})

if not broker.connect():
    print("Failed to connect to IB")
    exit(1)

# 2. Create agent with broker
agent = QuantTradingAgent(
    config_path='quant_config.json',
    broker=broker
)

# 3. Check status
status = agent.get_status()
print(f"Broker: {status['broker']['type']}")
print(f"Portfolio: ${status['broker']['portfolio_value']:,.2f}")

# 4. Run one analysis cycle
agent.run_analysis_cycle()

# 5. Get performance metrics
metrics = broker.get_performance_metrics()
print(f"Total Return: {metrics['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")

# 6. Export data
broker.export_trade_history('trades.csv')
broker.export_equity_curve('equity.csv')

# 7. Clean up
agent.stop()
```

## Best Practices

1. **Always validate orders** before placing them
2. **Use bracket orders** for automatic risk management
3. **Monitor connection status** and reconnect if needed
4. **Test with MockBroker** before going live
5. **Export data regularly** for analysis and debugging
6. **Handle exceptions** gracefully in production
7. **Use paper trading** (port 7497) for testing strategies

## Troubleshooting

### Connection Issues

```python
# Check if connected
if not broker.is_connected():
    print("Not connected, attempting to reconnect...")
    broker.connect()
```

### Order Validation Failures

```python
# Always validate before placing
is_valid, error_msg = broker.validate_order(symbol, 'BUY', quantity)
if not is_valid:
    print(f"Order validation failed: {error_msg}")
    # Handle error appropriately
```

### Market Data Issues

```python
# Check market data before using
data = broker.get_market_data(symbol)
if data is None or not data.get('close'):
    print(f"No market data for {symbol}")
    # Fall back to alternative data source
```

## Future Enhancements

Planned improvements:

1. **Additional Brokers** - Alpaca, TD Ameritrade
2. **WebSocket Support** - Real-time streaming data
3. **Advanced Order Types** - Trailing stops, OCO orders
4. **Risk Limits** - Max position size, daily loss limits
5. **Paper Trading Mode** - Built-in simulation
6. **Backtesting Integration** - Test strategies on historical data

## Contributing

To add a new broker implementation:

1. Create a new file in `brokers/` (e.g., `alpaca_broker.py`)
2. Inherit from `BrokerInterface`
3. Implement all abstract methods
4. Add to `brokers/__init__.py`
5. Update configuration handling in `QuantTradingAgent._create_broker()`
6. Add tests
7. Update this documentation

## See Also

- [Interactive Brokers Setup Guide](IB_SETUP.md)
- [Strategy Implementation Guide](strategies/README.md)
- [QuantTradingAgent Documentation](QUANT_AGENT_README.md)
