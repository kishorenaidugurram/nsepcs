#!/bin/bash
# Quick Start - NSE PCS Stock Scanner with Telegram

echo "=========================================="
echo "NSE Stock Scanner - Quick Start"
echo "=========================================="
echo ""

# Check if environment variables are set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  Telegram credentials not set!"
    echo ""
    echo "Set these environment variables:"
    echo "  export TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "  export TELEGRAM_CHAT_ID='your_chat_id'"
    echo ""
    echo "Get them from:"
    echo "  Bot Token: Message @BotFather on Telegram, send /newbot"
    echo "  Chat ID: Message @RawDataBot on Telegram"
    echo ""
    echo "Running without Telegram - results will be saved to CSV..."
    echo ""
fi

# Navigate to script directory
cd "$(dirname "$0")" || exit

# Run the scanner
echo "🚀 Starting stock scanner..."
echo "   Scanning 219 NSE F&O stocks..."
echo "   This may take 30-45 minutes..."
echo ""

python scan_and_send_telegram.py

echo ""
echo "✅ Scanner complete!"
echo ""
echo "Results saved to:"
echo "  /tmp/claude-0/.../scratchpad/scanner_results_*.csv"
echo "  /tmp/claude-0/.../scratchpad/scanner_results_*.txt"
