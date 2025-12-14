#!/usr/bin/env python3
"""
Interactive Brokers integration for QQQ Trading Bot

This module handles all interactions with the Interactive Brokers API including:
- Connection management
- Order execution
- Position tracking
- Account balance queries
"""

import logging
import time
import threading
from typing import Optional, Dict, List
from datetime import datetime
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

logger = logging.getLogger("QQQTradingBot.IB")


class IBClient(EWrapper, EClient):
    """Interactive Brokers API client combining wrapper and client functionality."""
    
    def __init__(self):
        EClient.__init__(self, self)
        
        # Connection state
        self.connected = False
        self.next_order_id = None
        
        # Data storage
        self.positions = {}
        self.account_info = {}
        self.orders = {}
        self.executions = {}
        
        # Threading
        self.lock = threading.Lock()
        
        # Error tracking
        self.errors = []
    
    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson=""):
        """Handle error messages from IB."""
        error_msg = f"Error {errorCode}: {errorString}"
        
        # Some codes are informational, not errors
        if errorCode in [2104, 2106, 2158]:  # Market data farm connection
            logger.info(error_msg)
        elif errorCode == 202:  # Order cancelled
            logger.info(error_msg)
        elif errorCode in [200, 201, 203]:  # Order-related errors
            logger.warning(error_msg)
            self.errors.append(error_msg)
        else:
            logger.error(error_msg)
            self.errors.append(error_msg)
    
    def nextValidId(self, orderId: int):
        """Receive next valid order ID."""
        super().nextValidId(orderId)
        self.next_order_id = orderId
        logger.info(f"Next valid order ID: {orderId}")
        self.connected = True
    
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        """Receive current positions."""
        symbol = contract.symbol
        with self.lock:
            self.positions[symbol] = {
                'position': position,
                'avg_cost': avgCost,
                'contract': contract,
                'account': account
            }
        logger.debug(f"Position update: {symbol} = {position} @ ${avgCost:.2f}")
    
    def positionEnd(self):
        """Called when all positions have been received."""
        logger.debug("Position updates complete")
    
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        """Receive account summary information."""
        with self.lock:
            if tag not in self.account_info:
                self.account_info[tag] = {}
            self.account_info[tag] = {'value': value, 'currency': currency}
        logger.debug(f"Account {account}: {tag} = {value} {currency}")
    
    def accountSummaryEnd(self, reqId: int):
        """Called when account summary is complete."""
        logger.debug("Account summary complete")
    
    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float,
                   avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float,
                   clientId: int, whyHeld: str, mktCapPrice: float):
        """Receive order status updates."""
        with self.lock:
            if orderId not in self.orders:
                self.orders[orderId] = {}
            self.orders[orderId].update({
                'status': status,
                'filled': filled,
                'remaining': remaining,
                'avg_fill_price': avgFillPrice,
                'last_fill_price': lastFillPrice
            })
        logger.info(f"Order {orderId} status: {status}, filled: {filled}, remaining: {remaining}")
    
    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState):
        """Receive open order information."""
        logger.debug(f"Open order {orderId}: {order.action} {order.totalQuantity} {contract.symbol}")
    
    def execDetails(self, reqId: int, contract: Contract, execution):
        """Receive execution details."""
        exec_id = execution.execId
        with self.lock:
            self.executions[exec_id] = {
                'symbol': contract.symbol,
                'shares': execution.shares,
                'price': execution.price,
                'time': execution.time,
                'side': execution.side
            }
        logger.info(f"Execution: {execution.side} {execution.shares} {contract.symbol} @ ${execution.price:.2f}")


class IBBroker:
    """High-level Interactive Brokers broker interface for the trading bot."""
    
    def __init__(self, config: Dict):
        """Initialize IB broker with configuration."""
        self.config = config
        self.client = IBClient()
        self.connected = False
        self.api_thread = None
        
        # Trading parameters
        self.host = config.get('ib_host', '127.0.0.1')
        self.port = config.get('ib_port', 7497)  # 7497 for paper trading, 7496 for live
        self.client_id = config.get('ib_client_id', 1)
        self.account = config.get('ib_account', '')
        
        # Position sizing
        self.total_capital = config.get('total_capital', 100000)
        self.position_size_pct = config.get('position_size_pct', 95)  # Use 95% of capital
        
        logger.info(f"IB Broker initialized: {self.host}:{self.port} (ClientID: {self.client_id})")
    
    def connect(self) -> bool:
        """Connect to Interactive Brokers TWS/Gateway."""
        try:
            logger.info(f"Connecting to IB at {self.host}:{self.port}...")
            self.client.connect(self.host, self.port, self.client_id)
            
            # Start the client thread
            self.api_thread = threading.Thread(target=self.client.run, daemon=True)
            self.api_thread.start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.client.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.client.connected:
                self.connected = True
                logger.info("Successfully connected to IB")
                
                # Request initial positions and account info
                self.update_positions()
                self.update_account_info()
                
                return True
            else:
                logger.error("Failed to connect to IB (timeout)")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to IB: {e}", exc_info=True)
            return False
    
    def disconnect(self):
        """Disconnect from Interactive Brokers."""
        if self.connected:
            logger.info("Disconnecting from IB...")
            self.client.disconnect()
            self.connected = False
    
    def update_positions(self):
        """Request current positions from IB."""
        if not self.connected:
            logger.error("Not connected to IB")
            return
        
        self.client.reqPositions()
        time.sleep(1)  # Wait for positions to be received
    
    def update_account_info(self):
        """Request account information from IB."""
        if not self.connected:
            logger.error("Not connected to IB")
            return
        
        tags = ["NetLiquidation", "TotalCashValue", "BuyingPower"]
        self.client.reqAccountSummary(9001, "All", ",".join(tags))
        time.sleep(1)  # Wait for account info
    
    def get_position(self, symbol: str) -> float:
        """Get current position quantity for a symbol."""
        with self.client.lock:
            if symbol in self.client.positions:
                return self.client.positions[symbol]['position']
        return 0.0
    
    def get_account_value(self) -> float:
        """Get total account value."""
        with self.client.lock:
            if 'NetLiquidation' in self.client.account_info:
                return float(self.client.account_info['NetLiquidation']['value'])
        return self.total_capital  # Fallback to configured value
    
    def create_stock_contract(self, symbol: str) -> Contract:
        """Create a stock contract for the given symbol."""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "NASDAQ"  # QQQ and TQQQ are on NASDAQ
        return contract
    
    def create_market_order(self, action: str, quantity: int) -> Order:
        """Create a market order."""
        order = Order()
        order.action = action  # "BUY" or "SELL"
        order.orderType = "MKT"
        order.totalQuantity = quantity
        order.tif = "DAY"  # Time in force: Day order
        return order
    
    def place_order(self, symbol: str, action: str, quantity: int) -> Optional[int]:
        """
        Place an order with Interactive Brokers.
        
        Args:
            symbol: Stock symbol (e.g., "QQQ", "TQQQ")
            action: "BUY" or "SELL"
            quantity: Number of shares
        
        Returns:
            Order ID if successful, None otherwise
        """
        if not self.connected:
            logger.error("Not connected to IB - cannot place order")
            return None
        
        if quantity <= 0:
            logger.warning(f"Invalid quantity {quantity} for {action} {symbol}")
            return None
        
        try:
            # Create contract and order
            contract = self.create_stock_contract(symbol)
            order = self.create_market_order(action, quantity)
            
            # Get next order ID
            order_id = self.client.next_order_id
            self.client.next_order_id += 1
            
            # Place the order
            logger.info(f"Placing order: {action} {quantity} {symbol} (Order ID: {order_id})")
            self.client.placeOrder(order_id, contract, order)
            
            # Wait a moment for order confirmation
            time.sleep(1)
            
            return order_id
            
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            return None
    
    def calculate_shares(self, symbol: str, current_price: float) -> int:
        """Calculate number of shares to trade based on position size."""
        account_value = self.get_account_value()
        position_value = account_value * (self.position_size_pct / 100.0)
        shares = int(position_value / current_price)
        return max(1, shares)  # At least 1 share
    
    def close_position(self, symbol: str) -> bool:
        """Close an existing position."""
        current_qty = self.get_position(symbol)
        
        if current_qty == 0:
            logger.info(f"No position to close for {symbol}")
            return True
        
        action = "SELL" if current_qty > 0 else "BUY"
        quantity = abs(int(current_qty))
        
        logger.info(f"Closing position: {action} {quantity} {symbol}")
        order_id = self.place_order(symbol, action, quantity)
        
        return order_id is not None
    
    def execute_position_change(self, old_position: Optional[str], new_position: str, 
                               prices: Dict[str, float]) -> bool:
        """
        Execute the position change from old to new.
        
        Args:
            old_position: Current position ('QQQ', 'TQQQ', 'Cash', or None)
            new_position: Target position ('QQQ', 'TQQQ', or 'Cash')
            prices: Dict with current prices {'qqq_price': float, 'tqqq_price': float}
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Close old position if exists
            if old_position and old_position != 'Cash':
                logger.info(f"Step 1: Closing {old_position} position")
                if not self.close_position(old_position):
                    logger.error(f"Failed to close {old_position} position")
                    return False
                time.sleep(2)  # Wait for order to fill
            
            # Step 2: Open new position if not Cash
            if new_position != 'Cash':
                symbol = new_position
                price = prices.get('tqqq_price' if symbol == 'TQQQ' else 'qqq_price', 0)
                
                if price <= 0:
                    logger.error(f"Invalid price for {symbol}: ${price}")
                    return False
                
                shares = self.calculate_shares(symbol, price)
                logger.info(f"Step 2: Opening {symbol} position ({shares} shares @ ${price:.2f})")
                
                order_id = self.place_order(symbol, "BUY", shares)
                if order_id is None:
                    logger.error(f"Failed to open {symbol} position")
                    return False
                
                time.sleep(2)  # Wait for order to fill
            else:
                logger.info("Step 2: Moving to Cash (no position to open)")
            
            # Update positions
            self.update_positions()
            
            logger.info("Position change executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error executing position change: {e}", exc_info=True)
            return False
    
    def get_current_holding(self) -> Optional[str]:
        """Determine current holding based on positions."""
        with self.client.lock:
            qqq_qty = self.get_position('QQQ')
            tqqq_qty = self.get_position('TQQQ')
            
            if tqqq_qty > 0:
                return 'TQQQ'
            elif qqq_qty > 0:
                return 'QQQ'
            else:
                return 'Cash'


def create_ib_broker(config: Dict) -> Optional[IBBroker]:
    """
    Factory function to create and connect an IB broker instance.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Connected IBBroker instance or None if connection failed
    """
    try:
        broker = IBBroker(config)
        if broker.connect():
            return broker
        else:
            logger.error("Failed to connect to Interactive Brokers")
            return None
    except Exception as e:
        logger.error(f"Error creating IB broker: {e}", exc_info=True)
        return None
