#!/usr/bin/env python3
"""
Example: Using the Broker Interface with QuantTradingAgent

This example demonstrates the different ways to use brokers with the trading agent.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def example_1_auto_broker():
    """Example 1: Let the agent create the broker from config"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Auto-Create Broker from Config")
    print("="*80 + "\n")
    
    from quant_trading_agent import QuantTradingAgent
    
    # Simple - just provide config path
    # Agent reads broker config from quant_config.json
    agent = QuantTradingAgent(config_path='quant_config.json')
    
    # Check what broker was created
    status = agent.get_status()
    print(f"✓ Broker Type: {status['broker']['type']}")
    print(f"✓ Connected: {status['broker']['connected']}")
    
    # Run one analysis cycle
    print("\nRunning analysis cycle...")
    agent.run_analysis_cycle()
    
    # Clean up
    agent.stop()
    print("✓ Done\n")


def example_2_mock_broker():
    """Example 2: Explicit MockBroker injection"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Explicit MockBroker for Testing")
    print("="*80 + "\n")
    
    from brokers.base_broker import MockBroker
    from quant_trading_agent import QuantTradingAgent
    
    # Create mock broker with custom config
    broker_config = {
        'total_capital': 50000,      # Starting with $50k
        'position_size_pct': 25      # Use 25% per position
    }
    
    broker = MockBroker(broker_config)
    broker.connect()
    
    print(f"✓ MockBroker initialized")
    print(f"  Starting Capital: ${broker.get_account_balance():,.2f}")
    print(f"  Buying Power: ${broker.get_buying_power():,.2f}")
    
    # Inject broker into agent
    agent = QuantTradingAgent(config_path='quant_config.json', broker=broker)
    
    # Simulate some trades
    print("\n✓ Placing test trades...")
    order_id_1 = broker.place_order('SPY', 'BUY', 50, 'MKT')
    order_id_2 = broker.place_order('QQQ', 'BUY', 30, 'MKT')
    
    print(f"  Order 1 ID: {order_id_1}")
    print(f"  Order 2 ID: {order_id_2}")
    
    # Check positions
    positions = broker.get_all_positions()
    print(f"\n✓ Current Positions: {len(positions)}")
    for symbol, pos in positions.items():
        print(f"  {symbol}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
    
    # Clean up
    agent.stop()
    print("\n✓ Done\n")


def example_3_ib_broker():
    """Example 3: Interactive Brokers integration"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Interactive Brokers Integration")
    print("="*80 + "\n")
    
    try:
        from brokers.ib_broker import IBBroker
        from quant_trading_agent import QuantTradingAgent
        
        # Configure IB broker
        broker_config = {
            'ib_host': '127.0.0.1',
            'ib_port': 7497,  # Paper trading
            'ib_client_id': 3,
            'total_capital': 100000,
            'position_size_pct': 95
        }
        
        print("Attempting to connect to Interactive Brokers...")
        print(f"  Host: {broker_config['ib_host']}")
        print(f"  Port: {broker_config['ib_port']}")
        print(f"  (Make sure TWS or IB Gateway is running)\n")
        
        broker = IBBroker(broker_config)
        
        if broker.connect():
            print("✓ Connected to Interactive Brokers!")
            
            # Get account info
            print(f"\n✓ Account Information:")
            print(f"  Portfolio Value: ${broker.get_portfolio_value():,.2f}")
            print(f"  Cash Balance: ${broker.get_account_balance():,.2f}")
            print(f"  Buying Power: ${broker.get_buying_power():,.2f}")
            
            # Get positions
            positions = broker.get_all_positions()
            print(f"\n✓ Current Positions: {len(positions)}")
            for symbol, pos in positions.items():
                print(f"  {symbol}: {pos.get('position', 0):.0f} shares")
            
            # Create agent with IB broker
            agent = QuantTradingAgent(config_path='quant_config.json', broker=broker)
            
            print(f"\n✓ Agent Status:")
            status = agent.get_status()
            print(f"  Broker: {status['broker']['type']}")
            print(f"  Connected: {status['broker']['connected']}")
            
            # Get market data through broker
            print(f"\n✓ Fetching market data for SPY...")
            market_data = broker.get_market_data('SPY')
            if market_data and market_data.get('close'):
                prices = market_data['close']
                latest_price = prices[-1] if isinstance(prices, list) else prices
                print(f"  Latest Price: ${latest_price:.2f}")
            
            # Clean up
            agent.stop()
            print("\n✓ Done - Disconnected from IB\n")
        else:
            print("✗ Could not connect to Interactive Brokers")
            print("  Make sure TWS/Gateway is running and accepting connections\n")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print("  This is expected if TWS/Gateway is not running\n")


def example_4_switching_brokers():
    """Example 4: Switching between brokers"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Switching Between Brokers")
    print("="*80 + "\n")
    
    from brokers.base_broker import MockBroker
    from quant_trading_agent import QuantTradingAgent
    
    print("Testing Strategy with MockBroker first...")
    
    # Phase 1: Test with mock broker
    mock_broker = MockBroker({'total_capital': 100000})
    mock_broker.connect()
    
    agent = QuantTradingAgent(config_path='quant_config.json', broker=mock_broker)
    agent.run_analysis_cycle()
    
    mock_metrics = mock_broker.get_performance_metrics()
    print(f"✓ Mock Trading Results:")
    print(f"  Total Trades: {mock_metrics['total_trades']}")
    
    agent.stop()
    
    print("\n" + "-"*80)
    print("Now testing with IB (if available)...")
    
    # Phase 2: Try with IB
    try:
        from brokers.ib_broker import IBBroker
        
        ib_broker = IBBroker({
            'ib_host': '127.0.0.1',
            'ib_port': 7497,
            'ib_client_id': 4,
            'total_capital': 100000
        })
        
        if ib_broker.connect():
            print("✓ Connected to IB - ready for live trading")
            
            # Create new agent with IB broker
            agent = QuantTradingAgent(config_path='quant_config.json', broker=ib_broker)
            
            # Could run live trading here
            # agent.run()
            
            agent.stop()
            print("✓ Done\n")
        else:
            print("⚠ IB not available, staying with mock broker\n")
            
    except Exception as e:
        print(f"⚠ IB not available: {e}")
        print("  Continuing with mock broker for development\n")


def example_5_validation():
    """Example 5: Order validation"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Order Validation")
    print("="*80 + "\n")
    
    from brokers.base_broker import MockBroker
    
    broker = MockBroker({'total_capital': 10000})  # Small account
    broker.connect()
    
    print(f"Account Balance: ${broker.get_account_balance():,.2f}")
    print(f"Buying Power: ${broker.get_buying_power():,.2f}\n")
    
    # Test various orders
    test_orders = [
        ('SPY', 'BUY', 10, 450.0),    # Valid order
        ('SPY', 'BUY', 1000, 450.0),  # Too large
        ('AAPL', 'SELL', 50, 180.0),  # No position
        ('QQQ', 'BUY', -10, 380.0),   # Invalid quantity
    ]
    
    for symbol, action, quantity, price in test_orders:
        is_valid, error_msg = broker.validate_order(
            symbol, action, quantity, 'MKT'
        )
        
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"{status}: {action} {quantity} {symbol} @ ${price:.2f}")
        if not is_valid:
            print(f"  Error: {error_msg}")
        print()


def main():
    """Run all examples"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Broker Interface Examples - QuantTradingAgent            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    examples = [
        ("Auto-Create Broker", example_1_auto_broker),
        ("Mock Broker", example_2_mock_broker),
        ("IB Broker", example_3_ib_broker),
        ("Switching Brokers", example_4_switching_brokers),
        ("Order Validation", example_5_validation),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n[{i}/{len(examples)}] {name}")
        try:
            func()
        except KeyboardInterrupt:
            print("\n\nExamples interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Error in example: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
