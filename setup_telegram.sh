#!/bin/bash

# NSE F&O Scanner - Telegram Setup Script
# This script helps you set up Telegram integration

echo "=================================================="
echo "  NSE F&O Scanner - Telegram Setup"
echo "=================================================="
echo ""

echo "Step 1: Create a Telegram Bot"
echo "  • Go to https://t.me/botfather"
echo "  • Type: /newbot"
echo "  • Follow the prompts"
echo "  • Copy your BOT TOKEN"
echo ""
read -p "Enter your Telegram BOT TOKEN: " BOT_TOKEN

echo ""
echo "Step 2: Get Your Chat ID"
echo "  • Go to https://t.me/userinfobot"
echo "  • It will show your CHAT ID"
echo ""
read -p "Enter your Telegram CHAT ID (your user ID): " CHAT_ID

echo ""
echo "Setting environment variables..."

# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
EOF

echo "✅ .env file created with your credentials"
echo ""
echo "Next steps:"
echo "  1. Install dependencies: pip install -r requirements.txt"
echo "  2. Run scanner: python simple_scanner.py"
echo "  3. Or schedule with: python run_scanner_telegram.py"
echo ""
echo "To verify setup: source .env && python -c 'import os; print(f\"Bot: {os.getenv(\"TELEGRAM_BOT_TOKEN\")[:10]}...\"); print(f\"Chat: {os.getenv(\"TELEGRAM_CHAT_ID\")}\"'"
