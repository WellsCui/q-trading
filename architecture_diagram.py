"""
Broker Integration Architecture Visualization

This file provides a text-based visualization of the broker integration architecture.
"""

ARCHITECTURE = """
╔══════════════════════════════════════════════════════════════════════════╗
║                    BROKER INTEGRATION ARCHITECTURE                       ║
╚══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│                          QuantTradingAgent                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  • Strategy Management (MA, Momentum, Mean Reversion, etc.)      │  │
│  │  • Risk Management (Stop Loss, Take Profit, Position Sizing)     │  │
│  │  • Trade Execution Logic                                          │  │
│  │  • Performance Tracking                                           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ uses / depends on
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BrokerInterface (ABC)                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Abstract Methods:                                                │  │
│  │  • connect(), disconnect(), is_connected()                        │  │
│  │  • get_market_data(), get_historical_data()                       │  │
│  │  • get_account_balance(), get_portfolio_value()                   │  │
│  │  • place_order(), cancel_order(), modify_order()                  │  │
│  │  • get_position(), close_position()                               │  │
│  │  • validate_order(), calculate_shares()                           │  │
│  │  • get_performance_metrics(), get_risk_metrics()                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│       MockBroker            │   │        IBBroker             │
│  ┌───────────────────────┐  │   │  ┌───────────────────────┐  │
│  │  • Simulated Trading  │  │   │  │  • Real TWS/Gateway   │  │
│  │  • No Real Money      │  │   │  │  • Real Orders        │  │
│  │  • Instant Fills      │  │   │  │  • Real Market Data   │  │
│  │  • Testing/Dev        │  │   │  │  • Paper/Live Trading │  │
│  └───────────────────────┘  │   │  └───────────────────────┘  │
└─────────────────────────────┘   └─────────────────────────────┘
                                              │
                                              │ connects to
                                              ▼
                                  ┌─────────────────────────────┐
                                  │   Interactive Brokers       │
                                  │   TWS / IB Gateway          │
                                  │   (Port 7497/7496)          │
                                  └─────────────────────────────┘
"""

WORKFLOW = """
╔══════════════════════════════════════════════════════════════════════════╗
║                         TRADING WORKFLOW                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

1. INITIALIZATION
   ┌──────────────────────────────────────────┐
   │ Load Config (quant_config.yaml)          │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Create/Inject Broker                     │
   │ • Type from config: "mock" or "ib"       │
   │ • MockBroker for testing                 │
   │ • IBBroker for live trading              │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Connect to Broker                        │
   │ broker.connect()                         │
   └──────────────┬───────────────────────────┘
                  │
                  ▼

2. MARKET ANALYSIS CYCLE
   ┌──────────────────────────────────────────┐
   │ Fetch Market Data                        │
   │ • Try broker.get_historical_data()       │
   │ • Fallback to yfinance if needed         │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Run Strategy Analysis                    │
   │ • Calculate signals                      │
   │ • Check risk management rules            │
   └──────────────┬───────────────────────────┘
                  │
                  ▼

3. TRADE EXECUTION
   ┌──────────────────────────────────────────┐
   │ Signal: BUY                              │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Calculate Position Size                  │
   │ shares = broker.calculate_shares()       │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Validate Order                           │
   │ is_valid, msg = broker.validate_order()  │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Place Order                              │
   │ order_id = broker.place_order()          │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Monitor Order Status                     │
   │ status = broker.get_order_status()       │
   └──────────────┬───────────────────────────┘
                  │
                  ▼

4. POSITION MONITORING
   ┌──────────────────────────────────────────┐
   │ Check Risk Management                    │
   │ • Stop Loss triggered?                   │
   │ • Take Profit triggered?                 │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Signal: SELL (if triggered)              │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Close Position                           │
   │ success = broker.close_position()        │
   └──────────────┬───────────────────────────┘
                  │
                  ▼

5. PERFORMANCE TRACKING
   ┌──────────────────────────────────────────┐
   │ Get Performance Metrics                  │
   │ metrics = broker.get_performance_metrics()│
   │ • Total Return                           │
   │ • Sharpe Ratio                           │
   │ • Max Drawdown                           │
   │ • Win Rate                               │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────┐
   │ Export Data                              │
   │ • broker.export_trade_history()          │
   │ • broker.export_equity_curve()           │
   └──────────────────────────────────────────┘
"""

DATA_FLOW = """
╔══════════════════════════════════════════════════════════════════════════╗
║                           DATA FLOW                                      ║
╚══════════════════════════════════════════════════════════════════════════╝

Market Data Flow:
─────────────────
    Interactive Brokers                    YFinance
            │                                  │
            │ (if connected)                   │ (fallback)
            ▼                                  ▼
    ┌──────────────────────────────────────────────┐
    │  broker.get_market_data(symbol)              │
    │  broker.get_historical_data(symbol, ...)     │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  agent.fetch_market_data(symbol)             │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  strategy.calculate_signals(data)            │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  Signal (BUY/SELL/HOLD)                      │
    └──────────────────────────────────────────────┘

Order Flow:
───────────
    QuantTradingAgent
            │
            │ execute_signal(symbol, signal, details)
            ▼
    ┌──────────────────────────────────────────────┐
    │  _open_position() or _close_position()       │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  broker.validate_order(...)                  │
    │  • Check buying power                        │
    │  • Check position exists (for SELL)          │
    │  • Validate quantities                       │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  broker.place_order(...) or                  │
    │  broker.close_position(symbol)               │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  Interactive Brokers TWS                     │
    │  (if live) or MockBroker (if testing)        │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  Order Execution                             │
    └──────────────────────────────────────────────┘
"""

if __name__ == "__main__":
    print(ARCHITECTURE)
    print("\n" * 2)
    print(WORKFLOW)
    print("\n" * 2)
    print(DATA_FLOW)
