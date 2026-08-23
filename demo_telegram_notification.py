#!/usr/bin/env python3
"""
Demo script to test Telegram notifications with mock data
Useful for testing without live market data
"""

import os
import json
import logging
from datetime import datetime
import requests
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
IST = pytz.timezone('Asia/Kolkata')

# Mock stock data
MOCK_RESULTS = [
    {'symbol': 'RELIANCE.NS', 'price': 2950.00, 'rsi': 58, 'adx': 28, 'score': 85},
    {'symbol': 'HDFCBANK.NS', 'price': 1680.50, 'rsi': 55, 'adx': 26, 'score': 82},
    {'symbol': 'INFY.NS', 'price': 4120.25, 'rsi': 52, 'adx': 24, 'score': 78},
    {'symbol': 'TCS.NS', 'price': 3890.00, 'rsi': 60, 'adx': 29, 'score': 88},
    {'symbol': 'ICICIBANK.NS', 'price': 1250.75, 'rsi': 54, 'adx': 22, 'score': 76},
    {'symbol': 'SBIN.NS', 'price': 580.50, 'rsi': 56, 'adx': 25, 'score': 79},
    {'symbol': 'KOTAKBANK.NS', 'price': 2180.00, 'rsi': 57, 'adx': 27, 'score': 81},
    {'symbol': 'MARUTI.NS', 'price': 10250.00, 'rsi': 53, 'adx': 23, 'score': 74},
    {'symbol': 'ASIANPAINT.NS', 'price': 3120.50, 'rsi': 59, 'adx': 28, 'score': 84},
    {'symbol': 'WIPRO.NS', 'price': 415.25, 'rsi': 51, 'adx': 21, 'score': 72},
]


def send_telegram_message(message, html=False):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️  Telegram credentials not configured")
        logger.info("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML" if html else "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Telegram notification sent successfully!")
            return True
        else:
            logger.error(f"❌ Telegram error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def format_message(results):
    """Format results as HTML for Telegram"""
    lines = []
    lines.append("🎯 <b>NSE F&O PCS Scan Results</b>")
    lines.append(f"📅 {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}")
    lines.append("")
    lines.append(f"✅ Found <b>{len(results)}</b> stocks meeting filter criteria")
    lines.append("")

    lines.append("<b>🏆 Top Opportunities:</b>")
    for i, result in enumerate(results[:10], 1):
        lines.append(
            f"{i}. <b>{result['symbol']}</b>\n"
            f"   💰 ₹{result['price']:.2f} | "
            f"RSI: {result['rsi']} | "
            f"ADX: {result['adx']} | "
            f"Score: {result['score']}%"
        )

    lines.append("")
    lines.append("<b>Filter Criteria Applied:</b>")
    lines.append("  • RSI: 30-75")
    lines.append("  • ADX: > 20")
    lines.append("  • Support: Above 20-day MA")
    lines.append("  • Volume: 1.2x average")
    lines.append("")
    lines.append("<i>For detailed analysis: streamlit run streamlit_app.py</i>")

    return "\n".join(lines)


def main():
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Screener - Telegram Notification Demo")
    logger.info("=" * 60)
    logger.info("")

    # Check Telegram config
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info("✅ Telegram Configuration:")
        logger.info(f"   Bot Token: {TELEGRAM_BOT_TOKEN[:20]}***")
        logger.info(f"   Chat ID: {TELEGRAM_CHAT_ID}")
        logger.info("")
    else:
        logger.warning("⚠️  Telegram not configured")
        logger.info("Set environment variables to enable notifications:")
        logger.info("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        logger.info("   export TELEGRAM_CHAT_ID='your_chat_id'")
        logger.info("")
        logger.info("See TELEGRAM_SETUP.md for complete instructions")
        logger.info("")

    # Format message
    message = format_message(MOCK_RESULTS)

    # Print preview
    logger.info("📨 Message Preview:")
    logger.info("-" * 60)
    print(message.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""))
    logger.info("-" * 60)
    logger.info("")

    # Send message
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info("Sending to Telegram...")
        success = send_telegram_message(message, html=True)
        if success:
            logger.info("✅ Notification sent! Check your Telegram chat.")
        else:
            logger.error("❌ Failed to send notification")
            return False
    else:
        logger.info("💡 To test: Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, then run again")

    # Save results
    demo_data = {
        'timestamp': datetime.now(IST).isoformat(),
        'demo': True,
        'total_found': len(MOCK_RESULTS),
        'results': MOCK_RESULTS
    }

    with open('/tmp/demo_results.json', 'w') as f:
        json.dump(demo_data, f, indent=2)
    logger.info("Saved results to /tmp/demo_results.json")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Demo complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
