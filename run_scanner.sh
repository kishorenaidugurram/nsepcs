#!/bin/bash
# NSE F&O PCS Scanner - Automated Execution Script
# This script runs the stock scanner and sends results to Telegram

set -e

# Configuration
PROJECT_DIR="/home/user/nsepcs"
LOG_DIR="/var/log"
LOG_FILE="${LOG_DIR}/pcs_scanner.log"
RESULTS_DIR="/tmp/claude-0/-home-user-nsepcs/scratchpad"

# Ensure directories exist
mkdir -p "$RESULTS_DIR"

# Ensure log directory is writable, fallback to project directory
if [ ! -w "$LOG_DIR" ]; then
    LOG_FILE="${PROJECT_DIR}/pcs_scanner.log"
fi

echo "========================================" >> "$LOG_FILE"
echo "PCS Scanner Run - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Load environment variables if .telegram.env exists
if [ -f "${PROJECT_DIR}/.telegram.env" ]; then
    echo "Loading Telegram credentials from .telegram.env..." >> "$LOG_FILE"
    export $(grep -v '^#' "${PROJECT_DIR}/.telegram.env" | xargs)
fi

# Navigate to project directory
cd "$PROJECT_DIR"

# Check which scanner to run based on environment
if [ "$SCANNER_MODE" = "online" ] && [ -z "$FORCE_OFFLINE" ]; then
    SCANNER_SCRIPT="telegram_scanner.py"
else
    SCANNER_SCRIPT="offline_scanner.py"
fi

echo "Running scanner: $SCANNER_SCRIPT" >> "$LOG_FILE"
echo "Telegram Token: ${TELEGRAM_BOT_TOKEN:0:10}..." >> "$LOG_FILE"
echo "Chat ID: $TELEGRAM_CHAT_ID" >> "$LOG_FILE"

# Run the scanner
python3 "$SCANNER_SCRIPT" >> "$LOG_FILE" 2>&1

SCAN_EXIT=$?

if [ $SCAN_EXIT -eq 0 ]; then
    echo "✅ Scan completed successfully" >> "$LOG_FILE"
else
    echo "❌ Scan failed with exit code $SCAN_EXIT" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
echo "Log file: $LOG_FILE" >> "$LOG_FILE"
echo "Results directory: $RESULTS_DIR" >> "$LOG_FILE"

exit $SCAN_EXIT
