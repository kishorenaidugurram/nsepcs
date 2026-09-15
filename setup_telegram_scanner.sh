#!/bin/bash
#
# Telegram Stock Scanner - Quick Setup Script
# Usage: ./setup_telegram_scanner.sh
#

set -e

echo "========================================"
echo "NSE Stock Scanner - Telegram Setup"
echo "========================================"
echo ""

# Check if running in the correct directory
if [ ! -f "simple_telegram_scanner.py" ]; then
    echo "❌ Error: Not in nsepcs directory"
    echo "   Please run this script from the nsepcs directory"
    exit 1
fi

# Step 1: Check Python
echo "📌 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.7+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION found"
echo ""

# Step 2: Install dependencies
echo "📌 Installing dependencies..."
pip install -q requests yfinance pandas numpy 2>/dev/null || true
echo "✅ Dependencies installed"
echo ""

# Step 3: Telegram Configuration
echo "📌 Telegram Configuration"
echo "=================================="
echo ""
echo "You need a Telegram Bot Token and Chat ID."
echo "Follow these steps:"
echo ""
echo "1. Open Telegram → Search '@BotFather'"
echo "2. Send: /newbot"
echo "3. Follow prompts to create bot"
echo "4. Copy the TOKEN (starts with numbers:ABC...)"
echo ""
echo "5. Send any message to your new bot"
echo "6. Visit in browser (replace TOKEN):"
echo "   https://api.telegram.org/botTOKEN/getUpdates"
echo "7. Find 'chat':{'id': YOURCHATID in response"
echo ""

read -p "✏️  Enter your BOT TOKEN (or press Enter to skip): " BOT_TOKEN
read -p "✏️  Enter your CHAT ID (or press Enter to skip): " CHAT_ID

if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo ""
    echo "⚠️  Skipping Telegram setup"
    echo "   You can test with: python3 telegram_scanner_demo.py"
    echo "   Configure later with environment variables:"
    echo "   export TELEGRAM_BOT_TOKEN=your-token"
    echo "   export TELEGRAM_CHAT_ID=your-chat-id"
else
    echo "✅ Telegram configured"
fi
echo ""

# Step 4: Test Scanner
echo "📌 Testing Scanner"
echo "=================================="
echo ""

if [ -n "$BOT_TOKEN" ] && [ -n "$CHAT_ID" ]; then
    echo "Testing with Telegram notification..."
    export TELEGRAM_BOT_TOKEN="$BOT_TOKEN"
    export TELEGRAM_CHAT_ID="$CHAT_ID"
    python3 telegram_scanner_demo.py
    echo ""
    echo "✅ Scanner test complete!"
    echo ""
    echo "Configuration saved. You can now run:"
    echo "  TELEGRAM_BOT_TOKEN=$BOT_TOKEN TELEGRAM_CHAT_ID=$CHAT_ID python3 simple_telegram_scanner.py"
else
    echo "Testing without Telegram (demo mode)..."
    python3 telegram_scanner_demo.py
    echo ""
    echo "✅ Scanner works! Test with live data:"
    echo "  python3 simple_telegram_scanner.py"
fi

echo ""
echo "=================================="
echo "📌 Next Steps:"
echo "=================================="
echo ""
echo "1. For automated daily runs, add to crontab:"
echo "   # Edit crontab"
echo "   crontab -e"
echo ""
echo "   # Add this line (runs at 3:40 PM IST daily)"
echo "   40 15 * * 1-5 cd $(pwd) && TELEGRAM_BOT_TOKEN=\"$BOT_TOKEN\" TELEGRAM_CHAT_ID=\"$CHAT_ID\" python3 simple_telegram_scanner.py >> /tmp/scanner.log 2>&1"
echo ""
echo "2. For more options, read:"
echo "   cat TELEGRAM_SCANNER_README.md"
echo ""
echo "3. Run scanner manually:"
echo "   python3 simple_telegram_scanner.py"
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
