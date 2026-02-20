# VWAP (Volume Weighted Average Price) Trading Strategy

## Overview

This VWAP strategy implementation is based on the research paper ["Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4629280) by Carlo Zarattini and Andrew Aziz (2023).

The strategy identifies market imbalances by comparing current price to the Volume Weighted Average Price, entering long positions when price is above VWAP (buying pressure) and short positions when price is below VWAP (selling pressure).

## Research Background

### Original Study Results (QQQ, Jan 2018 - Sep 2023)

| Metric | VWAP Strategy | Buy & Hold |
|--------|---------------|------------|
| Initial Investment | $25,000 | $25,000 |
| Final Value | $192,656 | $56,500 |
| Total Return | 671% | 126% |
| Annual Return | ~41% | ~22% |
| Maximum Drawdown | 9.4% | 37% |
| Sharpe Ratio | 2.1 | 0.7 |

### Enhanced Results with TQQQ (3x Leveraged)

- Initial Investment: $25,000
- Final Value: $2,085,417
- Total Return: 8,242%
- Annual Return: 116%
- Maximum Drawdown: ~37%

## Strategy Logic

### VWAP Calculation

The Volume Weighted Average Price is calculated as:

```
VWAP = Σ(Typical Price × Volume) / ΣVolume

where: Typical Price = (High + Low + Close) / 3
```

### Entry Signals

- **LONG Entry**: Price crosses above VWAP
  - Indicates net buying pressure
  - Market participants are actively buying
  - Upward momentum likely to continue

- **SHORT Entry**: Price crosses below VWAP
  - Indicates net selling pressure
  - Market participants are actively selling
  - Downward momentum likely to continue

### Exit Signals

- **Close LONG**: Price crosses below VWAP
  - Buying pressure has diminished
  - Risk of downward reversal

- **Close SHORT**: Price crosses above VWAP
  - Selling pressure has diminished
  - Risk of upward reversal

### Position Management

- **Position Sizing**: Use 100% of available capital per trade
- **Stop Loss**: Dynamic, based on VWAP crossover
- **End of Day**: Close all positions (no overnight holds)
- **Risk Management**: Automatic stops when price crosses VWAP

## Implementation Details

### Class: `VWAPStrategy`

Located in: `strategies/vwap.py`

### Configuration Parameters

```python
config = {
    'vwap_period': 20,          # Rolling window for daily VWAP calculation
    'min_distance_pct': 0.0,    # Minimum % distance from VWAP to generate signal
    'intraday_mode': False      # Use intraday calculation (requires intraday data)
}
```

### Key Methods

#### `calculate_vwap(data: pd.DataFrame) -> pd.Series`
Calculates Volume Weighted Average Price using either:
- **Intraday Mode**: Resets VWAP calculation at market open each day
- **Daily Mode**: Uses rolling window over specified period

#### `calculate_signals(data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict]`
Generates trading signals by:
1. Calculating current VWAP
2. Comparing price to VWAP
3. Detecting crossovers
4. Calculating signal strength based on distance from VWAP

Returns:
- `Signal`: BUY, SELL, or HOLD
- `Dict`: Detailed signal information including price, VWAP, distance, volume metrics

#### `get_stop_loss_price(entry_price: float, current_vwap: float, is_long: bool) -> float`
Calculates dynamic stop loss price:
- **Long positions**: Stop at VWAP (or slightly below)
- **Short positions**: Stop at VWAP (or slightly above)

## Usage Example

### Basic Usage

```python
from strategies.vwap import VWAPStrategy
import pandas as pd

# Configure strategy
config = {
    'vwap_period': 20,
    'min_distance_pct': 0.1
}

strategy = VWAPStrategy(config)

# Load market data (OHLCV format)
data = pd.read_csv('market_data.csv')

# Generate signal
signal, details = strategy.calculate_signals(data, 'QQQ')

print(f"Signal: {signal.value}")
print(f"Reason: {details['reason']}")
print(f"Current Price: ${details['price']:.2f}")
print(f"VWAP: ${details['vwap']:.2f}")
print(f"Distance: {details['distance_pct']:+.2f}%")
```

### Integration with Trading Bot

```python
# In your trading agent configuration
strategies = [
    {
        'name': 'VWAP',
        'class': VWAPStrategy,
        'config': {
            'vwap_period': 20,
            'min_distance_pct': 0.1
        },
        'weight': 1.0
    }
]
```

## Testing

Run the test script to verify the strategy:

```bash
python test_vwap_strategy.py
```

The test will:
1. Generate sample market data
2. Calculate VWAP signals
3. Show signal history over 10 days
4. Display stop loss calculations
5. Print strategy characteristics

## Key Insights from Research

### Why VWAP Works

1. **Reflects Market Liquidity**: VWAP accounts for both price and volume, emphasizing high-activity periods

2. **Institutional Benchmark**: ~50% of institutional orders use VWAP execution

3. **Trend Identification**: Price location relative to VWAP indicates market sentiment:
   - Above VWAP = Bullish sentiment
   - Below VWAP = Bearish sentiment

4. **Dynamic Support/Resistance**: VWAP acts as intraday support/resistance level

### Market Conditions Tested

The original study tested through:
- 2 bear markets
- Multiple high-volatility events
- COVID-19 pandemic period
- Various market regimes

## Performance Considerations

### Strengths

- Superior risk-adjusted returns vs buy-and-hold
- Lower maximum drawdown
- Higher Sharpe ratio
- Works in various market conditions
- Simple, objective rules

### Limitations

- Requires sufficient liquidity (QQQ, TQQQ recommended)
- High trading frequency = higher commission costs
- Not suitable for low-volume stocks
- May underperform in ranging/sideways markets
- Requires real-time or minute-level data for best results

### Optimal Instruments

The strategy works best with:
- **QQQ**: Nasdaq-100 ETF (high liquidity)
- **TQQQ**: 3x leveraged QQQ (higher returns, higher risk)
- **SPY**: S&P 500 ETF
- **SPXL**: 3x leveraged SPY
- Other highly liquid ETFs

## Backtesting Recommendations

When backtesting this strategy:

1. **Use 1-minute data** for accurate VWAP calculation
2. **Include commissions**: $0.0005/share or your broker's rate
3. **Account for slippage**: Especially important for larger accounts
4. **Test multiple periods**: Include bull, bear, and sideways markets
5. **Consider position sizing**: 100% capital allocation as per original study
6. **No overnight positions**: Close all positions at 4:00 PM ET

## Risk Management

### Position Sizing
- Original study: 100% of available capital
- Conservative approach: 50-75% of capital
- Aggressive approach: 100% + moderate leverage

### Stop Loss Strategy
- **Primary**: Exit when price crosses VWAP in opposite direction
- **Secondary**: Optional fixed % stop (e.g., 2% for additional protection)
- **Time-based**: Mandatory close at end of trading day

### Risk Controls
1. Never hold overnight positions
2. Monitor maximum drawdown
3. Reduce position size during high volatility
4. Consider using options for defined risk
5. Scale position size with account growth

## Future Enhancements

Potential improvements to explore:

1. **Volume Profile Integration**: Use volume profile for additional confirmation
2. **Multi-Timeframe Analysis**: Combine multiple VWAP periods
3. **Volatility Filter**: Adjust position size based on ATR
4. **Regime Detection**: Adapt to market conditions
5. **Machine Learning**: Use ML to optimize entry/exit timing
6. **Options Strategies**: Implement with options for defined risk

## Credits

**Research Paper**: "Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems"
- **Authors**: Carlo Zarattini (Concretum Research) and Andrew Aziz (Peak Capital Trading)
- **Published**: November 13, 2023
- **Link**: Available on SSRN

**Implementation**: Based on the original research, adapted for the q-trading framework

## Disclaimer

This strategy is for educational and research purposes only. Past performance does not guarantee future results. The impressive returns shown in the original study do not guarantee similar future performance. Always:

- Test thoroughly before live trading
- Start with paper trading
- Use appropriate position sizing
- Consider your risk tolerance
- Consult with a financial advisor

Trading involves substantial risk of loss and is not suitable for all investors.

## References

1. Zarattini, C., & Aziz, A. (2023). Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems. SSRN.

2. Original study data: QQQ and TQQQ, January 2018 - September 2023

3. Data providers: IQFeed and Interactive Brokers

## Support

For questions or issues:
- Review the test script: `test_vwap_strategy.py`
- Check the implementation: `strategies/vwap.py`
- Read the base strategy: `strategies/base.py`
- See other strategy examples in `strategies/` folder
