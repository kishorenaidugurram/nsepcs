#!/bin/bash

#############################################################
# NSE F&O PCS Screener - Setup and Run Script
# This script sets up Telegram and runs the screener
#############################################################

set -e

echo "=========================================="
echo "NSE F&O PCS Screener Setup"
echo "=========================================="
echo ""

# Check if Telegram credentials are provided
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  Telegram credentials not configured"
    echo ""
    echo "To enable Telegram notifications, set:"
    echo "  export TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "  export TELEGRAM_CHAT_ID='your_chat_id'"
    echo ""
    echo "To get these:"
    echo "  1. Chat with @BotFather on Telegram"
    echo "  2. Create a new bot (e.g., 'NSE PCS Screener Bot')"
    echo "  3. Get your Chat ID from: https://api.telegram.org/bot<TOKEN>/getUpdates"
    echo ""
    read -p "Continue without Telegram? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

echo "📦 Checking and installing dependencies..."

# Install Python dependencies
pip3 install -q streamlit yfinance pandas numpy requests pytz ta plotly scikit-learn scipy beautifulsoup4 openpyxl 2>&1 | grep -v "already satisfied" || true

echo "✅ Dependencies installed"
echo ""

# Test imports
echo "🔍 Verifying imports..."
python3 -c "import streamlit, yfinance, pandas, numpy, ta, requests" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ All imports successful"
else
    echo "⚠️  Some imports failed - continuing anyway..."
fi

echo ""
echo "=========================================="
echo "Running PCS Screener"
echo "=========================================="
echo ""

# Run the scanner
python3 run_scanner_simple.py

echo ""
echo "=========================================="
echo "✅ Screener execution complete"
echo "=========================================="
