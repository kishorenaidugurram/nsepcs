#!/usr/bin/env python3
"""
Telegram NSE F&O PCS Scanner
Runs the PCS analysis and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import pytz
import logging
from typing import List, Dict, Optional

# Add current directory to path to import streamlit_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE
)

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
    logger.warning("python-telegram-bot not installed. Install with: pip install python-telegram-bot")


class TelegramPCSScanner:
    """Run PCS analysis and send results to Telegram"""

    def __init__(self, telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
        """Initialize the scanner with Telegram credentials"""
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.scanner = ProfessionalPCSScanner()

        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning(
                "Telegram credentials not provided. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID "
                "environment variables to send results to Telegram."
            )
            self.telegram_bot = None
        elif TELEGRAM_AVAILABLE:
            try:
                self.telegram_bot = Bot(token=self.telegram_token)
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.telegram_bot = None
        else:
            self.telegram_bot = None

    def get_default_config(self) -> Dict:
        """Get default filter configuration for scanning"""
        return {
            'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,
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
            },
            'pattern_priority': 'PCS Optimized (>90% suitability)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'show_charts': False,
            'show_news': False,
            'export_results': False,
            'stocks_limit': len(COMPLETE_NSE_FO_UNIVERSE),
            'enhancements': {
                'delivery_volume': True,
                'fno_consolidation': True,
                'breakout_pullback': True,
                'enhanced_sr': True,
            }
        }

    def run_analysis(self, config: Optional[Dict] = None, max_stocks: int = 50) -> List[Dict]:
        """
        Run the PCS analysis with given configuration

        Args:
            config: Configuration dictionary. If None, uses default config.
            max_stocks: Maximum number of stocks to scan

        Returns:
            List of results matching filter criteria
        """
        if config is None:
            config = self.get_default_config()

        config['stocks_to_scan'] = config['stocks_to_scan'][:max_stocks]

        logger.info(f"Starting analysis on {len(config['stocks_to_scan'])} stocks...")
        results = []

        for i, symbol in enumerate(config['stocks_to_scan']):
            try:
                clean_symbol = symbol.replace('.NS', '').replace('^', '')
                logger.info(f"Analyzing {clean_symbol} ({i+1}/{len(config['stocks_to_scan'])})")

                # Get recent data focused on current day
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    logger.debug(f"Skipping {clean_symbol}: insufficient data")
                    continue

                # Check volume (current day focused)
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, config['min_volume_ratio']
                )
                if not volume_ok:
                    logger.debug(f"Skipping {clean_symbol}: volume criteria not met")
                    continue

                # Detect patterns (current day confirmation)
                patterns = self.scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    logger.debug(f"Skipping {clean_symbol}: no patterns detected")
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Create the stock result
                stock_result = {
                    'symbol': symbol,
                    'clean_symbol': clean_symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data
                }

                results.append(stock_result)
                logger.info(f"✓ {clean_symbol} - Found {len(patterns)} pattern(s)")

            except Exception as e:
                logger.error(f"Error analyzing {clean_symbol}: {str(e)}")
                continue

        # Sort by pattern strength
        if results:
            results.sort(
                key=lambda x: max(p.get('strength', 0) for p in x['patterns']),
                reverse=True
            )

        logger.info(f"Analysis complete. Found {len(results)} stocks meeting criteria.")
        return results

    def format_results_for_telegram(self, results: List[Dict]) -> str:
        """
        Format analysis results as a Telegram message

        Args:
            results: List of analysis results

        Returns:
            Formatted message string
        """
        if not results:
            return "No stocks found matching the filter criteria today."

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

        message = f"📊 *NSE F&O PCS Scanner Results*\n"
        message += f"🕐 {current_time}\n\n"
        message += f"🎯 Found *{len(results)}* stocks matching criteria\n"
        message += "=" * 50 + "\n\n"

        for i, result in enumerate(results[:20], 1):  # Limit to 20 results
            symbol = result['clean_symbol']
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']
            volume = result['volume_ratio']

            # Get best pattern
            best_pattern = max(result['patterns'], key=lambda p: p.get('strength', 0))
            pattern_type = best_pattern.get('type', 'Unknown')
            strength = best_pattern.get('strength', 0)
            confidence = best_pattern.get('confidence', 'LOW')

            # Confidence emoji
            conf_emoji = "🟢" if confidence == "HIGH" else "🟡" if confidence == "MEDIUM" else "🔴"

            message += f"{i}. *{symbol}*\n"
            message += f"   💰 Price: ₹{price:.2f}\n"
            message += f"   📈 RSI: {rsi:.1f} | ADX: {adx:.1f} | Vol: {volume:.2f}x\n"
            message += f"   {conf_emoji} {pattern_type} - Strength: {strength:.0f}%\n"
            message += f"   ({len(result['patterns'])} pattern(s) detected)\n\n"

        if len(results) > 20:
            message += f"... and {len(results) - 20} more stocks\n\n"

        message += "=" * 50 + "\n"
        message += "✅ *Trade Smart. Trade Safe. Trade Profitably.*\n"

        return message

    async def send_to_telegram(self, message: str) -> bool:
        """
        Send message to Telegram

        Args:
            message: Message text to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.telegram_bot:
            logger.error("Telegram bot not configured. Cannot send message.")
            return False

        try:
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("Message sent to Telegram successfully!")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False

    def send_to_telegram_sync(self, message: str) -> bool:
        """
        Send message to Telegram (synchronous wrapper)

        Args:
            message: Message text to send

        Returns:
            True if sent successfully, False otherwise
        """
        import asyncio

        if not self.telegram_bot:
            logger.error("Telegram bot not configured. Cannot send message.")
            return False

        try:
            asyncio.run(self.send_to_telegram(message))
            return True
        except Exception as e:
            logger.error(f"Error in async send: {e}")
            return False

    def run(self, max_stocks: int = 50, config: Optional[Dict] = None) -> bool:
        """
        Run the complete analysis and send to Telegram

        Args:
            max_stocks: Maximum number of stocks to analyze
            config: Optional custom configuration

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting Telegram PCS Scanner...")

        # Run analysis
        results = self.run_analysis(config=config, max_stocks=max_stocks)

        # Format results
        message = self.format_results_for_telegram(results)

        # Print to console
        print("\n" + "=" * 60)
        print(message)
        print("=" * 60 + "\n")

        # Send to Telegram if available
        if self.telegram_bot:
            logger.info("Sending results to Telegram...")
            success = self.send_to_telegram_sync(message)
            return success
        else:
            logger.warning("Telegram not configured. Skipping Telegram send.")
            return True

    def save_results_to_json(self, results: List[Dict], filename: str = 'scan_results.json') -> bool:
        """
        Save results to JSON file

        Args:
            results: Analysis results
            filename: Output filename

        Returns:
            True if successful
        """
        try:
            # Convert results to serializable format
            serializable_results = []
            for result in results:
                clean_result = {
                    'symbol': result['clean_symbol'],
                    'price': result['current_price'],
                    'rsi': result['rsi'],
                    'adx': result['adx'],
                    'volume_ratio': result['volume_ratio'],
                    'patterns': [
                        {
                            'type': p.get('type'),
                            'confidence': p.get('confidence'),
                            'strength': p.get('strength'),
                            'success_rate': p.get('success_rate'),
                        }
                        for p in result['patterns']
                    ]
                }
                serializable_results.append(clean_result)

            with open(filename, 'w') as f:
                json.dump(serializable_results, f, indent=2)

            logger.info(f"Results saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner with Telegram integration')
    parser.add_argument('--max-stocks', type=int, default=50, help='Maximum number of stocks to scan')
    parser.add_argument('--telegram-token', help='Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)')
    parser.add_argument('--telegram-chat-id', help='Telegram chat ID (or set TELEGRAM_CHAT_ID env var)')
    parser.add_argument('--save-json', action='store_true', help='Save results to JSON file')

    args = parser.parse_args()

    # Initialize scanner
    scanner = TelegramPCSScanner(
        telegram_token=args.telegram_token,
        telegram_chat_id=args.telegram_chat_id
    )

    # Run analysis
    success = scanner.run(max_stocks=args.max_stocks)

    # Save results if requested
    if args.save_json:
        config = scanner.get_default_config()
        results = scanner.run_analysis(config=config, max_stocks=args.max_stocks)
        scanner.save_results_to_json(results)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
