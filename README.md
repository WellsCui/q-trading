# QQQ/TQQQ Automated Trading Bot

A Python-based automated trading bot that implements a leveraged ETF rotation strategy between QQQ and TQQQ based on moving averages.

## 🎯 Strategy Overview

The bot uses a systematic approach to rotate between:
- **TQQQ** (3x leveraged): During strong uptrends
- **QQQ** (unleveraged): During uptrend corrections
- **Cash**: During downtrends

### Trading Rules

1. **Hold TQQQ**: When 30-day MA > 120-day MA AND price > 30-day MA (strong uptrend)
2. **Hold QQQ**: When 30-day MA > 120-day MA BUT price < 30-day MA (uptrend with correction)
3. **Hold Cash**: When 30-day MA < 120-day MA (downtrend - capital preservation)

This approach aims to:
- Maximize gains during strong bull markets using leverage
- Reduce risk during corrections by switching to unleveraged exposure
- Preserve capital during bear markets by moving to cash

## 📁 Project Structure

```
.
├── qqq_trading_bot.py      # Main trading bot script
├── monitor.py              # Monitoring and status tool
├── bot_control.sh          # Control script (start/stop/status)
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── logs/                   # Log files (auto-created)
│   ├── trading_bot_YYYYMMDD.log
│   └── trades.jsonl
└── factor-testing/         # Strategy backtesting notebooks
    └── quantitative_trading_strategy_qqq.ipynb
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make control script executable
chmod +x bot_control.sh
```

### 2. Configuration

Edit `config.json` to customize:
- Moving average periods (default: 30-day and 120-day)
- Check interval (default: 15 minutes)
- Trading hours settings
- Dry-run mode (recommended to start)

### 3. Run the Bot

```bash
# Start the bot in background
./bot_control.sh start

# Check status
./bot_control.sh status

# View logs in real-time
./bot_control.sh tail

# Stop the bot
./bot_control.sh stop
```

## 🔧 Configuration Options

### Strategy Parameters

```json
{
  "short_ma_period": 30,        // Short moving average (days)
  "long_ma_period": 120,        // Long moving average (days)
  "check_interval_minutes": 15, // How often to check signals
  "dry_run": true,              // Simulate trades (set false for live)
  "trading_hours_only": true,   // Only trade during market hours
  "data_lookback_days": 200     // Historical data to fetch
}
```

### Market Hours

The bot respects U.S. market hours (9:30 AM - 4:00 PM ET) by default and won't trade on weekends.

## 📊 Monitoring

### Real-time Monitoring

```bash
# Show current position and status
python3 monitor.py --status

# Show recent trade history
python3 monitor.py --trades

# Show recent logs
python3 monitor.py --logs

# Tail logs in real-time
python3 monitor.py --tail
```

### Log Files

- `logs/trading_bot_YYYYMMDD.log` - Detailed activity logs
- `logs/trades.jsonl` - Trade history in JSON format
- `logs/nohup.log` - Background process output

## 🛡️ Safety Features

### Dry-Run Mode (Default)

The bot starts in **dry-run mode** by default, which means:
- ✅ All calculations are performed
- ✅ Signals are generated and logged
- ✅ No real trades are executed
- ✅ Safe for testing and validation

To enable live trading:
1. Set `"dry_run": false` in `config.json`
2. Add broker API credentials
3. Implement broker integration (see below)

### Error Handling

- Automatic retry on data fetch failures
- Graceful shutdown on Ctrl+C or system signals
- Comprehensive error logging
- Position state persistence

## 🔌 Broker Integration

### Interactive Brokers (Fully Implemented)

The bot includes **full Interactive Brokers integration** with automatic order execution.

**Quick Setup**:

1. **Install IB API**: `pip install ibapi`
2. **Start IB Gateway/TWS** with API enabled (port 7497 for paper trading)
3. **Update config.json**:
```json
{
  "dry_run": false,
  "use_interactive_brokers": true,
  "ib_port": 7497
}
```

📖 **[Complete IB Setup Guide](IB_SETUP.md)** - Detailed instructions for Interactive Brokers integration

### Key Features

✅ Automatic position management  
✅ Real-time order execution  
✅ Position verification and sync  
✅ Paper trading support  
✅ Error handling and retry logic  
✅ Market orders with smart position sizing  

### Other Brokers

The architecture supports other brokers with minimal changes:

- **Alpaca**: `pip install alpaca-trade-api`
- **TD Ameritrade**: REST API integration
- **Others**: Implement broker interface in `execute_trade()`

## 📈 Performance Monitoring

### Key Metrics Tracked

- Current position (TQQQ/QQQ/Cash)
- QQQ price vs. moving averages
- Position change history
- Entry/exit prices
- Time in each position

### Trade History

All trades are logged in `logs/trades.jsonl` with:
- Timestamp
- Position (TQQQ/QQQ/Cash)
- QQQ and TQQQ prices
- Moving average values
- Signal rationale

## ⚠️ Risk Disclaimer

**IMPORTANT**: This bot is for educational and research purposes.

- Automated trading carries significant risk
- Past performance does not guarantee future results
- TQQQ is a leveraged ETF with higher volatility and decay
- Always start with dry-run mode
- Only invest capital you can afford to lose
- Consult with a financial advisor before live trading

## 🔧 Troubleshooting

### Bot won't start

```bash
# Check Python version (requires 3.7+)
python3 --version

# Install missing dependencies
pip install -r requirements.txt

# Check for errors in logs
cat logs/nohup.log
```

### Data fetch failures

- Check internet connection
- Verify yfinance package is installed
- Yahoo Finance API may have rate limits

### Bot stops unexpectedly

```bash
# Check system logs
./bot_control.sh logs

# Restart the bot
./bot_control.sh restart
```

## 🛠️ Advanced Usage

### Custom Strategy Parameters

Test different moving average periods:
```json
{
  "short_ma_period": 50,
  "long_ma_period": 200
}
```

### Extended Trading Hours

To check positions outside market hours:
```json
{
  "trading_hours_only": false
}
```

### More Frequent Checks

For faster signal detection:
```json
{
  "check_interval_minutes": 5
}
```

## 📚 Additional Resources

- **Backtesting Notebook**: `factor-testing/quantitative_trading_strategy_qqq.ipynb`
- **Strategy Analysis**: Review historical performance in the notebook
- **Parameter Optimization**: Test different MA periods before going live

## 🤝 Contributing

This is a personal trading bot. Modify and adapt it to your needs:
- Add new indicators (RSI, MACD, etc.)
- Implement different position sizing
- Add stop-loss rules
- Integrate with your preferred broker

## 📝 License

This project is provided as-is for educational purposes. Use at your own risk.

## 📧 Support

For questions or issues:
1. Review the troubleshooting section
2. Check log files for error messages
3. Ensure all dependencies are installed
4. Test in dry-run mode first

---

**Last Updated**: December 2025
**Strategy**: QQQ/TQQQ Moving Average Rotation
**Status**: Production-ready (dry-run mode)
