#!/bin/bash

################################################################################
# Telegram Setup Helper - Interactive Configuration
#
# This script helps you set up Telegram integration for the PCS scanner
# It will guide you through getting your bot token and chat ID
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════════════════╗"
    echo "║             NSE F&O PCS Scanner - Telegram Setup                           ║"
    echo "║                                                                            ║"
    echo "║  This will guide you through setting up Telegram notifications            ║"
    echo "╚════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}STEP: $1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

step1_create_bot() {
    print_step "1: Create a Telegram Bot with @BotFather"

    echo ""
    echo "Follow these steps:"
    echo "1. Open Telegram and search for '@BotFather'"
    echo "2. Start a chat with @BotFather"
    echo "3. Send: /newbot"
    echo "4. Give it a name (e.g., 'NSE PCS Scanner')"
    echo "5. Give it a username ending in 'bot' (e.g., 'nse_pcs_scanner_bot')"
    echo "6. Copy the API Token (looks like: 123456789:ABCdef...)"
    echo ""

    read -p "Have you created the bot and got the API token? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please create the bot first and try again"
        return 1
    fi

    echo ""
    read -sp "Paste your API Token and press Enter: " TELEGRAM_BOT_TOKEN
    echo

    if [[ -z "$TELEGRAM_BOT_TOKEN" ]]; then
        print_error "Token cannot be empty"
        return 1
    fi

    if [[ ! "$TELEGRAM_BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        print_error "Token format looks invalid. Should be: 123456789:ABCdef..."
        return 1
    fi

    print_success "Bot token saved: ${TELEGRAM_BOT_TOKEN:0:15}..."
}

step2_get_chat_id() {
    print_step "2: Get Your Telegram Chat ID"

    echo ""
    echo "Follow these steps:"
    echo "1. Message your bot with: /start"
    echo "2. Copy this command:"
    echo ""
    echo -e "${GREEN}curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates${NC}"
    echo ""
    echo "3. Paste it in your terminal and press Enter"
    echo "4. Look for the 'id' field - that's your Chat ID"
    echo ""

    read -p "Paste your Chat ID (should be a number) and press Enter: " TELEGRAM_CHAT_ID

    if ! [[ "$TELEGRAM_CHAT_ID" =~ ^-?[0-9]+$ ]]; then
        print_error "Chat ID must be numeric"
        return 1
    fi

    print_success "Chat ID saved: $TELEGRAM_CHAT_ID"
}

step3_test_connection() {
    print_step "3: Test the Connection"

    echo ""
    echo "Testing Telegram connection..."
    echo ""

    # Create a Python script to test
    python3 << EOF
import requests
import sys

token = "$TELEGRAM_BOT_TOKEN"
chat_id = "$TELEGRAM_CHAT_ID"

try:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "✅ NSE PCS Scanner - Connection Test Successful!"
    }
    response = requests.post(url, json=payload, timeout=5)

    if response.status_code == 200:
        print("${GREEN}✓ Connection successful!${NC}")
        print("${GREEN}✓ Test message sent to Telegram!${NC}")
    else:
        print("${RED}✗ Error: " + response.text + "${NC}")
        sys.exit(1)
except Exception as e:
    print("${RED}✗ Error: " + str(e) + "${NC}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        print_error "Connection test failed"
        return 1
    fi
}

step4_save_config() {
    print_step "4: Save Configuration"

    echo ""
    echo "How would you like to save the credentials?"
    echo ""
    echo "1) Create .env file (recommended - secure and portable)"
    echo "2) Export to current shell only (temporary - lost after closing terminal)"
    echo "3) Add to ~/.bashrc (permanent for all future terminals)"
    echo ""

    read -p "Choose option (1-3): " -n 1 option
    echo ""
    echo ""

    case $option in
        1)
            cat > /home/user/nsepcs/.env << EOF
# NSE F&O PCS Scanner - Telegram Configuration
# Generated: $(date)
TELEGRAM_BOT_TOKEN='$TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID='$TELEGRAM_CHAT_ID'
EOF
            chmod 600 /home/user/nsepcs/.env
            print_success ".env file created and secured (chmod 600)"
            echo ""
            print_info "Usage: source /home/user/nsepcs/.env"
            echo ""
            # Add to .gitignore
            if ! grep -q "^.env$" /home/user/nsepcs/.gitignore 2>/dev/null; then
                echo ".env" >> /home/user/nsepcs/.gitignore
                print_success "Added .env to .gitignore"
            fi
            ;;
        2)
            export TELEGRAM_BOT_TOKEN
            export TELEGRAM_CHAT_ID
            print_success "Credentials exported to current shell"
            print_info "Note: These will be lost when you close this terminal"
            ;;
        3)
            cat >> ~/.bashrc << EOF

# NSE F&O PCS Scanner Configuration
export TELEGRAM_BOT_TOKEN='$TELEGRAM_BOT_TOKEN'
export TELEGRAM_CHAT_ID='$TELEGRAM_CHAT_ID'
EOF
            print_success "Credentials added to ~/.bashrc"
            print_info "Run: source ~/.bashrc"
            ;;
        *)
            print_error "Invalid option"
            return 1
            ;;
    esac
}

step5_setup_cron() {
    print_step "5: Set Up Automation (Optional)"

    echo ""
    read -p "Do you want to set up automated daily scanning? (y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "What time should the scanner run?"
        echo ""
        echo "Examples:"
        echo "  9:30  - Market opening (IST)"
        echo "  15:45 - Market close (IST)"
        echo ""
        read -p "Enter time (HH:MM) in IST or press Enter to skip: " scan_time

        if [[ -n "$scan_time" ]]; then
            # Parse time
            hour=$(echo $scan_time | cut -d: -f1)
            minute=$(echo $scan_time | cut -d: -f2)

            if [[ ! "$hour" =~ ^[0-9]{1,2}$ ]] || [[ ! "$minute" =~ ^[0-9]{1,2}$ ]]; then
                print_error "Invalid time format"
                return 1
            fi

            # Create cron job
            cron_cmd="$minute $hour * * 1-5 cd /home/user/nsepcs && source .env 2>/dev/null && ./scan_and_notify.sh >> /tmp/pcs_scan_cron.log 2>&1"

            print_info "Would add to crontab: $cron_cmd"
            echo ""

            read -p "Ready to add this to your crontab? (y/n): " -n 1 -r
            echo

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                (crontab -l 2>/dev/null || echo "") | grep -v "pcs_scan\|PCS" | (cat; echo "$cron_cmd") | crontab -
                print_success "Cron job added!"
                echo ""
                echo "Your scanner will run at $scan_time IST on weekdays"
                echo "View cron logs: tail -f /tmp/pcs_scan_cron.log"
            fi
        fi
    fi
}

step6_summary() {
    print_step "6: Setup Complete! 🎉"

    echo ""
    echo "Configuration Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}✓ Telegram Bot Token${NC}: Configured"
    echo -e "${GREEN}✓ Telegram Chat ID${NC}: Configured"
    echo -e "${GREEN}✓ Connection${NC}: Tested Successfully"
    echo ""
    echo "Next steps:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Run your first scan:"
    echo -e "${BLUE}   cd /home/user/nsepcs${NC}"
    echo -e "${BLUE}   source .env${NC}"
    echo -e "${BLUE}   ./scan_and_notify.sh${NC}"
    echo ""
    echo "2. Check the results:"
    echo -e "${BLUE}   tail -f /tmp/pcs_scan_cron.log${NC}"
    echo ""
    echo "3. View the CSV results:"
    echo -e "${BLUE}   cat /tmp/pcs_scan_*.csv${NC}"
    echo ""
    echo "For more information, see:"
    echo "  • AUTOMATED_SCANNING.md - Complete automation guide"
    echo "  • TELEGRAM_SETUP.md - Detailed Telegram setup"
    echo ""
    echo -e "${GREEN}Happy scanning! 📈${NC}"
}

# Main execution
main() {
    print_header

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    if ! python3 -c "import requests" 2>/dev/null; then
        print_error "requests library not found"
        print_info "Install with: pip install requests"
        exit 1
    fi

    # Run all steps
    if step1_create_bot && \
       step2_get_chat_id && \
       step3_test_connection && \
       step4_save_config && \
       step5_setup_cron; then
        step6_summary
    else
        echo ""
        print_error "Setup was not completed"
        print_info "See TELEGRAM_SETUP.md for manual configuration"
        exit 1
    fi
}

main "$@"
