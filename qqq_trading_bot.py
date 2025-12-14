#!/usr/bin/env python3
"""
QQQ/TQQQ Automated Trading Bot

This bot implements a leveraged ETF rotation strategy based on moving averages:
- Switch to TQQQ (3x leveraged) when conditions indicate strong uptrend
- Switch to QQQ (unleveraged) during uptrend corrections
- Hold Cash during downtrends

Strategy Rules:
- Hold TQQQ: 30-day MA > 120-day MA AND price > 30-day MA
- Hold QQQ: 30-day MA > 120-day MA BUT price < 30-day MA
- Hold Cash: 30-day MA < 120-day MA
"""

import os
import sys
import json
import logging
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Optional, Tuple

# Configure logging (before importing IB broker)
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'trading_bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("QQQTradingBot")

# Import IB broker (only if not in dry-run mode)
try:
    from ib_broker import create_ib_broker, IBBroker
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    logger.warning("IB broker module not available. Install ibapi: pip install ibapi")


class QQQTradingBot:
    """Automated trading bot for QQQ/TQQQ rotation strategy."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the trading bot with configuration."""
        self.config = self._load_config(config_path)
        self.running = True
        self.current_position = None  # 'TQQQ', 'QQQ', or 'Cash'
        self.last_check_time = None
        self.data_cache = None
        self.cache_timestamp = None
        self.broker = None  # IB broker instance
        
        # Strategy parameters
        self.short_ma_period = self.config.get('short_ma_period', 30)
        self.long_ma_period = self.config.get('long_ma_period', 120)
        self.check_interval = self.config.get('check_interval_minutes', 15) * 60  # Convert to seconds
        
        # Trading settings
        self.dry_run = self.config.get('dry_run', True)
        self.notification_enabled = self.config.get('enable_notifications', False)
        self.use_ib = self.config.get('use_interactive_brokers', False)
        
        logger.info("QQQ Trading Bot initialized")
        logger.info(f"Strategy: {self.short_ma_period}-day MA / {self.long_ma_period}-day MA")
        logger.info(f"Check interval: {self.check_interval // 60} minutes")
        logger.info(f"Mode: {'DRY RUN (Simulated)' if self.dry_run else 'LIVE TRADING'}")
        
        # Initialize IB broker if enabled
        if not self.dry_run and self.use_ib:
            self._initialize_broker()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
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
        """Return default configuration."""
        return {
            'short_ma_period': 30,
            'long_ma_period': 120,
            'check_interval_minutes': 15,
            'dry_run': True,
            'enable_notifications': False,
            'data_lookback_days': 200,
            'trading_hours_only': True,
            'market_open_hour': 9,
            'market_close_hour': 16,
            'use_interactive_brokers': False,
            'ib_host': '127.0.0.1',
            'ib_port': 7497,  # 7497 for paper, 7496 for live
            'ib_client_id': 1,
        }
    
    def _initialize_broker(self):
        """Initialize Interactive Brokers connection."""
        if not IB_AVAILABLE:
            logger.error("Cannot use Interactive Brokers: ibapi not installed")
            logger.error("Install with: pip install ibapi")
            self.running = False
            return
        
        logger.info("Initializing Interactive Brokers connection...")
        try:
            self.broker = create_ib_broker(self.config)
            if self.broker:
                # Get current position from IB
                current_holding = self.broker.get_current_holding()
                if current_holding:
                    self.current_position = current_holding
                    logger.info(f"Current position from IB: {self.current_position}")
                logger.info("Interactive Brokers connected successfully")
            else:
                logger.error("Failed to connect to Interactive Brokers")
                self.running = False
        except Exception as e:
            logger.error(f"Error initializing IB broker: {e}", exc_info=True)
            self.running = False
    
    def is_market_hours(self) -> bool:
        """Check if current time is within trading hours (9:30 AM - 4:00 PM ET)."""
        if not self.config.get('trading_hours_only', True):
            return True
        
        now = datetime.now()
        # Note: This is a simplified check. For production, use proper timezone handling
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        hour = now.hour
        minute = now.minute
        
        market_open = self.config.get('market_open_hour', 9)
        market_close = self.config.get('market_close_hour', 16)
        
        # Market hours: 9:30 AM to 4:00 PM
        if hour < market_open or (hour == market_open and minute < 30):
            return False
        if hour >= market_close:
            return False
        
        return True
    
    def fetch_market_data(self, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """Fetch current market data for QQQ and TQQQ."""
        # Use cached data if available and recent (< 5 minutes old)
        if not force_refresh and self.data_cache is not None and self.cache_timestamp:
            age = (datetime.now() - self.cache_timestamp).total_seconds()
            if age < 300:  # 5 minutes
                logger.debug("Using cached market data")
                return self.data_cache
        
        try:
            logger.info("Fetching market data...")
            
            # Calculate date range
            lookback_days = self.config.get('data_lookback_days', 200)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            # Download data
            qqq = yf.download('QQQ', start=start_date, end=end_date, progress=False, auto_adjust=True)
            tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False, auto_adjust=True)
            
            if qqq.empty or tqqq.empty:
                logger.error("Failed to download market data")
                return None
            
            # Extract close prices
            if isinstance(qqq.columns, pd.MultiIndex):
                qqq_close = qqq[('Close', 'QQQ')]
                tqqq_close = tqqq[('Close', 'TQQQ')]
            else:
                qqq_close = qqq['Close']
                tqqq_close = tqqq['Close']
            
            # Create dataframe
            df = pd.DataFrame({
                'QQQ_Close': qqq_close,
                'TQQQ_Close': tqqq_close,
            })
            
            # Calculate moving averages
            df['QQQ_SMA_Short'] = df['QQQ_Close'].rolling(window=self.short_ma_period).mean()
            df['QQQ_SMA_Long'] = df['QQQ_Close'].rolling(window=self.long_ma_period).mean()
            
            # Drop NaN values
            df.dropna(inplace=True)
            
            if len(df) < self.long_ma_period:
                logger.error(f"Insufficient data: only {len(df)} days available")
                return None
            
            # Cache the data
            self.data_cache = df
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Market data updated: {len(df)} days, latest: {df.index[-1].date()}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}", exc_info=True)
            return None
    
    def calculate_position(self, df: pd.DataFrame) -> Tuple[str, Dict]:
        """
        Calculate the recommended position based on strategy rules.
        
        Returns:
            Tuple of (position_name, signal_details)
        """
        try:
            # Get latest values
            current_price = df['QQQ_Close'].iloc[-1]
            sma_short = df['QQQ_SMA_Short'].iloc[-1]
            sma_long = df['QQQ_SMA_Long'].iloc[-1]
            
            # Apply strategy rules
            if sma_short > sma_long:
                # Short MA above long MA (uptrend)
                if current_price >= sma_short:
                    position = 'TQQQ'
                    reason = f"Strong uptrend: Price ${current_price:.2f} > {self.short_ma_period}-day MA ${sma_short:.2f} > {self.long_ma_period}-day MA ${sma_long:.2f}"
                else:
                    position = 'QQQ'
                    reason = f"Uptrend with correction: Price ${current_price:.2f} < {self.short_ma_period}-day MA ${sma_short:.2f}, but {self.short_ma_period}-day MA > {self.long_ma_period}-day MA ${sma_long:.2f}"
            else:
                # Short MA below long MA (downtrend)
                position = 'Cash'
                reason = f"Downtrend: {self.short_ma_period}-day MA ${sma_short:.2f} < {self.long_ma_period}-day MA ${sma_long:.2f}"
            
            signal_details = {
                'timestamp': datetime.now().isoformat(),
                'position': position,
                'reason': reason,
                'qqq_price': float(current_price),
                'tqqq_price': float(df['TQQQ_Close'].iloc[-1]),
                'short_ma': float(sma_short),
                'long_ma': float(sma_long),
                'price_to_short_ma': float((current_price / sma_short - 1) * 100),
                'short_to_long_ma': float((sma_short / sma_long - 1) * 100),
            }
            
            return position, signal_details
            
        except Exception as e:
            logger.error(f"Error calculating position: {e}", exc_info=True)
            return None, {}
    
    def execute_trade(self, new_position: str, signal_details: Dict) -> bool:
        """
        Execute a trade to move from current position to new position.
        
        In dry-run mode, this just logs the action.
        In live mode, this would interface with a broker API.
        """
        if new_position == self.current_position:
            logger.debug(f"No change needed, staying in {self.current_position}")
            return True
        
        logger.info("=" * 80)
        logger.info(f"POSITION CHANGE SIGNAL")
        logger.info("=" * 80)
        logger.info(f"Previous Position: {self.current_position or 'None (Initial)'}")
        logger.info(f"New Position: {new_position}")
        logger.info(f"Reason: {signal_details['reason']}")
        logger.info(f"QQQ Price: ${signal_details['qqq_price']:.2f}")
        logger.info(f"TQQQ Price: ${signal_details['tqqq_price']:.2f}")
        logger.info(f"Short MA ({self.short_ma_period}-day): ${signal_details['short_ma']:.2f}")
        logger.info(f"Long MA ({self.long_ma_period}-day): ${signal_details['long_ma']:.2f}")
        logger.info(f"Price vs Short MA: {signal_details['price_to_short_ma']:+.2f}%")
        logger.info(f"Short MA vs Long MA: {signal_details['short_to_long_ma']:+.2f}%")
        logger.info("=" * 80)
        
        if self.dry_run:
            logger.info("DRY RUN MODE - Trade simulated (not executed)")
            self._log_trade(signal_details)
            # Update current position
            self.current_position = new_position
        else:
            logger.warning("LIVE TRADING MODE - Executing trade via Interactive Brokers")
            
            if self.use_ib and self.broker:
                # Execute trade via Interactive Brokers
                prices = {
                    'qqq_price': signal_details['qqq_price'],
                    'tqqq_price': signal_details['tqqq_price']
                }
                
                success = self.broker.execute_position_change(
                    self.current_position,
                    new_position,
                    prices
                )
                
                if success:
                    logger.info("Trade executed successfully via IB")
                    self._log_trade(signal_details)
                    # Update current position
                    self.current_position = new_position
                    
                    # Verify position with broker
                    time.sleep(3)  # Wait for execution
                    actual_position = self.broker.get_current_holding()
                    if actual_position != new_position:
                        logger.warning(f"Position mismatch: Expected {new_position}, got {actual_position}")
                else:
                    logger.error("Failed to execute trade via IB")
                    return False
            else:
                logger.error("IB broker not available but live trading enabled")
                return False
        
        # Send notification if enabled
        if self.notification_enabled:
            self._send_notification(signal_details)
        
        return True
    
    def _log_trade(self, signal_details: Dict):
        """Log trade details to a separate trades log file."""
        trades_log = LOG_DIR / "trades.jsonl"
        try:
            with open(trades_log, 'a') as f:
                f.write(json.dumps(signal_details) + '\n')
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def _send_notification(self, signal_details: Dict):
        """Send notification about position change (placeholder for email/SMS/webhook)."""
        # TODO: Implement notification system (email, SMS, Telegram, Discord, etc.)
        logger.info("Notification sent (placeholder)")
    
    def run_check(self):
        """Run a single check cycle."""
        logger.info("Running position check...")
        
        # Check if market is open
        if not self.is_market_hours():
            logger.info("Outside market hours, skipping check")
            return
        
        # Fetch market data
        df = self.fetch_market_data()
        if df is None:
            logger.error("Failed to fetch market data, skipping check")
            return
        
        # Calculate recommended position
        new_position, signal_details = self.calculate_position(df)
        if new_position is None:
            logger.error("Failed to calculate position")
            return
        
        # Log current status
        logger.info(f"Current Position: {self.current_position or 'Not set'}")
        logger.info(f"Recommended Position: {new_position}")
        logger.info(f"QQQ: ${signal_details['qqq_price']:.2f} | "
                   f"{self.short_ma_period}d MA: ${signal_details['short_ma']:.2f} | "
                   f"{self.long_ma_period}d MA: ${signal_details['long_ma']:.2f}")
        
        # Execute trade if position change is needed
        if new_position != self.current_position:
            self.execute_trade(new_position, signal_details)
        
        self.last_check_time = datetime.now()
    
    def run(self):
        """Main loop for the trading bot."""
        logger.info("Starting QQQ Trading Bot...")
        logger.info("Press Ctrl+C to stop")
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initial check
        try:
            self.run_check()
        except Exception as e:
            logger.error(f"Error during initial check: {e}", exc_info=True)
        
        # Main loop
        while self.running:
            try:
                # Wait for next check interval
                time.sleep(self.check_interval)
                
                # Run check
                self.run_check()
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying
        
        logger.info("Trading bot stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
        # Disconnect from broker
        if self.broker:
            logger.info("Disconnecting from Interactive Brokers...")
            self.broker.disconnect()


def main():
    """Main entry point for the trading bot."""
    print("=" * 80)
    print("QQQ/TQQQ Automated Trading Bot")
    print("=" * 80)
    print()
    
    # Check for config file
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"WARNING: Config file '{config_path}' not found!")
        print("The bot will run with default settings (dry-run mode).")
        print("Create a config.json file to customize settings.")
        print()
        response = input("Continue with defaults? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
        print()
    
    # Create and run bot
    bot = QQQTradingBot(config_path)
    bot.run()


if __name__ == "__main__":
    main()
