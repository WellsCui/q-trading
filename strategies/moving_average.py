"""
Moving Average Crossover Strategy
"""

from datetime import datetime
from typing import Dict, Tuple, Any
import logging
import pandas as pd

from .base import TradingStrategy, Signal


class MovingAverageCrossoverStrategy(TradingStrategy):
    """
    Moving Average Crossover Strategy
    
    Generates signals when short-term MA crosses above/below long-term MA.
    Classic trend-following strategy.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger = None):
        super().__init__(config, logger)
        self.short_window = config.get('short_window', 50)
        self.long_window = config.get('long_window', 120)
        self.price_threshold = config.get('price_threshold', 0.0)  # Additional price filter
        
    def get_required_data_period(self) -> int:
        return self.long_window + 10  # Extra buffer
    
    def calculate_signals(self, data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict[str, Any]]:
        """Calculate MA crossover signals"""
        if not self.validate_data(data):
            return Signal.HOLD, {'error': 'Invalid data'}
        self.long_window=len(data)
        
        # Calculate moving averages
        data['SMA_Short'] = data['Close'].rolling(window=self.short_window).mean()
        data['SMA_Long'] = data['Close'].rolling(window=self.long_window).mean()
        
        # Get latest values
        current_price = float(data['Close'].iloc[-1])
        sma_short = float(data['SMA_Short'].iloc[-1])
        sma_long = float(data['SMA_Long'].iloc[-1])
        prev_sma_short = float(data['SMA_Short'].iloc[-2])
        prev_sma_long = float(data['SMA_Long'].iloc[-2])
        
        # Detect crossover
        signal = Signal.HOLD
        reason = ""
        score = 0.0
        
        # Calculate MA spread percentage
        ma_spread = ((sma_short - sma_long) / sma_long) * 100
        price_vs_short = ((current_price - sma_short) / sma_short) * 100
        
        if sma_short > sma_long and prev_sma_short <= prev_sma_long:
            # Bullish crossover (golden cross)
            if current_price >= sma_short * (1 + self.price_threshold):
                signal = Signal.BUY
                reason = f"Golden Cross: {self.short_window}-MA crossed above {self.long_window}-MA"
                # Strong buy signal with crossover bonus
                score = min(100, 70 + ma_spread * 10 + price_vs_short * 5)
        elif sma_short < sma_long and prev_sma_short >= prev_sma_long:
            # Bearish crossover (death cross)
            signal = Signal.SELL
            reason = f"Death Cross: {self.short_window}-MA crossed below {self.long_window}-MA"
            # Strong sell signal with crossover bonus
            score = max(-100, -70 + ma_spread * 10 + price_vs_short * 5)
        elif sma_short > sma_long and current_price >= sma_short:
            # Uptrend confirmation
            signal = Signal.BUY
            reason = f"Uptrend: Price above {self.short_window}-MA, {self.short_window}-MA above {self.long_window}-MA"
            # Moderate buy signal based on trend strength
            score = min(100, 30 + ma_spread * 15 + price_vs_short * 3)
        elif sma_short < sma_long:
            # Downtrend
            signal = Signal.SELL
            reason = f"Downtrend: {self.short_window}-MA below {self.long_window}-MA"
            # Moderate sell signal based on trend weakness
            score = max(-100, -30 + ma_spread * 15 + price_vs_short * 3)
        
        details = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': self.name,
            'signal': signal.value,
            'reason': reason,
            'score': score,
            'price': current_price,
            'sma_short': sma_short,
            'sma_long': sma_long,
            'short_window': self.short_window,
            'long_window': self.long_window,
        }
        
        return signal, details
