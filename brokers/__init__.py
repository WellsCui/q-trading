"""
Brokers Package

Contains broker integrations for live trading
"""

from .base_broker import BrokerInterface, MockBroker

try:
    from .ib_broker import create_ib_broker, IBBroker
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    create_ib_broker = None
    IBBroker = None

__all__ = [
    'BrokerInterface',
    'MockBroker',
    'create_ib_broker',
    'IBBroker',
    'IB_AVAILABLE',
]
