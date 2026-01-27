# Brokers Package

This package contains broker integrations for live trading with the quantitative trading system.

## Structure

```
brokers/
├── __init__.py              # Package initialization
├── ib_broker.py             # Interactive Brokers integration
├── test_ib_broker.py        # Tests for IB broker
├── test_ib_connection.py    # IB connection test script
└── test_ib_connection.ipynb # IB connection test notebook
```

## Interactive Brokers Integration

### Usage

```python
from brokers import create_ib_broker, IBBroker, IB_AVAILABLE

# Check if IB is available
if IB_AVAILABLE:
    # Create broker instance
    config = {
        'ib_host': '127.0.0.1',
        'ib_port': 7497,  # 7497 for paper trading, 7496 for live
        'ib_client_id': 1,
        'ib_account': 'YOUR_ACCOUNT'
    }
    
    broker = create_ib_broker(config)
    if broker:
        print("Connected to Interactive Brokers!")
```

### Testing

Run the test scripts from the project root:

```bash
# Test IB broker functionality
python brokers/test_ib_broker.py

# Test IB connection
python brokers/test_ib_connection.py

# Or use the Jupyter notebook
jupyter notebook brokers/test_ib_connection.ipynb
```

### Requirements

- Interactive Brokers TWS or IB Gateway must be running
- `ibapi` Python package: `pip install ibapi`
- API connections enabled in TWS/Gateway settings

### Configuration

Configure IB settings in your `config.json`:

```json
{
  "use_interactive_brokers": true,
  "ib_host": "127.0.0.1",
  "ib_port": 7497,
  "ib_client_id": 1,
  "ib_account": "",
  "dry_run": false
}
```

### Adding New Brokers

To add a new broker integration:

1. Create a new file in this directory (e.g., `alpaca_broker.py`)
2. Implement the broker interface (similar to `ib_broker.py`)
3. Add imports to `__init__.py`
4. Create corresponding test files

## Documentation

- [IB Setup Guide](../IB_SETUP.md)
- [IB Quantitative Trading Guide](../IB_QUANTITATIVE_TRADING.md)

## Notes

- Always test with paper trading first (`ib_port: 7497`)
- Ensure proper risk management is in place
- Monitor logs for connection issues
- Keep credentials secure (never commit to version control)
