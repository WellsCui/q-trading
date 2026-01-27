# Quantitative Trading Agent - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install pandas numpy yfinance
```

### Step 2: Test the Agent
```bash
python test_quant_agent.py
```

### Step 3: Run the Agent
```bash
# Run once to test
python quant_trading_agent.py --once

# Run continuously (checks every hour)
python quant_trading_agent.py
```

## 📁 Project Structure

```
q-trading/
├── quant_trading_agent.py      # Main agent
├── quant_config.json            # Configuration
├── test_quant_agent.py          # Test suite
├── strategies/                  # Strategy modules (organized!)
│   ├── __init__.py             # Package initialization
│   ├── base.py                 # Base classes (TradingStrategy, Signal)
│   ├── moving_average.py       # MA Crossover strategy
│   ├── momentum.py             # RSI/ROC momentum strategy
│   ├── mean_reversion.py       # Bollinger Bands strategy
│   └── trend_following.py      # ADX trend following strategy
└── logs/                        # Generated logs and trades
```

## 📋 Available Strategies

| Strategy | Best For | Key Indicators |
|----------|----------|----------------|
| **MovingAverageCrossover** | Trending markets | SMA 50/200 |
| **Momentum** | Volatile markets | RSI, ROC |
| **MeanReversion** | Range-bound markets | Bollinger Bands |
| **TrendFollowing** | Strong trends | ADX, Volume |

## 🎯 Common Configurations

### Conservative Setup (Low Risk)
```json
{
  "symbols": ["SPY", "QQQ"],
  "active_strategy": "MovingAverageCrossover",
  "max_position_size": 0.15,
  "stop_loss_pct": 0.03,
  "take_profit_pct": 0.10
}
```

### Aggressive Setup (High Risk/Reward)
```json
{
  "symbols": ["QQQ", "TQQQ", "SQQQ"],
  "active_strategy": "Momentum",
  "max_position_size": 0.30,
  "stop_loss_pct": 0.08,
  "take_profit_pct": 0.25
}
```

### Diversified Multi-Strategy
```json
{
  "symbols": ["SPY", "QQQ", "IWM", "DIA", "TLT"],
  "active_strategy": "TrendFollowing",
  "max_position_size": 0.20,
  "check_interval_minutes": 30
}
```

## ⚙️ Strategy Parameters Cheat Sheet

### Moving Average Crossover
- `short_window`: 20-50 (faster) | 50-100 (slower)
- `long_window`: 100-200 (moderate) | 200-300 (conservative)

### Momentum
- `rsi_oversold`: 20-30 (aggressive) | 30-40 (conservative)
- `rsi_overbought`: 60-70 (conservative) | 70-80 (aggressive)

### Mean Reversion
- `bb_std`: 1.5 (tight bands) | 2.0 (standard) | 2.5-3.0 (wide bands)
- `entry_threshold`: 0.01 (1%, aggressive) | 0.02 (2%, moderate)

### Trend Following
- `adx_threshold`: 20 (more signals) | 25 (balanced) | 30+ (strong trends only)

## 📊 Example Workflows

### Workflow 1: Test New Strategy
```bash
# 1. Edit config
nano quant_config.json

# 2. Change active_strategy
"active_strategy": "Momentum"

# 3. Run once
python quant_trading_agent.py --once

# 4. Check logs
tail -f logs/quant_agent_*.log
```

### Workflow 2: Monitor Multiple Symbols
```bash
# 1. Add symbols to config
"symbols": ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]

# 2. Run analysis
python quant_trading_agent.py --once

# 3. Check which gave signals
cat logs/trades_*.json | grep "BUY\|SELL"
```

### Workflow 3: Use Custom Strategy
```python
# Create your own strategy in strategies/ folder
from strategies.base import TradingStrategy, Signal

class MyStrategy(TradingStrategy):
    def get_required_data_period(self):
        return 30
    
    def calculate_signals(self, data, symbol):
        # Your logic here
        return Signal.BUY, {'reason': 'Custom signal'}
```

## 🛠️ Common Commands

```bash
# Run once and exit
python quant_trading_agent.py --once

# Use custom config
python quant_trading_agent.py --config my_config.json

# View recent logs
tail -50 logs/quant_agent_$(date +%Y%m%d).log

# View recent trades
cat logs/trades_$(date +%Y%m).json | python -m json.tool

# Monitor live (continuously show new log entries)
tail -f logs/quant_agent_$(date +%Y%m%d).log

# Run in background (Unix/Mac)
nohup python quant_trading_agent.py > output.log 2>&1 &

# Stop background process
pkill -f quant_trading_agent
```

## 📈 Reading the Output

### Signal Output Example
```
================================================================================
SIGNAL: SPY - BUY
================================================================================
Strategy: MovingAverageCrossover
Price: $485.50
Reason: Golden Cross: 50-MA crossed above 200-MA
================================================================================
```

### Understanding Details
- **Golden Cross** = Bullish signal (50-MA crosses above 200-MA)
- **Death Cross** = Bearish signal (50-MA crosses below 200-MA)
- **Oversold** = RSI < 30, potential buy opportunity
- **Overbought** = RSI > 70, potential sell opportunity

## 🔍 Troubleshooting

### Issue: No signals generated
**Solution:** 
- Lower strategy thresholds
- Check if market conditions match strategy
- Try different strategy

### Issue: Too many signals
**Solution:**
- Increase thresholds (e.g., `adx_threshold`)
- Add stricter filters
- Increase `check_interval_minutes`

### Issue: Data fetch errors
**Solution:**
- Check internet connection
- Verify symbol is valid (use Yahoo Finance format)
- Increase `data_lookback_days`

## 💡 Tips & Best Practices

1. **Always start with dry_run = true**
2. **Test with one symbol first**
3. **Review logs daily**
4. **Start with conservative parameters**
5. **Keep stop losses in place**
6. **Don't over-optimize**

## 📝 Configuration Template

Minimal working config:
```json
{
  "symbols": ["SPY"],
  "active_strategy": "MovingAverageCrossover",
  "dry_run": true,
  "strategies": {
    "MovingAverageCrossover": {
      "short_window": 50,
      "long_window": 200
    }
  }
}
```

## 🎓 Learning Path

1. **Week 1:** Run with defaults, understand output
2. **Week 2:** Try different strategies, compare results
3. **Week 3:** Adjust parameters, test on different symbols
4. **Week 4:** Add custom symbols, monitor performance

## ⚠️ Important Disclaimers

- **Educational purposes only**
- **Past performance ≠ future results**
- **Always use risk management**
- **Start with paper trading**
- **Never risk more than you can afford to lose**

## 🔗 Quick Links

- Main Agent: `quant_trading_agent.py`
- Configuration: `quant_config.json`
- Test Suite: `test_quant_agent.py`
- Strategies: `strategies/` folder
- Full Documentation: `QUANT_AGENT_README.md`
- Logs: `logs/`

---

**Need help?** Check the full README or review the test output for examples.
