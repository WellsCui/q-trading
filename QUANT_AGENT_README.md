# Quantitative Trading Agent

A flexible, extensible quantitative trading system supporting multiple strategies and configurable stock symbols.

## Features

### 🎯 Multiple Trading Strategies

1. **Moving Average Crossover**
   - Classic trend-following strategy
   - Golden Cross / Death Cross detection
   - Configurable short and long windows

2. **Momentum Strategy**
   - RSI (Relative Strength Index) based
   - Rate of Change (ROC) confirmation
   - Oversold/overbought detection

3. **Mean Reversion Strategy**
   - Bollinger Bands based
   - Entry at band extremes
   - Configurable standard deviations

4. **Trend Following Strategy**
   - ADX for trend strength
   - Volume confirmation
   - Multiple indicator confirmation

### 📊 Configurable Symbols

- Trade any stock symbols (ETFs, stocks, indices)
- Multi-symbol support
- Independent analysis per symbol
- Default: SPY, QQQ, IWM, DIA

### 🛡️ Risk Management

- Position sizing (default: 20% per position)
- Stop loss (default: 5%)
- Take profit (default: 15%)
- Maximum exposure limits

### 🔧 Flexible Configuration

- JSON-based configuration
- Strategy parameters customization
- Symbol list management
- Risk parameters adjustment

## Installation

```bash
# Install required packages
pip install pandas numpy yfinance

# For Interactive Brokers integration (optional)
pip install ibapi
```

## Quick Start

### 1. Configure Your Settings

Edit `quant_config.yaml`:

```yaml
symbols:
  - SPY
  - QQQ
  - AAPL
active_strategy: MovingAverageCrossover
dry_run: true
check_interval_minutes: 60
```

### 2. Run the Agent

```bash
# Run continuously (checks every interval)
python quant_trading_agent.py

# Run once and exit
python quant_trading_agent.py --once

# Use custom config file
python quant_trading_agent.py --config my_config.json
```

### 3. View Results

- Logs: `logs/quant_agent_YYYYMMDD.log`
- Trades: `logs/trades_YYYYMM.json`

## Configuration Guide

### Strategy Configuration

#### Moving Average Crossover

```json
"MovingAverageCrossover": {
  "short_window": 50,      // Fast MA period
  "long_window": 200,      // Slow MA period
  "price_threshold": 0.0   // Additional price filter
}
```

**Signals:**
- BUY: Short MA crosses above Long MA (Golden Cross)
- SELL: Short MA crosses below Long MA (Death Cross)

#### Momentum Strategy

```json
"Momentum": {
  "rsi_period": 14,        // RSI calculation period
  "rsi_oversold": 30,      // Oversold threshold
  "rsi_overbought": 70,    // Overbought threshold
  "roc_period": 20         // Rate of Change period
}
```

**Signals:**
- BUY: RSI < oversold threshold + negative ROC
- SELL: RSI > overbought threshold + positive ROC

#### Mean Reversion Strategy

```json
"MeanReversion": {
  "bb_period": 20,         // Bollinger Bands period
  "bb_std": 2.0,          // Standard deviation multiplier
  "entry_threshold": 0.02  // Entry distance from bands (2%)
}
```

**Signals:**
- BUY: Price near lower Bollinger Band
- SELL: Price near upper Bollinger Band

#### Trend Following Strategy

```json
"TrendFollowing": {
  "ma_period": 50,         // Moving average period
  "adx_period": 14,        // ADX calculation period
  "adx_threshold": 25,     // Minimum ADX for strong trend
  "volume_ma_period": 20   // Volume MA period
}
```

**Signals:**
- BUY: Price > MA + Strong ADX + Volume confirmation
- SELL: Price < MA + Strong ADX + Volume confirmation

### Risk Management

```json
{
  "max_position_size": 0.2,    // 20% max per position
  "stop_loss_pct": 0.05,       // 5% stop loss
  "take_profit_pct": 0.15,     // 15% take profit
  "max_total_exposure": 0.8    // 80% max total exposure
}
```

### Trading Settings

```json
{
  "check_interval_minutes": 60,  // How often to check
  "dry_run": true,               // Paper trading mode
  "data_lookback_days": 300,     // Historical data to fetch
  "trading_hours_only": true     // Only trade during market hours
}
```

## Usage Examples

### Example 1: Single Symbol, Single Strategy

```json
{
  "symbols": ["SPY"],
  "active_strategy": "MovingAverageCrossover",
  "strategies": {
    "MovingAverageCrossover": {
      "short_window": 50,
      "long_window": 200
    }
  }
}
```

### Example 2: Multiple Symbols, Momentum Strategy

```json
{
  "symbols": ["SPY", "QQQ", "IWM", "AAPL", "MSFT"],
  "active_strategy": "Momentum",
  "strategies": {
    "Momentum": {
      "rsi_period": 14,
      "rsi_oversold": 35,
      "rsi_overbought": 65
    }
  }
}
```

### Example 3: Mean Reversion with Tight Stops

```json
{
  "symbols": ["SPY", "QQQ"],
  "active_strategy": "MeanReversion",
  "stop_loss_pct": 0.03,
  "take_profit_pct": 0.06,
  "strategies": {
    "MeanReversion": {
      "bb_period": 20,
      "bb_std": 2.0,
      "entry_threshold": 0.01
    }
  }
}
```

## Python API Usage

```python
from quant_trading_agent import QuantTradingAgent, Signal

# Create agent
agent = QuantTradingAgent(config_path='quant_config.yaml')

# Analyze a single symbol
signal, details = agent.analyze_symbol('SPY', strategy_name='Momentum')
print(f"Signal: {signal.value}")
print(f"Reason: {details['reason']}")

# Run one analysis cycle
agent.run_analysis_cycle()

# Get agent status
status = agent.get_status()
print(f"Current positions: {status['positions']}")
```

## Adding Custom Strategies

To add your own strategy:

1. Create a new class inheriting from `TradingStrategy`
2. Implement required methods:
   - `calculate_signals()`: Generate trading signals
   - `get_required_data_period()`: Return minimum data needed

```python
class MyCustomStrategy(TradingStrategy):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.my_param = config.get('my_param', 10)
    
    def get_required_data_period(self) -> int:
        return self.my_param + 20
    
    def calculate_signals(self, data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict[str, Any]]:
        if not self.validate_data(data):
            return Signal.HOLD, {'error': 'Invalid data'}
        
        # Your strategy logic here
        signal = Signal.BUY  # or SELL, HOLD
        
        details = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': self.name,
            'signal': signal.value,
            'reason': 'Your reason here',
            'price': float(data['Close'].iloc[-1]),
        }
        
        return signal, details
```

3. Register your strategy in `_initialize_strategies()`:

```python
strategy_classes = {
    'MovingAverageCrossover': MovingAverageCrossoverStrategy,
    'Momentum': MomentumStrategy,
    'MyCustomStrategy': MyCustomStrategy,  # Add here
}
```

## Integration with Interactive Brokers

To enable live trading with Interactive Brokers:

1. Install TWS or IB Gateway
2. Enable API connections in TWS/Gateway
3. Update configuration:

```json
{
  "dry_run": false,
  "use_interactive_brokers": true,
  "ib_host": "127.0.0.1",
  "ib_port": 7497,  // 7497 for paper, 7496 for live
  "ib_client_id": 3
}
```

## Logging and Monitoring

### Log Files

- **Application Log**: `logs/quant_agent_YYYYMMDD.log`
  - All agent activity
  - Strategy calculations
  - Error messages

- **Trade Log**: `logs/trades_YYYYMM.json`
  - All executed trades
  - Entry/exit prices
  - P&L tracking

### Example Trade Log Entry

```json
{
  "timestamp": "2026-01-25T10:30:00",
  "symbol": "SPY",
  "action": "BUY",
  "price": 485.50,
  "strategy": "MovingAverageCrossover",
  "reason": "Golden Cross detected",
  "dry_run": true
}
```

## Performance Monitoring

Check positions and performance:

```python
agent = QuantTradingAgent()
status = agent.get_status()

for symbol, position in status['positions'].items():
    if position.get('has_position'):
        print(f"{symbol}: Entry ${position['entry_price']:.2f}")
```

## Testing and Backtesting

Run the agent once to test configuration:

```bash
python quant_trading_agent.py --once
```

For backtesting, modify the data fetching to use historical periods:

```python
# Fetch historical data
start_date = '2024-01-01'
end_date = '2025-01-01'
data = agent.fetch_market_data('SPY', days=365)

# Test strategy
signal, details = strategy.calculate_signals(data, 'SPY')
```

## Troubleshooting

### Common Issues

1. **"Insufficient data" error**
   - Increase `data_lookback_days` in config
   - Check if symbol has enough history

2. **No signals generated**
   - Review strategy parameters
   - Check if conditions are too strict
   - Verify market data quality

3. **Connection errors**
   - Check internet connection
   - Verify IB Gateway is running (if using IB)
   - Check API settings

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Security Best Practices

1. **Never commit sensitive data**
   - Keep API keys out of config files
   - Use environment variables for credentials

2. **Start with dry_run = true**
   - Test thoroughly before live trading
   - Verify strategy logic

3. **Monitor positions regularly**
   - Check logs daily
   - Review trade history
   - Validate P&L

## License

This is a trading bot framework for educational and research purposes. Use at your own risk. Trading involves substantial risk of loss.

## Support

For issues or questions:
- Check the logs for error details
- Review configuration parameters
- Test with single symbol first
- Use dry_run mode for testing

## Roadmap

- [ ] Backtesting engine with performance metrics
- [ ] Portfolio optimization
- [ ] Machine learning strategy support
- [ ] Real-time alerts and notifications
- [ ] Web dashboard for monitoring
- [ ] Multi-timeframe analysis
- [ ] Options trading strategies
