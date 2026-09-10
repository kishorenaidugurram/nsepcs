#!/usr/bin/env python3
"""
Standalone scanner for NSE F&O stocks with Telegram notifications.
Runs the scanning logic independently without Streamlit UI.
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import pytz
import requests
from io import StringIO

# Try to import telegram bot
try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: python-telegram-bot not installed. Run: pip install python-telegram-bot")

# Import the scanner class from streamlit_app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Send notifications to Telegram"""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token) if TELEGRAM_AVAILABLE else None

    async def send_message(self, message):
        """Send message to Telegram chat"""
        if not self.bot:
            logger.warning("Telegram bot not available")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("Message sent to Telegram successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_stocks_list(self, stocks, total_found, scan_date):
        """Send formatted stocks list to Telegram"""
        if not stocks:
            message = "❌ No qualifying stocks found today."
        else:
            message = f"""
📊 <b>NSE F&O PCS Scan Results</b>
📅 Date: {scan_date}
🎯 Total Qualified: {total_found}

<b>Top Stocks Meeting Criteria:</b>
"""
            for i, stock in enumerate(stocks[:15], 1):
                symbol = stock['symbol'].replace('.NS', '')
                price = stock['current_price']
                volume = stock['volume_ratio']
                strength = max(p['strength'] for p in stock['patterns']) if stock['patterns'] else 0
                patterns_count = len(stock['patterns'])

                message += f"\n{i}. <b>{symbol}</b> | ₹{price:.2f} | Vol: {volume:.1f}x | Strength: {strength:.0f}% | Patterns: {patterns_count}"

        await self.send_message(message)


def run_scanner(stock_universe, filters, max_workers=10):
    """Run the scanner on the stock universe"""

    scanner = ProfessionalPCSScanner()
    results = []

    logger.info(f"Starting scan of {len(stock_universe)} stocks with filters: {filters}")

    def scan_single_stock(symbol):
        """Scan a single stock"""
        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                return None

            weekly_data = scanner.get_weekly_stock_data(symbol, period="6mo")

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Check volume criteria
            volume_check, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                min_ratio=filters.get('min_volume_ratio', 1.0)
            )

            # Filter by RSI
            rsi_min, rsi_max = filters.get('rsi_range', (30, 70))
            if not (rsi_min <= current_rsi <= rsi_max):
                return None

            # Check if passes volume criteria
            if not volume_check and filters.get('min_volume_ratio', 1.0) > 0:
                return None

            # Detect patterns
            pattern_config = {
                'current_day_breakout': True,
                'cup_handle': True,
                'flat_base': True,
                'rectangle_bottom': True,
            }

            patterns = scanner.detect_patterns(data, symbol, {
                'pattern_strength_min': filters.get('min_strength', 50),
                'pattern_filters': pattern_config,
                'weekly_data': weekly_data
            })

            if not patterns:
                return None

            # Filter by minimum strength
            min_strength = filters.get('min_strength', 50)
            patterns = [p for p in patterns if p['strength'] >= min_strength]

            if not patterns:
                return None

            return {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_details': volume_details,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns
            }

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            return None

    # Run parallel scanning
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_single_stock, symbol): symbol
                  for symbol in stock_universe}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 10 == 0:
                logger.info(f"Progress: {completed}/{len(stock_universe)}")

            result = future.result()
            if result:
                results.append(result)

    # Sort by strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    logger.info(f"Scan complete. Found {len(results)} qualifying stocks.")
    return results


async def main():
    """Main execution"""

    # Get Telegram credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Results will not be sent to Telegram.")
        notifier = None
    else:
        notifier = TelegramNotifier(bot_token, chat_id)

    # Define scanning filters
    filters = {
        'min_strength': 60,          # Minimum pattern strength
        'min_volume_ratio': 1.0,     # Minimum volume ratio
        'rsi_range': (30, 70),       # RSI range
        'max_stocks': 208            # Max stocks to scan
    }

    logger.info("=" * 60)
    logger.info("NSE F&O PCS SCANNER - TELEGRAM NOTIFIER")
    logger.info("=" * 60)
    logger.info(f"Scan Date: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}")

    # Run the scanner
    try:
        results = run_scanner(COMPLETE_NSE_FO_UNIVERSE, filters, max_workers=15)

        # Format results
        logger.info(f"\n✅ SCAN RESULTS: Found {len(results)} stocks\n")

        if results:
            print("\n" + "=" * 80)
            print("QUALIFYING STOCKS - MEETING FILTER CRITERIA")
            print("=" * 80)
            for i, stock in enumerate(results[:20], 1):
                max_strength = max(p['strength'] for p in stock['patterns'])
                print(f"{i:2d}. {stock['symbol']:<12} | ₹{stock['current_price']:>8.2f} | Vol: {stock['volume_ratio']:>4.1f}x | RSI: {stock['rsi']:>5.1f} | Strength: {max_strength:>5.0f}%")
            print("=" * 80)

        # Send to Telegram
        if notifier:
            scan_date = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')
            await notifier.send_stocks_list(results, len(results), scan_date)
        else:
            logger.info("Telegram notifier not configured. Results saved locally.")

        # Save results to CSV
        if results:
            csv_data = []
            for stock in results:
                max_strength = max(p['strength'] for p in stock['patterns'])
                pattern_types = ', '.join([p['type'] for p in stock['patterns']])
                csv_data.append({
                    'Symbol': stock['symbol'].replace('.NS', ''),
                    'Price': f"{stock['current_price']:.2f}",
                    'Volume': f"{stock['volume_ratio']:.2f}x",
                    'RSI': f"{stock['rsi']:.1f}",
                    'ADX': f"{stock['adx']:.1f}",
                    'Strength': f"{max_strength:.0f}%",
                    'Patterns': pattern_types
                })

            df = pd.DataFrame(csv_data)
            csv_file = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_file, index=False)
            logger.info(f"Results saved to {csv_file}")

        return True

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        if notifier:
            await notifier.send_message(f"❌ Scanner Error: {str(e)}")
        return False


if __name__ == "__main__":
    if TELEGRAM_AVAILABLE:
        asyncio.run(main())
    else:
        # Run without telegram
        print("Running scanner without Telegram notifications...")
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
