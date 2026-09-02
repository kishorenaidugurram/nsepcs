#!/usr/bin/env python3
"""
Test version of the scanner with mock data to demonstrate Telegram integration
"""

import os
import logging
from datetime import datetime
import pytz
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Handle sending messages to Telegram"""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message):
        """Send a message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("✅ Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            return False


def test_telegram_integration():
    """Test Telegram integration with mock stock data"""

    logger.info("=" * 60)
    logger.info("🚀 NSE Scanner - Telegram Integration Test")
    logger.info("=" * 60)

    # Load credentials from environment
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        logger.info("Set these environment variables and try again:")
        logger.info("export TELEGRAM_BOT_TOKEN='your_bot_token'")
        logger.info("export TELEGRAM_CHAT_ID='your_chat_id'")
        return False

    logger.info(f"✅ Bot Token: {bot_token[:20]}...")
    logger.info(f"✅ Chat ID: {chat_id}")

    # Initialize Telegram
    telegram = TelegramNotifier(bot_token, chat_id)

    # Mock stock data
    mock_results = [
        {'symbol': 'RELIANCE', 'price': 2850.50, 'rsi': 65, 'score': 85},
        {'symbol': 'TCS', 'price': 3650.25, 'rsi': 62, 'score': 78},
        {'symbol': 'HDFCBANK', 'price': 1950.75, 'rsi': 58, 'score': 72},
        {'symbol': 'INFY', 'price': 2350.00, 'rsi': 55, 'score': 65},
        {'symbol': 'ICICIBANK', 'price': 980.40, 'rsi': 68, 'score': 88},
    ]

    # Send start message
    telegram.send_message("🚀 Starting NSE stock scan...")

    # Create and send results message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""🎯 *NSE Stock Scan Results*
━━━━━━━━━━━━━━━━━━━━
📅 {current_time}
📊 Stocks Found: {len(mock_results)}
━━━━━━━━━━━━━━━━━━━━

"""

    for idx, stock in enumerate(mock_results, 1):
        score_stars = '⭐' * int(stock['score'] / 20)
        message += f"""`{idx}. {stock['symbol']}`
💰 ₹{stock['price']:.0f} | RSI: {stock['rsi']:.0f}
{score_stars} Score: {stock['score']:.0f}%

"""

    message += """━━━━━━━━━━━━━━━━━━━━
*Scan Parameters:*
• RSI Range: 30-80
• Price > SMA20
• Bullish MACD
• High Volume

*⚠️ For educational purposes only*
"""

    logger.info("📤 Sending scan results to Telegram...")
    success = telegram.send_message(message)

    if success:
        # Send summary
        logger.info("📤 Sending summary to Telegram...")
        summary = f"""✅ *Scan Complete!*

*Summary:*
• Stocks Analyzed: 45
• Qualified Stocks: {len(mock_results)}
• Top Candidate: {mock_results[0]['symbol']} (Score: {mock_results[0]['score']:.0f}%)
• Scan Time: {current_time}

💡 Use these signals with your own research and risk management!
"""
        telegram.send_message(summary)

    return success


if __name__ == "__main__":
    success = test_telegram_integration()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed. Check your Telegram credentials.")
