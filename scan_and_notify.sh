#!/bin/bash

################################################################################
# NSE F&O PCS Scanner - Automated Scan with Telegram Notification
#
# This script scans NSE F&O stocks for PCS opportunities and sends results
# to Telegram (if configured with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
#
# Usage:
#   ./scan_and_notify.sh
#
# Setup:
#   export TELEGRAM_BOT_TOKEN='your_token'
#   export TELEGRAM_CHAT_ID='your_chat_id'
################################################################################

set -e

# Configuration
REPO_DIR="/home/user/nsepcs"
PYTHON_SCRIPT="${REPO_DIR}/run_pcs_scan.py"
LOG_FILE="/tmp/pcs_scan_$(date +%Y%m%d_%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

send_telegram() {
    local message=$1

    if [[ -z "$TELEGRAM_BOT_TOKEN" || -z "$TELEGRAM_CHAT_ID" ]]; then
        print_warning "Telegram credentials not configured"
        return 1
    fi

    local payload=$(cat <<EOF
{
    "chat_id": "$TELEGRAM_CHAT_ID",
    "text": "$message",
    "parse_mode": "HTML"
}
EOF
)

    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage")

    if echo "$response" | grep -q '"ok":true'; then
        print_success "Message sent to Telegram"
        return 0
    else
        print_error "Failed to send Telegram message: $response"
        return 1
    fi
}

check_dependencies() {
    print_header "Checking Dependencies"

    local required=("python3" "curl")
    local missing=()

    for cmd in "${required[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            print_success "$cmd is installed"
        else
            missing+=("$cmd")
            print_error "$cmd is NOT installed"
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing[*]}"
        return 1
    fi
}

run_scanner() {
    print_header "Running PCS Scanner"
    echo "Scanning NSE F&O stocks for PCS opportunities..."
    echo "Results will be logged to: $LOG_FILE"
    echo ""

    if [[ -f "$PYTHON_SCRIPT" ]]; then
        if python3 "$PYTHON_SCRIPT" 2>&1 | tee "$LOG_FILE"; then
            print_success "Scanner completed successfully"
            return 0
        else
            print_error "Scanner encountered an error"
            return 1
        fi
    else
        print_error "Scanner script not found: $PYTHON_SCRIPT"
        return 1
    fi
}

check_telegram_config() {
    print_header "Telegram Configuration"

    if [[ -n "$TELEGRAM_BOT_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        print_success "Telegram bot token is configured"
        print_success "Telegram chat ID is configured"
        return 0
    else
        if [[ -z "$TELEGRAM_BOT_TOKEN" ]]; then
            print_warning "TELEGRAM_BOT_TOKEN is not set"
        fi
        if [[ -z "$TELEGRAM_CHAT_ID" ]]; then
            print_warning "TELEGRAM_CHAT_ID is not set"
        fi
        echo ""
        echo "To enable Telegram notifications:"
        echo "  export TELEGRAM_BOT_TOKEN='your_token'"
        echo "  export TELEGRAM_CHAT_ID='your_chat_id'"
        echo ""
        echo "See TELEGRAM_SETUP.md for complete setup instructions"
        return 1
    fi
}

send_results() {
    print_header "Sending Results"

    if ! check_telegram_config; then
        print_warning "Telegram not configured - skipping notification"
        return 0
    fi

    # Count results from log
    local high_count=$(grep -c "🟢" "$LOG_FILE" 2>/dev/null || echo 0)
    local med_count=$(grep -c "🟡" "$LOG_FILE" 2>/dev/null || echo 0)

    local message="<b>🎯 NSE PCS Scanner Results</b>
<i>$(date '+%Y-%m-%d %H:%M IST')</i>

Scan completed successfully!
High Confidence: $high_count
Medium Confidence: $med_count

See log for details: pcs_scan.log"

    send_telegram "$message"
}

# Main execution
main() {
    echo ""
    print_header "NSE F&O PCS Scanner v1.0"

    # Check dependencies
    if ! check_dependencies; then
        print_error "Required dependencies missing"
        exit 1
    fi

    echo ""

    # Check Telegram config
    check_telegram_config

    echo ""

    # Run scanner
    if run_scanner; then
        echo ""
        send_results
        echo ""
        print_header "✅ Process Completed"
        echo "Log saved to: $LOG_FILE"
        echo "CSV saved to: /tmp/pcs_scan_*.csv"
    else
        echo ""
        print_error "Scanner failed - check log for details"
        exit 1
    fi
}

# Execute main
main "$@"
