#!/usr/bin/env python3
"""
Trading Bot Monitor - View logs and trading activity in real-time
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse


def display_recent_logs(log_dir: Path, lines: int = 50):
    """Display recent log entries."""
    today = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"trading_bot_{today}.log"
    
    if not log_file.exists():
        print(f"No log file found for today: {log_file}")
        return
    
    print(f"\n{'=' * 80}")
    print(f"RECENT LOG ENTRIES (Last {lines} lines)")
    print(f"{'=' * 80}\n")
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
            for line in recent_lines:
                print(line.rstrip())
    except Exception as e:
        print(f"Error reading log file: {e}")


def display_trade_history(log_dir: Path, limit: int = 10):
    """Display recent trades from the trades log."""
    trades_log = log_dir / "trades.jsonl"
    
    if not trades_log.exists():
        print(f"\nNo trades recorded yet: {trades_log}")
        return
    
    print(f"\n{'=' * 80}")
    print(f"TRADE HISTORY (Last {limit} trades)")
    print(f"{'=' * 80}\n")
    
    try:
        with open(trades_log, 'r') as f:
            trades = [json.loads(line) for line in f]
        
        recent_trades = trades[-limit:]
        
        for i, trade in enumerate(recent_trades, 1):
            timestamp = trade.get('timestamp', 'N/A')
            position = trade.get('position', 'N/A')
            reason = trade.get('reason', 'N/A')
            qqq_price = trade.get('qqq_price', 0)
            
            print(f"Trade #{len(trades) - limit + i}")
            print(f"  Time:     {timestamp}")
            print(f"  Position: {position}")
            print(f"  QQQ:      ${qqq_price:.2f}")
            print(f"  Reason:   {reason}")
            print()
    
    except Exception as e:
        print(f"Error reading trades: {e}")


def display_current_status(log_dir: Path):
    """Display current bot status."""
    trades_log = log_dir / "trades.jsonl"
    
    print(f"\n{'=' * 80}")
    print(f"CURRENT STATUS")
    print(f"{'=' * 80}\n")
    
    if trades_log.exists():
        try:
            with open(trades_log, 'r') as f:
                trades = [json.loads(line) for line in f]
            
            if trades:
                last_trade = trades[-1]
                print(f"Current Position:  {last_trade.get('position', 'Unknown')}")
                print(f"Last Update:       {last_trade.get('timestamp', 'N/A')}")
                print(f"QQQ Price:         ${last_trade.get('qqq_price', 0):.2f}")
                print(f"TQQQ Price:        ${last_trade.get('tqqq_price', 0):.2f}")
                print(f"30-day MA:         ${last_trade.get('short_ma', 0):.2f}")
                print(f"120-day MA:        ${last_trade.get('long_ma', 0):.2f}")
                print(f"Price vs 30d MA:   {last_trade.get('price_to_short_ma', 0):+.2f}%")
                print(f"30d MA vs 120d MA: {last_trade.get('short_to_long_ma', 0):+.2f}%")
                print(f"\nTotal Trades:      {len(trades)}")
            else:
                print("No trades recorded yet")
        except Exception as e:
            print(f"Error reading status: {e}")
    else:
        print("Bot has not executed any trades yet")


def tail_logs(log_dir: Path):
    """Tail the log file in real-time (similar to 'tail -f')."""
    today = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"trading_bot_{today}.log"
    
    print(f"\n{'=' * 80}")
    print(f"LIVE LOG MONITORING (Press Ctrl+C to stop)")
    print(f"{'=' * 80}\n")
    
    if not log_file.exists():
        print(f"Waiting for log file: {log_file}")
        # Wait for file to be created
        import time
        while not log_file.exists():
            time.sleep(1)
    
    try:
        with open(log_file, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            
            import time
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped monitoring")
    except Exception as e:
        print(f"Error tailing log: {e}")


def main():
    parser = argparse.ArgumentParser(description='Monitor QQQ Trading Bot')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--logs', action='store_true', help='Show recent logs')
    parser.add_argument('--trades', action='store_true', help='Show trade history')
    parser.add_argument('--tail', action='store_true', help='Tail logs in real-time')
    parser.add_argument('--lines', type=int, default=50, help='Number of log lines to show')
    parser.add_argument('--limit', type=int, default=10, help='Number of trades to show')
    
    args = parser.parse_args()
    
    log_dir = Path("logs")
    
    if not log_dir.exists():
        print(f"Log directory not found: {log_dir}")
        print("The bot may not have been run yet.")
        return
    
    # If no arguments, show status and recent trades
    if not any([args.status, args.logs, args.trades, args.tail]):
        display_current_status(log_dir)
        display_trade_history(log_dir, args.limit)
        return
    
    if args.status:
        display_current_status(log_dir)
    
    if args.trades:
        display_trade_history(log_dir, args.limit)
    
    if args.logs:
        display_recent_logs(log_dir, args.lines)
    
    if args.tail:
        tail_logs(log_dir)


if __name__ == "__main__":
    main()
