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
import yaml
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yfinance as yf
import requests

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


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical market data for a symbol"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance data provider"""
    
    def __init__(self):
        self._available = True
    
    @property
    def name(self) -> str:
        return "YFinance"
    
    def is_available(self) -> bool:
        return self._available
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"[YFinance] Fetching {days} days of data for {symbol} ({start_date} to {end_date})")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.error(f"[YFinance] No data received for {symbol}")
                return None
            
            logger.info(f"[YFinance] Fetched {len(data)} days of data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"[YFinance] Error fetching data for {symbol}: {e}")
            self._available = False
            return None


class BrokerDataProvider(MarketDataProvider):
    """Broker-based data provider (e.g., Interactive Brokers)"""
    
    def __init__(self, broker: Optional[BrokerInterface]):
        self.broker = broker
    
    @property
    def name(self) -> str:
        return f"Broker ({type(self.broker).__name__ if self.broker else 'None'})"
    
    def is_available(self) -> bool:
        return self.broker is not None and self.broker.is_connected()
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from broker"""
        if not self.is_available():
            logger.warning(f"[Broker] Not connected, cannot fetch data for {symbol}")
            return None
        
        try:
            duration = kwargs.get('duration', f"{days} D")
            bar_size = kwargs.get('bar_size', "1 D")
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"[Broker] Fetching {days} days of data for {symbol} ({start_date} to {end_date})")
            
            data = self.broker.get_historical_data(symbol, duration=duration, bar_size=bar_size)
            
            if data is not None and not data.empty:
                logger.info(f"[Broker] Fetched {len(data)} data points for {symbol}")
                return data
            else:
                logger.warning(f"[Broker] No data received for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"[Broker] Error fetching data for {symbol}: {e}")
            return None


class TwelveDataProvider(MarketDataProvider):
    """Twelve Data API provider for market data"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('TWELVEDATA_API_KEY')
        self._available = self.api_key is not None
        self.base_url = "https://api.twelvedata.com"
        
        if not self._available:
            logger.warning("[TwelveData] No API key provided. Set 'twelvedata_api_key' in config or TWELVEDATA_API_KEY environment variable.")
    
    @property
    def name(self) -> str:
        return "TwelveData"
    
    def is_available(self) -> bool:
        return self._available
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch historical data from Twelve Data API"""
        if not self.is_available():
            logger.warning(f"[TwelveData] API key not available, cannot fetch data for {symbol}")
            return None
        
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"[TwelveData] Fetching {days} days of data for {symbol} ({start_date} to {end_date})")
            
            # Determine interval based on days requested
            if days <= 30:
                interval = "1day"
                outputsize = days
            elif days <= 365:
                interval = "1day"
                outputsize = min(days, 5000)  # API limit
            else:
                interval = "1week"
                outputsize = min(days // 7, 5000)
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key,
                'format': 'JSON',
                'start_date': start_date,
                'end_date': end_date
            }
            
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"[TwelveData] API request failed with status {response.status_code}: {response.text}")
                return None
            
            data_json = response.json()
            
            # Check for API errors
            if 'status' in data_json and data_json['status'] == 'error':
                logger.error(f"[TwelveData] API error: {data_json.get('message', 'Unknown error')}")
                return None
            
            if 'values' not in data_json or not data_json['values']:
                logger.error(f"[TwelveData] No data received for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data_json['values'])
            
            # Convert column names to match yfinance format
            df = df.rename(columns={
                'datetime': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            
            # Convert types
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df = df.sort_index()  # Sort by date ascending
            
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if 'Volume' in df.columns:
                df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype(int)
            
            logger.info(f"[TwelveData] Fetched {len(df)} days of data for {symbol}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[TwelveData] Network error fetching data for {symbol}: {e}")
            self._available = False
            return None
        except Exception as e:
            logger.error(f"[TwelveData] Error fetching data for {symbol}: {e}")
            return None


class MultiProviderDataSource:
    """Manages multiple data providers with fallback support"""
    
    def __init__(self, providers: List[MarketDataProvider]):
        self.providers = providers
        logger.info(f"Initialized data source with {len(providers)} providers: {[p.name for p in providers]}")
    
    def get_historical_data(self, symbol: str, days: int, **kwargs) -> Optional[pd.DataFrame]:
        """Fetch data from first available provider"""
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Provider {provider.name} not available, trying next...")
                continue
            
            logger.info(f"Attempting to fetch {symbol} data from {provider.name}")
            data = provider.get_historical_data(symbol, days, **kwargs)
            
            if data is not None and not data.empty:
                logger.info(f"Successfully fetched {symbol} data from {provider.name}")
                return data
            else:
                logger.warning(f"Failed to fetch {symbol} data from {provider.name}, trying next provider")
        
        logger.error(f"All providers failed for {symbol}")
        return None


class QuantTradingAgent:
    """
    Main Quantitative Trading Agent that coordinates strategies and manages positions
    """
    
    def __init__(self, config_path: str = "quant_config.yaml", broker: Optional[BrokerInterface] = None):
        """
        Initialize the quantitative trading agent
        
        Args:
            config_path: Path to configuration file
            broker: Broker instance (if None, will create based on config)
        """
        logger.info("loading agent configuration...")
        self.config = self._load_config(config_path)
        self.strategies: Dict[str, TradingStrategy] = {}
        self.positions: Dict[str, Dict] = {}  # Current positions per symbol
        self.running = True
        
        # Initialize broker
        logger.info("Initializing broker...")
        self.broker = broker
        if self.broker is None:
            self.broker = self._create_broker()
        
        # Initialize market data providers
        logger.info("Initializing market data providers...")
        self.data_source = self._create_data_source()
        
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
        logger.info(f"Data Providers: {[p.name for p in self.data_source.providers]}")
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
        """Load configuration from JSON or YAML file"""
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith(('.yaml', '.yml')):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
        except (json.JSONDecodeError, yaml.YAMLError) as e:
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
            'data_lookback_days': 120,
            'data_provider': 'yfinance',  # yfinance, broker, or auto (fallback)
            'data_provider_priority': ['broker', 'yfinance']  # Priority order for auto mode
        }
    
    def _create_broker(self) -> BrokerInterface:
        """Create broker instance based on configuration"""
        broker_type = self.config.get('broker', {}).get('type', 'mock')
        logger.info(f"creating broker: {broker_type} ...")
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
    
    def _create_data_source(self) -> MultiProviderDataSource:
        """Create market data source with configured providers"""
        data_provider_config = self.config.get('data_provider', 'yfinance')
        provider_priority = self.config.get('data_provider_priority', ['yfinance'])
        
        providers = []
        
        if data_provider_config == 'auto':
            # Use priority order
            for provider_name in provider_priority:
                provider = self._create_provider(provider_name)
                if provider:
                    providers.append(provider)
        else:
            # Use single specified provider
            provider = self._create_provider(data_provider_config)
            if provider:
                providers.append(provider)
            # Add yfinance as fallback if not already included
            if data_provider_config != 'yfinance':
                providers.append(YFinanceProvider())
        
        if not providers:
            logger.warning("No data providers configured, using YFinance as default")
            providers.append(YFinanceProvider())
        
        return MultiProviderDataSource(providers)
    
    def _create_provider(self, provider_name: str) -> Optional[MarketDataProvider]:
        """Create a specific data provider"""
        if provider_name == 'yfinance':
            return YFinanceProvider()
        elif provider_name == 'broker':
            return BrokerDataProvider(self.broker)
        elif provider_name == 'twelvedata':
            api_key = self.config.get('twelvedata_api_key')
            return TwelveDataProvider(api_key)
        else:
            logger.warning(f"Unknown data provider: {provider_name}")
            return None
    
    def fetch_market_data_from_broker(self, symbol: str, duration="1 D", bar_size="1 min") -> Optional[pd.DataFrame]:
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
            data = self.broker.get_historical_data(symbol, duration=duration, bar_size=bar_size)
            if data is not None and not data.empty:
                logger.info(f"Fetched {len(data)} data points for {symbol} from broker")
                return data
        except Exception as e:
            logger.warning(f"Error fetching data from broker for {symbol}: {e}")
        
        return None
    
    def fetch_market_data(self, symbol: str, days: int = None) -> Optional[pd.DataFrame]:
        """
        Fetch market data for a symbol using configured data source
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data (None = use config default)
            
        Returns:
            DataFrame with OHLCV data
        """
        if days is None:
            days = self.config.get('data_lookback_days', 300)
        
        try:
            data = self.data_source.get_historical_data(symbol, days)
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
        
        # Step 1: Analyze all symbols and collect scores
        symbol_scores = []
        
        for symbol in self.symbols:
            try:
                logger.info(f"\nAnalyzing {symbol}...")
                
                # Get signal from strategy
                result = self.analyze_symbol(symbol)
                if result is None:
                    logger.warning(f"Failed to analyze {symbol}")
                    continue
                
                signal, details = result
                score = details.get('score', 0)
                
                # Check risk management for existing positions
                current_price = details.get('price')
                risk_signal = self.check_risk_management(symbol, current_price)
                
                # If risk management triggers, close position immediately
                if risk_signal:
                    logger.warning(f"{symbol}: Risk management triggered")
                    self.execute_signal(symbol, risk_signal, details)
                    continue
                
                # Store symbol with its score and details
                symbol_scores.append({
                    'symbol': symbol,
                    'score': score,
                    'signal': signal,
                    'details': details,
                    'has_position': symbol in self.positions and self.positions[symbol].get('has_position', False)
                })
                
                logger.info(f"{symbol}: Score={score:.2f}, Signal={signal.value}")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
        
        # Step 2: Sort by score (highest first for buy signals)
        symbol_scores.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"\n{'='*80}")
        logger.info("Symbol Ranking by Score")
        logger.info(f"{'='*80}")
        for i, item in enumerate(symbol_scores[:10], 1):  # Show top 10
            logger.info(f"{i}. {item['symbol']}: Score={item['score']:.2f}, Signal={item['signal'].value}")
        
        # Step 3: Calculate current exposure
        current_exposure = sum(
            self.max_position_size for sym, pos in self.positions.items()
            if pos.get('has_position', False)
        )
        
        max_total_exposure = self.config.get('max_total_exposure', 0.8)
        available_exposure = max_total_exposure - current_exposure
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Portfolio Exposure")
        logger.info(f"{'='*80}")
        logger.info(f"Current Exposure: {current_exposure * 100:.1f}%")
        logger.info(f"Max Total Exposure: {max_total_exposure * 100:.1f}%")
        logger.info(f"Available Exposure: {available_exposure * 100:.1f}%")
        logger.info(f"Max Position Size: {self.max_position_size * 100:.1f}%")
        
        # Step 4: Select top symbols to buy (limit to top 5 buy signals)
        positions_to_open = []
        buy_candidates = [item for item in symbol_scores if item['score'] > 0 and not item['has_position']]
        
        for item in buy_candidates[:5]:  # Top 5 buy signals
            if available_exposure >= self.max_position_size:
                positions_to_open.append(item)
                available_exposure -= self.max_position_size
            else:
                logger.info(f"Skipping {item['symbol']}: Insufficient exposure available")
                break
        
        # Step 5: Execute trades for selected symbols
        logger.info(f"\n{'='*80}")
        logger.info(f"Executing Trades")
        logger.info(f"{'='*80}")
        
        if positions_to_open:
            logger.info(f"Opening {len(positions_to_open)} new positions:")
            for item in positions_to_open:
                logger.info(f"  - {item['symbol']}: Score={item['score']:.2f}")
                self.execute_signal(item['symbol'], Signal.BUY, item['details'])
        else:
            logger.info("No new positions to open")
        
        # Step 6: Check existing positions for sell signals
        sell_candidates = [item for item in symbol_scores if item['has_position'] and item['score'] < -20]
        
        if sell_candidates:
            logger.info(f"\nClosing {len(sell_candidates)} positions with weak signals:")
            for item in sell_candidates:
                logger.info(f"  - {item['symbol']}: Score={item['score']:.2f}")
                self.execute_signal(item['symbol'], Signal.SELL, item['details'])
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Analysis Cycle Completed")
        logger.info(f"Active Positions: {sum(1 for pos in self.positions.values() if pos.get('has_position', False))}")
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
    parser.add_argument('--config', type=str, default='quant_config.yaml',
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
