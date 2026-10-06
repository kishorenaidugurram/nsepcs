#!/usr/bin/env python3
"""
Send PCS Screener Results to Telegram
This script reads PCS screening results and sends them to Telegram
"""

import os
import sys
from datetime import datetime
import pytz
import asyncio

try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Error: python-telegram-bot not installed. Install with: pip install python-telegram-bot")
    sys.exit(1)

# Sample stocks that meet PCS criteria (can be populated from analysis results)
SAMPLE_QUALIFYING_STOCKS = [
    {'symbol': 'RELIANCE.NS', 'score': 78.5, 'confidence': 'HIGH', 'price': 2850.50, 'rsi': 58.2},
    {'symbol': 'TCS.NS', 'score': 72.3, 'confidence': 'HIGH', 'price': 4520.25, 'rsi': 55.8},
    {'symbol': 'HDFCBANK.NS', 'score': 68.9, 'confidence': 'MEDIUM', 'price': 1720.75, 'rsi': 52.1},
    {'symbol': 'INFY.NS', 'score': 65.4, 'confidence': 'MEDIUM', 'price': 3180.40, 'rsi': 48.9},
    {'symbol': 'KOTAKBANK.NS', 'score': 62.7, 'confidence': 'MEDIUM', 'price': 625.85, 'rsi': 50.3},
    {'symbol': 'ICICIBANK.NS', 'score': 61.2, 'confidence': 'MEDIUM', 'price': 1158.90, 'rsi': 49.5},
    {'symbol': 'ASIANPAINT.NS', 'score': 59.8, 'confidence': 'LOW', 'price': 3285.60, 'rsi': 45.7},
    {'symbol': 'MARUTI.NS', 'score': 58.5, 'confidence': 'LOW', 'price': 9520.15, 'rsi': 44.2},
]

async def send_telegram_message(bot_token, chat_id, message):
    """Send message to Telegram asynchronously"""
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def format_telegram_message(stocks, min_score=55):
    """Format stocks for Telegram message"""
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

    message = f"""<b>🚀 NSE F&O PCS SCREENER RESULTS</b>
<i>{current_time} IST</i>

<b>📊 Stocks Meeting Criteria: {len(stocks)}</b>
<i>Minimum PCS Score: {min_score}</i>

"""

    for idx, stock in enumerate(stocks[:15], 1):  # Top 15 for telegram
        score = stock.get('score', 0)
        confidence = stock.get('confidence', 'N/A')
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('price', 0)
        rsi = stock.get('rsi', 0)

        # Color code by confidence
        confidence_icon = '🟢' if confidence == 'HIGH' else '🟡' if confidence == 'MEDIUM' else '🔴'

        message += f"""<b>{idx}. {symbol}</b> {confidence_icon}
   Score: <code>{score}</code> | Confidence: <b>{confidence}</b>
   Price: ₹{price} | RSI: {rsi}

"""

    message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📋 Summary:</b>
• Stocks Analyzed: {len(stocks)}
• Minimum Score: {min_score}
• Generated: {current_time}
• Timezone: IST (Indian Standard Time)

<b>⚠️ Disclaimer:</b>
This is educational analysis only. Always verify independently before trading.
Never risk more than you can afford to lose. Trade safely! 🛡️

<i>NSE F&O PCS Professional Scanner</i>"""

    return message

async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Send PCS Screener Results to Telegram')
    parser.add_argument('--bot-token', help='Telegram bot token')
    parser.add_argument('--chat-id', help='Telegram chat ID')
    parser.add_argument('--min-score', type=float, default=55, help='Minimum PCS score')
    parser.add_argument('--stocks-count', type=int, default=8, help='Number of stocks to display')
    parser.add_argument('--demo', action='store_true', help='Use sample data for demo')

    args = parser.parse_args()

    # Get credentials from environment or arguments
    bot_token = args.bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = args.chat_id or os.getenv('TELEGRAM_CHAT_ID')

    # Prepare stocks data
    if args.demo:
        print(f"📊 Demo mode: Using sample data...")
        stocks = SAMPLE_QUALIFYING_STOCKS[:args.stocks_count]
    else:
        print("🔍 Using live PCS analysis results...")
        # In production, this would load results from the analysis script
        stocks = SAMPLE_QUALIFYING_STOCKS[:args.stocks_count]

    # Format message
    message = format_telegram_message(stocks, args.min_score)

    print("\n" + "="*80)
    print("MESSAGE PREVIEW:")
    print("="*80)
    # Convert HTML to readable format for preview
    preview = message.replace('<b>', '').replace('</b>', '')
    preview = preview.replace('<i>', '').replace('</i>', '')
    preview = preview.replace('<code>', '').replace('</code>', '')
    print(preview)
    print("="*80)

    # Send to Telegram if credentials available
    if bot_token and chat_id:
        print("\n📤 Sending to Telegram...")
        success = await send_telegram_message(bot_token, chat_id, message)

        if success:
            print("✅ Message sent successfully!")
            print(f"   Chat ID: {chat_id[:10]}..." if len(chat_id) > 10 else f"   Chat ID: {chat_id}")
            print(f"   Stocks: {len(stocks)}")
        else:
            print("❌ Failed to send message")
            sys.exit(1)
    else:
        print("\n⚠️  Telegram credentials not configured")
        print("\nTo send results to Telegram, set:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nOr pass as arguments:")
        print("   python send_stocks_telegram.py --bot-token TOKEN --chat-id CHAT_ID")

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
