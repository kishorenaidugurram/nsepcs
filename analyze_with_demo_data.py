#!/usr/bin/env python3
"""
NSE Stock Screener - Demo Version with Sample Data
Shows how the analysis would work with actual Telegram integration
"""

import os
import requests
from datetime import datetime
import pytz

# ============ TELEGRAM INTEGRATION ============
def get_telegram_credentials():
    """Get Telegram credentials from environment"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    return token, chat_id


def send_to_telegram(message, token, chat_id, parse_mode='HTML'):
    """Send message to Telegram"""
    if not token or not chat_id:
        print("✗ Telegram not configured")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Split into chunks if needed (max 4096 chars)
    max_length = 4096
    messages = [message[i:i+max_length] for i in range(0, len(message), max_length)] if len(message) > max_length else [message]

    for msg in messages:
        try:
            payload = {
                'chat_id': chat_id,
                'text': msg,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"✗ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False

    return True


# ============ SAMPLE DATA ============
def get_sample_analysis_results():
    """Return sample analysis results for demonstration"""
    return [
        {
            'clean_symbol': 'RELIANCE',
            'price': 3045.50,
            'strength': 92,
            'rsi': 62,
            'adx': 28,
            'volume_ratio': 2.8,
            'breakout': True,
            'bullish_trend': True,
            'near_resistance': True
        },
        {
            'clean_symbol': 'HDFCBANK',
            'price': 2180.75,
            'strength': 85,
            'rsi': 58,
            'adx': 26,
            'volume_ratio': 2.3,
            'breakout': True,
            'bullish_trend': True,
            'near_resistance': False
        },
        {
            'clean_symbol': 'ICICIBANK',
            'price': 1078.20,
            'strength': 78,
            'rsi': 55,
            'adx': 22,
            'volume_ratio': 1.9,
            'breakout': False,
            'bullish_trend': True,
            'near_resistance': False
        },
        {
            'clean_symbol': 'INFY',
            'price': 4278.65,
            'strength': 88,
            'rsi': 61,
            'adx': 25,
            'volume_ratio': 2.5,
            'breakout': True,
            'bullish_trend': True,
            'near_resistance': True
        },
        {
            'clean_symbol': 'TCS',
            'price': 3685.40,
            'strength': 81,
            'rsi': 57,
            'adx': 23,
            'volume_ratio': 2.1,
            'breakout': False,
            'bullish_trend': True,
            'near_resistance': False
        },
        {
            'clean_symbol': 'SBIN',
            'price': 645.30,
            'strength': 75,
            'rsi': 54,
            'adx': 20,
            'volume_ratio': 1.8,
            'breakout': False,
            'bullish_trend': True,
            'near_resistance': False
        },
        {
            'clean_symbol': 'LT',
            'price': 2890.15,
            'strength': 72,
            'rsi': 52,
            'adx': 19,
            'volume_ratio': 1.7,
            'breakout': False,
            'bullish_trend': False,
            'near_resistance': False
        },
        {
            'clean_symbol': 'MARUTI',
            'price': 10845.75,
            'strength': 86,
            'rsi': 60,
            'adx': 27,
            'volume_ratio': 2.4,
            'breakout': True,
            'bullish_trend': True,
            'near_resistance': True
        },
        {
            'clean_symbol': 'ASIANPAINT',
            'price': 3245.80,
            'strength': 79,
            'rsi': 56,
            'adx': 21,
            'volume_ratio': 2.0,
            'breakout': False,
            'bullish_trend': True,
            'near_resistance': False
        },
        {
            'clean_symbol': 'KOTAKBANK',
            'price': 1965.40,
            'strength': 84,
            'rsi': 59,
            'adx': 25,
            'volume_ratio': 2.2,
            'breakout': True,
            'bullish_trend': True,
            'near_resistance': False
        }
    ]


def format_telegram_message(results):
    """Format analysis results for Telegram"""
    if not results:
        return "❌ No stocks found meeting the criteria today."

    # Sort by breakout first, then strength
    results.sort(key=lambda x: (not x['breakout'], -x['strength']))

    breakout_stocks = [r for r in results if r['breakout']]
    other_stocks = [r for r in results if not r['breakout']]

    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M IST")

    message = f"""
<b>🎯 NSE Stock Screener Results</b>
<i>{timestamp}</i>

<b>📊 Summary:</b>
• Total qualified: {len(results)}
• 🔥 Current Day Breakouts: {len(breakout_stocks)}
• 📈 Other Setups: {len(other_stocks)}

"""

    # Current day breakouts
    if breakout_stocks:
        message += "<b>🔥 CURRENT DAY BREAKOUTS (Highest Priority):</b>\n"
        for i, stock in enumerate(breakout_stocks[:15], 1):
            message += f"{i}. <b>{stock['clean_symbol']}</b> ₹{stock['price']:,.2f} | 💪 {stock['strength']:.0f}% | RSI: {stock['rsi']:.0f} | Vol: {stock['volume_ratio']:.1f}x\n"
        message += "\n"

    # Other stocks
    if other_stocks:
        message += "<b>📈 OTHER QUALIFIED STOCKS:</b>\n"
        for i, stock in enumerate(other_stocks[:15], 1):
            trend = "📈" if stock['bullish_trend'] else "➡️"
            message += f"{i}. <b>{stock['clean_symbol']}</b> ₹{stock['price']:,.2f} | 💪 {stock['strength']:.0f}% | RSI: {stock['rsi']:.0f} | Vol: {stock['volume_ratio']:.1f}x {trend}\n"

    # Export list
    message += "\n<b>📋 Quick Stock List:</b>\n<code>"
    all_symbols = [r['clean_symbol'] for r in results[:25]]
    message += ", ".join(all_symbols)
    message += "</code>"

    message += "\n\n<i>Scan completed successfully ✓</i>"

    return message


def main():
    """Main function"""
    print("=" * 70)
    print("NSE STOCK SCREENER - Demo with Sample Data")
    print("=" * 70)

    # Get Telegram credentials
    telegram_token, telegram_chat_id = get_telegram_credentials()

    # Get sample results
    print("\n📈 Generating sample analysis results...")
    results = get_sample_analysis_results()

    print(f"✓ Found {len(results)} stocks in sample data\n")

    # Format message
    message = format_telegram_message(results)

    print("=" * 70)
    print("MESSAGE PREVIEW:")
    print("=" * 70)
    # Show message without HTML tags
    preview = message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<code>', '').replace('</code>', '')
    print(preview)
    print("=" * 70)

    # Send to Telegram
    if telegram_token and telegram_chat_id:
        print("\n📤 Sending to Telegram...")
        if send_to_telegram(message, telegram_token, telegram_chat_id, parse_mode='HTML'):
            print("✅ Message sent successfully to Telegram!")
        else:
            print("❌ Failed to send message to Telegram")
    else:
        print("\n⚠️  Telegram credentials not configured")
        print("\n   To enable Telegram notifications, set environment variables:")
        print("   • TELEGRAM_BOT_TOKEN - Your bot token from @BotFather")
        print("   • TELEGRAM_CHAT_ID - Your Telegram chat ID (use @userinfobot)")
        print("\n   Example:")
        print("   export TELEGRAM_BOT_TOKEN='123456789:ABCDefghIJKlmnOPQrstuVwxYZ'")
        print("   export TELEGRAM_CHAT_ID='9876543210'")
        print("\n   Then run this script:")
        print("   python3 analyze_with_demo_data.py")

    print("\n✓ Demo complete!")


if __name__ == "__main__":
    main()
