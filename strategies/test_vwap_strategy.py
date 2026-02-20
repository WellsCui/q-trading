"""
Test script for VWAP Trading Strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.vwap import VWAPStrategy
from strategies.base import Signal


def generate_sample_data(days=100, start_price=100):
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    data = []
    price = start_price
    
    for date in dates:
        # Simulate price movement
        change = np.random.randn() * 2
        price += change
        
        # Generate OHLCV
        open_price = price
        high = price + abs(np.random.randn() * 1.5)
        low = price - abs(np.random.randn() * 1.5)
        close = price + np.random.randn() * 1
        volume = int(np.random.uniform(1000000, 5000000))
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume
        })
        
        price = close
    
    df = pd.DataFrame(data, index=dates)
    return df


def test_vwap_strategy():
    """Test the VWAP strategy with sample data"""
    print("=" * 70)
    print("VWAP Strategy Test")
    print("=" * 70)
    
    # Create strategy instance
    config = {
        'vwap_period': 20,
        'min_distance_pct': 0.1,
        'intraday_mode': False
    }
    strategy = VWAPStrategy(config)
    
    print(f"\nStrategy: {strategy.name}")
    print(f"Configuration:")
    print(f"  - VWAP Period: {strategy.vwap_period}")
    print(f"  - Min Distance: {strategy.min_distance_pct}%")
    print(f"  - Intraday Mode: {strategy.intraday_mode}")
    
    # Generate test data
    print("\nGenerating sample market data...")
    data = generate_sample_data(days=100, start_price=350)  # QQQ-like price
    print(f"Data shape: {data.shape}")
    print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    
    # Calculate signals
    print("\n" + "-" * 70)
    print("Calculating trading signals...")
    print("-" * 70)
    
    signal, details = strategy.calculate_signals(data, 'QQQ')
    
    print(f"\nSignal: {signal.value}")
    print(f"Reason: {details['reason']}")
    print(f"\nDetails:")
    print(f"  Current Price: ${details['price']:.2f}")
    print(f"  VWAP: ${details['vwap']:.2f}")
    print(f"  Distance from VWAP: {details['distance_pct']:+.2f}%")
    print(f"  Price Above VWAP: {details['price_above_vwap']}")
    print(f"  Bullish Cross: {details['bullish_cross']}")
    print(f"  Bearish Cross: {details['bearish_cross']}")
    print(f"  Signal Score: {details['score']:.2f}")
    print(f"  Volume: {details['volume']:,.0f}")
    print(f"  Avg Volume: {details['avg_volume']:,.0f}")
    print(f"  Volume Ratio: {details['volume_ratio']:.2f}x")
    
    # Test over multiple periods
    print("\n" + "-" * 70)
    print("Testing signal generation over last 10 days...")
    print("-" * 70)
    
    signals_history = []
    for i in range(10, 0, -1):
        test_data = data.iloc[:-i] if i > 1 else data
        signal, details = strategy.calculate_signals(test_data, 'QQQ')
        
        signals_history.append({
            'date': test_data.index[-1].date(),
            'price': details['price'],
            'vwap': details['vwap'],
            'distance': details['distance_pct'],
            'signal': signal.value
        })
    
    print(f"{'Date':<12} {'Price':>10} {'VWAP':>10} {'Distance':>10} {'Signal':>10}")
    print("-" * 70)
    for s in signals_history:
        print(f"{str(s['date']):<12} ${s['price']:>9.2f} ${s['vwap']:>9.2f} "
              f"{s['distance']:>9.2f}% {s['signal']:>10}")
    
    # Test stop loss calculation
    print("\n" + "-" * 70)
    print("Testing stop loss calculation...")
    print("-" * 70)
    
    current_price = details['price']
    current_vwap = details['vwap']
    
    long_stop = strategy.get_stop_loss_price(current_price, current_vwap, is_long=True)
    short_stop = strategy.get_stop_loss_price(current_price, current_vwap, is_long=False)
    
    print(f"Current Price: ${current_price:.2f}")
    print(f"Current VWAP: ${current_vwap:.2f}")
    print(f"Long Position Stop Loss: ${long_stop:.2f} ({((long_stop/current_price - 1) * 100):.2f}%)")
    print(f"Short Position Stop Loss: ${short_stop:.2f} ({((short_stop/current_price - 1) * 100):.2f}%)")
    
    # Strategy characteristics
    print("\n" + "=" * 70)
    print("VWAP Strategy Characteristics")
    print("=" * 70)
    print("""
Based on "The Holy Grail for Day Trading Systems" (Zarattini & Aziz, 2023):

Key Findings from Original Research:
- Tested on QQQ from Jan 2018 to Sep 2023
- Initial investment: $25,000
- Final value: $192,656 (671% return)
- Maximum drawdown: 9.4%
- Sharpe Ratio: 2.1
- Compared to buy-and-hold: 126% return, 37% drawdown, 0.7 Sharpe

Strategy Rules:
1. Go LONG when price is above VWAP (buying pressure)
2. Go SHORT when price is below VWAP (selling pressure)
3. Stop loss triggers when price crosses VWAP in opposite direction
4. No positions held overnight (close at end of day)

The strategy identifies market imbalances:
- Price above VWAP → Net buyers → Upward pressure continues
- Price below VWAP → Net sellers → Downward pressure continues
    """)
    
    print("=" * 70)
    print("Test completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    test_vwap_strategy()
