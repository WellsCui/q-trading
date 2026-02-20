"""
VWAP (Volume Weighted Average Price) Strategy
Based on "The Holy Grail for Day Trading Systems" by Zarattini & Aziz (2023)

This strategy identifies market imbalances by comparing price to VWAP:
- Long positions when price is above VWAP (buying pressure)
- Short positions when price is below VWAP (selling pressure)
"""

from datetime import datetime
from typing import Dict, Tuple, Any
import pandas as pd
import numpy as np

from .base import TradingStrategy, Signal


class VWAPStrategy(TradingStrategy):
    """
    VWAP Trend Trading Strategy
    
    The strategy positions the portfolio according to market imbalance
    as measured by the difference between current price and VWAP.
    
    Entry Conditions:
    - Long: When price crosses above VWAP
    - Short: When price crosses below VWAP
    
    Exit Conditions:
    - Close Long: When price crosses below VWAP
    - Close Short: When price crosses above VWAP
    
    Original paper tested on QQQ and TQQQ with 1-minute data,
    achieving 671% return vs 126% buy-and-hold over 2018-2023.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # VWAP calculation period (for daily data adaptation)
        self.vwap_period = config.get('vwap_period', 20)
        # Minimum distance from VWAP to generate signal (as percentage)
        self.min_distance_pct = config.get('min_distance_pct', 0.0)
        # Use intraday calculation if available
        self.intraday_mode = config.get('intraday_mode', False)
        
    def get_required_data_period(self) -> int:
        """Require enough data for VWAP calculation"""
        return self.vwap_period + 10
    
    def calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price
        
        Formula: VWAP = Σ(Typical Price × Volume) / ΣVolume
        where Typical Price = (High + Low + Close) / 3
        
        For intraday trading, this would reset daily at market open.
        For daily data, we use a rolling window.
        """
        # Calculate typical price (HLC/3)
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        
        if self.intraday_mode:
            # For intraday data, VWAP resets each day
            # This would require datetime index with intraday timestamps
            data['Date'] = pd.to_datetime(data.index).date
            cumulative_typical_volume = (typical_price * data['Volume']).groupby(data['Date']).cumsum()
            cumulative_volume = data['Volume'].groupby(data['Date']).cumsum()
            vwap = cumulative_typical_volume / cumulative_volume
        else:
            # For daily data, use rolling window
            rolling_typical_volume = (typical_price * data['Volume']).rolling(window=self.vwap_period).sum()
            rolling_volume = data['Volume'].rolling(window=self.vwap_period).sum()
            vwap = rolling_typical_volume / rolling_volume
        
        return vwap
    
    def calculate_signals(self, data: pd.DataFrame, symbol: str) -> Tuple[Signal, Dict[str, Any]]:
        """
        Calculate VWAP-based trading signals
        
        The strategy follows market imbalances:
        - Price above VWAP indicates buying pressure → Go Long
        - Price below VWAP indicates selling pressure → Go Short
        """
        if not self.validate_data(data):
            return Signal.HOLD, {'error': 'Invalid data'}
        
        # Make a copy to avoid SettingWithCopyWarning
        data = data.copy()
        
        # Calculate VWAP
        data['VWAP'] = self.calculate_vwap(data)
        
        # Get latest values
        current_price = float(data['Close'].iloc[-1])
        current_vwap = float(data['VWAP'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])
        prev_vwap = float(data['VWAP'].iloc[-2])
        
        # Check for NaN values
        if pd.isna(current_vwap) or pd.isna(prev_vwap):
            return Signal.HOLD, {'error': 'Insufficient data for VWAP calculation'}
        
        # Calculate distance from VWAP
        distance_pct = ((current_price - current_vwap) / current_vwap) * 100
        
        # Determine current position relative to VWAP
        price_above_vwap = current_price > current_vwap
        prev_price_above_vwap = prev_price > prev_vwap
        
        # Calculate signal strength based on distance from VWAP
        # Greater distance = stronger signal
        score = distance_pct * 10  # Scale distance to score
        score = max(-100, min(100, score))  # Clamp between -100 and 100
        
        # Detect crossovers
        bullish_cross = not prev_price_above_vwap and price_above_vwap
        bearish_cross = prev_price_above_vwap and not price_above_vwap
        
        # Generate signals
        signal = Signal.HOLD
        reason = ""
        
        if bullish_cross:
            # Price crossed above VWAP - bullish signal
            signal = Signal.BUY
            reason = f"Bullish cross: Price {current_price:.2f} crossed above VWAP {current_vwap:.2f} (+{distance_pct:.2f}%)"
        elif bearish_cross:
            # Price crossed below VWAP - bearish signal
            signal = Signal.SELL
            reason = f"Bearish cross: Price {current_price:.2f} crossed below VWAP {current_vwap:.2f} ({distance_pct:.2f}%)"
        elif price_above_vwap and abs(distance_pct) >= self.min_distance_pct:
            # Price above VWAP - continue long (buying pressure)
            signal = Signal.BUY
            reason = f"Above VWAP: Price {current_price:.2f} > VWAP {current_vwap:.2f} (+{distance_pct:.2f}%)"
        elif not price_above_vwap and abs(distance_pct) >= self.min_distance_pct:
            # Price below VWAP - continue short (selling pressure)
            signal = Signal.SELL
            reason = f"Below VWAP: Price {current_price:.2f} < VWAP {current_vwap:.2f} ({distance_pct:.2f}%)"
        else:
            # Too close to VWAP or no clear signal
            reason = f"Near VWAP: Price {current_price:.2f} ≈ VWAP {current_vwap:.2f} ({distance_pct:+.2f}%)"
        
        # Calculate additional metrics for context
        volume = float(data['Volume'].iloc[-1])
        avg_volume = float(data['Volume'].rolling(window=20).mean().iloc[-1])
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        
        details = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': self.name,
            'signal': signal.value,
            'reason': reason,
            'score': score,
            'price': current_price,
            'vwap': current_vwap,
            'distance_pct': distance_pct,
            'price_above_vwap': price_above_vwap,
            'bullish_cross': bullish_cross,
            'bearish_cross': bearish_cross,
            'volume': volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
        }
        
        return signal, details
    
    def get_stop_loss_price(self, entry_price: float, current_vwap: float, is_long: bool) -> float:
        """
        Calculate stop loss price based on VWAP
        
        For long positions: Stop at VWAP (or slightly below)
        For short positions: Stop at VWAP (or slightly above)
        """
        buffer = 0.001  # 0.1% buffer
        if is_long:
            return current_vwap * (1 - buffer)
        else:
            return current_vwap * (1 + buffer)
    
    def should_close_eod(self) -> bool:
        """
        Determine if positions should be closed at end of day
        
        According to the paper: "No positions are held overnight"
        """
        return True
