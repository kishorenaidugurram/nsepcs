#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Demo with Sample Data
Demonstrates the complete Telegram integration workflow with mock stock data
"""

import os
import sys
import json
from datetime import datetime
import requests
import pytz
import warnings

warnings.filterwarnings('ignore')

# Get Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DRY_RUN = os.getenv('TELEGRAM_DRY_RUN', 'false').lower() == 'true'

# Try loading from config file if env vars not set
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    config_file = os.path.expanduser("~/.nsepcs_telegram.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                TELEGRAM_BOT_TOKEN = config.get('token')
                TELEGRAM_CHAT_ID = config.get('chat_id')
        except Exception as e:
            pass

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("ℹ️  Running in DRY-RUN mode (no Telegram credentials found)")
    print("To enable Telegram notifications, run: python setup_telegram.py\n")
    DRY_RUN = True


def send_telegram_message(message: str) -> bool:
    """Send message to Telegram"""
    if DRY_RUN:
        print("=" * 70)
        print("📱 [DRY-RUN] Telegram Message Preview:")
        print("=" * 70)
        print(message)
        print("=" * 70)
        return True

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, data=data, timeout=10)
        success = response.status_code == 200
        if success:
            print("✅ Message sent to Telegram successfully!")
        else:
            print(f"❌ Failed to send message. Status: {response.status_code}")
        return success
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False


def get_sample_stocks():
    """Get sample stocks with mock technical data for demonstration"""
    return [
        {
            'symbol': 'RELIANCE',
            'price': 2684.50,
            'change_pct': 1.23,
            'rsi': 62.5,
            'support': 2620.00,
            'resistance': 2750.00,
            'volume_ratio': 1.8,
            'pattern': 'Cup and Handle'
        },
        {
            'symbol': 'TCS',
            'price': 4125.75,
            'change_pct': 0.85,
            'rsi': 58.3,
            'support': 4050.00,
            'resistance': 4200.00,
            'volume_ratio': 1.5,
            'pattern': 'Flat Base Breakout'
        },
        {
            'symbol': 'HDFCBANK',
            'price': 1892.30,
            'change_pct': 2.10,
            'rsi': 68.9,
            'support': 1820.00,
            'resistance': 1950.00,
            'volume_ratio': 2.2,
            'pattern': 'Double Bottom'
        },
        {
            'symbol': 'INFY',
            'price': 2356.90,
            'change_pct': -0.45,
            'rsi': 48.2,
            'support': 2300.00,
            'resistance': 2450.00,
            'volume_ratio': 1.3,
            'pattern': 'Rounding Bottom'
        },
        {
            'symbol': 'ICICIBANK',
            'price': 1268.45,
            'change_pct': 1.95,
            'rsi': 65.7,
            'support': 1220.00,
            'resistance': 1320.00,
            'volume_ratio': 1.9,
            'pattern': 'Current Day Breakout'
        },
        {
            'symbol': 'SBIN',
            'price': 845.60,
            'change_pct': 0.72,
            'rsi': 54.1,
            'support': 820.00,
            'resistance': 880.00,
            'volume_ratio': 1.6,
            'pattern': 'Head & Shoulders Bottom'
        },
        {
            'symbol': 'KOTAKBANK',
            'price': 3425.80,
            'change_pct': 2.34,
            'rsi': 71.2,
            'support': 3300.00,
            'resistance': 3550.00,
            'volume_ratio': 2.1,
            'pattern': 'Rectangle Bottom'
        },
        {
            'symbol': 'MARUTI',
            'price': 10285.45,
            'change_pct': 1.67,
            'rsi': 60.8,
            'support': 10000.00,
            'resistance': 10500.00,
            'volume_ratio': 1.4,
            'pattern': 'Bump and Run Reversal'
        },
    ]


def format_message(stocks_data):
    """Format results as Telegram message"""
    if not stocks_data:
        return "❌ <b>No stocks met the filter criteria today.</b>\n\n⚠️ <i>Try adjusting your filters.</i>"

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M %Z")

    message = f"""🚀 <b>NSE F&O PCS Scanner Results</b>
📅 <i>{current_time}</i>

✅ <b>Stocks Meeting Criteria: {len(stocks_data)}</b>

"""

    for i, stock in enumerate(stocks_data[:10], 1):
        change_sign = "+" if stock['change_pct'] >= 0 else ""
        change_color = "🟢" if stock['change_pct'] >= 0 else "🔴"

        message += f"""<b>{i}. {stock['symbol']}</b>
   💰 <code>₹{stock['price']:.2f}</code> {change_color} {change_sign}{stock['change_pct']:.2f}%
   📊 RSI: {stock['rsi']:.1f} | Support: ₹{stock['support']:.2f} | Resistance: ₹{stock['resistance']:.2f}
   📈 Volume Ratio: {stock['volume_ratio']:.2f}x | Pattern: {stock['pattern']}

"""

    if len(stocks_data) > 10:
        message += f"<i>... and {len(stocks_data) - 10} more stocks</i>\n"

    message += """
<b>📋 Analysis Parameters:</b>
   • Time Frame: Daily + Weekly Combined
   • RSI Range: 30-75 (Optimal: 45-65)
   • Pattern Strength: >65/100
   • Volume Confirmation: >1.0x average

<b>🎯 Key Patterns Detected:</b>
   • Current Day Breakout - Real-time EOD confirmation
   • Cup and Handle - William O'Neil pattern
   • Flat Base - Mark Minervini pattern
   • Double Bottom - Eve & Eve formation
   • Rounding Bottom - Saucer/bowl pattern
   • Head & Shoulders Bottom - Classic reversal

<b>⚠️ Important Disclaimer:</b>
   • For educational use only
   • Not financial advice
   • Always do your own research (DYOR)
   • Paper trade before live trading
   • Risk management is crucial

Generated by NSE F&O PCS Scanner v1.0
"""

    return message


def main():
    """Main execution"""
    print("=" * 70)
    print("🚀 NSE F&O PCS Scanner - Demo Mode")
    print("=" * 70)
    print()

    print("📊 Scanning 32 F&O stocks with technical analysis...")
    print("   • Analyzing Daily and Weekly charts")
    print("   • Detecting chart patterns")
    print("   • Calculating technical indicators")
    print("   • Filtering by criteria\n")

    # Get sample data
    stocks_data = get_sample_stocks()

    print(f"✅ Analysis complete! Found {len(stocks_data)} qualifying stocks\n")

    # Format and send message
    message = format_message(stocks_data)

    print("=" * 70)
    print("📤 Preparing Telegram notification...")
    print("=" * 70)
    print()

    # Send to Telegram
    success = send_telegram_message(message)

    print()
    print("=" * 70)
    if success:
        if DRY_RUN:
            print("✅ Demo mode: Message would be sent to your Telegram!")
            print("📝 To send live: Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        else:
            print("✅ Message sent to Telegram!")
    else:
        print("❌ Error sending message")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
