#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Notification Service
Runs stock analysis and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import requests
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramPCSNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram bot and configuration"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.scanner = ProfessionalPCSScanner()

        # Default filter configuration
        self.config = {
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
            'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,
            'show_news': True,
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
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
        }

    def run_analysis(self) -> list:
        """Run stock analysis and return filtered results"""
        results = []
        total_stocks = len(self.config['stocks_to_scan'])

        logger.info(f"Starting analysis of {total_stocks} stocks...")

        for i, symbol in enumerate(self.config['stocks_to_scan'], 1):
            try:
                clean_symbol = symbol.replace('.NS', '').replace('^', '')
                logger.info(f"[{i}/{total_stocks}] Analyzing {clean_symbol}...")

                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue

                # Check volume criteria
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, self.config['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, self.config)
                if not patterns:
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Get news if enabled
                news_data = None
                if self.config['show_news']:
                    try:
                        stock_name = clean_symbol
                        news_data = self.scanner.get_fundamental_news(symbol, stock_name)
                    except:
                        news_data = None

                # Create stock result
                stock_result = {
                    'symbol': symbol,
                    'clean_symbol': clean_symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'news_data': news_data
                }

                results.append(stock_result)
                logger.info(f"✓ {clean_symbol} qualified with {len(patterns)} pattern(s)")

            except Exception as e:
                logger.warning(f"Error analyzing {symbol}: {str(e)}")
                continue

        # Sort by pattern strength
        if results:
            results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        logger.info(f"Analysis complete. Found {len(results)} qualifying stocks.")
        return results

    def send_telegram_message(self, text: str, parse_mode='HTML') -> bool:
        """Send message to Telegram"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False

    def format_results_for_telegram(self, results: list) -> str:
        """Format analysis results for Telegram message"""
        if not results:
            return "❌ No stocks met the filter criteria today."

        # Header
        message = f"""📊 <b>NSE F&O PCS Scanner Results</b>
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 <b>Found {len(results)} Qualifying Stocks</b>

"""

        # Summary metrics
        total_patterns = sum(len(r['patterns']) for r in results)
        current_day_breakouts = sum(1 for r in results for p in r['patterns'] if 'Current Day' in p['type'])
        high_strength = sum(1 for r in results for p in r['patterns'] if p['strength'] >= 85)

        message += f"""📈 <b>Summary:</b>
• Total Stocks: {len(results)}
• Total Patterns: {total_patterns}
• Current Day Breakouts: 🔥 {current_day_breakouts}
• High Strength (85+%): 💪 {high_strength}

"""

        # Stock details (limit to top 15 for Telegram message size)
        message += f"<b>Top Stocks:</b>\n"
        for idx, result in enumerate(results[:15], 1):
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = '🟢 HIGH' if max_strength >= 85 else '🟡 MEDIUM' if max_strength >= 70 else '🔴 LOW'
            current_breakout = '🔥' if any('Current Day' in p['type'] for p in result['patterns']) else ''

            message += f"""
{idx}. <b>{result['clean_symbol']}</b> {current_breakout}
   Price: ₹{result['current_price']:.2f}
   RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}
   Strength: {max_strength:.0f}% {confidence}
   Volume: {result['volume_ratio']:.1f}x | Patterns: {len(result['patterns'])}
"""

        if len(results) > 15:
            message += f"\n... and {len(results) - 15} more stocks"

        # Footer
        message += f"""

⚠️ <i>This is for educational purposes only. Not financial advice.</i>
📱 Use at your own risk. Always verify before trading."""

        return message

    def run(self):
        """Run the complete analysis and send notification"""
        try:
            logger.info("=" * 50)
            logger.info("NSE F&O PCS Scanner - Telegram Notifier Started")
            logger.info("=" * 50)

            # Test Telegram connection
            logger.info("Testing Telegram connection...")
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            if response.status_code != 200:
                raise Exception(f"Telegram connection failed: {response.text}")
            logger.info("✓ Telegram connection successful")

            # Run analysis
            logger.info("Running stock analysis...")
            results = self.run_analysis()

            # Format and send results
            logger.info("Formatting results...")
            message = self.format_results_for_telegram(results)

            logger.info("Sending Telegram notification...")
            self.send_telegram_message(message)

            logger.info("=" * 50)
            logger.info("Scan Complete!")
            logger.info("=" * 50)

            return True

        except Exception as e:
            logger.error(f"Error in run: {str(e)}")
            error_msg = f"❌ <b>NSE PCS Scanner Error</b>\n\n{str(e)}\n\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            try:
                self.send_telegram_message(error_msg)
            except:
                pass
            return False


def main():
    """Main entry point"""
    # Get credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Missing environment variables:")
        logger.error("  TELEGRAM_BOT_TOKEN - Your Telegram bot token")
        logger.error("  TELEGRAM_CHAT_ID - Your Telegram chat ID")
        sys.exit(1)

    # Run scanner
    notifier = TelegramPCSNotifier(bot_token, chat_id)
    success = notifier.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
