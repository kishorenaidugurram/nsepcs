#!/usr/bin/env python3
"""
Send PCS analysis results to Telegram.
Usage: python3 telegram_notifier.py [stocks_file] [telegram_token] [chat_id]
"""

import sys
import json
import os
from datetime import datetime
import pytz

def send_telegram_message(bot_token, chat_id, message):
    """Send message to Telegram via API"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            return True, "Message sent successfully"
        else:
            return False, f"API error: {response.status_code}"
    except Exception as e:
        return False, str(e)

def format_results_message(stocks_data, total_scanned=None):
    """Format stock results for Telegram"""
    if not stocks_data:
        return "📊 <b>PCS Analysis Complete</b>\n\nNo stocks met filter criteria.\n\n⏰ Check back later!"

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%H:%M IST')

    message = f"📊 <b>NSE F&O PCS - Analysis Results</b>\n"
    message += f"<i>Time: {current_time}</i>\n\n"

    if isinstance(stocks_data, list) and len(stocks_data) > 0 and isinstance(stocks_data[0], dict):
        # Process dictionary format
        high_conf = [s for s in stocks_data if s.get('confidence', '') == 'HIGH']
        med_conf = [s for s in stocks_data if s.get('confidence', '') == 'MEDIUM']

        if total_scanned:
            message += f"<b>Summary:</b> {len(stocks_data)}/{total_scanned} stocks\n\n"
        else:
            message += f"<b>Summary:</b> {len(stocks_data)} stocks found\n\n"

        if high_conf:
            message += "🟢 <b>HIGH Confidence</b>\n"
            for s in high_conf[:5]:
                strength = s.get('strength', 0)
                price = s.get('price', 'N/A')
                rsi = s.get('rsi', 'N/A')
                if isinstance(price, (int, float)):
                    price = f"₹{price:.2f}"
                if isinstance(rsi, (int, float)):
                    rsi = f"{rsi:.0f}"
                message += f"<code>{s['symbol']:10}</code> {strength:.0f}% | {price} | RSI: {rsi}\n"
            if len(high_conf) > 5:
                message += f"  +{len(high_conf) - 5} more stocks\n"
            message += "\n"

        if med_conf:
            message += "🟡 <b>MEDIUM Confidence</b>\n"
            for s in med_conf[:3]:
                strength = s.get('strength', 0)
                symbol = s.get('symbol', 'N/A')
                message += f"<code>{symbol:10}</code> {strength:.0f}%\n"
            if len(med_conf) > 3:
                message += f"  +{len(med_conf) - 3} more stocks\n"
    else:
        # Simple format
        message += str(stocks_data)

    message += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "View full analysis 👉 <a href='https://nse-fo-pcs-screener.streamlit.app'>PCS Screener</a>"

    return message

def main():
    """Main function"""

    # Get credentials from environment
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not configured!")
        print("\nTo enable notifications, set:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id_here'")
        return False

    # Example stocks data (in production, this would come from the analysis)
    example_stocks = [
        {'symbol': 'RELIANCE', 'confidence': 'HIGH', 'strength': 92, 'price': 2850.50, 'rsi': 65},
        {'symbol': 'TCS', 'confidence': 'HIGH', 'strength': 88, 'price': 3450.25, 'rsi': 62},
        {'symbol': 'HDFCBANK', 'confidence': 'MEDIUM', 'strength': 76, 'price': 1650.75, 'rsi': 58},
    ]

    # Format message
    message = format_results_message(example_stocks, total_scanned=219)

    # Send message
    print("📱 Sending Telegram message...")
    success, response = send_telegram_message(bot_token, chat_id, message)

    if success:
        print("✅ Message sent successfully!")
        print(f"   Chat ID: {chat_id}")
        return True
    else:
        print(f"❌ Failed to send message: {response}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
