#!/bin/bash
# NSE F&O PCS Screener - Automated Scan and Telegram Notification
# Usage: ./run_scan.sh

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESULTS_DIR="/tmp/pcs_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$RESULTS_DIR/stocks_$TIMESTAMP.json"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Get Telegram credentials from environment
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

echo "=========================================="
echo "NSE F&O PCS Screener - Automated Scan"
echo "=========================================="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S IST')"
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Check if Telegram is configured
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  WARNING: Telegram not configured!"
    echo ""
    echo "To enable Telegram notifications, set environment variables:"
    echo "  export TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "  export TELEGRAM_CHAT_ID='your_chat_id'"
    echo ""
fi

echo "Note: Full Python implementation required. Please run:"
echo "  pip3 install -r requirements.txt"
echo "  python3 run_analysis.py"
echo ""
echo "Then to send results to Telegram:"
echo "  python3 telegram_notifier.py"
echo ""
echo "Or set up as cron job:"
echo "  0 15 * * * cd /home/user/nsepcs && python3 run_analysis.py && python3 telegram_notifier.py"
