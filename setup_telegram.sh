#!/bin/bash
# Setup script for Telegram credentials

echo "========================================"
echo "🤖 NSE PCS Scanner - Telegram Setup"
echo "========================================"
echo ""

# Check if credentials already set
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    echo "✅ Telegram credentials already configured!"
    echo "   Bot Token: ${TELEGRAM_BOT_TOKEN:0:20}..."
    echo "   Chat ID: $TELEGRAM_CHAT_ID"
    echo ""
    read -p "Do you want to update them? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "📱 Telegram Credentials Setup"
echo "========================================"
echo ""
echo "To get your credentials:"
echo ""
echo "1️⃣  BOT TOKEN"
echo "   • Open Telegram, search for @BotFather"
echo "   • Send /newbot and follow instructions"
echo "   • Copy the token (looks like: 123456:ABCdef...)"
echo ""
echo "2️⃣  CHAT ID"
echo "   • Send a message to your bot or @userinfobot"
echo "   • Visit: https://api.telegram.org/bot{TOKEN}/getUpdates"
echo "   • Copy your chat ID (usually a number)"
echo ""

read -p "Enter your Telegram BOT TOKEN: " bot_token
if [ -z "$bot_token" ]; then
    echo "❌ Bot token cannot be empty"
    exit 1
fi

read -p "Enter your Telegram CHAT ID: " chat_id
if [ -z "$chat_id" ]; then
    echo "❌ Chat ID cannot be empty"
    exit 1
fi

echo ""
echo "💾 Saving credentials..."

# Add to bashrc if not already there
if ! grep -q "TELEGRAM_BOT_TOKEN" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# NSE PCS Scanner - Telegram Credentials" >> ~/.bashrc
    echo "export TELEGRAM_BOT_TOKEN='$bot_token'" >> ~/.bashrc
    echo "export TELEGRAM_CHAT_ID='$chat_id'" >> ~/.bashrc
fi

# Also export for current session
export TELEGRAM_BOT_TOKEN="$bot_token"
export TELEGRAM_CHAT_ID="$chat_id"

echo "✅ Credentials saved to ~/.bashrc"
echo ""

# Test the credentials
echo "🧪 Testing Telegram connection..."
python3.13 << EOF
import requests
import sys

bot_token = "$bot_token"
chat_id = "$chat_id"

try:
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url, timeout=5)

    if response.status_code == 200:
        bot_info = response.json()['result']
        print(f"✅ Bot verified: @{bot_info['username']}")
        print(f"   Bot name: {bot_info['first_name']}")

        # Test sending a message
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": "$chat_id",
            "text": "🎉 NSE PCS Scanner configured successfully!",
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 200:
            print(f"✅ Test message sent to chat ID: $chat_id")
        else:
            print(f"❌ Failed to send test message: {response.status_code}")
            sys.exit(1)
    else:
        print(f"❌ Invalid bot token: {response.status_code}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "🎉 Setup Complete!"
    echo "========================================"
    echo ""
    echo "You can now run the scanner:"
    echo "  python3.13 run_scanner.py"
    echo ""
    echo "Or schedule it with cron:"
    echo "  crontab -e"
    echo "  # Add: 30 10 * * 1-5 cd /home/user/nsepcs && python3.13 run_scanner.py"
    echo ""
else
    echo "❌ Setup failed. Please check your credentials."
    exit 1
fi
