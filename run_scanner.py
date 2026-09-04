#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Integration
Runs the stock scanner and sends results meeting filter criteria to Telegram or file
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
import requests
import warnings

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scanner
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Send messages to Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML"):
        """Send a text message to Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"✓ Message sent to Telegram")
                return True
            else:
                logger.error(f"✗ Failed to send message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False


def run_scanner(config: dict) -> list:
    """Run the stock scanner with given configuration"""
    scanner = ProfessionalPCSScanner()
    results = []

    logger.info(f"Starting scan of {len(config['stocks_to_scan'])} stocks...")

    total_stocks = len(config['stocks_to_scan'])
    successful = 0
    failed = 0

    for idx, symbol in enumerate(config['stocks_to_scan'], 1):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')

            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 50:
                failed += 1
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                config.get('min_volume_ratio', 1.2)
            )
            if not volume_ok:
                failed += 1
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                failed += 1
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Calculate overall strength
            max_strength = max(p['strength'] for p in patterns)
            overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            # Filter by minimum strength
            if max_strength < config.get('pattern_strength_min', 65):
                failed += 1
                continue

            result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'max_strength': max_strength,
                'confidence': overall_confidence
            }

            results.append(result)
            successful += 1

            # Progress update every 20 stocks
            if idx % 20 == 0 or idx == total_stocks:
                logger.info(f"  [{idx}/{total_stocks}] Progress: {successful} found, {failed} skipped")

        except Exception as e:
            failed += 1
            continue

    # Sort by strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)
    logger.info(f"✓ Scan complete: Found {len(results)} stocks meeting criteria")

    return results


def format_results_for_telegram(results: list) -> str:
    """Format scan results as Telegram message"""
    if not results:
        return "📊 <b>NSE F&O Scanner - No Results</b>\n\nNo stocks found meeting the current filter criteria."

    ist = pytz.timezone('Asia/Kolkata')
    scan_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')

    # Header
    message = f"📊 <b>NSE F&O Scanner Results</b>\n"
    message += f"<i>Scan Time: {scan_time}</i>\n"
    message += f"<i>Stocks Found: {len(results)}</i>\n"
    message += "─" * 40 + "\n\n"

    # Group by confidence level
    high_conf = [r for r in results if r['confidence'] == 'HIGH']
    med_conf = [r for r in results if r['confidence'] == 'MEDIUM']
    low_conf = [r for r in results if r['confidence'] == 'LOW']

    # HIGH Confidence
    if high_conf:
        message += "🟢 <b>HIGH CONFIDENCE</b>\n"
        for result in high_conf[:10]:
            symbol = result['clean_symbol']
            price = result['current_price']
            strength = result['max_strength']
            patterns = len(result['patterns'])
            message += f"  • <code>{symbol:12}</code> ₹{price:8.2f} | 💪{strength:.0f}% | {patterns} pattern(s)\n"
        message += "\n"

    # MEDIUM Confidence
    if med_conf:
        message += "🟡 <b>MEDIUM CONFIDENCE</b>\n"
        for result in med_conf[:10]:
            symbol = result['clean_symbol']
            price = result['current_price']
            strength = result['max_strength']
            patterns = len(result['patterns'])
            message += f"  • <code>{symbol:12}</code> ₹{price:8.2f} | 💪{strength:.0f}% | {patterns} pattern(s)\n"
        message += "\n"

    # LOW Confidence
    if low_conf:
        message += "🔴 <b>LOW CONFIDENCE</b>\n"
        for result in low_conf[:5]:
            symbol = result['clean_symbol']
            price = result['current_price']
            strength = result['max_strength']
            patterns = len(result['patterns'])
            message += f"  • <code>{symbol:12}</code> ₹{price:8.2f} | 💪{strength:.0f}% | {patterns} pattern(s)\n"
        if len(low_conf) > 5:
            message += f"  ... and {len(low_conf) - 5} more\n"
        message += "\n"

    # Summary stats
    message += "─" * 40 + "\n"
    message += f"📈 Total: {len(results)} stocks\n"
    message += f"🟢 High: {len(high_conf)} | 🟡 Medium: {len(med_conf)} | 🔴 Low: {len(low_conf)}\n"
    message += "🤖 Generated by NSE F&O PCS Scanner"

    return message


def save_results_to_file(results: list, filename: str = "scanner_results.json"):
    """Save results to a JSON file"""
    try:
        # Convert to serializable format
        serializable_results = []
        for r in results:
            result_copy = r.copy()
            # Convert patterns to simplified format
            result_copy['patterns'] = [
                {
                    'type': p.get('type', 'Unknown'),
                    'strength': p.get('strength', 0),
                    'confidence': p.get('confidence', 'Unknown')
                }
                for p in r.get('patterns', [])
            ]
            serializable_results.append(result_copy)

        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        logger.info(f"✓ Results saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving results to file: {e}")
        return False


def save_results_to_csv(results: list, filename: str = "scanner_results.csv"):
    """Save results to a CSV file"""
    try:
        import csv

        with open(filename, 'w', newline='') as f:
            if results:
                fieldnames = ['Symbol', 'Price', 'RSI', 'ADX', 'Volume_Ratio', 'Pattern_Count', 'Max_Strength', 'Confidence']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for result in results:
                    writer.writerow({
                        'Symbol': result['clean_symbol'],
                        'Price': f"{result['current_price']:.2f}",
                        'RSI': f"{result['rsi']:.1f}",
                        'ADX': f"{result['adx']:.1f}",
                        'Volume_Ratio': f"{result['volume_ratio']:.1f}",
                        'Pattern_Count': len(result['patterns']),
                        'Max_Strength': f"{result['max_strength']:.0f}",
                        'Confidence': result['confidence']
                    })

        logger.info(f"✓ Results saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving CSV: {e}")
        return False


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Telegram Integration")
    logger.info("=" * 60)

    # Configure scanner with default filters
    config = {
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
            'rectangle_top': False,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': True,
            'inverted_scallop': True
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True
    }

    # Run scanner
    try:
        results = run_scanner(config)

        # Format results
        message = format_results_for_telegram(results)

        # Try to send to Telegram if credentials are available
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if bot_token and chat_id:
            logger.info("\n📱 Sending results to Telegram...")
            notifier = TelegramNotifier(bot_token, chat_id)
            if notifier.send_message(message):
                logger.info("✓ Successfully sent scan results to Telegram!")
            else:
                logger.warning("⚠ Failed to send to Telegram, but saving results to file...")
                save_results_to_file(results)
                save_results_to_csv(results)
        else:
            logger.warning("⚠ Telegram credentials not found (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
            logger.info("💾 Saving results to files instead...")
            save_results_to_file(results)
            save_results_to_csv(results)

            # Also print message preview
            logger.info("\n" + "=" * 60)
            logger.info("📋 Message that would be sent to Telegram:")
            logger.info("=" * 60)
            logger.info(message.replace('<b>', '**').replace('</b>', '**').replace('<i>', '_').replace('</i>', '_').replace('<code>', '`').replace('</code>', '`'))
            logger.info("=" * 60)

        logger.info("=" * 60)
        logger.info("✓ Scan complete!")
        logger.info(f"  📈 Stocks found: {len(results)}")
        high = len([r for r in results if r['confidence'] == 'HIGH'])
        med = len([r for r in results if r['confidence'] == 'MEDIUM'])
        low = len([r for r in results if r['confidence'] == 'LOW'])
        logger.info(f"  🟢 High confidence: {high}")
        logger.info(f"  🟡 Medium confidence: {med}")
        logger.info(f"  🔴 Low confidence: {low}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during scan: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
