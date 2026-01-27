"""
Testing utilities for trading strategies
"""

from datetime import datetime
from typing import Dict, Tuple
import pandas as pd
import numpy as np

from .base import Signal, TradingStrategy


def generate_sample_data(symbol: str, days: int = 300, trend: str = 'uptrend') -> pd.DataFrame:
    """
    Generate sample market data for testing
    
    Args:
        symbol: Stock symbol
        days: Number of days
        trend: 'uptrend', 'downtrend', or 'sideways'
    
    Returns:
        DataFrame with OHLCV data
    """
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Base price
    base_price = 100.0
    
    # Generate price series based on trend
    if trend == 'uptrend':
        trend_component = np.linspace(0, 20, days)
    elif trend == 'downtrend':
        trend_component = np.linspace(0, -20, days)
    else:  # sideways
        trend_component = np.sin(np.linspace(0, 4 * np.pi, days)) * 5
    
    # Add random noise
    noise = np.random.randn(days) * 2
    
    # Generate close prices
    close_prices = base_price + trend_component + noise
    
    # Generate OHLCV data
    data = {
        'Open': close_prices + np.random.randn(days) * 0.5,
        'High': close_prices + abs(np.random.randn(days)) * 1.0,
        'Low': close_prices - abs(np.random.randn(days)) * 1.0,
        'Close': close_prices,
        'Volume': np.random.randint(1000000, 10000000, days)
    }
    
    df = pd.DataFrame(data, index=dates)
    
    # Ensure High is highest and Low is lowest
    df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
    df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)
    
    return df


def test_strategy(strategy_name: str, strategy_class, config: dict, trend: str = 'uptrend') -> Tuple[Signal, Dict]:
    """
    Test a specific strategy with sample data
    
    Args:
        strategy_name: Name of the strategy
        strategy_class: Strategy class to instantiate
        config: Configuration dictionary for the strategy
        trend: Market trend to simulate ('uptrend', 'downtrend', or 'sideways')
    
    Returns:
        Tuple of (signal, details)
    """
    print(f"\n{'='*80}")
    print(f"Testing {strategy_name} - {trend.upper()}")
    print(f"{'='*80}")
    
    # Create strategy instance
    strategy = strategy_class(config)
    
    # Generate sample data
    data = generate_sample_data('TEST', days=strategy.get_required_data_period(), trend=trend)
    
    print(f"Data period: {len(data)} days")
    print(f"Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    
    # Calculate signals
    signal, details = strategy.calculate_signals(data, 'TEST')
    
    print(f"\nSignal: {signal.value}")
    print(f"Reason: {details.get('reason', 'N/A')}")
    print(f"Current Price: ${details.get('price', 0):.2f}")
    
    # Print strategy-specific details
    print("\nStrategy Details:")
    for key, value in details.items():
        if key not in ['timestamp', 'symbol', 'strategy', 'signal', 'reason', 'price']:
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
    
    return signal, details


def test_all_strategies(strategies_to_test: list) -> Dict[str, Dict[str, str]]:
    """
    Test all provided strategies with different market conditions
    
    Args:
        strategies_to_test: List of tuples (name, class, config)
    
    Returns:
        Dictionary with test results for each strategy and trend
    """
    print("\n" + "="*80)
    print("QUANTITATIVE TRADING AGENT - STRATEGY TESTS")
    print("="*80)
    
    results = {}
    
    # Test each strategy with different market conditions
    for strategy_name, strategy_class, config in strategies_to_test:
        results[strategy_name] = {}
        
        for trend in ['uptrend', 'downtrend', 'sideways']:
            try:
                signal, details = test_strategy(strategy_name, strategy_class, config, trend)
                results[strategy_name][trend] = signal.value
            except Exception as e:
                print(f"ERROR: {e}")
                results[strategy_name][trend] = 'ERROR'
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\n{'Strategy':<30} {'Uptrend':<12} {'Downtrend':<12} {'Sideways':<12}")
    print("-" * 80)
    
    for strategy_name in results:
        uptrend = results[strategy_name].get('uptrend', 'N/A')
        downtrend = results[strategy_name].get('downtrend', 'N/A')
        sideways = results[strategy_name].get('sideways', 'N/A')
        print(f"{strategy_name:<30} {uptrend:<12} {downtrend:<12} {sideways:<12}")
    
    print("\n✅ All strategy tests completed!")
    
    return results
