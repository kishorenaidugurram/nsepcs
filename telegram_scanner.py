#!/usr/bin/env python3
"""
Stock Scanner Telegram Bot
Automatically scans for NSE F&O stocks meeting filter criteria and sends to Telegram
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import traceback

import pandas as pd
import requests
from requests.exceptions import RequestException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path to import scanner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from streamlit_app (extract scanner class separately)
try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE, STOCK_CATEGORIES
except ImportError:
    logger.error("Could not import from streamlit_app. Make sure streamlit_app.py is in the same directory.")
    sys.exit(1)


class TelegramStockScanner:
    def __init__(self, config_file='telegram_config.json'):
        """Initialize the scanner with Telegram integration"""
        self.config_file = config_file
        self.config = self.load_config()
        self.scanner = ProfessionalPCSScanner()
        self.results = []

    def load_config(self):
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_file):
            logger.error(f"Config file not found: {self.config_file}")
            logger.info("Please copy telegram_config.example.json to telegram_config.json and add your credentials")
            sys.exit(1)

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            # Validate required fields
            if 'telegram' not in config:
                raise ValueError("Missing 'telegram' section in config")
            if not config['telegram'].get('bot_token'):
                raise ValueError("Missing Telegram bot_token in config")
            if not config['telegram'].get('chat_id'):
                raise ValueError("Missing Telegram chat_id in config")

            logger.info("Configuration loaded successfully")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)

    def get_filters(self):
        """Extract filters from config"""
        scanner_config = self.config.get('scanner', {})

        filters = {
            'rsi_min': scanner_config.get('rsi_min', 30),
            'rsi_max': scanner_config.get('rsi_max', 70),
            'adx_min': scanner_config.get('adx_min', 20),
            'ma_support': scanner_config.get('ma_support', True),
            'ma_tolerance': scanner_config.get('ma_tolerance', 5),
            'ma_type': scanner_config.get('ma_type', 'EMA'),
            'pattern_strength_min': scanner_config.get('pattern_strength_min', 65),
            'lookback_days': scanner_config.get('lookback_days', 20),
            'volume_breakout_ratio': scanner_config.get('volume_breakout_ratio', 2.0),
            'analysis_mode': scanner_config.get('analysis_mode', 'Daily + Weekly Combined (Recommended)'),
            'pattern_filters': scanner_config.get('pattern_filters', {
                'current_day_breakout': True,
                'cup_and_handle': True,
                'flat_base': True,
            }),
            'pattern_priority': scanner_config.get('pattern_priority', 'All Patterns (Comprehensive)'),
            'enable_enhancements': scanner_config.get('enable_enhancements', True),
        }

        return filters

    def get_stock_universe(self):
        """Get stock universe to scan based on config"""
        scanner_config = self.config.get('scanner', {})
        universe_name = scanner_config.get('universe', 'Nifty 50')

        if universe_name in STOCK_CATEGORIES:
            stocks = STOCK_CATEGORIES[universe_name]
            logger.info(f"Scanning {len(stocks)} stocks from {universe_name}")
            return stocks
        else:
            logger.info(f"Scanning all {len(COMPLETE_NSE_FO_UNIVERSE)} F&O stocks")
            return COMPLETE_NSE_FO_UNIVERSE

    def scan_stocks(self):
        """Scan stocks with current filters"""
        filters = self.get_filters()
        stocks = self.get_stock_universe()

        logger.info(f"Starting scan with filters: RSI({filters['rsi_min']}-{filters['rsi_max']}), "
                   f"ADX>{filters['adx_min']}, Strength>{filters['pattern_strength_min']}%")

        self.results = []
        total_stocks = len(stocks)
        scanned_count = 0
        errors_count = 0

        for stock_symbol in stocks:
            try:
                scanned_count += 1

                # Get stock data
                data = self.scanner.get_stock_data(stock_symbol, period="3mo")
                if data is None or len(data) < 20:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, stock_symbol, filters)

                # Keep stocks that have patterns
                if patterns:
                    # Sort by strength
                    patterns = sorted(patterns, key=lambda x: x['strength'], reverse=True)

                    result = {
                        'symbol': stock_symbol,
                        'clean_symbol': stock_symbol.replace('.NS', ''),
                        'current_price': data['Close'].iloc[-1],
                        'patterns': patterns,
                        'data': data,
                        'timestamp': datetime.now()
                    }
                    self.results.append(result)
                    logger.info(f"✓ [{scanned_count}/{total_stocks}] {stock_symbol}: Found {len(patterns)} pattern(s)")
                else:
                    logger.debug(f"  [{scanned_count}/{total_stocks}] {stock_symbol}: No patterns")

            except Exception as e:
                errors_count += 1
                logger.warning(f"  [{scanned_count}/{total_stocks}] {stock_symbol}: Error - {str(e)}")

        logger.info(f"\nScan complete: {len(self.results)} stocks matched, {errors_count} errors")
        return self.results

    def send_to_telegram(self):
        """Send results to Telegram"""
        if not self.results:
            self.send_telegram_message("📊 Stock Scanner\n\n❌ No stocks matched the filter criteria today.", parse_mode="Markdown")
            return True

        bot_token = self.config['telegram']['bot_token']
        chat_id = self.config['telegram']['chat_id']
        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Create summary message
        summary_message = self._create_summary_message()

        try:
            # Send summary
            response = requests.post(
                telegram_url,
                json={
                    'chat_id': chat_id,
                    'text': summary_message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True
                },
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Telegram API error: {response.text}")
                return False

            logger.info(f"Summary sent to Telegram successfully")

            # Send individual stock details
            for result in self.results[:10]:  # Limit to first 10 to avoid spam
                detail_message = self._create_stock_message(result)
                try:
                    response = requests.post(
                        telegram_url,
                        json={
                            'chat_id': chat_id,
                            'text': detail_message,
                            'parse_mode': 'Markdown',
                            'disable_web_page_preview': True
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        logger.info(f"Sent details for {result['clean_symbol']}")
                    else:
                        logger.warning(f"Failed to send details for {result['clean_symbol']}")

                except RequestException as e:
                    logger.warning(f"Error sending stock details: {e}")

            return True

        except RequestException as e:
            logger.error(f"Telegram API request failed: {e}")
            return False

    def _create_summary_message(self):
        """Create summary message for Telegram"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = len(self.results)

        message = f"""📊 *NSE F&O Stock Scanner - {timestamp}*

✅ Matching Stocks: *{count}*

*Filter Criteria:*
• RSI: {self.config['scanner']['rsi_min']}-{self.config['scanner']['rsi_max']}
• ADX: >{self.config['scanner']['adx_min']}
• Pattern Strength: >{self.config['scanner']['pattern_strength_min']}%
• Universe: {self.config['scanner']['universe']}

"""

        # Add stock symbols
        if count > 0:
            symbols = [r['clean_symbol'] for r in self.results[:15]]
            message += "*Symbols:*\n" + ", ".join(symbols)

            if count > 15:
                message += f"\n... and {count - 15} more"

        return message

    def _create_stock_message(self, result):
        """Create detailed message for a single stock"""
        symbol = result['clean_symbol']
        price = result['current_price']
        patterns = result['patterns']

        message = f"""
🎯 *{symbol}*
💰 Price: ₹{price:.2f}

*Patterns Detected: {len(patterns)}*
"""

        for i, pattern in enumerate(patterns[:3], 1):  # Show top 3 patterns
            message += f"""
{i}. *{pattern['type']}*
   • Strength: {pattern['strength']}%
   • Confidence: {pattern.get('confidence', 'N/A')}
   • Success Rate: {pattern['success_rate']}%
   • PCS Fit: {pattern['pcs_suitability']}%
"""

        return message

    def send_telegram_message(self, message, parse_mode="Markdown"):
        """Send a single Telegram message (helper method)"""
        bot_token = self.config['telegram']['bot_token']
        chat_id = self.config['telegram']['chat_id']
        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        try:
            response = requests.post(
                telegram_url,
                json={
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': parse_mode,
                    'disable_web_page_preview': True
                },
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Message sent to Telegram")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False

        except RequestException as e:
            logger.error(f"Telegram request failed: {e}")
            return False

    def run(self):
        """Run the complete scanner and send results"""
        try:
            logger.info("=" * 60)
            logger.info("NSE F&O Stock Scanner with Telegram Integration")
            logger.info("=" * 60)

            # Run scan
            logger.info("\nStarting stock scan...")
            self.scan_stocks()

            # Send to Telegram
            logger.info("\nSending results to Telegram...")
            success = self.send_to_telegram()

            if success:
                logger.info("\n✅ Scan complete and results sent to Telegram")
                return 0
            else:
                logger.error("\n❌ Scan complete but failed to send to Telegram")
                return 1

        except Exception as e:
            logger.error(f"\n❌ Error during scan: {e}")
            logger.error(traceback.format_exc())
            return 1


def main():
    """Main entry point"""
    try:
        scanner = TelegramStockScanner()
        exit_code = scanner.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Scanner interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
