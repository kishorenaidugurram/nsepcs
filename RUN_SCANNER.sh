#!/bin/bash

# NSE Stock Scanner with Telegram Integration
# This script runs the scanner and sends results to Telegram

# Configuration
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-""}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-""}
STOCK_LIMIT=${1:-50}
PATTERN_STRENGTH=${2:-65}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 NSE Stock Scanner with Telegram Integration${NC}\n"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo "✅ Python 3 found"

# Install dependencies
echo -e "\n${YELLOW}📦 Installing dependencies...${NC}"
pip install -q yfinance requests numpy pandas 2>&1 | grep -E "Successfully|ERROR" || true

# Set environment variables if provided
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    export TELEGRAM_BOT_TOKEN
    export TELEGRAM_CHAT_ID
    echo "✅ Telegram credentials configured"
fi

# Run scanner
echo -e "\n${YELLOW}🔍 Running scanner...${NC}"
echo "Scanning: $STOCK_LIMIT stocks"
echo "Pattern strength minimum: $PATTERN_STRENGTH\n"

python3 simple_scanner.py --limit $STOCK_LIMIT --telegram --file results_$(date +%Y%m%d_%H%M%S).csv

echo -e "\n${GREEN}✅ Scan complete!${NC}"
