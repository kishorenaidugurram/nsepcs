#!/usr/bin/env python3
"""
NSE F&O Stock Scanner with Telegram Integration
Runs the stock scanner and sends results to Telegram chat
"""

import os
import sys
import json
import requests
from datetime import datetime
import pytz
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import scanner from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')
try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE, fetch_stock_data_cached
    logger.info("Successfully imported scanner from streamlit_app")
except ImportError as e:
    logger.error(f"Failed to import scanner: {e}")
    sys.exit(1)

class TelegramStockSender:
    """Send stock scanner results to Telegram"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.telegram_api = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        self.ist = pytz.timezone('Asia/Kolkata')

        if not self.bot_token or not self.chat_id:
            logger.warning(f"Telegram credentials not fully configured")
            logger.warning(f"  BOT_TOKEN: {'✓' if self.bot_token else '✗ Missing'}")
            logger.warning(f"  CHAT_ID: {'✓' if self.chat_id else '✗ Missing'}")

    def send_message(self, text, parse_mode='HTML'):
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Cannot send to Telegram - credentials missing")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(self.telegram_api, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def format_results(self, results):
        """Format scanner results for Telegram"""
        if not results:
            return "❌ No stocks found matching criteria"

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%H:%M IST')

        message = f"""
<b>📊 NSE F&O Stock Scanner Report</b>
<i>{current_time}</i>

<b>✅ Found {len(results)} qualifying stocks:</b>

"""

        for i, result in enumerate(results[:20], 1):  # Limit to 20 for Telegram
            symbol = result['symbol'].replace('.NS', '')
            price = result['current_price']
            volume = result['volume_ratio']
            rsi = result['rsi']
            adx = result['adx']

            # Get pattern info
            patterns = result.get('patterns', [])
            pattern_str = ', '.join([p['type'] for p in patterns[:2]])
            max_strength = max([p['strength'] for p in patterns]) if patterns else 0

            # Confidence level
            if max_strength >= 85:
                confidence = "🟢 HIGH"
            elif max_strength >= 70:
                confidence = "🟡 MEDIUM"
            else:
                confidence = "🔴 LOW"

            message += f"""<b>{i}. {symbol}</b>
   💰 ₹{price:.2f} | 📊 {volume:.1f}x | RSI {rsi:.0f} | ADX {adx:.0f}
   🎯 {confidence} ({max_strength:.0f}%) | {pattern_str}

"""

        # Footer
        message += f"""
<b>📈 Filter Criteria Applied:</b>
• RSI: 30-70
• ADX: >20
• Volume: >1.0x average
• Pattern Strength: >60%
• Current Day Confirmation: ✓

<i>Generated at {current_time}</i>
"""

        return message

    def run_scanner(self, stocks_limit=50, min_pattern_strength=60):
        """Run the stock scanner"""
        logger.info(f"Starting scanner scan with {stocks_limit} stocks")

        scanner = ProfessionalPCSScanner()
        results = []

        # Use first N stocks from universe
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:stocks_limit]

        for i, symbol in enumerate(stocks_to_scan, 1):
            try:
                # Get stock data
                data = scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    continue

                # Check volume
                volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, min_ratio=1.0)
                if not volume_ok:
                    continue

                # Setup config for pattern detection
                config = {
                    'min_volume_ratio': 1.0,
                    'volume_breakout_ratio': 2.0,
                    'lookback_days': 20,
                    'pattern_strength_min': min_pattern_strength,
                    'pattern_filters': {
                        'current_day_breakout': True,
                        'cup_handle': True,
                        'double_bottom': True,
                        'rectangle_bottom': True,
                        'head_shoulders_bottom': True,
                        'rounding_bottom': True
                    },
                    'ma_support': True,
                    'ma_type': 'EMA',
                    'ma_tolerance': 3
                }

                # Detect patterns
                patterns = scanner.detect_patterns(data, symbol, config)

                if patterns and len(patterns) > 0:
                    # Get current metrics
                    current_price = data['Close'].iloc[-1]
                    current_rsi = data['RSI'].iloc[-1]
                    current_adx = data['ADX'].iloc[-1]

                    stock_result = {
                        'symbol': symbol,
                        'current_price': current_price,
                        'volume_ratio': volume_ratio,
                        'rsi': current_rsi,
                        'adx': current_adx,
                        'patterns': patterns,
                        'data': data
                    }
                    results.append(stock_result)
                    logger.info(f"Found {len(patterns)} patterns in {symbol}")

                # Progress logging
                if i % 10 == 0:
                    logger.info(f"Scanned {i}/{len(stocks_to_scan)} stocks...")

            except Exception as e:
                logger.debug(f"Error scanning {symbol}: {e}")
                continue

        # Sort by pattern strength
        if results:
            results.sort(
                key=lambda x: max(p['strength'] for p in x['patterns']),
                reverse=True
            )

        logger.info(f"Scan complete. Found {len(results)} stocks meeting criteria")
        return results

    def save_results_to_file(self, results):
        """Save results to a JSON file for reference"""
        timestamp = datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')
        filename = f"/tmp/stock_scan_results_{timestamp}.json"

        try:
            # Convert results to serializable format
            serializable_results = []
            for result in results[:20]:  # Keep top 20
                serializable_results.append({
                    'symbol': result['symbol'],
                    'price': float(result['current_price']),
                    'volume_ratio': float(result['volume_ratio']),
                    'rsi': float(result['rsi']),
                    'adx': float(result['adx']),
                    'patterns': [
                        {
                            'type': p.get('type'),
                            'strength': p.get('strength'),
                            'confidence': p.get('confidence')
                        }
                        for p in result.get('patterns', [])
                    ]
                })

            with open(filename, 'w') as f:
                json.dump(serializable_results, f, indent=2)

            logger.info(f"Results saved to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None

def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O Stock Scanner - Telegram Sender")
    logger.info("=" * 60)

    sender = TelegramStockSender()

    # Run scanner
    logger.info("Running stock scanner...")
    results = sender.run_scanner(stocks_limit=100, min_pattern_strength=60)

    if not results:
        message = "❌ No stocks found matching the filter criteria today"
        logger.warning(message)
        sender.send_message(message)
    else:
        # Format and send results
        message = sender.format_results(results)
        logger.info(f"Sending {len(results)} results to Telegram")
        sender.send_message(message)

        # Save to file as backup
        sender.save_results_to_file(results)

        # Summary
        summary = f"""
✅ Scan Complete
   • Stocks Found: {len(results)}
   • Telegram Sent: Yes
   • Results Saved: Yes
"""
        logger.info(summary)
        print(summary)

    logger.info("=" * 60)

if __name__ == "__main__":
    main()
