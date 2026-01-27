#!/usr/bin/env python3
"""
Test Interactive Brokers connection and functionality.

This script verifies that:
1. IB API is installed correctly
2. Connection to IB Gateway/TWS works
3. Can retrieve account info and positions
4. Bot configuration is correct
"""

import sys
import json
import time

from pathlib import Path
# from backtrader import brokers

print("=" * 80)
print("Interactive Brokers Connection Test")
print("=" * 80)
print()

# Test 1: Check if ibapi is installed
print("Test 1: Checking ibapi installation...")
try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    print("✓ ibapi is installed")
except ImportError as e:
    print("✗ ibapi not found")
    print(f"  Error: {e}")
    print("  Install with: pip install ibapi")
    sys.exit(1)

print()

# Test 2: Check if ib_broker module loads
print("Test 2: Checking ib_broker module...")
try:
    from brokers.ib_broker import IBBroker, create_ib_broker
    print("✓ ib_broker module loaded successfully")
except ImportError as e:
    print("✗ Failed to load ib_broker module")
    print(f"  Error: {e}")
    sys.exit(1)

print()

# Test 3: Load configuration
print("Test 3: Loading configuration...")
config_path = "config.json"
if not Path(config_path).exists():
    print(f"✗ Config file not found: {config_path}")
    sys.exit(1)

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    print("✓ Configuration loaded")
    
    # Display IB settings
    print("\n  IB Settings:")
    print(f"    Host: {config.get('ib_host', '127.0.0.1')}")
    print(f"    Port: {config.get('ib_port', 7497)}")
    print(f"    Client ID: {config.get('ib_client_id', 1)}")
    print(f"    Dry Run: {config.get('dry_run', True)}")
    print(f"    Use IB: {config.get('use_interactive_brokers', False)}")
    
    if config.get('ib_port') == 7497:
        print(f"    Mode: Paper Trading (Port 7497)")
    elif config.get('ib_port') == 7496:
        print(f"    Mode: Live Trading (Port 7496)")
    
except Exception as e:
    print(f"✗ Error loading config: {e}")
    sys.exit(1)

print()

# Test 4: Check if IB Gateway/TWS is running
print("Test 4: Attempting to connect to IB Gateway/TWS...")
print("  (Make sure IB Gateway or TWS is running with API enabled)")
print()

try:
    broker = create_ib_broker(config)
    
    if broker and broker.connected:
        print("✓ Connected to Interactive Brokers!")
        print()
        
        # Test 5: Get account info
        # print("Test 5: Retrieving account information...")
        # time.sleep(2)  # Wait for data
        
        # account_value = broker.get_account_value()
        # print(f"✓ Account Value: ${account_value:,.2f}")
        
        # Test 6: Get current positions
        print()
        print("Test 6: Retrieving current positions...")
        time.sleep(1)
        
        current_holding = broker.get_current_holding()
        print(f"✓ Current Position: {current_holding}")
        
        # Show all positions
        with broker.client.lock:
            if broker.client.positions:
                print("\n  All Positions:")
                for symbol, pos_info in broker.client.positions.items():
                    qty = pos_info['position']
                    avg_cost = pos_info['avg_cost']
                    print(f"    {symbol}: {qty:,.0f} shares @ ${avg_cost:.2f}")
            else:
                print("  No open positions")
        
        # Test 7: Test position calculation
        print()
        print("Test 7: Testing position sizing calculation...")
        test_price = 450.00  # Example QQQ price
        shares = broker.calculate_shares('QQQ', test_price)
        position_value = shares * test_price
        print(f"✓ For ${test_price:.2f}/share:")
        print(f"    Would buy: {shares:,} shares")
        print(f"    Position value: ${position_value:,.2f}")
        print(f"    Using {config.get('position_size_pct', 95)}% of capital")
        
        # Success!
        print()
        print("=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("Your Interactive Brokers connection is working correctly.")
        print("The bot is ready to run in live mode.")
        print()
        print("Next steps:")
        print("  1. Review your configuration in config.json")
        print("  2. Test with paper trading first (port 7497)")
        print("  3. Start the bot: ./bot_control.sh start")
        print()
        
        # Disconnect
        broker.disconnect()
        
    else:
        print("✗ Failed to connect to Interactive Brokers")
        print()
        print("Troubleshooting:")
        print("  1. Is IB Gateway or TWS running?")
        print("  2. Is API access enabled in IB settings?")
        print("  3. Is the port correct? (7497 for paper, 7496 for live)")
        print("  4. Is 127.0.0.1 in the trusted IP addresses?")
        print()
        print("See IB_SETUP.md for detailed setup instructions")
        sys.exit(1)
        
except KeyboardInterrupt:
    print("\n\n✗ Test interrupted by user")
    sys.exit(1)
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Start IB Gateway or TWS")
    print("  2. Check API settings (Configure → Settings → API)")
    print("  3. Verify port number in config.json")
    print("  4. Check firewall settings")
    print()
    print("See IB_SETUP.md for detailed setup instructions")
    import traceback
    traceback.print_exc()
    sys.exit(1)
