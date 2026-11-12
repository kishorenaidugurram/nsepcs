#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Telegram Integration
Runs the scanner analysis and sends qualifying stocks to Telegram
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime
import pytz
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import scanner from streamlit app (will work with or without streamlit)
sys.path.insert(0, '/home/user/nsepcs')

try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
    logger.info("Successfully imported ProfessionalPCSScanner")
except ImportError as e:
    logger.error(f"Failed to import scanner: {e}")
    sys.exit(1)


class TelegramNotifier:
    """Handle Telegram notifications"""

    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Results will be logged only.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Telegram notifications enabled")

    def send_message(self, text, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.enabled:
            logger.info(f"[Would send to Telegram]:\n{text}\n")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }

            data = urllib.parse.urlencode(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.api_url}/sendMessage",
                data=data
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info("Message sent to Telegram")
                    return True
                else:
                    logger.error(f"Telegram API error: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_document(self, file_data, filename):
        """Send file to Telegram"""
        if not self.enabled:
            logger.info(f"[Would send document to Telegram]: {filename}")
            return False

        logger.info(f"Document sending not implemented in urllib version: {filename}")
        return False


def run_scanner_analysis(min_pattern_strength=65, max_stocks=50):
    """Run the PCS scanner analysis"""
    logger.info(f"Starting NSE F&O PCS Scanner Analysis")
    logger.info(f"   Scanning up to {max_stocks} stocks from {len(COMPLETE_NSE_FO_UNIVERSE)} in universe")
    logger.info(f"   Min Pattern Strength: {min_pattern_strength}%")

    scanner = ProfessionalPCSScanner()
    results = []

    # Default configuration
    config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': min_pattern_strength,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'show_charts': False,
        'show_news': False,
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
        'enable_daily_analysis': True,
        'enable_weekly_validation': False,
        'pattern_priority': 'All Patterns (Comprehensive)',
        'enhancements': {
            'delivery_volume': False,
            'fno_consolidation': False,
            'breakout_pullback': False,
            'enhanced_sr': False,
        }
    }

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    for i, symbol in enumerate(stocks_to_scan, 1):
        try:
            logger.info(f"[{i}/{len(stocks_to_scan)}] Analyzing {symbol}...")

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Filter by pattern strength
            strong_patterns = [p for p in patterns if p['strength'] >= min_pattern_strength]
            if not strong_patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Store result
            result = {
                'symbol': symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': strong_patterns,
                'max_strength': max(p['strength'] for p in strong_patterns),
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            }

            results.append(result)
            logger.info(f"Qualified - Max Strength: {result['max_strength']:.0f}%")

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue

    # Sort by strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    logger.info(f"Analysis complete - Found {len(results)} qualifying stocks")
    return results


def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "No stocks found meeting the filter criteria today."

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""
NSE F&O PCS Scanner Results
{timestamp}

Found: {len(results)} stocks

"""

    for i, result in enumerate(results[:10], 1):  # Top 10
        stock_name = result['symbol'].replace('.NS', '')
        strength = result['max_strength']
        confidence = "HIGH" if strength >= 85 else "MEDIUM" if strength >= 70 else "LOW"

        message += f"""
{i}. {stock_name}
   Price: Rs{result['price']:.2f} | RSI: {result['rsi']:.0f} | ADX: {result['adx']:.0f}
   Volume Ratio: {result['volume_ratio']:.2f}x | Strength: {strength:.0f}%
   Confidence: {confidence}

"""

    if len(results) > 10:
        message += f"\n... and {len(results) - 10} more stocks\n"

    message += f"""
Analysis Parameters:
- Min Pattern Strength: 65%
- Volume Ratio: 1.2x minimum
- ADX Minimum: 20
- RSI Range: 30-75

Warning: For trading purposes only. Always verify before execution.
"""

    return message


def format_csv_results(results):
    """Format results as CSV for export"""
    if not results:
        return ""

    lines = ["Symbol,Price,RSI,ADX,Volume_Ratio,Max_Strength,Pattern_Count"]

    for result in results:
        stock_name = result['symbol'].replace('.NS', '')
        pattern_count = len(result['patterns'])

        line = f"{stock_name},{result['price']:.2f},{result['rsi']:.1f},{result['adx']:.1f},{result['volume_ratio']:.2f},{result['max_strength']:.0f},{pattern_count}"
        lines.append(line)

    return "\n".join(lines)


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Telegram Integration")
    logger.info("=" * 60)

    # Initialize Telegram notifier
    telegram = TelegramNotifier()

    # Run scanner analysis
    try:
        results = run_scanner_analysis(min_pattern_strength=65, max_stocks=50)
    except Exception as e:
        logger.error(f"Scanner analysis failed: {e}")
        import traceback
        traceback.print_exc()
        error_message = f"Scanner Error:\n{str(e)}"
        telegram.send_message(error_message)
        sys.exit(1)

    # Format and send results
    try:
        # Send main message
        message = format_telegram_message(results)
        telegram.send_message(message, parse_mode='HTML')

        # Print to console
        print("\n" + "=" * 60)
        print("SCAN RESULTS")
        print("=" * 60)
        print(message)
        print("=" * 60)

        # Save results as JSON
        results_file = f"/tmp/pcs_scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {results_file}")

        # Save CSV export
        csv_data = format_csv_results(results)
        if csv_data:
            csv_file = f"/tmp/pcs_scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(csv_file, 'w') as f:
                f.write(csv_data)
            logger.info(f"CSV export saved to {csv_file}")

        logger.info("Scan complete and results sent to Telegram")

    except Exception as e:
        logger.error(f"Failed to process results: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
