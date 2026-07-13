#!/bin/bash

# Telegram Stock Scanner Setup Script

echo "=========================================="
echo "Telegram Stock Scanner Setup"
echo "=========================================="
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Would you like to overwrite it? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

echo ""
echo "Please enter your Telegram Bot Token:"
echo "(Get it from @BotFather on Telegram)"
read -r BOT_TOKEN

echo ""
echo "Please enter your Telegram Chat ID:"
echo "(Get it from @userinfobot on Telegram)"
read -r CHAT_ID

# Validate inputs
if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "❌ Error: Both token and chat ID are required!"
    exit 1
fi

# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
EOF

chmod 600 .env

echo ""
echo "✅ Setup complete!"
echo ""
echo "Your credentials have been saved to .env (permissions: 600)"
echo ""
echo "To run the scanner manually:"
echo "  source .env && python3 telegram_scanner.py"
echo ""
echo "To schedule it with cron (daily at 9:30 AM):"
echo "  crontab -e"
echo "  Add: 30 9 * * 1-5 cd /home/user/nsepcs && source .env && python3 telegram_scanner.py >> /tmp/stock_scan.log 2>&1"
echo ""
