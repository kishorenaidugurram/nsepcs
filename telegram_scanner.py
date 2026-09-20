#!/usr/bin/env python3
"""
NSE F&O Stock Scanner with Telegram Integration
Runs scanner with default filters and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pytz

# Import core dependencies
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Telegram bot
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("telegram library not available. Install with: pip install python-telegram-bot")

# Import scanner class from streamlit app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached,
    fetch_weekly_data_cached
)


class TelegramStockScanner:
    """Scanner that runs and sends results to Telegram"""

    def __init__(self, telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
        """Initialize scanner with optional Telegram credentials"""
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

        # Get Telegram credentials from environment or parameters
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')

        self.telegram_bot = None
        if TELEGRAM_AVAILABLE and self.telegram_token and self.telegram_chat_id:
            try:
                self.telegram_bot = Bot(token=self.telegram_token)
                logger.info("Telegram bot initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Telegram bot: {e}")

        self.results = []

    def run_scan(self,
                 stocks_to_scan: List[str] = None,
                 rsi_min: int = 30,
                 rsi_max: int = 75,
                 adx_min: int = 20,
                 ma_support: bool = True,
                 ma_type: str = 'EMA',
                 ma_tolerance: float = 3,
                 min_volume_ratio: float = 1.2,
                 pattern_strength_min: int = 65,
                 lookback_days: int = 20) -> List[Dict]:
        """
        Run the scanner with specified filter criteria

        Args:
            stocks_to_scan: List of stock symbols to scan
            rsi_min: Minimum RSI value
            rsi_max: Maximum RSI value
            adx_min: Minimum ADX value
            ma_support: Whether to check moving average support
            ma_type: Type of moving average (EMA or SMA)
            ma_tolerance: Tolerance percentage for moving average
            min_volume_ratio: Minimum volume ratio
            pattern_strength_min: Minimum pattern strength (0-100)
            lookback_days: Number of days to look back for consolidation

        Returns:
            List of stocks meeting the criteria
        """
        if stocks_to_scan is None:
            stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE

        # Create config for scanner
        config = {
            'stocks_to_scan': stocks_to_scan,
            'rsi_min': rsi_min,
            'rsi_max': rsi_max,
            'adx_min': adx_min,
            'ma_support': ma_support,
            'ma_type': ma_type,
            'ma_tolerance': ma_tolerance,
            'min_volume_ratio': min_volume_ratio,
            'volume_breakout_ratio': 2.0,
            'lookback_days': lookback_days,
            'pattern_strength_min': pattern_strength_min,
            'pattern_filters': {
                'current_day_breakout': True,
                'cup_and_handle': True,
                'flat_base': True,
                'bump_and_run': True,
                'rectangle_bottom': True,
                'rectangle_top': False,
                'head_shoulders_bottom': True,
                'double_bottom': True,
                'three_rising_valleys': True,
                'rounding_bottom': True,
                'rounding_top_upside': True,
                'inverted_scallop': True,
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'show_charts': False,
            'show_news': False,
            'export_results': False,
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False
            }
        }

        logger.info(f"Starting scan of {len(stocks_to_scan)} stocks with default filters...")

        results = []
        total_stocks = len(stocks_to_scan)

        for i, symbol in enumerate(stocks_to_scan):
            progress = (i + 1) / total_stocks * 100
            clean_symbol = symbol.replace('.NS', '').replace('^', '')

            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {clean_symbol} ({i+1}/{total_stocks}) - {progress:.1f}%")

            try:
                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    continue

                # Check volume
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, config['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Create result
                stock_result = {
                    'symbol': symbol,
                    'clean_symbol': clean_symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data,
                    'timestamp': datetime.now(self.ist).isoformat()
                }

                results.append(stock_result)

            except Exception as e:
                logger.debug(f"Error scanning {clean_symbol}: {str(e)}")
                continue

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)
        self.results = results

        logger.info(f"Scan complete! Found {len(results)} stocks meeting criteria")
        return results

    def format_results_for_telegram(self) -> str:
        """Format scan results as Telegram message"""
        if not self.results:
            return "❌ No stocks found matching the criteria"

        ist = pytz.timezone('Asia/Kolkata')
        scan_time = datetime.now(ist).strftime('%d-%b-%Y %H:%M IST')

        message = f"📊 *NSE F&O Stock Scanner Results*\n"
        message += f"🕐 {scan_time}\n"
        message += f"━━━━━━━━━━━━━━━━━\n\n"

        message += f"✅ Found {len(self.results)} stocks with current day patterns\n\n"

        # Summary stats
        total_patterns = sum(len(r['patterns']) for r in self.results)
        avg_strength = np.mean([p['strength'] for r in self.results for p in r['patterns']])
        current_day_count = sum(1 for r in self.results for p in r['patterns']
                               if 'Current Day' in p['type'])

        message += f"📈 Statistics:\n"
        message += f"• Total Patterns: {total_patterns}\n"
        message += f"• Avg Strength: {avg_strength:.1f}%\n"
        message += f"• Current Day Breakouts: {current_day_count}\n\n"

        # Top 10 results
        message += f"🏆 Top Stocks (by pattern strength):\n"
        message += "━━━━━━━━━━━━━━━━━\n"

        for i, result in enumerate(self.results[:10], 1):
            symbol = result['clean_symbol']
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']

            max_strength = max(p['strength'] for p in result['patterns'])
            pattern_types = [p['type'] for p in result['patterns']]

            # Confidence rating
            if max_strength >= 85:
                confidence = "🟢 HIGH"
            elif max_strength >= 70:
                confidence = "🟡 MEDIUM"
            else:
                confidence = "🟠 LOW"

            message += f"\n{i}. *{symbol}* {confidence}\n"
            message += f"   💰 ₹{price:.2f} | 📊 RSI:{rsi:.1f} | ADX:{adx:.1f}\n"
            message += f"   💪 Strength: {max_strength:.0f}% | Patterns: {len(result['patterns'])}\n"
            message += f"   🎯 {', '.join(set(pattern_types[:2]))}\n"

        # Footer
        message += f"\n━━━━━━━━━━━━━━━━━\n"
        if len(self.results) > 10:
            message += f"📌 Showing top 10 of {len(self.results)} results\n"

        message += f"🤖 Generated by NSE F&O Scanner"

        return message

    def send_to_telegram(self) -> bool:
        """Send scan results to Telegram"""
        if not self.telegram_bot or not self.telegram_chat_id:
            logger.warning("Telegram credentials not configured. Cannot send message.")
            return False

        try:
            message = self.format_results_for_telegram()
            self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("Results sent to Telegram successfully")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False

    def save_results_to_file(self, filename: str = "scan_results.json") -> str:
        """Save results to JSON file"""
        output_data = {
            'timestamp': datetime.now(self.ist).isoformat(),
            'total_stocks_found': len(self.results),
            'stocks': []
        }

        for result in self.results:
            output_data['stocks'].append({
                'symbol': result['clean_symbol'],
                'price': float(result['current_price']),
                'rsi': float(result['rsi']),
                'adx': float(result['adx']),
                'volume_ratio': float(result['volume_ratio']),
                'patterns': [
                    {
                        'type': p['type'],
                        'strength': float(p['strength']),
                        'confidence': p.get('confidence', 'MEDIUM')
                    }
                    for p in result['patterns']
                ]
            })

        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Results saved to {filename}")
        return filename

    def print_results(self):
        """Print results to console"""
        print("\n" + "="*70)
        print(f"NSE F&O STOCK SCANNER RESULTS")
        print(f"Scan Time: {datetime.now(self.ist).strftime('%d-%b-%Y %H:%M IST')}")
        print("="*70)

        if not self.results:
            print("\n❌ No stocks found matching the criteria")
            return

        print(f"\n✅ Found {len(self.results)} stocks\n")

        # Summary
        total_patterns = sum(len(r['patterns']) for r in self.results)
        avg_strength = np.mean([p['strength'] for r in self.results for p in r['patterns']])

        print(f"📊 Statistics:")
        print(f"  • Total Patterns: {total_patterns}")
        print(f"  • Avg Strength: {avg_strength:.1f}%")
        print()

        # Top results
        print("🏆 Top 10 Stocks by Pattern Strength:\n")
        print(f"{'#':<3} {'Symbol':<8} {'Price':<10} {'RSI':<7} {'ADX':<7} {'Vol.Ratio':<10} {'Strength':<10} {'Patterns':<30}")
        print("-" * 90)

        for i, result in enumerate(self.results[:10], 1):
            symbol = result['clean_symbol']
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']
            vol_ratio = result['volume_ratio']

            max_strength = max(p['strength'] for p in result['patterns'])
            pattern_types = ', '.join(set([p['type'] for p in result['patterns'][:2]]))

            print(f"{i:<3} {symbol:<8} ₹{price:<9.2f} {rsi:<7.1f} {adx:<7.1f} {vol_ratio:<10.1f}x {max_strength:<10.0f}% {pattern_types:<30}")

        print("-" * 90)
        if len(self.results) > 10:
            print(f"\nShowing top 10 of {len(self.results)} results")

        print("\n" + "="*70 + "\n")


def main():
    """Main entry point"""
    logger.info("Starting NSE F&O Stock Scanner with Telegram Integration")

    # Get Telegram credentials from environment
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    # Initialize scanner
    scanner = TelegramStockScanner(telegram_token, telegram_chat_id)

    # Run scan with default criteria
    logger.info("Running scan with default filter criteria...")
    results = scanner.run_scan(
        stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE,
        rsi_min=30,
        rsi_max=75,
        adx_min=20,
        ma_support=True,
        ma_type='EMA',
        ma_tolerance=3,
        min_volume_ratio=1.2,
        pattern_strength_min=65,
        lookback_days=20
    )

    # Print results
    scanner.print_results()

    # Save to file
    scanner.save_results_to_file()

    # Send to Telegram
    if scanner.telegram_bot and scanner.telegram_chat_id:
        logger.info("Sending results to Telegram...")
        success = scanner.send_to_telegram()
        if success:
            logger.info("✅ Scan results sent to Telegram successfully!")
        else:
            logger.warning("⚠️  Failed to send to Telegram, but results are saved locally")
    else:
        if not TELEGRAM_AVAILABLE:
            logger.warning("⚠️  Telegram library not available. Install with: pip install python-telegram-bot")
        if not telegram_token:
            logger.warning("⚠️  TELEGRAM_BOT_TOKEN environment variable not set")
        if not telegram_chat_id:
            logger.warning("⚠️  TELEGRAM_CHAT_ID environment variable not set")
        logger.info("Results saved to scan_results.json")

    return len(results)


if __name__ == "__main__":
    stock_count = main()
    sys.exit(0 if stock_count > 0 else 1)
