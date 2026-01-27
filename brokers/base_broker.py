#!/usr/bin/env python3
"""
Base Broker Interface

This module defines the abstract interface that all broker implementations must follow.
It provides a standard API for trading operations, market data, and account management.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd


class BrokerInterface(ABC):
    """
    Abstract base class defining the broker interface.
    
    All broker implementations (Interactive Brokers, Alpaca, etc.) should inherit
    from this class and implement all abstract methods.
    """
    
    # ==================== Connection Management ====================
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the broker.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the broker."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connected to the broker.
        
        Returns:
            bool: True if connected, False otherwise
        """
        pass
    
    # ==================== Market Data ====================
    
    @abstractmethod
    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current market data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary containing market data (price, volume, etc.) or None
        """
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, duration: str = "1 D", 
                          bar_size: str = "1 min") -> Optional[pd.DataFrame]:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Stock symbol
            duration: Duration string (e.g., "1 D", "5 D", "1 M")
            bar_size: Bar size string (e.g., "1 min", "5 mins", "1 hour")
            
        Returns:
            DataFrame with historical OHLCV data or None
        """
        pass
    
    @abstractmethod
    def get_tick_data(self, symbol: str, as_dataframe: bool = True) -> Optional[Any]:
        """
        Get real-time tick data for a symbol.
        
        Args:
            symbol: Stock symbol
            as_dataframe: Return as DataFrame if True, dict if False
            
        Returns:
            Tick data (DataFrame or dict) or None
        """
        pass
    
    @abstractmethod
    def get_order_book(self, symbol: str) -> Dict[str, List[Tuple[float, int]]]:
        """
        Get order book (Level 2 data) for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with 'bids' and 'asks' lists of (price, size) tuples
        """
        pass
    
    # ==================== Account Information ====================
    
    @abstractmethod
    def get_account_balance(self) -> float:
        """
        Get account cash balance.
        
        Returns:
            Account balance
        """
        pass
    
    @abstractmethod
    def get_buying_power(self) -> float:
        """
        Get available buying power.
        
        Returns:
            Buying power
        """
        pass
    
    @abstractmethod
    def get_portfolio_value(self) -> float:
        """
        Get total portfolio value.
        
        Returns:
            Portfolio value
        """
        pass
    
    @abstractmethod
    def get_account_value(self) -> float:
        """
        Get total account value (alias for get_portfolio_value).
        
        Returns:
            Account value
        """
        pass
    
    # ==================== Position Management ====================
    
    @abstractmethod
    def get_position(self, symbol: str) -> float:
        """
        Get current position quantity for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Position quantity (positive for long, negative for short, 0 for no position)
        """
        pass
    
    @abstractmethod
    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all current positions.
        
        Returns:
            Dictionary mapping symbols to position details
        """
        pass
    
    @abstractmethod
    def get_position_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Position details dictionary or None
        """
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> bool:
        """
        Close an existing position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if order placed successfully, False otherwise
        """
        pass
    
    # ==================== Order Management ====================
    
    @abstractmethod
    def place_order(self, symbol: str, action: str, quantity: int, 
                   order_type: str = "MKT", limit_price: float = None,
                   stop_price: float = None, **kwargs) -> Optional[int]:
        """
        Place a trading order.
        
        Args:
            symbol: Stock symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            order_type: Order type ("MKT", "LMT", "STP", "STP LMT")
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            **kwargs: Additional order parameters
            
        Returns:
            Order ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def place_bracket_order(self, symbol: str, action: str, quantity: int,
                          entry_price: float, take_profit_price: float,
                          stop_loss_price: float) -> Optional[List[int]]:
        """
        Place a bracket order (entry + take profit + stop loss).
        
        Args:
            symbol: Stock symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            entry_price: Entry limit price
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss price
            
        Returns:
            List of order IDs [parent, take_profit, stop_loss] or None
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancel request sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def modify_order(self, order_id: int, symbol: str, action: str, 
                    quantity: int, order_type: str = "MKT",
                    limit_price: float = None, stop_price: float = None) -> bool:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            symbol: Stock symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            order_type: Order type
            limit_price: Limit price
            stop_price: Stop price
            
        Returns:
            True if modification successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: int) -> Optional[str]:
        """
        Get the status of an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order status string or None
        """
        pass
    
    @abstractmethod
    def get_all_orders(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all orders.
        
        Returns:
            Dictionary mapping order IDs to order details
        """
        pass
    
    @abstractmethod
    def get_open_orders(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all open (not filled/cancelled) orders.
        
        Returns:
            Dictionary mapping order IDs to order details
        """
        pass
    
    @abstractmethod
    def get_executions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Args:
            symbol: Filter by symbol (None = all symbols)
            
        Returns:
            List of execution dictionaries
        """
        pass
    
    # ==================== Risk Management & Validation ====================
    
    @abstractmethod
    def validate_order(self, symbol: str, action: str, quantity: int,
                      order_type: str = "MKT", limit_price: float = None,
                      stop_price: float = None) -> Tuple[bool, str]:
        """
        Validate an order before placement.
        
        Args:
            symbol: Stock symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            order_type: Order type
            limit_price: Limit price
            stop_price: Stop price
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def calculate_shares(self, symbol: str, current_price: float) -> int:
        """
        Calculate number of shares based on position sizing rules.
        
        Args:
            symbol: Stock symbol
            current_price: Current price per share
            
        Returns:
            Number of shares to trade
        """
        pass
    
    # ==================== Performance Tracking ====================
    
    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics (returns, Sharpe ratio, max drawdown, etc.).
        
        Returns:
            Dictionary of performance metrics
        """
        pass
    
    @abstractmethod
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get risk metrics (volatility, VaR, etc.).
        
        Returns:
            Dictionary of risk metrics
        """
        pass
    
    @abstractmethod
    def export_trade_history(self, filepath: str = 'trade_history.csv'):
        """
        Export trade history to CSV file.
        
        Args:
            filepath: Output file path
        """
        pass
    
    @abstractmethod
    def export_equity_curve(self, filepath: str = 'equity_curve.csv'):
        """
        Export equity curve to CSV file.
        
        Args:
            filepath: Output file path
        """
        pass


class MockBroker(BrokerInterface):
    """
    Mock broker implementation for testing and dry-run mode.
    
    Simulates broker operations without making real trades.
    """
    
    def __init__(self, config: Dict):
        """Initialize mock broker."""
        self.config = config
        self.connected = False
        self.cash = config.get('total_capital', 100000)
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[int, Dict[str, Any]] = {}
        self.next_order_id = 1
        self.executions: List[Dict[str, Any]] = []
        self.trade_history: List[Dict[str, Any]] = []
    
    def connect(self) -> bool:
        """Simulate connection."""
        self.connected = True
        return True
    
    def disconnect(self):
        """Simulate disconnection."""
        self.connected = False
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self.connected
    
    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return mock market data."""
        # In a real implementation, would fetch from data source
        return {
            'symbol': symbol,
            'timestamp': [datetime.now()],
            'close': [100.0],
            'high': [101.0],
            'low': [99.0],
            'volume': [1000000]
        }
    
    def get_historical_data(self, symbol: str, duration: str = "1 D",
                          bar_size: str = "1 min") -> Optional[pd.DataFrame]:
        """Return mock historical data."""
        # Would fetch from data source in real implementation
        return None
    
    def get_tick_data(self, symbol: str, as_dataframe: bool = True) -> Optional[Any]:
        """Return mock tick data."""
        return None
    
    def get_order_book(self, symbol: str) -> Dict[str, List[Tuple[float, int]]]:
        """Return mock order book."""
        return {'bids': [(99.5, 100)], 'asks': [(100.5, 100)]}
    
    def get_account_balance(self) -> float:
        """Return cash balance."""
        return self.cash
    
    def get_buying_power(self) -> float:
        """Return buying power."""
        return self.cash * 4  # Assume 4x margin
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value."""
        return self.cash + sum(p['market_value'] for p in self.positions.values())
    
    def get_account_value(self) -> float:
        """Get account value."""
        return self.get_portfolio_value()
    
    def get_position(self, symbol: str) -> float:
        """Get position quantity."""
        return self.positions.get(symbol, {}).get('quantity', 0)
    
    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_position_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position details."""
        return self.positions.get(symbol)
    
    def close_position(self, symbol: str) -> bool:
        """Close position."""
        if symbol in self.positions:
            quantity = abs(self.positions[symbol]['quantity'])
            action = 'SELL' if self.positions[symbol]['quantity'] > 0 else 'BUY'
            return self.place_order(symbol, action, int(quantity)) is not None
        return False
    
    def place_order(self, symbol: str, action: str, quantity: int,
                   order_type: str = "MKT", limit_price: float = None,
                   stop_price: float = None, **kwargs) -> Optional[int]:
        """Place mock order."""
        order_id = self.next_order_id
        self.next_order_id += 1
        
        self.orders[order_id] = {
            'order_id': order_id,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'order_type': order_type,
            'limit_price': limit_price,
            'stop_price': stop_price,
            'status': 'Filled',  # Mock immediate fill
            'timestamp': datetime.now()
        }
        
        # Update positions
        sign = 1 if action == 'BUY' else -1
        current_qty = self.get_position(symbol)
        new_qty = current_qty + (sign * quantity)
        
        if new_qty == 0:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = {
                'quantity': new_qty,
                'avg_cost': limit_price or 100.0,  # Mock price
                'market_value': new_qty * (limit_price or 100.0)
            }
        
        return order_id
    
    def place_bracket_order(self, symbol: str, action: str, quantity: int,
                          entry_price: float, take_profit_price: float,
                          stop_loss_price: float) -> Optional[List[int]]:
        """Place mock bracket order."""
        parent_id = self.place_order(symbol, action, quantity, 'LMT', entry_price)
        tp_id = self.place_order(symbol, 'SELL' if action == 'BUY' else 'BUY',
                                quantity, 'LMT', take_profit_price)
        sl_id = self.place_order(symbol, 'SELL' if action == 'BUY' else 'BUY',
                                quantity, 'STP', None, stop_loss_price)
        return [parent_id, tp_id, sl_id]
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel order."""
        if order_id in self.orders:
            self.orders[order_id]['status'] = 'Cancelled'
            return True
        return False
    
    def modify_order(self, order_id: int, symbol: str, action: str,
                    quantity: int, order_type: str = "MKT",
                    limit_price: float = None, stop_price: float = None) -> bool:
        """Modify order."""
        if order_id in self.orders:
            self.orders[order_id].update({
                'quantity': quantity,
                'order_type': order_type,
                'limit_price': limit_price,
                'stop_price': stop_price
            })
            return True
        return False
    
    def get_order_status(self, order_id: int) -> Optional[str]:
        """Get order status."""
        return self.orders.get(order_id, {}).get('status')
    
    def get_all_orders(self) -> Dict[int, Dict[str, Any]]:
        """Get all orders."""
        return self.orders.copy()
    
    def get_open_orders(self) -> Dict[int, Dict[str, Any]]:
        """Get open orders."""
        return {oid: o for oid, o in self.orders.items()
                if o['status'] not in ['Filled', 'Cancelled']}
    
    def get_executions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get executions."""
        if symbol:
            return [e for e in self.executions if e['symbol'] == symbol]
        return self.executions.copy()
    
    def validate_order(self, symbol: str, action: str, quantity: int,
                      order_type: str = "MKT", limit_price: float = None,
                      stop_price: float = None) -> Tuple[bool, str]:
        """Validate order."""
        if quantity <= 0:
            return False, "Quantity must be positive"
        if action not in ['BUY', 'SELL']:
            return False, "Action must be BUY or SELL"
        return True, ""
    
    def calculate_shares(self, symbol: str, current_price: float) -> int:
        """Calculate shares based on position sizing."""
        position_value = self.cash * self.config.get('position_size_pct', 0.2)
        return int(position_value / current_price)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            'total_trades': len(self.trade_history),
            'portfolio_value': self.get_portfolio_value(),
            'cash': self.cash
        }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk metrics."""
        return {'max_drawdown': 0.0}
    
    def export_trade_history(self, filepath: str = 'trade_history.csv'):
        """Export trade history."""
        pass
    
    def export_equity_curve(self, filepath: str = 'equity_curve.csv'):
        """Export equity curve."""
        pass
