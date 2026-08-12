#!/usr/bin/env python3
"""
NSE F&O Stock Scanner - Demo with Sample Data & Telegram Integration
This demo shows how the scanner works and sends formatted results to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz

class TelegramScannerDemo:
    """Demo scanner with sample data"""

    def __init__(self):
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.results = []

    def generate_sample_results(self):
        """Generate sample scanner results for demonstration"""
        sample_data = [
            {
                'symbol': 'RELIANCE',
                'price': 3245.50,
                'volume_ratio': 1.85,
                'rsi': 62.45,
                'adx': 32.10,
                'patterns': ['Strong Uptrend', 'Support Level Bounce'],
                'max_strength': 88
            },
            {
                'symbol': 'TCS',
                'price': 4128.75,
                'volume_ratio': 1.62,
                'rsi': 58.20,
                'adx': 28.50,
                'patterns': ['Oversold Bounce', 'Strong Uptrend'],
                'max_strength': 78
            },
            {
                'symbol': 'HDFCBANK',
                'price': 1645.80,
                'volume_ratio': 1.45,
                'rsi': 55.30,
                'adx': 25.80,
                'patterns': ['Support Level Bounce'],
                'max_strength': 72
            },
            {
                'symbol': 'INFY',
                'price': 2889.25,
                'volume_ratio': 1.92,
                'rsi': 68.15,
                'adx': 35.45,
                'patterns': ['Strong Uptrend', 'Breakout Volume Confirm'],
                'max_strength': 85
            },
            {
                'symbol': 'ICICIBANK',
                'price': 1154.50,
                'volume_ratio': 2.15,
                'rsi': 61.90,
                'adx': 29.20,
                'patterns': ['Strong Uptrend'],
                'max_strength': 80
            },
            {
                'symbol': 'SBIN',
                'price': 756.40,
                'volume_ratio': 1.68,
                'rsi': 52.45,
                'adx': 22.10,
                'patterns': ['Oversold Bounce'],
                'max_strength': 65
            },
            {
                'symbol': 'LT',
                'price': 3425.60,
                'volume_ratio': 1.38,
                'rsi': 66.80,
                'adx': 31.50,
                'patterns': ['Strong Uptrend', 'Support Level Bounce'],
                'max_strength': 82
            },
            {
                'symbol': 'ITC',
                'price': 445.50,
                'volume_ratio': 1.55,
                'rsi': 59.10,
                'adx': 26.40,
                'patterns': ['Support Level Bounce'],
                'max_strength': 70
            },
        ]

        self.results = sorted(sample_data, key=lambda x: x['max_strength'], reverse=True)
        return self.results

    def send_telegram_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("\n⚠️  Telegram credentials not configured.")
            print("To enable Telegram notifications, set these environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Message sent to Telegram Chat: {self.telegram_chat_id}")
                return True
            else:
                print(f"❌ Failed to send message: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending message: {str(e)}")
            return False

    def format_results_for_telegram(self, limit=8):
        """Format results as Telegram message"""
        if not self.results:
            return "📊 No stocks found matching today's criteria."

        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%d %b %Y, %H:%M IST')

        message = f"""
<b>📊 NSE F&O Stock Scanner Results</b>
<i>{timestamp}</i>

<b>Summary:</b>
• Total stocks found: <b>{len(self.results)}</b>
• Data source: NSE F&O Universe
• Analysis: Technical Patterns + Volume Confirmation

"""

        message += "<b>🏆 Top Performing Stocks Today:</b>\n"

        for idx, result in enumerate(self.results[:limit], 1):
            strength = result['max_strength']
            confidence = 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'
            emoji = '🟢' if confidence == 'HIGH' else '🟡' if confidence == 'MEDIUM' else '🔴'

            pattern_types = " • ".join(result['patterns'][:2])

            message += f"\n<b>{idx}. {result['symbol']}</b> {emoji}\n"
            message += f"   💰 <code>₹{result['price']:.2f}</code>\n"
            message += f"   📊 RSI: {result['rsi']:.0f} | ADX: {result['adx']:.0f} | Vol: {result['volume_ratio']:.1f}x\n"
            message += f"   🎯 {pattern_types}\n"
            message += f"   ⚡ Strength: {strength:.0f}% ({confidence})\n"

        message += f"\n<i>Last 8 updated results shown</i>"
        message += f"\n\n<b>📈 How to Use:</b>"
        message += f"\n1. Review stocks with 🟢 HIGH confidence first"
        message += f"\n2. Check technical charts on TradingView"
        message += f"\n3. Verify entry/exit levels"
        message += f"\n4. Place trades during market hours (9:15 AM - 3:30 PM)"
        message += f"\n\n<i>🔗 Full analysis: nse-fo-pcs-screener.streamlit.app</i>"

        return message

    def run_demo(self):
        """Run demo and send results"""
        print("=" * 70)
        print("NSE F&O STOCK SCANNER - TELEGRAM DEMO")
        print("=" * 70)

        print("\n📊 Generating sample scan results...")
        self.generate_sample_results()

        print(f"✅ Generated {len(self.results)} sample results\n")

        # Format message
        message = self.format_results_for_telegram()

        # Display the message
        print("📱 Message Preview:")
        print("─" * 70)
        # Convert HTML tags to readable format for terminal display
        display_msg = message.replace('<b>', '').replace('</b>', '')
        display_msg = display_msg.replace('<i>', '').replace('</i>', '')
        display_msg = display_msg.replace('<code>', '`').replace('</code>', '`')
        print(display_msg)
        print("─" * 70)

        # Try to send
        print("\n📤 Attempting to send to Telegram...")
        self.send_telegram_message(message)

        print("\n" + "=" * 70)
        print("Setup Instructions for Live Scanning")
        print("=" * 70)
        print("""
1. CREATE A TELEGRAM BOT:
   • Message @BotFather on Telegram
   • Send: /newbot
   • Follow the prompts to create your bot
   • Copy the bot token (e.g., 123456789:ABC...)

2. GET YOUR CHAT ID:
   • Message your bot something
   • Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   • Copy your chat_id from the response

3. SET ENVIRONMENT VARIABLES:
   export TELEGRAM_BOT_TOKEN='your_bot_token_here'
   export TELEGRAM_CHAT_ID='your_chat_id_here'

4. RUN LIVE SCANNER:
   python3 simple_telegram_scanner.py

5. SCHEDULE DAILY RUNS (with cron):
   Edit your crontab: crontab -e
   Add this line to run at 3 PM IST daily:
   0 15 * * * cd /home/user/nsepcs && python3 simple_telegram_scanner.py >> logs/scanner.log 2>&1
        """)


if __name__ == "__main__":
    demo = TelegramScannerDemo()
    demo.run_demo()
