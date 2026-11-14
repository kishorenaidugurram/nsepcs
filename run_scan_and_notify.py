#!/usr/bin/env python3
"""
NSE PCS Scanner - Run Analysis and Send to Telegram
Designed for scheduled execution (cron, airflow, etc.)
"""

import os
import sys
import json
from datetime import datetime
import pytz
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import ta
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    logger.info("Installing required packages...")
    os.system("pip install -q yfinance pandas numpy ta python-telegram-bot")
    sys.exit(1)

# Import scanner from streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)


class ScheduledPCSScanner:
    """Non-UI version of PCS Scanner for automated execution"""

    def __init__(self, telegram_token=None, telegram_chat_id=None):
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

        # Get Telegram credentials from environment or parameters
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if self.telegram_token and self.telegram_chat_id:
            self.bot = Bot(token=self.telegram_token)
        else:
            self.bot = None
            logger.warning("Telegram credentials not configured. Results will not be sent to Telegram.")

    def run_scan(self, stocks=None, config=None):
        """
        Run stock scan with default configuration

        Args:
            stocks: List of stock symbols to scan. Default: F&O universe
            config: Analysis configuration. Default: Production defaults

        Returns:
            List of qualifying stocks with details
        """
        if stocks is None:
            stocks = COMPLETE_NSE_FO_UNIVERSE

        if config is None:
            config = self._get_default_config()

        logger.info(f"Starting scan of {len(stocks)} stocks")
        logger.info(f"Configuration: RSI({config['rsi_min']}-{config['rsi_max']}), " +
                   f"ADX(>{config['adx_min']}), Pattern Strength(>{config['pattern_strength_min']})")

        results = []

        for idx, symbol in enumerate(stocks, 1):
            try:
                clean_symbol = symbol.replace('.NS', '').replace('^', '')

                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    continue

                # Check volume criteria
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, config['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, config)

                # Get weekly validation if enabled
                weekly_validation = None
                if config.get('enable_weekly_validation', True):
                    weekly_data = self.scanner.get_weekly_stock_data(symbol)
                    if patterns:
                        first_pattern = patterns[0]
                        weekly_validation = self.scanner.validate_weekly_strength(
                            data, weekly_data, first_pattern.get('pattern_type', 'Unknown')
                        )

                # Filter patterns by strength
                qualifying_patterns = [
                    p for p in patterns
                    if p.get('strength', 0) >= config['pattern_strength_min']
                ]

                if qualifying_patterns:
                    best_pattern = qualifying_patterns[0]

                    # Get current price
                    current_price = data['Close'].iloc[-1]

                    result = {
                        'symbol': clean_symbol,
                        'price': current_price,
                        'pattern': best_pattern.get('pattern_type', 'Unknown'),
                        'strength': best_pattern.get('strength', 0),
                        'volume_ratio': volume_ratio,
                        'rsi': data['RSI'].iloc[-1],
                        'adx': data['ADX'].iloc[-1],
                        'timestamp': datetime.now(self.ist).isoformat(),
                        'confidence': self._get_confidence(best_pattern, weekly_validation)
                    }

                    results.append(result)

                    if len(results) % 10 == 0:
                        logger.info(f"Processed {idx}/{len(stocks)} stocks, Found {len(results)} qualifying")

            except Exception as e:
                logger.debug(f"Error processing {symbol}: {str(e)}")
                continue

        logger.info(f"Scan complete: Found {len(results)} qualifying stocks")
        return results

    def _get_default_config(self):
        """Get default production configuration"""
        return {
            'rsi_min': 30,
            'rsi_max': 75,
            'adx_min': 20,
            'ma_support': True,
            'ma_type': 'EMA',
            'ma_tolerance': 3,
            'min_volume_ratio': 1.2,
            'volume_breakout_ratio': 2.0,
            'lookback_days': 20,
            'pattern_strength_min': 65,
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'pattern_filters': {
                'current_day_breakout': True,
                'cup_and_handle': True,
                'flat_base': True,
                'bump_and_run': True,
                'rectangle_bottom': True,
                'rectangle_top': True,
                'head_shoulders_bottom': True,
                'double_bottom': True,
                'three_rising_valleys': True,
                'rounding_bottom': True,
                'rounding_top_upside': True,
                'inverted_scallop': True,
            }
        }

    def _get_confidence(self, pattern, weekly_validation=None):
        """Determine confidence level based on pattern and weekly validation"""
        confidence_score = 0

        # Pattern strength contribution (0-40)
        strength = pattern.get('strength', 0)
        if strength >= 85:
            confidence_score += 40
        elif strength >= 75:
            confidence_score += 30
        elif strength >= 65:
            confidence_score += 20

        # Weekly validation bonus (0-30)
        if weekly_validation:
            if weekly_validation.get('weekly_validation', False):
                bonus = weekly_validation.get('weekly_strength_bonus', 0)
                if bonus >= 35:
                    confidence_score += 30
                elif bonus >= 25:
                    confidence_score += 20
                elif bonus >= 15:
                    confidence_score += 10

        # Volume confirmation (0-20)
        volume_ratio = pattern.get('volume_ratio', 1.0)
        if volume_ratio >= 3:
            confidence_score += 20
        elif volume_ratio >= 2:
            confidence_score += 15
        elif volume_ratio >= 1.2:
            confidence_score += 10

        # ADX trend strength (0-10)
        adx = pattern.get('adx', 0)
        if adx >= 30:
            confidence_score += 10
        elif adx >= 25:
            confidence_score += 7
        elif adx >= 20:
            confidence_score += 5

        if confidence_score >= 80:
            return "HIGH"
        elif confidence_score >= 65:
            return "MEDIUM"
        else:
            return "LOW"

    def send_to_telegram(self, results, limit=20):
        """Send qualifying stocks to Telegram"""
        if not self.bot or not results:
            if not self.bot:
                logger.warning("Telegram not configured. Skipping notification.")
            else:
                logger.info("No qualifying stocks to send.")
            return False

        # Sort by strength descending
        sorted_results = sorted(results, key=lambda x: x['strength'], reverse=True)[:limit]

        try:
            # Create message
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

            message = f"🚀 **NSE PCS Scanner Results** - {timestamp}\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"📊 Found {len(sorted_results)} qualifying stocks\n\n"

            for idx, stock in enumerate(sorted_results, 1):
                confidence_emoji = "🟢" if stock['confidence'] == "HIGH" else "🟡" if stock['confidence'] == "MEDIUM" else "🔴"

                message += f"{idx}. **{stock['symbol']}** {confidence_emoji}\n"
                message += f"   Price: ₹{stock['price']:.2f}\n"
                message += f"   Pattern: {stock['pattern']} ({stock['strength']:.0f}/100)\n"
                message += f"   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
                message += f"   Volume Ratio: {stock['volume_ratio']:.2f}x\n\n"

            message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "⚠️ **Disclaimer**: This is for educational purposes only.\n"
            message += "Always do your own research and consult financial advisors.\n"

            # Send message
            logger.info(f"Sending {len(sorted_results)} stocks to Telegram...")
            self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )

            logger.info("✅ Results sent to Telegram successfully")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def save_results_to_csv(self, results, filename=None):
        """Save results to CSV file"""
        if not results:
            logger.info("No results to save")
            return None

        if filename is None:
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/pcs_scan_results_{timestamp}.csv"

        try:
            df = pd.DataFrame(results)
            df.to_csv(filename, index=False)
            logger.info(f"Results saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("NSE PCS Scanner - Scheduled Execution")
    logger.info("=" * 60)

    try:
        # Initialize scanner with Telegram
        scanner = ScheduledPCSScanner()

        # Run scan
        results = scanner.run_scan()

        if not results:
            logger.warning("No qualifying stocks found in this scan")
        else:
            logger.info(f"Found {len(results)} qualifying stocks")

            # Save results
            csv_file = scanner.save_results_to_csv(results)

            # Send to Telegram
            scanner.send_to_telegram(results)

            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("TOP 5 QUALIFYING STOCKS:")
            logger.info("=" * 60)

            top_stocks = sorted(results, key=lambda x: x['strength'], reverse=True)[:5]
            for idx, stock in enumerate(top_stocks, 1):
                logger.info(f"{idx}. {stock['symbol']} - {stock['pattern']} "
                           f"(Strength: {stock['strength']:.0f}/100, Confidence: {stock['confidence']})")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Scan completed successfully")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
