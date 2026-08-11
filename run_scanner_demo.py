#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Demo Mode with Sample Data
Shows how the system works when Telegram credentials are configured
"""

import os
import sys
from datetime import datetime
import pytz
import requests
import pandas as pd
from io import StringIO

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class TelegramNotifier:
    """Send messages to Telegram"""
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, message, parse_mode="HTML"):
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print(f"⚠️ Telegram not configured. Would send:\n{message}")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            response = requests.post(self.api_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Message sent to Telegram")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending to Telegram: {str(e)}")
            return False

    def send_file(self, file_content, filename, caption=""):
        """Send a file to Telegram"""
        if not self.bot_token or not self.chat_id:
            print(f"⚠️ Telegram not configured. Would send file: {filename}")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"

            files = {
                'document': (filename, file_content, 'text/plain')
            }

            data = {
                'chat_id': self.chat_id,
                'caption': caption
            }

            response = requests.post(url, files=files, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ File sent to Telegram: {filename}")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending file to Telegram: {str(e)}")
            return False

def get_sample_results():
    """Return sample qualifying stocks for demonstration"""
    sample_results = [
        {
            'symbol': 'RELIANCE',
            'current_price': 2842.50,
            'rsi': 52.3,
            'adx': 28.5,
            'volume_ratio': 2.3,
            'has_breakout': True,
            'strength': 82
        },
        {
            'symbol': 'TCS',
            'current_price': 3945.75,
            'rsi': 48.1,
            'adx': 25.2,
            'volume_ratio': 1.8,
            'has_breakout': True,
            'strength': 75
        },
        {
            'symbol': 'HDFCBANK',
            'current_price': 1642.30,
            'rsi': 51.5,
            'adx': 22.8,
            'volume_ratio': 1.6,
            'has_breakout': False,
            'strength': 68
        },
        {
            'symbol': 'INFY',
            'current_price': 2156.80,
            'rsi': 49.7,
            'adx': 23.1,
            'volume_ratio': 1.5,
            'has_breakout': False,
            'strength': 65
        },
        {
            'symbol': 'ICICIBANK',
            'current_price': 1198.45,
            'rsi': 54.2,
            'adx': 26.5,
            'volume_ratio': 2.1,
            'has_breakout': True,
            'strength': 79
        },
        {
            'symbol': 'BHARTIARTL',
            'current_price': 1156.20,
            'rsi': 50.5,
            'adx': 21.3,
            'volume_ratio': 1.4,
            'has_breakout': False,
            'strength': 62
        },
        {
            'symbol': 'ITC',
            'current_price': 438.65,
            'rsi': 47.8,
            'adx': 24.6,
            'volume_ratio': 1.7,
            'has_breakout': False,
            'strength': 70
        },
        {
            'symbol': 'SBIN',
            'current_price': 685.30,
            'rsi': 52.1,
            'adx': 25.9,
            'volume_ratio': 2.2,
            'has_breakout': True,
            'strength': 77
        },
        {
            'symbol': 'LT',
            'current_price': 3254.90,
            'rsi': 48.4,
            'adx': 22.4,
            'volume_ratio': 1.5,
            'has_breakout': False,
            'strength': 63
        },
        {
            'symbol': 'KOTAKBANK',
            'current_price': 1956.75,
            'rsi': 51.9,
            'adx': 27.2,
            'volume_ratio': 1.9,
            'has_breakout': False,
            'strength': 73
        },
    ]

    return sample_results

def format_telegram_message(results):
    """Format results into a Telegram message"""
    if not results:
        return "❌ <b>No stocks found</b> meeting the filter criteria today."

    # Sort by strength
    results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""<b>📊 NSE F&O PCS Screener Results</b>
<code>Updated: {current_time}</code>

<b>✅ Stocks Found: {len(results_sorted)}</b>

"""

    for i, result in enumerate(results_sorted[:10], 1):  # Top 10
        symbol = result['symbol']
        strength = result['strength']
        price = result['current_price']
        rsi = result['rsi']
        adx = result['adx']
        volume = result['volume_ratio']
        breakout = "🔥 BREAKOUT" if result['has_breakout'] else "✅ Qualified"

        message += f"""<b>{i}. {symbol}</b>
💰 ₹{price:.2f} | 💪 {strength}% | RSI {rsi:.0f} | ADX {adx:.0f} | Vol {volume:.1f}x
{breakout}

"""

    if len(results_sorted) > 10:
        message += f"\n<i>... and {len(results_sorted) - 10} more stocks</i>"

    message += f"""
<b>⚙️ Filter Criteria:</b>
• RSI: 30-75
• ADX: 20+
• Volume: 1.2x+
• Lookback: 20 days"""

    return message

def format_csv_export(results):
    """Export results to CSV format"""
    if not results:
        return ""

    results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)

    csv_data = "Symbol,Price,RSI,ADX,Volume_Ratio,Strength_Score,Has_Breakout\n"

    for result in results_sorted:
        csv_data += f"{result['symbol']},{result['current_price']:.2f},{result['rsi']:.1f},{result['adx']:.1f},"
        csv_data += f"{result['volume_ratio']:.2f},{result['strength']},{'Yes' if result['has_breakout'] else 'No'}\n"

    return csv_data

def main():
    """Main execution"""

    print(f"\n{'='*70}")
    print("🚀 NSE F&O PCS Scanner - DEMO MODE")
    print(f"{'='*70}\n")

    print("📌 Note: Running with sample data (real system requires network access)\n")

    # Get sample results
    results = get_sample_results()

    print(f"✅ Found {len(results)} qualifying stocks\n")

    # Display top results
    results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)
    print("🏆 Top Results:")
    print("-" * 80)
    for i, result in enumerate(results_sorted[:10], 1):
        breakout = "🔥" if result['has_breakout'] else "✅"
        print(f"{i}. {result['symbol']:12} | Score: {result['strength']:3}% | "
              f"RSI: {result['rsi']:5.1f} | ADX: {result['adx']:5.1f} | "
              f"Vol: {result['volume_ratio']:4.1f}x | {breakout}")
    print("-" * 80)

    # Check Telegram configuration
    print("\n" + "="*70)
    print("📤 TELEGRAM INTEGRATION")
    print("="*70 + "\n")

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("✅ Telegram credentials detected!")
        print(f"   Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
        print(f"   Chat ID: {TELEGRAM_CHAT_ID}\n")

        print("Sending results to Telegram...")
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

        # Send summary message
        message = format_telegram_message(results)
        notifier.send_message(message)

        # Send CSV export
        csv_data = format_csv_export(results)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"nse_pcs_scan_{timestamp}.csv"
        notifier.send_file(csv_data.encode(), filename, "📊 Complete Results")

        print("✅ Results sent to Telegram!")

    else:
        print("⚠️ Telegram credentials not configured\n")
        print("To set up Telegram notifications:")
        print("\n1️⃣  Create a Telegram Bot:")
        print("   • Chat with @BotFather on Telegram")
        print("   • Use /newbot command")
        print("   • Follow the prompts and save your BOT TOKEN\n")

        print("2️⃣  Get your Chat ID:")
        print("   • Chat with @userinfobot on Telegram")
        print("   • It will tell you your chat ID\n")

        print("3️⃣  Configure environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id_here'\n")

        print("4️⃣  Run the scanner:")
        print("   python3 run_scanner_simple.py\n")

        print("✅ Once configured, results will be automatically sent to Telegram!\n")

    print("\n" + "="*70)
    print("📊 PRODUCTION DEPLOYMENT")
    print("="*70 + "\n")

    print("To use with real stock data in production:")
    print("\n1. Ensure network access to Yahoo Finance or alternative data source")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Set Telegram credentials as shown above")
    print("4. Run: python3 run_scanner_simple.py")
    print("\nOr schedule with cron:")
    print("   0 15 * * 1-5 cd /home/user/nsepcs && python3 run_scanner_simple.py")
    print("   (Runs at 3 PM IST on weekdays - after NSE market close)\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
