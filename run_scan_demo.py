#!/usr/bin/env python3
"""
PCS Scanner Demo - runs with sample data to demonstrate functionality
Sends sample results to Telegram
"""

import os
import json
import requests
from datetime import datetime
import pytz

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False

def get_sample_results():
    """Generate sample scanner results for demonstration"""
    return [
        {
            'symbol': 'RELIANCE.NS',
            'current_price': 2850.50,
            'rsi': 58.2,
            'adx': 28.5,
            'volume_ratio': 1.85,
            'score': 82,
            'uptrend_days': 4
        },
        {
            'symbol': 'TCS.NS',
            'current_price': 3920.75,
            'rsi': 52.8,
            'adx': 25.3,
            'volume_ratio': 1.45,
            'score': 76,
            'uptrend_days': 3
        },
        {
            'symbol': 'HDFCBANK.NS',
            'current_price': 1685.30,
            'rsi': 55.1,
            'adx': 22.8,
            'volume_ratio': 1.62,
            'score': 73,
            'uptrend_days': 3
        },
        {
            'symbol': 'INFY.NS',
            'current_price': 1812.45,
            'rsi': 49.5,
            'adx': 20.5,
            'volume_ratio': 1.35,
            'score': 68,
            'uptrend_days': 2
        },
        {
            'symbol': 'ICICIBANK.NS',
            'current_price': 1125.80,
            'rsi': 61.3,
            'adx': 26.2,
            'volume_ratio': 1.72,
            'score': 80,
            'uptrend_days': 4
        },
        {
            'symbol': 'SBIN.NS',
            'current_price': 648.50,
            'rsi': 56.7,
            'adx': 24.1,
            'volume_ratio': 1.55,
            'score': 72,
            'uptrend_days': 3
        },
        {
            'symbol': 'LT.NS',
            'current_price': 2310.25,
            'rsi': 54.2,
            'adx': 23.8,
            'volume_ratio': 1.48,
            'score': 70,
            'uptrend_days': 3
        },
        {
            'symbol': 'ITC.NS',
            'current_price': 425.80,
            'rsi': 51.9,
            'adx': 21.5,
            'volume_ratio': 1.38,
            'score': 65,
            'uptrend_days': 2
        },
        {
            'symbol': 'MARUTI.NS',
            'current_price': 8920.00,
            'rsi': 59.4,
            'adx': 27.2,
            'volume_ratio': 1.68,
            'score': 79,
            'uptrend_days': 4
        },
        {
            'symbol': 'ASIANPAINT.NS',
            'current_price': 3150.55,
            'rsi': 53.1,
            'adx': 24.6,
            'volume_ratio': 1.42,
            'score': 68,
            'uptrend_days': 2
        },
    ]

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found matching the criteria."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"<b>📊 NSE F&O PCS Scan Results</b>\n"
    message += f"<b>⏰ Time:</b> {current_time}\n"
    message += f"<b>✅ Stocks Found:</b> {len(results)}\n"
    message += "─" * 45 + "\n\n"

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    for i, result in enumerate(results[:15], 1):
        symbol = result['symbol'].replace('.NS', '')
        price = result['current_price']
        rsi = result['rsi']
        adx = result['adx']
        score = result['score']
        trend = "📈" if result['uptrend_days'] >= 3 else "➡️"

        # Confidence badge
        if score >= 80:
            badge = "🟢 HIGH"
        elif score >= 70:
            badge = "🟡 MEDIUM"
        else:
            badge = "🔴 LOW"

        message += f"<b>{i:2d}. {symbol}</b> {badge}\n"
        message += f"    💰 ₹{price:>8.2f} | RSI: {rsi:>5.1f} | ADX: {adx:>5.1f}\n"
        message += f"    🎯 Score: {score:>3.0f}/100 | Vol: {result['volume_ratio']:.1f}x {trend}\n\n"

    if len(results) > 15:
        message += f"... <b>and {len(results) - 15} more stocks</b>\n\n"

    message += "─" * 45 + "\n"
    message += "<i>📌 Note: This is a demo scan with sample data.\n"
    message += "Use with live market data for actual trading decisions.</i>"

    return message

def main():
    """Main function"""
    print("=" * 70)
    print(" NSE F&O PCS Screener - Automated Scan (Demo Mode)")
    print("=" * 70)

    # Get sample results
    results = get_sample_results()
    print(f"\n✅ Scan complete! Found {len(results)} stocks meeting criteria.\n")

    if results:
        # Display top results in terminal
        results.sort(key=lambda x: x['score'], reverse=True)
        print("📋 Top 10 Results:")
        print("-" * 70)
        print(f"{'#':>2} {'Symbol':>12} {'Price':>10} {'RSI':>6} {'ADX':>6} {'Vol':>6} {'Score':>6}")
        print("-" * 70)
        for i, r in enumerate(results[:10], 1):
            print(f"{i:>2} {r['symbol']:>12} ₹{r['current_price']:>8.2f} "
                  f"{r['rsi']:>6.1f} {r['adx']:>6.1f} {r['volume_ratio']:>5.1f}x {r['score']:>5.0f}")
        print("-" * 70 + "\n")

        # Format and display Telegram message
        telegram_msg = format_telegram_message(results)

        print("📱 Telegram Message Preview:")
        print("=" * 70)
        # Render the HTML for better visualization
        msg_preview = telegram_msg.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
        print(msg_preview)
        print("=" * 70)

        # Try to send to Telegram
        print("\n📤 Attempting to send results to Telegram...")
        if send_to_telegram(telegram_msg):
            print("✅ Results sent to Telegram successfully!")
        else:
            print("⚠️  Could not send to Telegram (credentials not configured)")
            print("\n🔧 To enable Telegram notifications, set these environment variables:")
            print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")
            print("\n📖 Get your bot token from: https://t.me/BotFather")

        # Save results to file
        results_file = '/tmp/pcs_scan_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {results_file}")
    else:
        print("No stocks found meeting the filter criteria")

if __name__ == '__main__':
    main()
