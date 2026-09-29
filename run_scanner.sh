#!/bin/bash

# NSE Stock Scanner with Telegram Integration
# This script sets up and runs the stock scanner

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     NSE Stock Scanner with Telegram Integration            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Telegram credentials are set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  TELEGRAM CREDENTIALS NOT FOUND"
    echo ""
    echo "To send results to Telegram, set these environment variables:"
    echo "  export TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "  export TELEGRAM_CHAT_ID='your_chat_id'"
    echo ""
    echo "See TELEGRAM_SETUP.md for setup instructions."
    echo ""
    echo "Running in EXCEL-ONLY mode (no Telegram)..."
    NO_TELEGRAM="--no-telegram"
else
    echo "✅ Telegram credentials found - results will be sent to Telegram"
    NO_TELEGRAM=""
fi

echo ""
echo "Configuration:"
echo "  Stocks to scan: ${STOCKS:-100}"
echo "  Minimum strength: ${STRENGTH:-65}%"
echo ""

# Install dependencies if needed
echo "Checking dependencies..."
python3 -c "import pandas" 2>/dev/null || {
    echo "Installing dependencies..."
    pip install pandas numpy yfinance openpyxl -q
}

# Run the scanner
echo ""
echo "Starting scan..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 simple_scanner.py \
    --stocks "${STOCKS:-100}" \
    --strength "${STRENGTH:-65}" \
    $NO_TELEGRAM

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Scan complete!"
