#!/usr/bin/env python3
"""
NSE F&O Scanner Runner with Telegram Integration
This script loads credentials from .env file and runs the scanner
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv  # Install with: pip install python-dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    print("⚠️  .env file not found!")
    print("Create one using: bash setup_telegram.sh")
    sys.exit(1)

# Now import and run the scanner
from simple_scanner import SimpleScanner

def main():
    """Run scanner with Telegram integration"""

    # Check credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("❌ Telegram credentials not found in .env file")
        print("\nSetup with: bash setup_telegram.sh")
        sys.exit(1)

    print("\n" + "="*60)
    print("🚀 NSE F&O Scanner with Telegram")
    print("="*60)
    print(f"📱 Telegram Bot: {bot_token[:15]}...")
    print(f"💬 Chat ID: {chat_id}")
    print("="*60 + "\n")

    # Run scanner with custom filters (optional)
    filters = {
        'rsi_min': 35,      # RSI lower bound
        'rsi_max': 70,      # RSI upper bound
        'volume_ratio': 1.2,  # Min volume ratio
        'min_score': 60      # Min qualifying score
    }

    print("📋 Scanning with filters:")
    print(f"   RSI: {filters['rsi_min']}-{filters['rsi_max']}")
    print(f"   Volume: ≥ {filters['volume_ratio']}x average")
    print(f"   Min Score: ≥ {filters['min_score']}/100\n")

    scanner = SimpleScanner()
    stocks = scanner.run(filters)

    print("\n✅ Scan complete!")
    print(f"📊 Found {len(stocks)} qualifying stocks")

if __name__ == "__main__":
    main()
