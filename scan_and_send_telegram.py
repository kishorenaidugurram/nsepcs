#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Notification Script
Runs the stock scanner and sends results to Telegram
"""

import asyncio
import json
import sys
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import telegram
from telegram import Bot
from telegram.error import TelegramError

# Import scanner components
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import pytz
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Configuration
DEFAULT_CONFIG = {
    'min_score': 60,
    'min_volume_ratio': 0.8,
    'max_stocks': 50,
    'show_news': False,
    'liquidity_tier': 1,
    'enhancements': {
        'delivery_volume': False,
        'fno_consolidation': False,
        'breakout_pullback': False,
        'enhanced_sr': False
    },
    'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:50]  # Default to first 50
}


async def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """Send message to Telegram"""
    try:
        bot = Bot(token=bot_token)
        # Split message if too long (Telegram limit is 4096)
        for msg_chunk in [message[i:i+4000] for i in range(0, len(message), 4000)]:
            await bot.send_message(chat_id=chat_id, text=msg_chunk, parse_mode='HTML')
        return True
    except TelegramError as e:
        print(f"❌ Telegram Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_scanner(config: dict) -> list:
    """Run the stock scanner and return results"""
    scanner = ProfessionalPCSScanner()
    results = []
    total_stocks = len(config['stocks_to_scan'])

    print(f"\n🚀 Starting scan of {total_stocks} stocks...")

    for idx, symbol in enumerate(config['stocks_to_scan'], 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"[{idx}/{total_stocks}] Analyzing {clean_symbol}...", end='\r')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config.get('min_volume_ratio', 0.8)
            )
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Calculate max strength
            max_strength = max(p['strength'] for p in patterns)

            # Filter by minimum score
            if max_strength < config.get('min_score', 60):
                continue

            # Add to results
            stock_result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'max_strength': max_strength,
                'patterns': patterns,
                'pattern_count': len(patterns)
            }

            results.append(stock_result)

        except Exception as e:
            continue

    # Sort by strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)
    print(f"\n✅ Scan complete! Found {len(results)} qualifying stocks.")

    return results


def format_results_for_telegram(results: list, config: dict) -> str:
    """Format scanner results for Telegram message"""
    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')

    message = f"""
🚀 <b>NSE F&O PCS SCREENER RESULTS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ <b>Scan Time:</b> {timestamp}

📊 <b>SUMMARY</b>
• <b>Stocks Scanned:</b> {len(config['stocks_to_scan'])}
• <b>Qualifying Stocks:</b> {len(results)}
• <b>Min Score Filter:</b> {config.get('min_score', 60)}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📋 QUALIFYING STOCKS (Top 20)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Add top 20 results
    for idx, result in enumerate(results[:20], 1):
        confidence = '🟢 HIGH' if result['max_strength'] >= 85 else '🟡 MEDIUM' if result['max_strength'] >= 70 else '🔴 LOW'

        message += f"""
{idx}. <b>{result['clean_symbol']}</b>
   └─ Strength: {result['max_strength']:.0f}% | {confidence}
   └─ Price: ₹{result['current_price']:.2f}
   └─ Volume: {result['volume_ratio']:.1f}x | RSI: {result['rsi']:.0f} | ADX: {result['adx']:.0f}
   └─ Patterns: {result['pattern_count']}
"""

    if len(results) > 20:
        message += f"\n\n... and {len(results) - 20} more stocks\n"

    message += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💡 TRADE SETUP RECOMMENDATIONS:</b>
✓ Use these for Put Credit Spread (PCS) opportunities
✓ Verify technical setups before executing trades
✓ Always use proper position sizing and risk management
✓ Paper trade first to validate signals

<b>⚠️ DISCLAIMER:</b>
This is for educational purposes. Not financial advice.
Conduct your own analysis before trading.
"""

    return message


def get_user_config() -> dict:
    """Get configuration from environment variables or user input"""
    config = DEFAULT_CONFIG.copy()

    # Allow environment variable overrides
    if os.getenv('MIN_SCORE'):
        config['min_score'] = int(os.getenv('MIN_SCORE'))

    if os.getenv('MIN_VOLUME_RATIO'):
        config['min_volume_ratio'] = float(os.getenv('MIN_VOLUME_RATIO'))

    if os.getenv('MAX_STOCKS'):
        max_stocks = int(os.getenv('MAX_STOCKS'))
        config['stocks_to_scan'] = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    return config


async def main():
    """Main function"""
    # Get credentials from environment or command line
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or sys.argv[1] if len(sys.argv) > 1 else None
    chat_id = os.getenv('TELEGRAM_CHAT_ID') or sys.argv[2] if len(sys.argv) > 2 else None

    if not bot_token or not chat_id:
        print("""
❌ Missing Telegram credentials!

Usage:
  python scan_and_send_telegram.py <BOT_TOKEN> <CHAT_ID>

Or set environment variables:
  export TELEGRAM_BOT_TOKEN="your_bot_token"
  export TELEGRAM_CHAT_ID="your_chat_id"

How to get Telegram Bot Token:
1. Open Telegram and search for @BotFather
2. Send /newbot command
3. Follow instructions to create a bot
4. Copy the bot token provided

How to get Chat ID:
1. Add your bot to a chat or group
2. Send any message to the chat
3. Visit: https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
4. Find your chat_id in the response
        """)
        sys.exit(1)

    print("="*50)
    print("NSE F&O PCS SCREENER - TELEGRAM EDITION")
    print("="*50)

    # Get configuration
    config = get_user_config()
    print(f"✅ Config loaded")
    print(f"   - Min Score: {config['min_score']}%")
    print(f"   - Max Stocks to Scan: {len(config['stocks_to_scan'])}")
    print(f"   - Min Volume Ratio: {config.get('min_volume_ratio', 0.8)}")

    # Send "Starting scan" message
    await send_telegram_message(
        bot_token,
        chat_id,
        f"🚀 <b>Scanning Started</b>\n\nScanning {len(config['stocks_to_scan'])} stocks...\n⏳ This may take a few minutes..."
    )

    # Run scanner
    results = run_scanner(config)

    if not results:
        print("❌ No qualifying stocks found!")
        await send_telegram_message(
            bot_token,
            chat_id,
            "❌ <b>No qualifying stocks found</b>\n\nTry adjusting your filters and scanning again."
        )
        return

    # Format and send results
    message = format_results_for_telegram(results, config)
    print(f"📨 Sending results to Telegram...")

    success = await send_telegram_message(bot_token, chat_id, message)

    if success:
        print("✅ Results sent successfully!")

        # Send detailed stock list
        stock_list = "📑 <b>COMPLETE STOCK LIST</b>\n\n"
        stock_list += "Symbol | Strength | Price | Volume\n"
        stock_list += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for result in results:
            stock_list += f"{result['clean_symbol']} | {result['max_strength']:.0f}% | ₹{result['current_price']:.2f} | {result['volume_ratio']:.1f}x\n"

        await send_telegram_message(bot_token, chat_id, stock_list)
    else:
        print("❌ Failed to send results to Telegram")
        print("\n" + message)  # Print to console as fallback


if __name__ == "__main__":
    asyncio.run(main())
