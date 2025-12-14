#!/bin/bash
# Start the QQQ Trading Bot as a background process

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

BOT_SCRIPT="qqq_trading_bot.py"
PID_FILE="bot.pid"
LOG_DIR="logs"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if bot is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the bot
start_bot() {
    if is_running; then
        echo -e "${YELLOW}Bot is already running (PID: $(cat $PID_FILE))${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Starting QQQ Trading Bot...${NC}"
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 not found${NC}"
        return 1
    fi
    
    # Check if required packages are installed
    if ! python3 -c "import pandas, numpy, yfinance" 2>/dev/null; then
        echo -e "${YELLOW}Warning: Some required packages may not be installed${NC}"
        echo "Run: pip install -r requirements.txt"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    # Start the bot in background
    nohup python3 "$BOT_SCRIPT" > "$LOG_DIR/nohup.log" 2>&1 &
    PID=$!
    
    # Save PID
    echo $PID > "$PID_FILE"
    
    # Wait a moment to see if it starts successfully
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}✓ Bot started successfully (PID: $PID)${NC}"
        echo -e "Logs: $LOG_DIR/"
        echo -e "Monitor: python3 monitor.py --tail"
        echo -e "Status: python3 monitor.py --status"
        return 0
    else
        echo -e "${RED}✗ Failed to start bot${NC}"
        echo "Check $LOG_DIR/nohup.log for errors"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the bot
stop_bot() {
    if ! is_running; then
        echo -e "${YELLOW}Bot is not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping bot (PID: $PID)...${NC}"
    
    # Send SIGTERM for graceful shutdown
    kill -TERM "$PID" 2>/dev/null
    
    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Bot stopped${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo -e "${YELLOW}Force stopping...${NC}"
    kill -KILL "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ Bot stopped (forced)${NC}"
    return 0
}

# Function to restart the bot
restart_bot() {
    echo -e "${YELLOW}Restarting bot...${NC}"
    stop_bot
    sleep 2
    start_bot
}

# Function to show bot status
status_bot() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ Bot is running (PID: $PID)${NC}"
        
        # Show process info
        ps -p "$PID" -o pid,etime,cmd
        
        # Show recent status
        echo ""
        python3 monitor.py --status
    else
        echo -e "${RED}✗ Bot is not running${NC}"
    fi
}

# Function to show logs
show_logs() {
    if [ -d "$LOG_DIR" ]; then
        echo -e "${GREEN}Recent logs:${NC}"
        python3 monitor.py --logs
    else
        echo -e "${RED}No logs found${NC}"
    fi
}

# Function to follow logs in real-time
tail_logs() {
    python3 monitor.py --tail
}

# Main script
case "${1:-}" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    logs)
        show_logs
        ;;
    tail)
        tail_logs
        ;;
    *)
        echo "QQQ Trading Bot Control Script"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|tail}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the trading bot in background"
        echo "  stop    - Stop the trading bot"
        echo "  restart - Restart the trading bot"
        echo "  status  - Check if bot is running and show current position"
        echo "  logs    - Show recent log entries"
        echo "  tail    - Follow logs in real-time"
        echo ""
        exit 1
        ;;
esac
