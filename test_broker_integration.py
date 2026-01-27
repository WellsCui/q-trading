#!/usr/bin/env python3
"""
Test Broker Integration with QuantTradingAgent

This script demonstrates how to:
1. Create a broker instance (Mock or IB)
2. Inject it into QuantTradingAgent
3. Use the agent with broker integration
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from brokers.base_broker import MockBroker
from brokers.ib_broker import IBBroker
from quant_trading_agent import QuantTradingAgent


def test_mock_broker():
    """Test with mock broker"""
    print("=" * 80)
    print("Testing with MockBroker")
    print("=" * 80)
    
    # Create mock broker
    config = {
        'total_capital': 100000,
        'position_size_pct': 20
    }
    broker = MockBroker(config)
    
    # Connect
    if broker.connect():
        print(f"✓ Connected to MockBroker")
        print(f"  Portfolio Value: ${broker.get_portfolio_value():,.2f}")
        print(f"  Buying Power: ${broker.get_buying_power():,.2f}")
    
    # Create agent with broker
    agent = QuantTradingAgent(config_path='quant_config.json', broker=broker)
    
    # Get status
    status = agent.get_status()
    print(f"\n✓ Agent Status:")
    print(f"  Broker Type: {status['broker']['type']}")
    print(f"  Broker Connected: {status['broker']['connected']}")
    print(f"  Strategies: {', '.join(status['strategies'])}")
    print(f"  Symbols: {', '.join(status['symbols'])}")
    
    # Test broker operations
    print(f"\n✓ Testing broker operations:")
    
    # Place a test order
    order_id = broker.place_order('SPY', 'BUY', 10, 'MKT')
    print(f"  Placed order: {order_id}")
    
    # Check positions
    positions = broker.get_all_positions()
    print(f"  Positions: {positions}")
    
    # Clean up
    agent.stop()
    print(f"\n✓ Agent stopped successfully")


def test_ib_broker():
    """Test with Interactive Brokers broker"""
    print("\n" + "=" * 80)
    print("Testing with IBBroker")
    print("=" * 80)
    
    # Load IB configuration
    try:
        with open('quant_config.json', 'r') as f:
            config_data = json.load(f)
        
        broker_config = config_data.get('broker', {})
        
        # Only test if IB is configured
        if broker_config.get('type') != 'ib':
            print("⚠ IBBroker not configured in quant_config.json (broker.type != 'ib')")
            print("  Skipping IB test")
            return
        
        # Create IB broker
        broker = IBBroker(broker_config)
        
        # Try to connect
        print(f"Attempting to connect to IB at {broker_config.get('ib_host')}:{broker_config.get('ib_port')}...")
        if broker.connect():
            print(f"✓ Connected to Interactive Brokers")
            print(f"  Portfolio Value: ${broker.get_portfolio_value():,.2f}")
            print(f"  Buying Power: ${broker.get_buying_power():,.2f}")
            
            # Create agent with IB broker
            agent = QuantTradingAgent(config_path='quant_config.json', broker=broker)
            
            # Get status
            status = agent.get_status()
            print(f"\n✓ Agent Status:")
            print(f"  Broker Type: {status['broker']['type']}")
            print(f"  Broker Connected: {status['broker']['connected']}")
            print(f"  Portfolio Value: ${status['broker'].get('portfolio_value', 0):,.2f}")
            print(f"  Positions: {status['broker'].get('positions', {})}")
            
            # Clean up
            agent.stop()
            print(f"\n✓ Agent stopped and disconnected from IB")
        else:
            print("✗ Failed to connect to Interactive Brokers")
            print("  Make sure TWS/IB Gateway is running and configured correctly")
            
    except FileNotFoundError:
        print("✗ quant_config.json not found")
    except Exception as e:
        print(f"✗ Error testing IB broker: {e}")


def test_agent_without_broker():
    """Test agent creating its own broker"""
    print("\n" + "=" * 80)
    print("Testing Agent with Auto-created Broker")
    print("=" * 80)
    
    # Create agent without providing broker - it will create one from config
    agent = QuantTradingAgent(config_path='quant_config.json')
    
    status = agent.get_status()
    print(f"✓ Agent created with auto-initialized broker:")
    print(f"  Broker Type: {status['broker']['type']}")
    print(f"  Broker Connected: {status['broker']['connected']}")
    
    agent.stop()
    print(f"✓ Agent stopped successfully")


def main():
    """Run all tests"""
    print("Broker Integration Test Suite")
    print("=" * 80)
    
    try:
        # Test 1: Mock broker
        test_mock_broker()
        
        # Test 2: IB broker (if configured)
        test_ib_broker()
        
        # Test 3: Agent auto-creates broker
        test_agent_without_broker()
        
        print("\n" + "=" * 80)
        print("All tests completed!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
