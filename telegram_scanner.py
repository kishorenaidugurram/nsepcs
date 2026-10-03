#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner with Telegram Integration
Runs the stock scanning analysis and sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import logging
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import the scanner class from streamlit_app
sys.path.insert(0, os.path.dirname(__file__))

try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
except ImportError as e:
    logger.error(f"Error importing scanner: {e}")
    logger.warning("Attempting workaround...")

    # Create a minimal mock if imports fail
    COMPLETE_NSE_FO_UNIVERSE = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS'
    ]

    class ProfessionalPCSScanner:
        """Fallback scanner"""
        def __init__(self):
            pass

        def get_stock_data(self, symbol, period="3mo"):
            return None

        def detect_patterns(self, data, symbol, config):
            return []

        def check_volume_criteria(self, data, min_ratio=1.0):
            return False, 0, {}

class TelegramNotifier:
    """Send messages to Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a text message to Telegram"""
        try:
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = self.session.post(f"{self.api_url}/sendMessage", data=data, timeout=10)
            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False

    def send_document(self, file_path: str, caption: str = "") -> bool:
        """Send a file to Telegram"""
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = self.session.post(
                    f"{self.api_url}/sendDocument",
                    data=data,
                    files=files,
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info("Document sent to Telegram successfully")
                    return True
                else:
                    logger.error(f"Failed to send document: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending document to Telegram: {e}")
            return False


class NSEPCSScanner:
    """Standalone scanner for NSE F&O PCS opportunities"""

    def __init__(self):
        self.scanner = ProfessionalPCSScanner()
        self.config = self._get_default_config()
        self.results = []

    def _get_default_config(self) -> Dict:
        """Get default scanner configuration"""
        return {
            'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:50],  # Scan top 50 for speed
            'min_volume_ratio': 1.5,
            'pattern_strength_min': 65,
            'rsi_min': 30,
            'rsi_max': 85,
            'adx_min': 15,
            'ma_support': True,
            'ma_type': 'SMA',
            'ma_tolerance': 5,
            'lookback_days': 20,
            'volume_breakout_ratio': 2.0,
            'pattern_filters': {
                'current_day_breakout': True,
                'cup_and_handle': True,
                'flat_base': True,
                'bump_and_run': True,
                'rectangle_bottom': True,
            },
            'show_news': False,
            'show_charts': False,
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'pattern_priority': 'All Patterns (Comprehensive)',
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False
            }
        }

    def run_scan(self, max_stocks: Optional[int] = None, filter_high_confidence_only: bool = True) -> List[Dict]:
        """Run the stock scanner"""
        logger.info(f"Starting scan of {len(self.config['stocks_to_scan'])} stocks...")

        stocks_to_scan = self.config['stocks_to_scan']
        if max_stocks:
            stocks_to_scan = stocks_to_scan[:max_stocks]

        self.results = []

        for i, symbol in enumerate(stocks_to_scan):
            try:
                clean_symbol = symbol.replace('.NS', '').replace('^', '')
                logger.info(f"[{i+1}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...")

                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    logger.debug(f"  ✗ Insufficient data")
                    continue

                # Check volume criteria
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, self.config['min_volume_ratio']
                )
                if not volume_ok:
                    logger.debug(f"  ✗ Volume criteria not met")
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, self.config)
                if not patterns:
                    logger.debug(f"  ✗ No patterns detected")
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Calculate max strength
                max_strength = max(p['strength'] for p in patterns)

                # Filter by confidence if requested
                if filter_high_confidence_only:
                    # Only keep HIGH and MEDIUM confidence patterns
                    high_quality_patterns = [p for p in patterns if p.get('confidence') in ['HIGH', 'MEDIUM']]
                    if not high_quality_patterns:
                        logger.debug(f"  ✗ No high confidence patterns")
                        continue
                    patterns = high_quality_patterns

                # Create result entry
                result = {
                    'symbol': clean_symbol,
                    'price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'max_strength': max_strength,
                    'pattern_count': len(patterns),
                    'patterns': [
                        {
                            'type': p['type'],
                            'strength': p['strength'],
                            'confidence': p.get('confidence', 'UNKNOWN'),
                            'pcs_suitability': p.get('pcs_suitability', 0),
                        }
                        for p in patterns
                    ],
                    'scan_time': datetime.now().isoformat()
                }

                self.results.append(result)
                logger.info(f"  ✓ Found {len(patterns)} pattern(s) - Strength: {max_strength:.0f}%")

            except Exception as e:
                logger.error(f"Error analyzing {clean_symbol}: {e}")
                continue

        # Sort by strength
        self.results.sort(key=lambda x: x['max_strength'], reverse=True)
        logger.info(f"Scan complete! Found {len(self.results)} stocks with qualified patterns.")

        return self.results

    def format_results_for_telegram(self, max_stocks: int = 10) -> str:
        """Format scan results for Telegram message"""
        if not self.results:
            return "❌ No stocks found meeting the filter criteria."

        results_to_show = self.results[:max_stocks]

        message = f"""
🎯 <b>NSE F&O PCS Scanner Results</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M IST')}

Found {len(self.results)} stocks with high-quality patterns
(Showing top {len(results_to_show)})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        for i, result in enumerate(results_to_show, 1):
            confidence_emoji = "🟢" if any(p['confidence'] == 'HIGH' for p in result['patterns']) else "🟡"

            message += f"""
{i}. {confidence_emoji} <b>{result['symbol']}</b>
   💰 Price: ₹{result['price']:.2f}
   📊 Strength: {result['max_strength']:.0f}% | RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}
   📈 Volume: {result['volume_ratio']:.1f}x | Patterns: {result['pattern_count']}
"""

            for pattern in result['patterns'][:2]:  # Show top 2 patterns per stock
                message += f"      • {pattern['type']}: {pattern['strength']:.0f}% ({pattern['confidence']})\n"

        message += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Download detailed results for complete analysis"""

        return message

    def save_results_to_csv(self, filename: str = "/tmp/claude-0/-home-user-nsepcs/1afda74d-5275-5193-93af-823cf3d99f2c/scratchpad/scan_results.csv") -> str:
        """Save results to CSV file"""
        if not self.results:
            return None

        # Prepare data for CSV
        data = []
        for result in self.results:
            # Get primary pattern
            primary_pattern = result['patterns'][0] if result['patterns'] else {}

            data.append({
                'Symbol': result['symbol'],
                'Price': f"₹{result['price']:.2f}",
                'Strength': f"{result['max_strength']:.0f}%",
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Volume_Ratio': f"{result['volume_ratio']:.1f}x",
                'Primary_Pattern': primary_pattern.get('type', 'N/A'),
                'Pattern_Confidence': primary_pattern.get('confidence', 'N/A'),
                'Pattern_Count': result['pattern_count'],
                'PCS_Suitability': f"{primary_pattern.get('pcs_suitability', 0):.0f}%",
            })

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logger.info(f"Results saved to {filename}")
        return filename

    def save_results_to_json(self, filename: str = "/tmp/claude-0/-home-user-nsepcs/1afda74d-5275-5193-93af-823cf3d99f2c/scratchpad/scan_results.json") -> str:
        """Save results to JSON file"""
        if not self.results:
            return None

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"Results saved to {filename}")
        return filename


def main():
    """Main function to run the scanner and send to Telegram"""

    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner with Telegram Integration")
    logger.info("=" * 60)

    # Check for Telegram credentials
    telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    notifier = None
    if telegram_bot_token and telegram_chat_id:
        logger.info(f"Telegram integration enabled (Chat ID: {telegram_chat_id[:10]}...)")
        notifier = TelegramNotifier(telegram_bot_token, telegram_chat_id)
    else:
        logger.warning("⚠️  Telegram credentials not found in environment variables")
        logger.warning("   To enable Telegram notifications, set:")
        logger.warning("   - TELEGRAM_BOT_TOKEN")
        logger.warning("   - TELEGRAM_CHAT_ID")

    # Run scanner
    logger.info("\nStarting stock scan...")
    scanner = NSEPCSScanner()
    results = scanner.run_scan(max_stocks=50, filter_high_confidence_only=True)

    # Save results
    logger.info("\nSaving results...")
    csv_file = scanner.save_results_to_csv()
    json_file = scanner.save_results_to_json()

    # Format and send results
    if results:
        logger.info(f"\n✅ Found {len(results)} qualified stocks!")

        # Display summary
        logger.info("\n" + "=" * 60)
        logger.info("SCAN RESULTS SUMMARY")
        logger.info("=" * 60)

        for i, result in enumerate(results[:5], 1):
            logger.info(f"\n{i}. {result['symbol']}")
            logger.info(f"   Price: ₹{result['price']:.2f} | Strength: {result['max_strength']:.0f}%")
            logger.info(f"   RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f} | Vol: {result['volume_ratio']:.1f}x")
            for pattern in result['patterns'][:2]:
                logger.info(f"   • {pattern['type']}: {pattern['strength']:.0f}% ({pattern['confidence']})")

        if len(results) > 5:
            logger.info(f"\n... and {len(results) - 5} more stocks")

        # Send to Telegram if configured
        if notifier:
            logger.info("\nSending results to Telegram...")
            message = scanner.format_results_for_telegram(max_stocks=10)
            if notifier.send_message(message):
                logger.info("✅ Message sent to Telegram successfully")

                # Try to send CSV file
                if csv_file:
                    caption = f"📊 Detailed scan results - {len(results)} stocks found"
                    if notifier.send_document(csv_file, caption):
                        logger.info("✅ CSV file sent to Telegram")
            else:
                logger.error("❌ Failed to send message to Telegram")
        else:
            logger.info("\n📝 Results saved locally (Telegram not configured)")
            logger.info(f"   CSV: {csv_file}")
            logger.info(f"   JSON: {json_file}")
    else:
        logger.warning("\n⚠️  No stocks found meeting the criteria")

        if notifier:
            notifier.send_message("❌ No stocks found in today's scan meeting the PCS criteria.")

    logger.info("\n" + "=" * 60)
    logger.info("Scan complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
