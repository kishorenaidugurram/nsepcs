#!/bin/bash
# Telegram Stock Scanner Runner
#
# Usage: ./run_telegram_scanner.sh <bot_token> <chat_id>
# Or set environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Default to environment variables, or use command line arguments
if [ -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$1" ]; then
    export TELEGRAM_BOT_TOKEN="$1"
fi

if [ -z "$TELEGRAM_CHAT_ID" ] && [ ! -z "$2" ]; then
    export TELEGRAM_CHAT_ID="$2"
fi

# Validate credentials
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ Missing Telegram credentials"
    echo ""
    echo "Usage:"
    echo "  1. Set environment variables:"
    echo "     export TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "     export TELEGRAM_CHAT_ID='your_chat_id'"
    echo "     ./run_telegram_scanner.sh"
    echo ""
    echo "  2. Or pass as arguments:"
    echo "     ./run_telegram_scanner.sh <bot_token> <chat_id>"
    echo ""
    echo "Get your credentials:"
    echo "  Bot Token:  Talk to @BotFather on Telegram"
    echo "  Chat ID:    Visit https://api.telegram.org/bot<TOKEN>/getUpdates"
    exit 1
fi

echo "📊 NSE F&O Telegram Stock Scanner"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Starting analysis at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Run the scanner
cd "$(dirname "$0")"
python3 telegram_scanner_standalone.py

exit $?
