#!/bin/bash

# NSE F&O PCS Scanner - Telegram Setup Helper Script
# This script helps set up automated scanning with Telegram notifications

set -e

echo "=========================================="
echo "NSE F&O PCS Scanner - Telegram Setup"
echo "=========================================="
echo ""

# Check if environment variables are already set
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    echo "✓ Telegram credentials already configured"
    echo "  Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
    echo "  Chat ID: $TELEGRAM_CHAT_ID"
    echo ""
else
    echo "⚠️  No Telegram credentials found. Please configure:"
    echo ""
    echo "Step 1: Get your Bot Token"
    echo "  - Search for @BotFather on Telegram"
    echo "  - Send /newbot and follow instructions"
    echo "  - Save the Bot Token"
    echo ""
    echo "Step 2: Get your Chat ID"
    echo "  - Search for @userinfobot on Telegram"
    echo "  - Send any message"
    echo "  - It will reply with your User ID"
    echo ""
    read -p "Enter TELEGRAM_BOT_TOKEN: " bot_token
    read -p "Enter TELEGRAM_CHAT_ID: " chat_id

    if [ -z "$bot_token" ] || [ -z "$chat_id" ]; then
        echo "❌ Error: Both token and chat ID are required"
        exit 1
    fi

    # Option to save to .env or bashrc
    echo ""
    echo "How would you like to save these credentials?"
    echo "1. Create .env file (local, git-ignored)"
    echo "2. Add to ~/.bashrc (system-wide)"
    echo "3. Just use them now (temporary)"
    read -p "Choose option [1-3]: " option

    case $option in
        1)
            echo "TELEGRAM_BOT_TOKEN=$bot_token" > .env
            echo "TELEGRAM_CHAT_ID=$chat_id" >> .env
            echo "✓ Credentials saved to .env file"
            echo "  Add to .gitignore: echo '.env' >> .gitignore"
            ;;
        2)
            echo "export TELEGRAM_BOT_TOKEN='$bot_token'" >> ~/.bashrc
            echo "export TELEGRAM_CHAT_ID='$chat_id'" >> ~/.bashrc
            echo "✓ Credentials saved to ~/.bashrc"
            source ~/.bashrc
            ;;
        3)
            export TELEGRAM_BOT_TOKEN="$bot_token"
            export TELEGRAM_CHAT_ID="$chat_id"
            echo "✓ Credentials set for this session"
            ;;
    esac
fi

echo ""
echo "Testing Scanner..."
echo ""

# Run a test scan
python3 telegram_pcs_scanner.py RELIANCE.NS INFY.NS 2>&1 | grep -E "Found|Starting|✓|✗" || true

echo ""
echo "=========================================="
echo "Setup Assistance Menu"
echo "=========================================="
echo "1. Set up daily cron job (9:15 AM)"
echo "2. Set up multiple daily scans (9:15 AM & 2:00 PM)"
echo "3. Run scanner now"
echo "4. View last scan results"
echo "5. Exit"
echo ""
read -p "Choose option [1-5]: " setup_option

case $setup_option in
    1)
        echo "Setting up cron job for daily 9:15 AM scan..."
        cron_cmd="15 9 * * 1-5 cd $(pwd) && python3 telegram_pcs_scanner.py >> logs/pcs_scanner.log 2>&1"
        (crontab -l 2>/dev/null | grep -v "telegram_pcs_scanner" || true; echo "$cron_cmd") | crontab -
        echo "✓ Cron job added"
        echo "  Runs Monday-Friday at 9:15 AM"
        echo "  Logs saved to: logs/pcs_scanner.log"
        crontab -l | grep telegram_pcs_scanner || true
        ;;
    2)
        echo "Setting up cron jobs for 9:15 AM and 2:00 PM..."
        cron_cmd1="15 9 * * 1-5 cd $(pwd) && python3 telegram_pcs_scanner.py >> logs/pcs_scanner.log 2>&1"
        cron_cmd2="0 14 * * 1-5 cd $(pwd) && python3 telegram_pcs_scanner.py >> logs/pcs_scanner.log 2>&1"
        (crontab -l 2>/dev/null | grep -v "telegram_pcs_scanner" || true; echo "$cron_cmd1"; echo "$cron_cmd2") | crontab -
        echo "✓ Cron jobs added"
        echo "  Runs Monday-Friday at 9:15 AM and 2:00 PM"
        crontab -l | grep telegram_pcs_scanner || true
        ;;
    3)
        echo "Running scanner now..."
        python3 telegram_pcs_scanner.py
        ;;
    4)
        if [ -f /tmp/pcs_scan_results.json ]; then
            echo "Latest scan results:"
            cat /tmp/pcs_scan_results.json | python3 -m json.tool 2>/dev/null || cat /tmp/pcs_scan_results.json
        else
            echo "No scan results found yet. Run the scanner first."
        fi
        ;;
    5)
        echo "Exiting setup..."
        ;;
esac

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify the scanner works: python3 telegram_pcs_scanner.py"
echo "2. Check results: cat /tmp/pcs_scan_results.json"
echo "3. View cron jobs: crontab -l"
echo "4. Monitor logs: tail -f logs/pcs_scanner.log"
echo ""
echo "For more help, see: TELEGRAM_SETUP.md"
echo ""
