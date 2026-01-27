#!/usr/bin/env python3
"""
Comprehensive tests for IBBroker and IBClient quantitative trading API

Tests cover:
- Connection management
- Market data retrieval (real-time ticks, order book)
- Order placement (market, limit, stop, bracket, batch)
- Position tracking
- Account information
- Order management (cancel, modify)
- Risk validation
- Performance metrics (Sharpe ratio, drawdown, win rate)
- Trade execution tracking
- Data export for analysis
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import BarData

from brokers.ib_broker import IBClient, IBBroker, create_ib_broker


class TestIBClient(unittest.TestCase):
    """Test IBClient class functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'api': {
                'tws_endpoint': '127.0.0.1',
                'port': 7497
            }
        }
        self.client = IBClient(self.config)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.client.isConnected():
            self.client.disconnect()
    
    def test_initialization(self):
        """Test IBClient initialization"""
        self.assertEqual(self.client.host, '127.0.0.1')
        self.assertEqual(self.client.port, 7497)
        self.assertEqual(self.client.client_id, 1)
        self.assertIsInstance(self.client.market_data, defaultdict)
        self.assertEqual(self.client.next_req_id, 0)
        self.assertFalse(self.client.connected)
        self.assertEqual(len(self.client.positions), 0)
        self.assertEqual(len(self.client.orders), 0)
    
    def test_create_stock_contract(self):
        """Test stock contract creation"""
        contract = self.client.create_stock_contract('AAPL')
        
        self.assertIsInstance(contract, Contract)
        self.assertEqual(contract.symbol, 'AAPL')
        self.assertEqual(contract.secType, 'STK')
        self.assertEqual(contract.exchange, 'SMART')
        self.assertEqual(contract.currency, 'USD')
        self.assertEqual(contract.primaryExchange, 'NASDAQ')
    
    def test_create_stock_contract_unknown_symbol(self):
        """Test contract creation for symbol without primary exchange"""
        contract = self.client.create_stock_contract('XYZ')
        
        self.assertEqual(contract.symbol, 'XYZ')
        self.assertEqual(contract.secType, 'STK')
        self.assertFalse(hasattr(contract, 'primaryExchange') and contract.primaryExchange)
    
    def test_next_req_id_increment(self):
        """Test request ID increments correctly"""
        first_id = self.client._get_next_req_id()
        second_id = self.client._get_next_req_id()
        third_id = self.client._get_next_req_id()
        
        self.assertEqual(first_id, 1)
        self.assertEqual(second_id, 2)
        self.assertEqual(third_id, 3)
    
    def test_next_valid_id_callback(self):
        """Test nextValidId callback updates order ID and connection status"""
        self.assertFalse(self.client.connected)
        
        self.client.nextValidId(100)
        
        self.assertTrue(self.client.connected)
        self.assertEqual(self.client.next_order_id, 100)
    
    def test_position_callback(self):
        """Test position callback updates positions"""
        contract = Contract()
        contract.symbol = 'QQQ'
        
        self.client.position('DU1234567', contract, 100.0, 350.50)
        
        positions = self.client.get_positions()
        self.assertIn('QQQ', positions)
        self.assertEqual(positions['QQQ']['position'], 100.0)
        self.assertEqual(positions['QQQ']['avgCost'], 350.50)
        self.assertEqual(positions['QQQ']['account'], 'DU1234567')
    
    def test_account_summary_callback(self):
        """Test account summary callback"""
        self.client.accountSummary(9001, 'DU1234567', 'NetLiquidation', '100000.00', 'USD')
        self.client.accountSummary(9001, 'DU1234567', 'BuyingPower', '50000.00', 'USD')
        
        account_info = self.client.get_account_summary()
        
        self.assertIn('NetLiquidation', account_info)
        self.assertEqual(account_info['NetLiquidation']['value'], '100000.00')
        self.assertIn('BuyingPower', account_info)
        self.assertEqual(account_info['BuyingPower']['value'], '50000.00')
    
    def test_order_status_callback(self):
        """Test order status callback"""
        self.client.orders[1] = {
            'orderId': 1,
            'symbol': 'QQQ',
            'action': 'BUY',
            'totalQuantity': 10
        }
        
        self.client.orderStatus(1, 'Filled', 10.0, 0.0, 350.50, 0, 0, 350.50, 1, '', 0.0)
        
        status = self.client.get_order_status(1)
        self.assertEqual(status, 'Filled')
        
        orders = self.client.get_orders()
        self.assertEqual(orders[1]['status'], 'Filled')
        self.assertEqual(orders[1]['filled'], 10.0)
        self.assertEqual(orders[1]['avgFillPrice'], 350.50)
    
    def test_open_order_callback(self):
        """Test open order callback"""
        contract = Contract()
        contract.symbol = 'TQQQ'
        
        order = Order()
        order.action = 'BUY'
        order.orderType = 'MKT'
        order.totalQuantity = 20
        
        order_state = Mock()
        order_state.status = 'Submitted'
        
        self.client.openOrder(1, contract, order, order_state)
        
        orders = self.client.get_orders()
        self.assertIn(1, orders)
        self.assertEqual(orders[1]['symbol'], 'TQQQ')
        self.assertEqual(orders[1]['action'], 'BUY')
        self.assertEqual(orders[1]['totalQuantity'], 20)
        self.assertEqual(orders[1]['status'], 'Submitted')
    
    def test_update_market_data(self):
        """Test market data update"""
        symbol = 'AAPL'
        price = 150.50
        size = 100
        
        self.client._update_market_data(symbol, price, size)
        
        self.assertIn(symbol, self.client.market_data)
        self.assertEqual(len(self.client.market_data[symbol]['close']), 1)
        self.assertEqual(self.client.market_data[symbol]['close'][0], price)
        self.assertEqual(self.client.market_data[symbol]['volume'][0], size)
        self.assertEqual(self.client.market_data[symbol]['current_high'], price)
        self.assertEqual(self.client.market_data[symbol]['current_low'], price)
        self.assertTrue(self.client.data_received[symbol])
    
    def test_update_market_data_high_low_tracking(self):
        """Test high/low price tracking in market data"""
        symbol = 'AAPL'
        
        # First update
        self.client._update_market_data(symbol, 150.00, 100)
        self.assertEqual(self.client.market_data[symbol]['current_high'], 150.00)
        self.assertEqual(self.client.market_data[symbol]['current_low'], 150.00)
        
        # Higher price
        self.client._update_market_data(symbol, 152.00, 100)
        self.assertEqual(self.client.market_data[symbol]['current_high'], 152.00)
        self.assertEqual(self.client.market_data[symbol]['current_low'], 150.00)
        
        # Lower price
        self.client._update_market_data(symbol, 148.00, 100)
        self.assertEqual(self.client.market_data[symbol]['current_high'], 152.00)
        self.assertEqual(self.client.market_data[symbol]['current_low'], 148.00)
    
    def test_tick_price_callback(self):
        """Test tick price callback for last price"""
        symbol = 'AAPL'
        req_id = 1
        self.client.active_requests[req_id] = symbol
        
        # Simulate last price tick (type 4)
        self.client.tickPrice(req_id, 4, 150.50, None)
        
        self.assertTrue(self.client.data_received[symbol])
        self.assertEqual(len(self.client.market_data[symbol]['close']), 1)
        self.assertEqual(self.client.market_data[symbol]['close'][0], 150.50)
    
    def test_portfolio_update(self):
        """Test portfolio update"""
        self.client.updatePortfolio(100000.0, -500.0)
        
        portfolio = self.client.getPortfolio()
        self.assertEqual(portfolio['total_value'], 100000.0)
        self.assertEqual(portfolio['daily_loss'], -500.0)
    
    def test_get_positions_thread_safe(self):
        """Test that get_positions is thread-safe"""
        # Add some positions
        contract = Contract()
        contract.symbol = 'QQQ'
        self.client.position('DU1234567', contract, 100.0, 350.50)
        
        # Access from multiple threads
        results = []
        def access_positions():
            positions = self.client.get_positions()
            results.append(len(positions))
        
        threads = [threading.Thread(target=access_positions) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should see the same position count
        self.assertTrue(all(r == 1 for r in results))
    
    def test_tick_data_streaming(self):
        """Test real-time tick data streaming"""
        symbol = 'AAPL'
        req_id = 1
        self.client.active_requests[req_id] = symbol
        
        # Simulate tick data
        self.client.tickPrice(req_id, 1, 150.00, None)  # BID
        self.client.tickPrice(req_id, 2, 150.10, None)  # ASK
        self.client.tickPrice(req_id, 4, 150.05, None)  # LAST
        self.client.tickSize(req_id, 0, 100)  # BID_SIZE
        self.client.tickSize(req_id, 3, 200)  # ASK_SIZE
        
        # Verify tick data was captured
        tick_data = self.client.get_tick_data(symbol, as_dataframe=False)
        self.assertIsNotNone(tick_data)
        self.assertTrue(len(tick_data['bid']) > 0)
        self.assertTrue(len(tick_data['ask']) > 0)
        self.assertTrue(len(tick_data['last_price']) > 0)
    
    def test_tick_data_as_dataframe(self):
        """Test tick data export as pandas DataFrame"""
        symbol = 'AAPL'
        req_id = 1
        self.client.active_requests[req_id] = symbol
        
        # Add some tick data
        self.client.tickPrice(req_id, 1, 150.00, None)  # BID
        self.client.tickPrice(req_id, 2, 150.10, None)  # ASK
        
        # Get as DataFrame
        df = self.client.get_tick_data(symbol, as_dataframe=True)
        
        if df is not None and not df.empty:
            self.assertIsInstance(df, pd.DataFrame)
            self.assertIn('bid', df.columns)
            self.assertIn('ask', df.columns)
            self.assertIn('spread', df.columns)
            self.assertIn('mid_price', df.columns)
    
    def test_order_book_updates(self):
        """Test order book data capture"""
        symbol = 'AAPL'
        req_id = 1
        self.client.active_requests[req_id] = symbol
        
        # Simulate order book updates
        self.client.tickPrice(req_id, 1, 150.00, None)  # BID
        self.client.tickSize(req_id, 0, 100)  # BID_SIZE
        self.client.tickPrice(req_id, 2, 150.10, None)  # ASK
        self.client.tickSize(req_id, 3, 200)  # ASK_SIZE
        
        order_book = self.client.get_order_book(symbol)
        
        self.assertIn('bids', order_book)
        self.assertIn('asks', order_book)
        if order_book['bids']:
            self.assertEqual(order_book['bids'][0], (150.00, 100))
        if order_book['asks']:
            self.assertEqual(order_book['asks'][0], (150.10, 200))
    
    def test_execution_tracking(self):
        """Test execution detail tracking"""
        contract = Contract()
        contract.symbol = 'QQQ'
        
        execution = Mock()
        execution.orderId = 1
        execution.side = 'BOT'
        execution.shares = 10
        execution.price = 350.50
        execution.execId = 'exec1'
        execution.cumQty = 10
        execution.avgPrice = 350.50
        
        self.client.execDetails(1, contract, execution)
        
        executions = self.client.get_executions()
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]['symbol'], 'QQQ')
        self.assertEqual(executions[0]['shares'], 10)
        self.assertEqual(executions[0]['price'], 350.50)
    
    def test_commission_tracking(self):
        """Test commission and PnL tracking"""
        # Add an execution first
        contract = Contract()
        contract.symbol = 'QQQ'
        execution = Mock()
        execution.orderId = 1
        execution.side = 'BOT'
        execution.shares = 10
        execution.price = 350.50
        execution.execId = 'exec1'
        execution.cumQty = 10
        execution.avgPrice = 350.50
        
        self.client.execDetails(1, contract, execution)
        
        # Now add commission
        commission_report = Mock()
        commission_report.execId = 'exec1'
        commission_report.commission = 1.50
        commission_report.realizedPNL = 25.00
        
        self.client.commissionReport(commission_report)
        
        # Verify commission was linked to execution
        executions = self.client.get_executions()
        self.assertEqual(executions[0]['commission'], 1.50)
        self.assertEqual(executions[0]['realizedPnL'], 25.00)
        self.assertEqual(self.client.get_realized_pnl(), 25.00)
    
    def test_realized_pnl_accumulation(self):
        """Test that realized PnL accumulates correctly"""
        self.assertEqual(self.client.get_realized_pnl(), 0.0)
        
        # Simulate multiple profitable trades
        for i in range(3):
            contract = Contract()
            contract.symbol = 'QQQ'
            execution = Mock()
            execution.orderId = i + 1
            execution.side = 'SLD'
            execution.shares = 10
            execution.price = 350.00 + i
            execution.execId = f'exec{i}'
            execution.cumQty = 10
            execution.avgPrice = 350.00 + i
            
            self.client.execDetails(i + 1, contract, execution)
            
            commission_report = Mock()
            commission_report.execId = f'exec{i}'
            commission_report.commission = 1.00
            commission_report.realizedPNL = 10.00 + i
            
            self.client.commissionReport(commission_report)
        
        # Should have cumulative PnL
        total_pnl = self.client.get_realized_pnl()
        self.assertEqual(total_pnl, 33.00)  # 10 + 11 + 12


class TestIBBroker(unittest.TestCase):
    """Test IBBroker class functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'api': {
                'tws_endpoint': '127.0.0.1',
                'port': 7497
            },
            'ib_host': '127.0.0.1',
            'ib_port': 7497,
            'ib_client_id': 1,
            'ib_account': 'DU1234567',
            'total_capital': 100000,
            'position_size_pct': 95
        }
        self.broker = IBBroker(self.config)
        
        # Mock the client to avoid actual connections
        self.broker.client = Mock(spec=IBClient)
        self.broker.client.lock = threading.Lock()
        self.broker.client.next_order_id = 1
        self.broker.client.positions = {}
        self.broker.client.account_info = {}
        self.broker.client.orders = {}
    
    def test_initialization(self):
        """Test IBBroker initialization"""
        self.assertEqual(self.broker.host, '127.0.0.1')
        self.assertEqual(self.broker.port, 7497)
        self.assertEqual(self.broker.client_id, 1)
        self.assertEqual(self.broker.account, 'DU1234567')
        self.assertEqual(self.broker.total_capital, 100000)
        self.assertEqual(self.broker.position_size_pct, 95)
    
    def test_create_market_order(self):
        """Test market order creation"""
        order = self.broker.create_market_order('BUY', 10)
        
        self.assertIsInstance(order, Order)
        self.assertEqual(order.action, 'BUY')
        self.assertEqual(order.orderType, 'MKT')
        self.assertEqual(order.totalQuantity, 10)
        self.assertEqual(order.tif, 'DAY')
    
    def test_create_limit_order(self):
        """Test limit order creation"""
        order = self.broker.create_limit_order('SELL', 10, 355.50)
        
        self.assertEqual(order.action, 'SELL')
        self.assertEqual(order.orderType, 'LMT')
        self.assertEqual(order.totalQuantity, 10)
        self.assertEqual(order.lmtPrice, 355.50)
        self.assertEqual(order.tif, 'DAY')
    
    def test_create_stop_order(self):
        """Test stop order creation"""
        order = self.broker.create_stop_order('SELL', 10, 345.00)
        
        self.assertEqual(order.action, 'SELL')
        self.assertEqual(order.orderType, 'STP')
        self.assertEqual(order.totalQuantity, 10)
        self.assertEqual(order.auxPrice, 345.00)
    
    def test_create_stop_limit_order(self):
        """Test stop-limit order creation"""
        order = self.broker.create_stop_limit_order('BUY', 10, 345.00, 350.00)
        
        self.assertEqual(order.orderType, 'STP LMT')
        self.assertEqual(order.auxPrice, 345.00)
        self.assertEqual(order.lmtPrice, 350.00)
    
    def test_create_bracket_order(self):
        """Test bracket order creation"""
        orders = self.broker.create_bracket_order('BUY', 10, 350.00, 360.00, 340.00)
        
        self.assertEqual(len(orders), 3)
        
        # Parent order
        self.assertEqual(orders[0].action, 'BUY')
        self.assertEqual(orders[0].orderType, 'LMT')
        self.assertEqual(orders[0].lmtPrice, 350.00)
        self.assertFalse(orders[0].transmit)
        
        # Take profit
        self.assertEqual(orders[1].action, 'SELL')
        self.assertEqual(orders[1].orderType, 'LMT')
        self.assertEqual(orders[1].lmtPrice, 360.00)
        self.assertEqual(orders[1].parentId, orders[0].orderId)
        
        # Stop loss
        self.assertEqual(orders[2].action, 'SELL')
        self.assertEqual(orders[2].orderType, 'STP')
        self.assertEqual(orders[2].auxPrice, 340.00)
        self.assertEqual(orders[2].parentId, orders[0].orderId)
        self.assertTrue(orders[2].transmit)
    
    def test_calculate_shares(self):
        """Test share calculation based on position size"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'}
        }
        
        shares = self.broker.calculate_shares('QQQ', 350.00)
        
        # 95% of 100000 = 95000, divided by 350 = 271.42, rounded to 271
        expected_shares = int(100000 * 0.95 / 350.00)
        self.assertEqual(shares, expected_shares)
    
    def test_calculate_shares_minimum(self):
        """Test that calculate_shares returns at least 1"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100.00'}
        }
        
        shares = self.broker.calculate_shares('QQQ', 350.00)
        self.assertEqual(shares, 1)
    
    def test_get_position(self):
        """Test getting position for a symbol"""
        self.broker.client.positions = {
            'QQQ': {'position': 100.0, 'avgCost': 350.50}
        }
        
        position = self.broker.get_position('QQQ')
        self.assertEqual(position, 100.0)
        
        position = self.broker.get_position('TQQQ')
        self.assertEqual(position, 0.0)
    
    def test_get_account_value(self):
        """Test getting account value"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '125000.50'}
        }
        
        value = self.broker.get_account_value()
        self.assertEqual(value, 125000.50)
    
    def test_get_account_value_fallback(self):
        """Test account value fallback to configured capital"""
        self.broker.client.account_info = {}
        
        value = self.broker.get_account_value()
        self.assertEqual(value, self.broker.total_capital)
    
    def test_get_current_holding_tqqq(self):
        """Test getting current holding when holding TQQQ"""
        self.broker.client.positions = {
            'TQQQ': {'position': 100.0}
        }
        
        holding = self.broker.get_current_holding()
        self.assertEqual(holding, 'TQQQ')
    
    def test_get_current_holding_qqq(self):
        """Test getting current holding when holding QQQ"""
        self.broker.client.positions = {
            'QQQ': {'position': 50.0}
        }
        
        holding = self.broker.get_current_holding()
        self.assertEqual(holding, 'QQQ')
    
    def test_get_current_holding_cash(self):
        """Test getting current holding when in cash"""
        self.broker.client.positions = {}
        
        holding = self.broker.get_current_holding()
        self.assertEqual(holding, 'Cash')
    
    def test_get_all_positions(self):
        """Test getting all positions"""
        self.broker.client.get_positions = Mock(return_value={
            'QQQ': {'position': 100.0},
            'TQQQ': {'position': 50.0}
        })
        
        positions = self.broker.get_all_positions()
        
        self.assertEqual(len(positions), 2)
        self.assertIn('QQQ', positions)
        self.assertIn('TQQQ', positions)
    
    def test_get_buying_power(self):
        """Test getting buying power"""
        self.broker.client.account_info = {
            'BuyingPower': {'value': '200000.00'}
        }
        
        buying_power = self.broker.get_buying_power()
        self.assertEqual(buying_power, 200000.00)
    
    def test_get_portfolio_value(self):
        """Test getting portfolio value"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '150000.00'}
        }
        
        value = self.broker.get_portfolio_value()
        self.assertEqual(value, 150000.00)
    
    def test_validate_order_success(self):
        """Test order validation with valid order"""
        self.broker.connected = True
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'},
            'BuyingPower': {'value': '50000.00'}
        }
        self.broker.client.positions = {}
        
        validation = self.broker.validate_order('QQQ', 'BUY', 100, 350.00)
        
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)
    
    def test_validate_order_not_connected(self):
        """Test order validation when not connected"""
        self.broker.connected = False
        
        validation = self.broker.validate_order('QQQ', 'BUY', 100, 350.00)
        
        self.assertFalse(validation['valid'])
        self.assertIn('Not connected to IB', validation['errors'])
    
    def test_validate_order_invalid_quantity(self):
        """Test order validation with invalid quantity"""
        self.broker.connected = True
        
        validation = self.broker.validate_order('QQQ', 'BUY', 0, 350.00)
        
        self.assertFalse(validation['valid'])
        self.assertIn('Invalid quantity', validation['errors'][0])
    
    def test_validate_order_insufficient_buying_power(self):
        """Test order validation with insufficient buying power"""
        self.broker.connected = True
        self.broker.client.account_info = {
            'BuyingPower': {'value': '10000.00'}
        }
        
        validation = self.broker.validate_order('QQQ', 'BUY', 100, 350.00)
        
        self.assertFalse(validation['valid'])
        self.assertIn('Insufficient buying power', validation['errors'][0])
    
    def test_validate_order_insufficient_position(self):
        """Test order validation when selling more than position"""
        self.broker.connected = True
        self.broker.client.positions = {
            'QQQ': {'position': 50.0}
        }
        
        validation = self.broker.validate_order('QQQ', 'SELL', 100, 350.00)
        
        self.assertFalse(validation['valid'])
        self.assertIn('Insufficient position', validation['errors'][0])
    
    def test_validate_order_large_order_warning(self):
        """Test order validation with large order warning"""
        self.broker.connected = True
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'},
            'BuyingPower': {'value': '100000.00'}
        }
        
        validation = self.broker.validate_order('QQQ', 'BUY', 200, 350.00)
        
        self.assertTrue(validation['valid'])
        self.assertTrue(len(validation['warnings']) > 0)
        self.assertIn('Large order', validation['warnings'][0])
    
    @patch('time.sleep')
    def test_place_order_market(self, mock_sleep):
        """Test placing a market order"""
        self.broker.connected = True
        self.broker.client.create_stock_contract = Mock(return_value=Contract())
        self.broker.client.placeOrder = Mock()
        
        order_id = self.broker.place_order('QQQ', 'BUY', 10)
        
        self.assertEqual(order_id, 1)
        self.broker.client.placeOrder.assert_called_once()
        self.assertEqual(self.broker.client.next_order_id, 2)
    
    @patch('time.sleep')
    def test_place_order_limit(self, mock_sleep):
        """Test placing a limit order"""
        self.broker.connected = True
        self.broker.client.create_stock_contract = Mock(return_value=Contract())
        self.broker.client.placeOrder = Mock()
        
        order_id = self.broker.place_order('QQQ', 'BUY', 10, 'LMT', limit_price=350.00)
        
        self.assertEqual(order_id, 1)
        self.broker.client.placeOrder.assert_called_once()
    
    def test_place_order_not_connected(self):
        """Test placing order when not connected"""
        self.broker.connected = False
        
        order_id = self.broker.place_order('QQQ', 'BUY', 10)
        
        self.assertIsNone(order_id)
    
    def test_place_order_invalid_quantity(self):
        """Test placing order with invalid quantity"""
        self.broker.connected = True
        
        order_id = self.broker.place_order('QQQ', 'BUY', 0)
        
        self.assertIsNone(order_id)
    
    def test_place_order_limit_without_price(self):
        """Test placing limit order without limit price"""
        self.broker.connected = True
        
        order_id = self.broker.place_order('QQQ', 'BUY', 10, 'LMT')
        
        self.assertIsNone(order_id)
    
    @patch('time.sleep')
    def test_cancel_order(self, mock_sleep):
        """Test cancelling an order"""
        self.broker.connected = True
        self.broker.client.cancelOrder = Mock()
        
        result = self.broker.cancel_order(1)
        
        self.assertTrue(result)
        self.broker.client.cancelOrder.assert_called_once_with(1, "")
    
    def test_cancel_order_not_connected(self):
        """Test cancelling order when not connected"""
        self.broker.connected = False
        
        result = self.broker.cancel_order(1)
        
        self.assertFalse(result)
    
    @patch('time.sleep')
    def test_close_position_long(self, mock_sleep):
        """Test closing a long position"""
        self.broker.connected = True
        self.broker.client.positions = {
            'QQQ': {'position': 100.0}
        }
        self.broker.client.create_stock_contract = Mock(return_value=Contract())
        self.broker.client.placeOrder = Mock()
        
        result = self.broker.close_position('QQQ')
        
        self.assertTrue(result)
        # Verify SELL order was placed
        call_args = self.broker.client.placeOrder.call_args
        order = call_args[0][2]
        self.assertEqual(order.action, 'SELL')
        self.assertEqual(order.totalQuantity, 100)
    
    def test_close_position_no_position(self):
        """Test closing position when no position exists"""
        self.broker.client.positions = {}
        
        result = self.broker.close_position('QQQ')
        
        self.assertTrue(result)
    
    @patch('time.sleep')
    def test_execute_position_change_to_tqqq(self, mock_sleep):
        """Test executing position change from QQQ to TQQQ"""
        self.broker.connected = True
        self.broker.client.positions = {
            'QQQ': {'position': 100.0}
        }
        self.broker.client.create_stock_contract = Mock(return_value=Contract())
        self.broker.client.placeOrder = Mock()
        self.broker.update_positions = Mock()
        
        prices = {'qqq_price': 350.00, 'tqqq_price': 35.00}
        result = self.broker.execute_position_change('QQQ', 'TQQQ', prices)
        
        self.assertTrue(result)
        # Should have called placeOrder twice (close QQQ, open TQQQ)
        self.assertEqual(self.broker.client.placeOrder.call_count, 2)
    
    @patch('time.sleep')
    def test_execute_position_change_to_cash(self, mock_sleep):
        """Test executing position change to cash"""
        self.broker.connected = True
        self.broker.client.positions = {
            'QQQ': {'position': 100.0}
        }
        self.broker.client.create_stock_contract = Mock(return_value=Contract())
        self.broker.client.placeOrder = Mock()
        self.broker.update_positions = Mock()
        
        prices = {'qqq_price': 350.00, 'tqqq_price': 35.00}
        result = self.broker.execute_position_change('QQQ', 'Cash', prices)
        
        self.assertTrue(result)
        # Should have called placeOrder once (close QQQ only)
        self.assertEqual(self.broker.client.placeOrder.call_count, 1)
    
    def test_get_tick_data(self):
        """Test getting tick data through broker"""
        self.broker.client.get_tick_data = Mock(return_value=pd.DataFrame({
            'timestamp': [datetime.now()],
            'last_price': [150.00],
            'bid': [149.90],
            'ask': [150.10]
        }))
        
        tick_data = self.broker.get_tick_data('AAPL')
        self.assertIsNotNone(tick_data)
        self.broker.client.get_tick_data.assert_called_once_with('AAPL', True)
    
    def test_get_order_book(self):
        """Test getting order book through broker"""
        self.broker.client.get_order_book = Mock(return_value={
            'bids': [(150.00, 100)],
            'asks': [(150.10, 200)]
        })
        
        order_book = self.broker.get_order_book('AAPL')
        self.assertIn('bids', order_book)
        self.assertIn('asks', order_book)
    
    def test_place_batch_orders(self):
        """Test placing multiple orders in batch"""
        self.broker.connected = True
        self.broker.client.create_stock_contract = Mock(return_value=Contract())
        self.broker.client.placeOrder = Mock()
        
        orders = [
            {'symbol': 'QQQ', 'action': 'BUY', 'quantity': 10, 'order_type': 'MKT'},
            {'symbol': 'TQQQ', 'action': 'BUY', 'quantity': 20, 'order_type': 'LMT', 'limit_price': 35.00},
            {'symbol': 'SPY', 'action': 'SELL', 'quantity': 5, 'order_type': 'MKT'}
        ]
        
        with patch('time.sleep'):
            order_ids = self.broker.place_batch_orders(orders)
        
        self.assertEqual(len(order_ids), 3)
        self.assertEqual(self.broker.client.placeOrder.call_count, 3)
    
    def test_update_equity_curve(self):
        """Test equity curve tracking"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '105000.00'}
        }
        
        self.broker.update_equity_curve()
        
        self.assertEqual(len(self.broker.equity_curve), 1)
        self.assertEqual(self.broker.equity_curve[0][1], 105000.00)
        self.assertEqual(self.broker.peak_equity, 105000.00)
    
    def test_max_drawdown_tracking(self):
        """Test maximum drawdown calculation"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'}
        }
        
        # Simulate equity changes
        equity_values = [100000, 105000, 103000, 108000, 95000, 102000]
        
        for value in equity_values:
            self.broker.client.account_info['NetLiquidation']['value'] = str(value)
            self.broker.update_equity_curve()
        
        # Max drawdown should be from 108000 to 95000 = 12.04%
        expected_drawdown = (108000 - 95000) / 108000
        self.assertAlmostEqual(self.broker.max_drawdown, expected_drawdown, places=4)
    
    def test_get_performance_metrics(self):
        """Test comprehensive performance metrics calculation"""
        # Setup equity curve
        self.broker.equity_curve = [
            (datetime.now() - timedelta(days=i), 100000 + i * 1000)
            for i in range(10)
        ]
        self.broker.peak_equity = 109000
        self.broker.max_drawdown = 0.05
        
        # Setup executions with PnL
        self.broker.client.executions = [
            {'realizedPnL': 100, 'commission': 1},
            {'realizedPnL': -50, 'commission': 1},
            {'realizedPnL': 200, 'commission': 1},
            {'realizedPnL': 150, 'commission': 1},
        ]
        
        metrics = self.broker.get_performance_metrics()
        
        self.assertIn('total_return', metrics)
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('max_drawdown', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('profit_factor', metrics)
        self.assertIn('total_trades', metrics)
        self.assertEqual(metrics['total_trades'], 4)
        self.assertEqual(metrics['winning_trades'], 3)
        self.assertEqual(metrics['losing_trades'], 1)
        self.assertEqual(metrics['win_rate'], 0.75)
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        # Create equity curve with known returns
        base_equity = 100000
        self.broker.equity_curve = []
        
        for i in range(50):
            # Simulate 1% daily return with some volatility
            equity = base_equity * (1.01 ** i) * (1 + np.random.normal(0, 0.005))
            self.broker.equity_curve.append((datetime.now() - timedelta(days=50-i), equity))
        
        metrics = self.broker.get_performance_metrics()
        
        # Should have a positive Sharpe ratio for positive returns
        self.assertGreater(metrics['sharpe_ratio'], 0)
    
    def test_profit_factor_calculation(self):
        """Test profit factor calculation"""
        self.broker.equity_curve = [(datetime.now(), 100000), (datetime.now(), 105000)]
        self.broker.client.executions = [
            {'realizedPnL': 100},  # Win
            {'realizedPnL': 200},  # Win
            {'realizedPnL': -50},  # Loss
            {'realizedPnL': -25},  # Loss
        ]
        
        metrics = self.broker.get_performance_metrics()
        
        # Profit factor = 300 / 75 = 4.0
        self.assertEqual(metrics['profit_factor'], 4.0)
    
    @patch('pandas.DataFrame.to_csv')
    def test_export_trade_history(self, mock_to_csv):
        """Test trade history export"""
        self.broker.client.executions = [
            {'symbol': 'QQQ', 'shares': 10, 'price': 350.00},
            {'symbol': 'TQQQ', 'shares': 20, 'price': 35.00}
        ]
        
        self.broker.export_trade_history('test.csv')
        
        mock_to_csv.assert_called_once_with('test.csv', index=False)
    
    @patch('pandas.DataFrame.to_csv')
    def test_export_equity_curve(self, mock_to_csv):
        """Test equity curve export"""
        self.broker.equity_curve = [
            (datetime.now(), 100000),
            (datetime.now(), 105000)
        ]
        
        self.broker.export_equity_curve('equity.csv')
        
        mock_to_csv.assert_called_once_with('equity.csv', index=False)
    
    def test_get_risk_metrics(self):
        """Test risk metrics calculation"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'},
            'BuyingPower': {'value': '50000.00'}
        }
        self.broker.client.positions = {
            'QQQ': {'position': 100, 'avgCost': 350.00},
            'TQQQ': {'position': 50, 'avgCost': 35.00}
        }
        
        risk_metrics = self.broker.get_risk_metrics()
        
        self.assertIn('portfolio_value', risk_metrics)
        self.assertIn('buying_power', risk_metrics)
        self.assertIn('cash_utilization', risk_metrics)
        self.assertIn('leverage', risk_metrics)
        self.assertIn('max_position_concentration', risk_metrics)
        self.assertIn('num_positions', risk_metrics)
        
        self.assertEqual(risk_metrics['num_positions'], 2)
        self.assertEqual(risk_metrics['portfolio_value'], 100000.00)
        self.assertEqual(risk_metrics['buying_power'], 50000.00)
    
    def test_position_concentration(self):
        """Test position concentration calculation"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'}
        }
        # One large position
        self.broker.client.positions = {
            'QQQ': {'position': 200, 'avgCost': 350.00},  # 70k
            'TQQQ': {'position': 100, 'avgCost': 35.00}   # 3.5k
        }
        
        risk_metrics = self.broker.get_risk_metrics()
        
        # Max concentration should be QQQ at 70%
        self.assertGreater(risk_metrics['max_position_concentration'], 0.5)
    
    def test_leverage_calculation(self):
        """Test leverage calculation"""
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'}
        }
        self.broker.client.positions = {
            'QQQ': {'position': 500, 'avgCost': 350.00}  # 175k position on 100k equity = 1.75x leverage
        }
        
        risk_metrics = self.broker.get_risk_metrics()
        
        self.assertGreater(risk_metrics['leverage'], 1.0)


class TestFactoryFunction(unittest.TestCase):
    """Test create_ib_broker factory function"""
    
    @patch('ib_broker.IBBroker.connect')
    def test_create_ib_broker_success(self, mock_connect):
        """Test successful broker creation"""
        mock_connect.return_value = True
        
        config = {
            'ib_host': '127.0.0.1',
            'ib_port': 7497,
            'ib_client_id': 1,
            'total_capital': 100000
        }
        
        broker = create_ib_broker(config)
        
        self.assertIsNotNone(broker)
        self.assertIsInstance(broker, IBBroker)
        mock_connect.assert_called_once()
    
    @patch('ib_broker.IBBroker.connect')
    def test_create_ib_broker_failure(self, mock_connect):
        """Test broker creation failure"""
        mock_connect.return_value = False
        
        config = {'ib_host': '127.0.0.1'}
        broker = create_ib_broker(config)
        
        self.assertIsNone(broker)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for common trading scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'api': {
                'tws_endpoint': '127.0.0.1',
                'port': 7497
            },
            'ib_host': '127.0.0.1',
            'ib_port': 7497,
            'ib_client_id': 1,
            'total_capital': 100000,
            'position_size_pct': 95
        }
        self.broker = IBBroker(self.config)
        self.broker.connected = True
        
        # Mock client
        self.broker.client = Mock()
        self.broker.client.lock = threading.Lock()
        self.broker.client.next_order_id = 1
        self.broker.client.create_stock_contract = Mock(return_value=Contract())
        self.broker.client.placeOrder = Mock()
        self.broker.client.positions = {}
        self.broker.client.account_info = {
            'NetLiquidation': {'value': '100000.00'},
            'BuyingPower': {'value': '100000.00'}
        }
    
    @patch('time.sleep')
    def test_scenario_open_long_position(self, mock_sleep):
        """Test opening a long position"""
        # Validate order
        validation = self.broker.validate_order('QQQ', 'BUY', 100, 350.00)
        self.assertTrue(validation['valid'])
        
        # Place order
        order_id = self.broker.place_order('QQQ', 'BUY', 100)
        self.assertIsNotNone(order_id)
        
        # Verify order was placed
        self.broker.client.placeOrder.assert_called_once()
    
    @patch('time.sleep')
    def test_scenario_scale_into_position(self, mock_sleep):
        """Test scaling into a position with multiple orders"""
        # First entry
        order_id1 = self.broker.place_order('QQQ', 'BUY', 50, 'LMT', limit_price=350.00)
        self.assertIsNotNone(order_id1)
        
        # Second entry
        order_id2 = self.broker.place_order('QQQ', 'BUY', 50, 'LMT', limit_price=348.00)
        self.assertIsNotNone(order_id2)
        
        # Should have placed two orders
        self.assertEqual(self.broker.client.placeOrder.call_count, 2)
    
    @patch('time.sleep')
    def test_scenario_bracket_order_entry(self, mock_sleep):
        """Test entering position with bracket order"""
        order_ids = self.broker.place_bracket_order('QQQ', 'BUY', 100, 350.00, 360.00, 340.00)
        
        self.assertIsNotNone(order_ids)
        self.assertEqual(len(order_ids), 3)
        
        # Should have placed three orders (entry, take profit, stop loss)
        self.assertEqual(self.broker.client.placeOrder.call_count, 3)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
