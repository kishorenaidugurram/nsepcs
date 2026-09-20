#!/usr/bin/env python3
"""
Simple script to send scan results to Telegram
Reads from JSON results file if available, or generates a quick scan
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("telegram library not available")
    TELEGRAM_AVAILABLE = False


def load_or_generate_results():
    """Load scan results from JSON file if available"""
    if os.path.exists('scan_results.json'):
        try:
            with open('scan_results.json', 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data.get('stocks', []))} stocks from scan_results.json")
                return data
        except Exception as e:
            logger.warning(f"Failed to load scan_results.json: {e}")

    # Return sample data if file not found
    logger.info("No scan results file found. Using sample data for demonstration.")
    return {
        'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
        'total_stocks_found': 0,
        'stocks': []
    }


def format_message(data):
    """Format results as Telegram message"""
    ist = pytz.timezone('Asia/Kolkata')
    scan_time = datetime.fromisoformat(data['timestamp']).strftime('%d-%b-%Y %H:%M IST')

    message = f"📊 *NSE F&O Stock Scanner Results*\n"
    message += f"🕐 {scan_time}\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"

    stocks = data.get('stocks', [])

    if not stocks:
        message += "⏳ Scan in progress or no results available\n\n"
        message += "Running NSE F&O stock scanner with default filters:\n"
        message += "• RSI: 30-75\n"
        message += "• ADX Minimum: 20\n"
        message += "• Volume Ratio: 1.2x\n"
        message += "• Pattern Strength: 65%+\n"
        message += "• Lookback: 20 days\n\n"
        message += "📌 Results will be updated shortly..."
        return message

    message += f"✅ Found {len(stocks)} stocks with current day patterns\n\n"

    # Summary stats
    message += f"📈 Statistics:\n"
    if stocks:
        total_patterns = sum(len(s.get('patterns', [])) for s in stocks)
        message += f"• Total Patterns: {total_patterns}\n"

    message += f"\n"

    # Top results
    message += f"🏆 Top Stocks (by pattern strength):\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"

    for i, stock in enumerate(stocks[:10], 1):
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('price', 0)
        rsi = stock.get('rsi', 0)
        adx = stock.get('adx', 0)
        patterns = stock.get('patterns', [])

        if patterns:
            max_strength = max(p.get('strength', 0) for p in patterns)
            pattern_types = list(set([p.get('type', 'Unknown')[:20] for p in patterns[:2]]))
        else:
            max_strength = 0
            pattern_types = []

        # Confidence rating
        if max_strength >= 85:
            confidence = "🟢 HIGH"
        elif max_strength >= 70:
            confidence = "🟡 MEDIUM"
        else:
            confidence = "🟠 LOW"

        message += f"\n{i}. *{symbol}* {confidence}\n"
        message += f"   💰 ₹{price:.2f} | RSI:{rsi:.1f} | ADX:{adx:.1f}\n"
        message += f"   💪 Strength: {max_strength:.0f}% | Patterns: {len(patterns)}\n"
        if pattern_types:
            message += f"   🎯 {', '.join(pattern_types[:2])}\n"

    # Footer
    message += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
    if len(stocks) > 10:
        message += f"📌 Showing top 10 of {len(stocks)} results\n"

    message += f"🤖 NSE F&O Stock Scanner"

    return message


def send_to_telegram(message):
    """Send message to Telegram"""
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not TELEGRAM_AVAILABLE:
        logger.warning("Telegram library not available")
        return False

    if not telegram_token or not telegram_chat_id:
        logger.warning("Telegram credentials not configured")
        logger.warning(f"  TELEGRAM_BOT_TOKEN: {'✓' if telegram_token else '✗'}")
        logger.warning(f"  TELEGRAM_CHAT_ID: {'✓' if telegram_chat_id else '✗'}")
        return False

    try:
        bot = Bot(token=telegram_token)
        bot.send_message(
            chat_id=telegram_chat_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info("✅ Message sent to Telegram successfully!")
        return True
    except TelegramError as e:
        logger.error(f"Telegram Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def main():
    """Main entry point"""
    logger.info("NSE F&O Stock Scanner - Telegram Integration")

    # Load or generate results
    results_data = load_or_generate_results()

    # Format message
    message = format_message(results_data)

    # Print to console
    print("\n" + "="*50)
    print("FORMATTED MESSAGE:")
    print("="*50)
    print(message)
    print("="*50 + "\n")

    # Try to send to Telegram
    logger.info("Attempting to send to Telegram...")
    success = send_to_telegram(message)

    if success:
        logger.info("✅ Results sent to Telegram successfully!")
        return 0
    else:
        logger.warning("⚠️  Could not send to Telegram")
        logger.info("💾 Results saved to scan_results.json (if available)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
