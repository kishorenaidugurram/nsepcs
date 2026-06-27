#!/bin/bash
# Simple script to run the scanner with Telegram integration
# Usage: ./run_scanner.sh

# Set your Telegram credentials here, or use environment variables
# TELEGRAM_BOT_TOKEN="your_bot_token"
# TELEGRAM_CHAT_ID="your_chat_id"

# Check if credentials are set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  Telegram credentials not configured!"
    echo ""
    echo "To set up Telegram integration:"
    echo "1. Create a bot: Message @BotFather on Telegram and use /newbot"
    echo "2. Get your chat ID: Message @userinfobot"
    echo ""
    echo "Then set environment variables:"
    echo "  export TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "  export TELEGRAM_CHAT_ID='your_chat_id'"
    echo ""
    echo "Or edit this script and add them directly."
    echo ""
    echo "Running scanner without Telegram..."
fi

# Run the scanner
python3 run_scanner_with_telegram.py
