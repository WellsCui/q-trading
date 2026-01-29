"""
Trend Following Strategy using ADX and Volume
"""

from datetime import datetime
from typing import Dict, Tuple, Any
import pandas as pd
import numpy as np

from .base import TradingStrategy, Signal


class TrendFollowingStrategy(TradingStrategy):
    """
    Advanced Trend Following Strategy using multiple indicators:
    - ADX for trend strength
    - Moving Averages for trend direction
    - Volume for confirmation
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ma_period = config.get('ma_period', 50)
        self.adx_period = config.get('adx_period', 14)
        self.adx_threshold = config.get('adx_threshold', 25)
        self.volume_ma_period = config.get('volume_ma_period', 20)
        
    def get_required_data_period(self) -> int:
        return max(self.ma_period, self.adx_period, self.volume_ma_period) + 20
    
    def calculate_adx(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average Directional Index"""
        # Calculate True Range
        data['TR'] = np.maximum(
            data['High'] - data['Low'],
            np.maximum(
                abs(data['High'] - data['Close'].shift(1)),
                abs(data['Low'] - data['Close'].shift(1))
            )
        )
        
        # Calculate directional movements
        data['DMPlus'] = np.where(
            (data['High'] - data['High'].shift(1)) > (data['Low'].shift(1) - data['Low']),
            np.maximum(data['High'] - data['High'].shift(1), 0),
            0
        )
        data['DMMinus'] = np.where(
            (data['Low'].shift(1) - data['Low']) > (data['High'] - data['High'].shift(1)),
            np.maximum(data['Low'].shift(1) - data['Low'], 0),
            0
        )
        
        # Smooth the values
        atr = data['TR'].rolling(window=self.adx_period).mean()
        di_plus = 100 * (data['DMPlus'].rolling(window=self.adx_period).mean() / atr)
        di_minus = 100 * (data['DMMinus'].rolling(window=self.adx_period).mean() / atr)
        
        # Calculate ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=self.adx_period).mean()
        
        return adx
    
    def calculate_signals(self, data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict[str, Any]]:
        """Calculate trend following signals"""
        if not self.validate_data(data):
            return Signal.HOLD, {'error': 'Invalid data'}
        
        # Calculate indicators
        data['MA'] = data['Close'].rolling(window=self.ma_period).mean()
        data['ADX'] = self.calculate_adx(data)
        data['Volume_MA'] = data['Volume'].rolling(window=self.volume_ma_period).mean()
        
        # Get latest values
        current_price = float(data['Close'].iloc[-1])
        ma = float(data['MA'].iloc[-1])
        adx = float(data['ADX'].iloc[-1])
        current_volume = float(data['Volume'].iloc[-1])
        volume_ma = float(data['Volume_MA'].iloc[-1])
        
        # Trend determination
        is_uptrend = current_price > ma
        is_strong_trend = adx > self.adx_threshold
        volume_confirmed = current_volume > volume_ma * 0.8
        
        # Generate signals
        signal = Signal.HOLD
        reason = ""
        score = 0.0
        
        # Calculate components for score
        price_vs_ma = ((current_price - ma) / ma) * 100
        adx_strength = min(100, (adx / 50) * 100)  # Normalize ADX to 0-100
        volume_ratio = (current_volume / volume_ma) if volume_ma > 0 else 1
        
        if is_uptrend and is_strong_trend and volume_confirmed:
            signal = Signal.BUY
            reason = f"Strong uptrend: Price > MA, ADX={adx:.1f} > {self.adx_threshold}, volume confirmed"
            # Strong buy: combine trend strength, ADX, and volume
            base_score = 50
            adx_bonus = min(30, (adx - self.adx_threshold) * 1.5)
            price_bonus = min(20, price_vs_ma * 2)
            volume_bonus = min(20, (volume_ratio - 0.8) * 50)
            score = min(100, base_score + adx_bonus + price_bonus + volume_bonus)
        elif not is_uptrend and is_strong_trend and volume_confirmed:
            signal = Signal.SELL
            reason = f"Strong downtrend: Price < MA, ADX={adx:.1f} > {self.adx_threshold}, volume confirmed"
            # Strong sell: combine trend strength, ADX, and volume
            base_score = -50
            adx_penalty = -min(30, (adx - self.adx_threshold) * 1.5)
            price_penalty = -min(20, abs(price_vs_ma) * 2)
            volume_penalty = -min(20, (volume_ratio - 0.8) * 50)
            score = max(-100, base_score + adx_penalty + price_penalty + volume_penalty)
        elif is_uptrend and not is_strong_trend:
            signal = Signal.HOLD
            reason = f"Weak uptrend: ADX={adx:.1f} < {self.adx_threshold}"
            # Weak buy signal
            score = min(30, 10 + price_vs_ma + (adx / self.adx_threshold) * 10)
        else:
            signal = Signal.HOLD
            reason = f"No clear trend: ADX={adx:.1f}"
            # Very weak signal based on price position
            score = price_vs_ma * 0.5
            score = max(-20, min(20, score))
        
        details = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': self.name,
            'signal': signal.value,
            'reason': reason,
            'score': score,
            'price': current_price,
            'ma': ma,
            'adx': adx,
            'volume': current_volume,
            'volume_ma': volume_ma,
            'is_uptrend': is_uptrend,
            'is_strong_trend': is_strong_trend,
        }
        
        return signal, details
