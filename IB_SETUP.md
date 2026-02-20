# Interactive Brokers Setup Guide

This guide will help you set up and configure Interactive Brokers (IB) for automated trading with the QQQ Trading Bot.

## 📋 Prerequisites

1. **Interactive Brokers Account**
   - Sign up at [www.interactivebrokers.com](https://www.interactivebrokers.com)
   - Complete account verification
   - Fund your account (or use paper trading)

2. **TWS or IB Gateway**
   - Download and install either:
     - **TWS (Trader Workstation)**: Full-featured trading platform
     - **IB Gateway**: Lightweight API interface (recommended for bots)
   - Available at: https://www.interactivebrokers.com/en/trading/tws.php

3. **API Permissions**
   - Enable API access in your IB account settings
   - Set socket port for API connections

## 🔧 Installation

### 1. Install IB API Python Package

```bash
pip install ibapi
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Configure IB Gateway/TWS

#### For Paper Trading (Recommended for Testing)

1. Open **IB Gateway** or **TWS**
2. Go to **Configure** → **Settings** → **API** → **Settings**
3. Configure:
   - ✅ Enable ActiveX and Socket Clients
   - ✅ Socket port: **7497** (paper trading default)
   - ✅ Master API client ID: Leave blank or set to specific ID
   - ✅ Read-Only API: Unchecked (we need to place orders)
   - ✅ Trusted IP addresses: Add `127.0.0.1`

#### For Live Trading

1. Same steps as paper trading, but:
   - Socket port: **7496** (live trading default)
   - **IMPORTANT**: Double-check all settings before enabling live trading!

### 3. Configure the Trading Bot

Edit `config.json`:

```json
{
  "dry_run": false,
  "use_interactive_brokers": true,
  
  "ib_host": "127.0.0.1",
  "ib_port": 7497,
  "ib_client_id": 1,
  "ib_account": "",
  
  "total_capital": 100000,
  "position_size_pct": 95
}
```

#### Configuration Parameters:

- **`dry_run`**: Set to `false` to enable live trading
- **`use_interactive_brokers`**: Set to `true` to use IB
- **`ib_host`**: IP address of IB Gateway/TWS (usually `127.0.0.1`)
- **`ib_port`**: 
  - `7497` for Paper Trading
  - `7496` for Live Trading
- **`ib_client_id`**: Unique ID for this bot (1-999)
- **`ib_account`**: Your IB account number (optional, auto-detected if blank)
- **`total_capital`**: Total capital to manage (used for position sizing)
- **`position_size_pct`**: Percentage of capital to use (95% recommended)

## 🚀 Starting the Bot with IB

### 1. Start IB Gateway/TWS

```bash
# Launch IB Gateway (or TWS)
# Log in with your credentials
# Ensure API settings are configured correctly
```

### 2. Verify Connection

Test the connection before running the bot:

```python
python3 -c "from brokers import create_ib_broker; import json; config = json.load(open('config.json')); broker = create_ib_broker(config); print('Connected!' if broker else 'Failed')"
```

### 3. Start the Trading Bot

```bash
# Start the bot
./bot_control.sh start

# Check status
./bot_control.sh status

# Monitor logs
./bot_control.sh tail
```

## 🔍 Monitoring & Verification

### Check Current Positions

```bash
# Via the monitoring script
python3 monitor.py --status

# Via IB Gateway/TWS
# Check the Portfolio tab to see current positions
```

### View Trade History

```bash
# View recent trades
python3 monitor.py --trades

# View detailed logs
python3 monitor.py --logs
```

### IB Activity Log

- In TWS/Gateway: **View** → **Activity** → **Audit Trail**
- Shows all API orders and executions

## ⚠️ Important Safety Notes

### Paper Trading First

**ALWAYS** test with paper trading before live trading:

1. Create a paper trading account in IB
2. Use port 7497 in config
3. Run for several days to verify behavior
4. Check all trades in the paper account

### Position Sizing

- Default: Uses 95% of capital, keeps 5% cash buffer
- Adjust `position_size_pct` in config.json
- Bot calculates shares based on current prices

### Order Types

- Bot uses **Market Orders** by default
- Orders execute at current market price
- Consider slippage, especially for TQQQ

### Error Handling

The bot handles common errors:
- Connection failures → Retries automatically
- Order rejections → Logs error and continues
- Insufficient funds → Logs warning

## 🔧 Troubleshooting

### "Connection refused" Error

**Cause**: IB Gateway/TWS not running or API not enabled

**Solution**:
1. Start IB Gateway/TWS
2. Verify API settings are enabled
3. Check port number matches config
4. Verify IP address `127.0.0.1` is in trusted IPs

### "Not connected" Messages

**Cause**: Lost connection to IB

**Solution**:
1. Check if IB Gateway/TWS is still running
2. Look for IB popup messages requiring attention
3. Restart the bot: `./bot_control.sh restart`

### "Order rejected" Errors

**Possible Causes**:
- Insufficient funds
- Outside market hours
- Symbol not found
- Account restrictions

**Solution**:
1. Check account balance in IB
2. Verify trading hours
3. Check IB activity log for details
4. Review bot logs: `./bot_control.sh logs`

### Orders Not Executing

**Check**:
1. Is market open?
2. Is IB Gateway showing "Connected" status?
3. Are there any IB popup messages?
4. Check order status in IB TWS/Gateway
5. Review bot logs for errors

### Position Mismatch

If bot thinks it has a different position than IB shows:

```bash
# Stop the bot
./bot_control.sh stop

# Manually close positions in IB if needed

# Restart the bot (it will sync with IB)
./bot_control.sh start
```

## 📊 Testing Checklist

Before live trading, verify:

- [ ] Paper trading account set up
- [ ] IB Gateway/TWS running with correct port
- [ ] Bot connects successfully
- [ ] Bot reads current positions correctly
- [ ] Test trades execute in paper account
- [ ] Position changes reflected in IB
- [ ] Bot logs show correct information
- [ ] Can stop/start bot cleanly
- [ ] Notifications work (if enabled)
- [ ] Run for at least 1 week in paper mode

## 🔐 Security Best Practices

1. **Never share** your IB credentials
2. **Use strong passwords** for IB account
3. **Enable 2FA** on IB account
4. **Restrict API access** to localhost only
5. **Monitor regularly** - check positions daily
6. **Set up alerts** in IB for unusual activity
7. **Use read-only API** for monitoring only (if not trading)

## 📚 Additional Resources

- [IB API Documentation](https://interactivebrokers.github.io/tws-api/)
- [IB Python API Guide](https://interactivebrokers.github.io/tws-api/python_api.html)
- [IB API Settings](https://www.interactivebrokers.com/en/index.php?f=5041)

## 🆘 Support

### IB Support

- Client Portal: https://www.interactivebrokers.com/sso/
- Phone: 1-877-442-2757 (US)
- Live Chat: Available in Client Portal

### Bot Issues

1. Check logs: `./bot_control.sh logs`
2. Review this guide
3. Test connection manually
4. Verify IB settings

## 📝 Change Log

### Enabling Live Trading

When ready to switch from paper to live:

1. **Stop the bot**: `./bot_control.sh stop`
2. **Update config.json**:
   ```json
   {
     "ib_port": 7496,
     "dry_run": false
   }
   ```
3. **Close IB Gateway** and reopen with live account
4. **Test connection** manually first
5. **Start small** - reduce position_size_pct initially
6. **Monitor closely** for first few days
7. **Gradually increase** position size as confidence grows

---

**Remember**: Start with paper trading, monitor closely, and only move to live trading when you're completely comfortable with the bot's behavior!
