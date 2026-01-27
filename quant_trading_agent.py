#!/usr/bin/env python3
"""
Quantitative Trading Agent with Multiple Strategy Support

This agent provides a flexible framework for implementing various quantitative trading strategies
with configurable stock symbols. It supports:

- Multiple trading strategies (momentum, mean reversion, trend following, etc.)
- Configurable stock symbols
- Risk management
- Position sizing
- Backtesting capabilities
- Live trading integration with Interactive Brokers

Author: Trading Agent System
Date: 2026-01-25
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import yfinance as yf

# Import broker interface
from brokers.base_broker import BrokerInterface, MockBroker
from brokers.ib_broker import IBBroker

# Import strategy classes
from strategies import (
    TradingStrategy,
    Signal,
    MovingAverageCrossoverStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    TrendFollowingStrategy
)

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'quant_agent_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("QuantTradingAgent")


class QuantTradingAgent:
    """
    Main Quantitative Trading Agent that coordinates strategies and manages positions
    """
    
    def __init__(self, config_path: str = "quant_config.json", broker: Optional[BrokerInterface] = None):
        """
        Initialize the quantitative trading agent
        
        Args:
            config_path: Path to configuration file
            broker: Broker instance (if None, will create based on config)
        """
        self.config = self._load_config(config_path)
        self.strategies: Dict[str, TradingStrategy] = {}
        self.positions: Dict[str, Dict] = {}  # Current positions per symbol
        self.running = True
        
        # Initialize broker
        self.broker = broker
        if self.broker is None:
            self.broker = self._create_broker()
        
        # Initialize strategies
        self._initialize_strategies()
        
        # Get trading symbols from config
        self.symbols = self.config.get('symbols', ['SPY'])
        
        # Risk management parameters
        self.max_position_size = self.config.get('max_position_size', 0.2)  # 20% per position
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.05)  # 5% stop loss
        self.take_profit_pct = self.config.get('take_profit_pct', 0.15)  # 15% take profit
        
        # Trading settings
        self.dry_run = self.config.get('dry_run', True)
        self.check_interval = self.config.get('check_interval_minutes', 60) * 60
        
        logger.info("=" * 80)
        logger.info("Quantitative Trading Agent Initialized")
        logger.info("=" * 80)
        logger.info(f"Broker: {type(self.broker).__name__}")
        logger.info(f"Broker Connected: {self.broker.is_connected() if self.broker else False}")
        logger.info(f"Strategies: {', '.join(self.strategies.keys())}")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE TRADING'}")
        logger.info(f"Max Position Size: {self.max_position_size * 100:.1f}%")
        logger.info(f"Stop Loss: {self.stop_loss_pct * 100:.1f}%")
        logger.info(f"Take Profit: {self.take_profit_pct * 100:.1f}%")
        logger.info("=" * 80)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            'symbols': ['SPY', 'QQQ', 'IWM'],
            'active_strategy': 'MovingAverageCrossover',
            'strategies': {
                'MovingAverageCrossover': {
                    'short_window': 50,
                    'long_window': 200,
                    'price_threshold': 0.0
                },
                'Momentum': {
                    'rsi_period': 14,
                    'rsi_oversold': 30,
                    'rsi_overbought': 70,
                    'roc_period': 20
                },
                'MeanReversion': {
                    'bb_period': 20,
                    'bb_std': 2.0,
                    'entry_threshold': 0.02
                },
                'TrendFollowing': {
                    'ma_period': 50,
                    'adx_period': 14,
                    'adx_threshold': 25,
                    'volume_ma_period': 20
                }
            },
            'max_position_size': 0.2,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.15,
            'check_interval_minutes': 60,
            'dry_run': True,
            'data_lookback_days': 300
        }
    
    def _create_broker(self) -> BrokerInterface:
        """Create broker instance based on configuration"""
        broker_type = self.config.get('broker', {}).get('type', 'mock')
        
        if broker_type == 'ib' or broker_type == 'interactive_brokers':
            # Create Interactive Brokers connection
            try:
                broker = IBBroker(self.config.get('broker', {}))
                if broker.connect():
                    logger.info("Connected to Interactive Brokers")
                    return broker
                else:
                    logger.warning("Failed to connect to IB, falling back to MockBroker")
                    return MockBroker(self.config.get('broker', {}))
            except Exception as e:
                logger.error(f"Error connecting to IB: {e}, falling back to MockBroker")
                return MockBroker(self.config.get('broker', {}))
        else:
            # Use mock broker for dry-run mode
            logger.info("Using MockBroker for dry-run mode")
            return MockBroker(self.config.get('broker', {}))
    
    def _initialize_strategies(self):
        """Initialize all configured trading strategies"""
        strategy_configs = self.config.get('strategies', {})
        
        # Map strategy names to classes
        strategy_classes = {
            'MovingAverageCrossover': MovingAverageCrossoverStrategy,
            'Momentum': MomentumStrategy,
            'MeanReversion': MeanReversionStrategy,
            'TrendFollowing': TrendFollowingStrategy,
        }
        
        for strategy_name, strategy_config in strategy_configs.items():
            if strategy_name in strategy_classes:
                self.strategies[strategy_name] = strategy_classes[strategy_name](strategy_config)
                logger.info(f"Initialized strategy: {strategy_name}")
    
    def fetch_market_data_from_broker(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch market data from the broker
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if not self.broker or not self.broker.is_connected():
            logger.warning(f"Broker not connected, cannot fetch market data for {symbol}")
            return None
        
        try:
            # Try to get historical data from broker
            data = self.broker.get_historical_data(symbol, duration="1 D", bar_size="1 min")
            if data is not None and not data.empty:
                logger.info(f"Fetched {len(data)} data points for {symbol} from broker")
                return data
        except Exception as e:
            logger.warning(f"Error fetching data from broker for {symbol}: {e}")
        
        return None
    
    def fetch_market_data(self, symbol: str, days: int = None) -> Optional[pd.DataFrame]:
        """
        Fetch market data for a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data (None = use config default)
            
        Returns:
            DataFrame with OHLCV data
        """
        # First try to get data from broker if connected
        if self.broker and self.broker.is_connected():
            broker_data = self.fetch_market_data_from_broker(symbol)
            if broker_data is not None and not broker_data.empty:
                return broker_data
        
        # Fall back to yfinance
        if days is None:
            days = self.config.get('data_lookback_days', 300)
        
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Fetching {days} days of data for {symbol} ({start_date} to {end_date})")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.error(f"No data received for {symbol}")
                return None
            
            logger.info(f"Fetched {len(data)} days of data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}", exc_info=True)
            return None
    
    def analyze_symbol(self, symbol: str, strategy_name: str = None) -> Optional[Tuple[Signal, Dict]]:
        """
        Analyze a symbol using specified strategy
        
        Args:
            symbol: Stock symbol to analyze
            strategy_name: Name of strategy to use (None = use active strategy from config)
            
        Returns:
            Tuple of (Signal, signal_details) or None on error
        """
        if strategy_name is None:
            strategy_name = self.config.get('active_strategy', 'MovingAverageCrossover')
        
        if strategy_name not in self.strategies:
            logger.error(f"Strategy '{strategy_name}' not found")
            return None
        
        strategy = self.strategies[strategy_name]
        
        # Fetch market data
        data = self.fetch_market_data(symbol, days=strategy.get_required_data_period())
        if data is None:
            return None
        
        # Calculate signals
        signal, details = strategy.calculate_signals(data, symbol)
        
        return signal, details
    
    def check_risk_management(self, symbol: str, current_price: float) -> Optional[Signal]:
        """
        Check if any risk management rules trigger
        
        Args:
            symbol: Stock symbol
            current_price: Current price
            
        Returns:
            Signal if stop loss or take profit triggered, None otherwise
        """
        if symbol not in self.positions or not self.positions[symbol].get('has_position'):
            return None
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        
        # Calculate profit/loss percentage
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Check stop loss
        if pnl_pct <= -self.stop_loss_pct:
            logger.warning(f"{symbol}: Stop loss triggered at {pnl_pct*100:.2f}%")
            return Signal.SELL
        
        # Check take profit
        if pnl_pct >= self.take_profit_pct:
            logger.info(f"{symbol}: Take profit triggered at {pnl_pct*100:.2f}%")
            return Signal.SELL
        
        return None
    
    def execute_signal(self, symbol: str, signal: Signal, details: Dict):
        """
        Execute a trading signal
        
        Args:
            symbol: Stock symbol
            signal: Trading signal
            details: Signal details
        """
        logger.info("=" * 80)
        logger.info(f"SIGNAL: {symbol} - {signal.value}")
        logger.info("=" * 80)
        logger.info(f"Strategy: {details.get('strategy', 'Unknown')}")
        logger.info(f"Price: ${details.get('price', 0):.2f}")
        logger.info(f"Reason: {details.get('reason', 'No reason provided')}")
        
        # Check if we have a position
        has_position = symbol in self.positions and self.positions[symbol].get('has_position', False)
        
        if signal == Signal.BUY and not has_position:
            # Open long position
            self._open_position(symbol, details)
        elif signal == Signal.SELL and has_position:
            # Close position
            self._close_position(symbol, details)
        elif signal == Signal.HOLD:
            logger.info(f"Holding position for {symbol}")
        
        logger.info("=" * 80)
    
    def _open_position(self, symbol: str, details: Dict):
        """Open a new position"""
        current_price = details.get('price', 0)
        
        if self.dry_run:
            logger.info(f"DRY RUN: Opening position in {symbol} @ ${current_price:.2f}")
            quantity = 100  # Mock quantity
        else:
            logger.info(f"LIVE: Opening position in {symbol} @ ${current_price:.2f}")
            
            # Use broker to calculate shares and place order
            if self.broker and self.broker.is_connected():
                try:
                    # Calculate position size
                    quantity = self.broker.calculate_shares(symbol, current_price)
                    
                    # Validate order
                    is_valid, error_msg = self.broker.validate_order(symbol, 'BUY', quantity)
                    if not is_valid:
                        logger.error(f"Order validation failed: {error_msg}")
                        return
                    
                    # Place order
                    order_id = self.broker.place_order(symbol, 'BUY', quantity)
                    if order_id is None:
                        logger.error(f"Failed to place order for {symbol}")
                        return
                    
                    logger.info(f"Order placed successfully: Order ID {order_id}")
                except Exception as e:
                    logger.error(f"Error placing order: {e}", exc_info=True)
                    return
            else:
                logger.error("Broker not connected, cannot place order")
                return
        
        # Record position
        self.positions[symbol] = {
            'has_position': True,
            'entry_price': details.get('price'),
            'entry_time': datetime.now(),
            'strategy': details.get('strategy'),
            'quantity': 100,  # TODO: Calculate based on position sizing
        }
        
        # Log trade
        self._log_trade(symbol, 'BUY', details)
    
    def _close_position(self, symbol: str, details: Dict):
        """Close existing position"""
        if symbol not in self.positions or not self.positions[symbol].get('has_position'):
            logger.warning(f"No position to close for {symbol}")
            return
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        exit_price = details.get('price')
        quantity = position.get('quantity', 0)
        pnl_pct = (exit_price - entry_price) / entry_price * 100
        
        if self.dry_run:
            logger.info(f"DRY RUN: Closing position in {symbol} @ ${exit_price:.2f}")
        else:
            logger.info(f"LIVE: Closing position in {symbol} @ ${exit_price:.2f}")
            
            # Use broker to close position
            if self.broker and self.broker.is_connected():
                try:
                    # Validate order
                    is_valid, error_msg = self.broker.validate_order(symbol, 'SELL', quantity)
                    if not is_valid:
                        logger.error(f"Order validation failed: {error_msg}")
                        return
                    
                    # Close position
                    success = self.broker.close_position(symbol)
                    if not success:
                        logger.error(f"Failed to close position for {symbol}")
                        return
                    
                    logger.info(f"Position closed successfully")
                except Exception as e:
                    logger.error(f"Error closing position: {e}", exc_info=True)
                    return
            else:
                logger.error("Broker not connected, cannot close position")
                return
        
        logger.info(f"Entry: ${entry_price:.2f}, Exit: ${exit_price:.2f}, P&L: {pnl_pct:+.2f}%")
        
        # Clear position
        self.positions[symbol]['has_position'] = False
        
        # Log trade
        self._log_trade(symbol, 'SELL', details)
    
    def _log_trade(self, symbol: str, action: str, details: Dict):
        """Log trade to file"""
        trade_log_path = LOG_DIR / f"trades_{datetime.now().strftime('%Y%m')}.json"
        
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'price': details.get('price'),
            'strategy': details.get('strategy'),
            'reason': details.get('reason'),
            'dry_run': self.dry_run,
        }
        
        # Append to log file
        trades = []
        if trade_log_path.exists():
            with open(trade_log_path, 'r') as f:
                try:
                    trades = json.load(f)
                except json.JSONDecodeError:
                    trades = []
        
        trades.append(trade_record)
        
        with open(trade_log_path, 'w') as f:
            json.dump(trades, f, indent=2)
    
    def run_analysis_cycle(self):
        """Run one complete analysis cycle for all symbols"""
        logger.info(f"\n{'='*80}")
        logger.info(f"Analysis Cycle Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*80}")
        
        for symbol in self.symbols:
            try:
                logger.info(f"\nAnalyzing {symbol}...")
                
                # Get signal from strategy
                result = self.analyze_symbol(symbol)
                if result is None:
                    logger.warning(f"Failed to analyze {symbol}")
                    continue
                
                signal, details = result
                
                # Check risk management
                current_price = details.get('price')
                risk_signal = self.check_risk_management(symbol, current_price)
                if risk_signal:
                    signal = risk_signal
                
                # Execute signal
                if signal != Signal.HOLD or symbol in self.positions:
                    self.execute_signal(symbol, signal, details)
                else:
                    logger.info(f"{symbol}: {signal.value} - {details.get('reason', '')}")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Analysis Cycle Completed")
        logger.info(f"{'='*80}\n")
    
    def run(self):
        """Main run loop"""
        logger.info("Starting Quantitative Trading Agent...")
        
        # Setup signal handlers for graceful shutdown
        import signal
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.stop())
        
        try:
            while self.running:
                self.run_analysis_cycle()
                
                if self.running:
                    logger.info(f"Waiting {self.check_interval // 60} minutes until next check...")
                    time.sleep(self.check_interval)
        
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self):
        """Stop the agent"""
        logger.info("Shutting down Quantitative Trading Agent...")
        self.running = False
        
        # Disconnect broker
        if self.broker and self.broker.is_connected():
            logger.info("Disconnecting broker...")
            try:
                self.broker.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting broker: {e}")
    
    def get_status(self) -> Dict:
        """Get current status of the agent"""
        broker_status = {
            'type': type(self.broker).__name__ if self.broker else 'None',
            'connected': self.broker.is_connected() if self.broker else False
        }
        
        # Add portfolio info if broker is connected
        if self.broker and self.broker.is_connected():
            try:
                broker_status['portfolio_value'] = self.broker.get_portfolio_value()
                broker_status['buying_power'] = self.broker.get_buying_power()
                broker_status['positions'] = self.broker.get_all_positions()
            except Exception as e:
                logger.warning(f"Error fetching broker status: {e}")
        
        return {
            'running': self.running,
            'symbols': self.symbols,
            'strategies': list(self.strategies.keys()),
            'active_strategy': self.config.get('active_strategy'),
            'positions': self.positions,
            'dry_run': self.dry_run,
            'broker': broker_status
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quantitative Trading Agent')
    parser.add_argument('--config', type=str, default='quant_config.json',
                       help='Path to configuration file')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (no loop)')
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = QuantTradingAgent(config_path=args.config)
    
    if args.once:
        agent.run_analysis_cycle()
    else:
        agent.run()


if __name__ == "__main__":
    main()
