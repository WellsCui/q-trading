"""
Trading Strategies Package

Contains various quantitative trading strategy implementations
"""

from .base import TradingStrategy, Signal
from .moving_average import MovingAverageCrossoverStrategy
from .momentum import MomentumStrategy
from .mean_reversion import MeanReversionStrategy
from .trend_following import TrendFollowingStrategy

__all__ = [
    'TradingStrategy',
    'Signal',
    'MovingAverageCrossoverStrategy',
    'MomentumStrategy',
    'MeanReversionStrategy',
    'TrendFollowingStrategy',
]
