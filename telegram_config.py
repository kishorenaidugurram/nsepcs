"""Telegram configuration for NSE PCS Scanner"""
import os

# Get Telegram credentials from environment variables
# Set these in your environment before running the scanner:
# export TELEGRAM_BOT_TOKEN="your_bot_token_here"
# export TELEGRAM_CHAT_ID="your_chat_id_here"

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Validate configuration
def is_configured():
    """Check if Telegram is properly configured"""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

def get_config_status():
    """Get configuration status message"""
    if is_configured():
        return "✅ Telegram is configured and ready"
    else:
        missing = []
        if not TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")
        return f"⚠️ Telegram not configured. Missing: {', '.join(missing)}"
