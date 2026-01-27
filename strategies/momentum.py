"""
Momentum Strategy based on RSI and Rate of Change
"""

from datetime import datetime
from typing import Dict, Tuple, Any
import pandas as pd

from .base import TradingStrategy, Signal


class MomentumStrategy(TradingStrategy):
    """
    Momentum Strategy based on RSI and Price Rate of Change
    
    Buys on oversold conditions, sells on overbought conditions
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.roc_period = config.get('roc_period', 20)
        
    def get_required_data_period(self) -> int:
        return max(self.rsi_period, self.roc_period) + 20
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_signals(self, data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict[str, Any]]:
        """Calculate momentum-based signals"""
        if not self.validate_data(data):
            return Signal.HOLD, {'error': 'Invalid data'}
        
        # Calculate indicators
        data['RSI'] = self.calculate_rsi(data)
        data['ROC'] = (data['Close'] / data['Close'].shift(self.roc_period) - 1) * 100
        
        # Get latest values
        current_price = float(data['Close'].iloc[-1])
        current_rsi = float(data['RSI'].iloc[-1])
        current_roc = float(data['ROC'].iloc[-1])
        
        # Generate signals
        signal = Signal.HOLD
        reason = ""
        
        if current_rsi < self.rsi_oversold and current_roc < 0:
            signal = Signal.BUY
            reason = f"Oversold: RSI={current_rsi:.1f} < {self.rsi_oversold}, ROC={current_roc:.2f}%"
        elif current_rsi > self.rsi_overbought and current_roc > 5:
            signal = Signal.SELL
            reason = f"Overbought: RSI={current_rsi:.1f} > {self.rsi_overbought}, ROC={current_roc:.2f}%"
        elif current_rsi > 50 and current_roc > 0:
            signal = Signal.BUY
            reason = f"Momentum: RSI={current_rsi:.1f}, positive ROC={current_roc:.2f}%"
        
        details = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': self.name,
            'signal': signal.value,
            'reason': reason,
            'price': current_price,
            'rsi': current_rsi,
            'roc': current_roc,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
        }
        
        return signal, details
