"""
Mean Reversion Strategy using Bollinger Bands
"""

from datetime import datetime
from typing import Dict, Tuple, Any
import logging
import pandas as pd

from .base import TradingStrategy, Signal


class MeanReversionStrategy(TradingStrategy):
    """
    Mean Reversion Strategy using Bollinger Bands
    
    Buys when price touches lower band, sells when price touches upper band
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger = None):
        super().__init__(config, logger)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2.0)
        self.entry_threshold = config.get('entry_threshold', 0.02)  # 2% from band
        
    def get_required_data_period(self) -> int:
        return self.bb_period + 20
    
    def calculate_signals(self, data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict[str, Any]]:
        """Calculate mean reversion signals"""
        if not self.validate_data(data):
            return Signal.HOLD, {'error': 'Invalid data'}
        
        # Calculate Bollinger Bands
        data['BB_Middle'] = data['Close'].rolling(window=self.bb_period).mean()
        data['BB_Std'] = data['Close'].rolling(window=self.bb_period).std()
        data['BB_Upper'] = data['BB_Middle'] + (self.bb_std * data['BB_Std'])
        data['BB_Lower'] = data['BB_Middle'] - (self.bb_std * data['BB_Std'])
        data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']
        
        # Get latest values
        current_price = float(data['Close'].iloc[-1])
        bb_upper = float(data['BB_Upper'].iloc[-1])
        bb_lower = float(data['BB_Lower'].iloc[-1])
        bb_middle = float(data['BB_Middle'].iloc[-1])
        bb_width = float(data['BB_Width'].iloc[-1])
        
        # Calculate position within bands
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
        
        # Generate signals
        signal = Signal.HOLD
        reason = ""
        score = 0.0
        
        if bb_position <= self.entry_threshold:
            # Price near lower band - oversold
            signal = Signal.BUY
            reason = f"Oversold: Price ${current_price:.2f} near lower band ${bb_lower:.2f}"
            # Score: stronger buy as price gets closer to lower band (0 = strongest)
            score = (self.entry_threshold - bb_position) * 500  # Scale to 0-100
            score = min(100, score)
        elif bb_position >= (1 - self.entry_threshold):
            # Price near upper band - overbought
            signal = Signal.SELL
            reason = f"Overbought: Price ${current_price:.2f} near upper band ${bb_upper:.2f}"
            # Score: stronger sell as price gets closer to upper band (1 = strongest)
            score = (bb_position - (1 - self.entry_threshold)) * -500  # Scale to -100-0
            score = max(-100, score)
        elif abs(current_price - bb_middle) / bb_middle < 0.005:
            # Price near middle - potential entry
            signal = Signal.HOLD
            reason = f"Neutral: Price near middle band ${bb_middle:.2f}"
            # Score based on position relative to middle
            score = (bb_position - 0.5) * 20  # Small score near 0
        
        details = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': self.name,
            'signal': signal.value,
            'reason': reason,
            'score': score,
            'price': current_price,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'bb_middle': bb_middle,
            'bb_position': bb_position * 100,  # Percentage
            'bb_width': bb_width * 100,
        }
        
        return signal, details
