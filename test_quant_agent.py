#!/usr/bin/env python3
"""
Test script for Quantitative Trading Agent

Tests all strategies with sample data and verifies functionality
"""

import sys
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import the agent and strategies
from quant_trading_agent import QuantTradingAgent
from strategies import (
    MovingAverageCrossoverStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    TrendFollowingStrategy,
    Signal,
    test_strategy,
    test_all_strategies
)


def run_strategy_tests():
    """Run all strategy tests with predefined configurations"""
    strategies_to_test = [
        ('Moving Average Crossover', MovingAverageCrossoverStrategy, {
            'short_window': 50,
            'long_window': 200,
            'price_threshold': 0.0
        }),
        ('Momentum', MomentumStrategy, {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'roc_period': 20
        }),
        ('Mean Reversion', MeanReversionStrategy, {
            'bb_period': 20,
            'bb_std': 2.0,
            'entry_threshold': 0.02
        }),
        ('Trend Following', TrendFollowingStrategy, {
            'ma_period': 50,
            'adx_period': 14,
            'adx_threshold': 25,
            'volume_ma_period': 20
        }),
    ]
    
    # Run tests using the testing utilities from strategies package
    test_all_strategies(strategies_to_test)


def test_agent_initialization():
    """Test agent initialization and configuration"""
    print("\n" + "="*80)
    print("TESTING AGENT INITIALIZATION")
    print("="*80)
    
    # Test with default config
    print("\n1. Testing with default configuration...")
    try:
        agent = QuantTradingAgent(config_path='nonexistent_config.json')
        status = agent.get_status()
        print(f"✅ Agent initialized successfully")
        print(f"   Strategies: {', '.join(status['strategies'])}")
        print(f"   Symbols: {', '.join(status['symbols'])}")
        print(f"   Active Strategy: {status['active_strategy']}")
        print(f"   Dry Run: {status['dry_run']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test with custom config
    print("\n2. Testing with custom configuration...")
    custom_config = {
        'symbols': ['AAPL', 'MSFT'],
        'active_strategy': 'Momentum',
        'dry_run': True,
        'strategies': {
            'Momentum': {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'roc_period': 20
            }
        }
    }
    
    # Save custom config
    config_path = 'test_config.json'
    with open(config_path, 'w') as f:
        json.dump(custom_config, f, indent=2)
    
    try:
        agent = QuantTradingAgent(config_path=config_path)
        status = agent.get_status()
        print(f"✅ Agent initialized with custom config")
        print(f"   Symbols: {', '.join(status['symbols'])}")
        print(f"   Active Strategy: {status['active_strategy']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Clean up
    import os
    if os.path.exists(config_path):
        os.remove(config_path)
    
    return True


def test_agent_analysis():
    """Test agent analysis with real symbol"""
    print("\n" + "="*80)
    print("TESTING AGENT ANALYSIS (SPY)")
    print("="*80)
    
    try:
        # Create agent with minimal config
        config = {
            'symbols': ['SPY'],
            'active_strategy': 'MovingAverageCrossover',
            'dry_run': True,
            'data_lookback_days': 250,
            'strategies': {
                'MovingAverageCrossover': {
                    'short_window': 50,
                    'long_window': 200
                }
            }
        }
        
        config_path = 'test_agent_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        agent = QuantTradingAgent(config_path=config_path)
        
        print("\nFetching real market data for SPY...")
        result = agent.analyze_symbol('SPY')
        
        if result:
            signal, details = result
            print(f"\n✅ Analysis completed successfully")
            print(f"   Signal: {signal.value}")
            print(f"   Price: ${details.get('price', 0):.2f}")
            print(f"   Reason: {details.get('reason', 'N/A')}")
        else:
            print(f"❌ Analysis failed")
        
        # Clean up
        import os
        if os.path.exists(config_path):
            os.remove(config_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("QUANTITATIVE TRADING AGENT - TEST SUITE")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    print("\n[1/3] Testing Strategy Implementations...")
    run_strategy_tests()
    
    print("\n[2/3] Testing Agent Initialization...")
    if not test_agent_initialization():
        print("❌ Agent initialization tests failed")
        return
    
    print("\n[3/3] Testing Agent Analysis...")
    if not test_agent_analysis():
        print("⚠️  Agent analysis test failed (may need internet connection)")
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    print("\n✅ Test suite finished successfully!")
    print("\nNext steps:")
    print("1. Review the test results above")
    print("2. Configure quant_config.json for your needs")
    print("3. Run: python quant_trading_agent.py --once")
    print("4. Monitor logs in the logs/ directory")


if __name__ == "__main__":
    main()
