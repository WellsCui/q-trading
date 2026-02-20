"""
Trading Strategies Package

Contains various quantitative trading strategy implementations
"""

from .base import TradingStrategy, Signal
from .moving_average import MovingAverageCrossoverStrategy
from .momentum import MomentumStrategy
from .mean_reversion import MeanReversionStrategy
from .trend_following import TrendFollowingStrategy
from .vwap import VWAPStrategy
from .testing import generate_sample_data, test_strategy, test_all_strategies

__all__ = [
    'TradingStrategy',
    'Signal',
    'MovingAverageCrossoverStrategy',
    'MomentumStrategy',
    'MeanReversionStrategy',
    'TrendFollowingStrategy',
    'VWAPStrategy',
    'generate_sample_data',
    'test_strategy',
    'test_all_strategies',
]
