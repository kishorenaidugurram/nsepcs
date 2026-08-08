#!/bin/bash
#
# NSE F&O PCS Scanner - Automated Telegram Notification Script
#
# This script runs the scanner and sends results to Telegram automatically
#
# Setup:
#   1. Set environment variables: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
#   2. Make this script executable: chmod +x scan_and_notify.sh
#   3. Run it: ./scan_and_notify.sh
#
# For scheduled execution, add to crontab:
#   30 4 * * * cd /home/user/nsepcs && ./scan_and_notify.sh
#

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/scan_history.log"
PYTHON_SCRIPT="$SCRIPT_DIR/run_scanner.py"

# Check if .env file exists and source it
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${BLUE}Loading configuration from .env${NC}"
    source "$SCRIPT_DIR/.env"
fi

# Verify configuration
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo -e "${YELLOW}⚠️  Telegram credentials not configured${NC}"
    echo ""
    echo "Setup instructions:"
    echo "1. Create a .env file in $SCRIPT_DIR"
    echo "2. Add the following:"
    echo "   TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "   TELEGRAM_CHAT_ID='your_chat_id'"
    echo ""
    echo "See TELEGRAM_SETUP.md for detailed instructions"
    exit 1
fi

# Run the scanner
echo -e "${BLUE}Starting NSE F&O PCS Scanner...${NC}"
cd "$SCRIPT_DIR"

# Run Python script with environment variables
python3 "$PYTHON_SCRIPT"
EXIT_CODE=$?

# Log the result
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Scan completed successfully at $TIMESTAMP${NC}"
    echo "[$TIMESTAMP] SUCCESS - Scan completed" >> "$LOG_FILE"
else
    echo -e "${RED}❌ Scan failed at $TIMESTAMP${NC}"
    echo "[$TIMESTAMP] FAILED - Scan returned exit code $EXIT_CODE" >> "$LOG_FILE"
    exit $EXIT_CODE
fi
