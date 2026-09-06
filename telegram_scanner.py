#!/usr/bin/env python3
"""
Telegram Stock Scanner - Automated analysis and alerting for NSE F&O stocks
Runs pattern detection and sends filtered results to Telegram
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from typing import List, Dict, Optional
import logging
import yfinance as yf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Mock streamlit to allow importing from streamlit_app
class MockStreamlit:
    @staticmethod
    def set_page_config(**kwargs):
        pass
    @staticmethod
    def cache_resource(**kwargs):
        return lambda f: f
    @staticmethod
    def cache_data(**kwargs):
        return lambda f: f

sys.modules['streamlit'] = MockStreamlit()

# Now we can safely import from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')

# Try importing the scanner from streamlit_app
try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
    logger.info("✓ Imported ProfessionalPCSScanner from streamlit_app")
except ImportError as e:
    logger.error(f"Failed to import from streamlit_app: {e}")
    logger.error("Attempting to run in fallback mode...")
    # We'll define fallback stock list if import fails
    COMPLETE_NSE_FO_UNIVERSE = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'SBIN.NS', 'LT.NS', 'ITC.NS', 'NIFTY.NS', 'BANKNIFTY.NS'
    ]


class TelegramStockAlert:
    """Sends stock analysis results to Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram sender

        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a single message to Telegram"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode
                },
                timeout=10
            )
            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False

    def format_stock_alert(self, symbol: str, data: Dict) -> str:
        """Format stock analysis results as Telegram message"""
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        patterns = data.get('patterns', [])

        # Get best pattern
        best_pattern = max(patterns, key=lambda x: x['strength']) if patterns else None

        price = data.get('current_price', 0)
        rsi = data.get('rsi', 0)
        adx = data.get('adx', 0)
        volume_ratio = data.get('volume_ratio', 0)

        # Determine confidence emoji
        if best_pattern:
            strength = best_pattern['strength']
            if strength >= 85:
                confidence_emoji = "🟢"
                confidence_text = "HIGH"
            elif strength >= 70:
                confidence_emoji = "🟡"
                confidence_text = "MEDIUM"
            else:
                confidence_emoji = "🔴"
                confidence_text = "LOW"

            pattern_type = best_pattern.get('type', 'Unknown')
            success_rate = best_pattern.get('success_rate', 0)
        else:
            return ""

        message = f"""
{confidence_emoji} <b>{clean_symbol}</b> - {confidence_text} Confidence
━━━━━━━━━━━━━━━━━━━━
<b>Pattern:</b> {pattern_type}
<b>Strength:</b> {strength:.0f}%
<b>Success Rate:</b> {success_rate}%

<b>Technicals:</b>
├─ Price: ₹{price:.2f}
├─ RSI: {rsi:.1f}
├─ ADX: {adx:.1f}
└─ Volume: {volume_ratio:.2f}x
"""
        return message.strip()


class StockScreener:
    """Screens stocks for trading opportunities"""

    def __init__(self, min_pattern_strength: float = 70):
        """
        Initialize screener

        Args:
            min_pattern_strength: Minimum pattern strength (0-100)
        """
        self.scanner = ProfessionalPCSScanner()
        self.min_pattern_strength = min_pattern_strength
        self.config = self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default screening configuration"""
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
            'pattern_strength_min': self.min_pattern_strength,
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
            'analysis_mode': 'Daily Only (V6.0 Style)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': False,
            'show_charts': False,
            'show_news': False,
            'export_results': False,
            'stocks_limit': len(COMPLETE_NSE_FO_UNIVERSE),
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False,
            }
        }

    def scan(self, max_stocks: Optional[int] = None, high_confidence_only: bool = True) -> List[Dict]:
        """
        Scan stocks for trading opportunities

        Args:
            max_stocks: Maximum number of stocks to scan (None = all)
            high_confidence_only: Only return HIGH confidence patterns

        Returns:
            List of stock results meeting criteria
        """
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
        if max_stocks:
            stocks_to_scan = stocks_to_scan[:max_stocks]

        results = []
        total = len(stocks_to_scan)

        logger.info(f"Starting scan of {total} stocks...")

        for i, symbol in enumerate(stocks_to_scan):
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            logger.info(f"[{i+1}/{total}] Analyzing {clean_symbol}...")

            try:
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

                # Filter patterns by strength
                valid_patterns = [p for p in patterns if p['strength'] >= self.min_pattern_strength]
                if not valid_patterns:
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # If high_confidence_only, filter for best patterns
                if high_confidence_only:
                    high_conf = [p for p in valid_patterns if p['strength'] >= 85]
                    if not high_conf:
                        continue
                    valid_patterns = high_conf

                stock_result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': valid_patterns,
                    'data': data
                }

                results.append(stock_result)

            except Exception as e:
                logger.warning(f"Error analyzing {clean_symbol}: {e}")
                continue

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        logger.info(f"Scan complete. Found {len(results)} stocks meeting criteria.")
        return results


def main():
    """Main execution function"""

    # Get Telegram credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Missing Telegram credentials:")
        logger.error("  - Set TELEGRAM_BOT_TOKEN environment variable")
        logger.error("  - Set TELEGRAM_CHAT_ID environment variable")
        sys.exit(1)

    # Initialize components
    screener = StockScreener(min_pattern_strength=70)
    telegram = TelegramStockAlert(bot_token, chat_id)

    # Run scan
    results = screener.scan(max_stocks=None, high_confidence_only=True)

    if not results:
        message = "📊 NSE F&O Scan Complete\n\nNo HIGH confidence patterns found today."
        telegram.send_message(message)
        logger.info("No results to send")
        return

    # Send header message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    header_message = f"""
📊 <b>NSE F&O Stock Scanner Results</b>
━━━━━━━━━━━━━━━━━━━━
<b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}
<b>Stocks Found:</b> {len(results)}
<b>Filter:</b> HIGH Confidence (Strength ≥ 85%)

<i>Detailed results below...</i>
"""
    telegram.send_message(header_message)

    # Send individual stock alerts (limit to top 10 to avoid spam)
    for result in results[:10]:
        message = telegram.format_stock_alert(result['symbol'], result)
        if message:
            telegram.send_message(message)
            # Small delay to avoid rate limiting
            import time
            time.sleep(0.5)

    # Send summary
    if len(results) > 10:
        summary = f"\n\n📈 <b>Additional Stocks:</b> {len(results) - 10} more stocks found\n\nRun full analysis for complete details."
        telegram.send_message(summary)

    logger.info(f"Successfully sent {min(10, len(results))} results to Telegram")


if __name__ == "__main__":
    main()
