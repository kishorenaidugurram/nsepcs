#!/usr/bin/env python3.13
"""
Standalone NSE PCS Scanner - Runs without Streamlit UI
Extracts scanner logic and sends results to Telegram
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Patch the 'ta' module with our compatibility layer before importing streamlit_app
import ta_compat
sys.modules['ta'] = ta_compat

from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    get_nse_non_fno_stocks
)
from telegram_sender import send_stock_results, send_error_notification
from telegram_config import is_configured, get_config_status

class StandaloneScanner:
    """Standalone scanner that runs without Streamlit"""

    def __init__(self, config=None):
        """Initialize scanner with configuration"""
        self.scanner = ProfessionalPCSScanner()
        self.config = config or self._get_default_config()

    def _get_default_config(self):
        """Get default scanner configuration"""
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
            'show_news': False,
            'show_charts': False,
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False
            }
        }

    def run(self):
        """Run the scanner and return results"""
        print(f"🚀 Starting NSE PCS Scanner at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Scanning {len(self.config['stocks_to_scan'])} stocks...")

        results = []
        failed_stocks = 0

        for i, symbol in enumerate(self.config['stocks_to_scan']):
            # Progress update every 20 stocks
            if (i + 1) % 20 == 0:
                print(f"   [{i+1}/{len(self.config['stocks_to_scan'])}] Processing...")

            try:
                # Get recent data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue

                # Check volume criteria
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data,
                    self.config['min_volume_ratio']
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

                # Create result
                stock_result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                }

                results.append(stock_result)

            except Exception as e:
                failed_stocks += 1
                continue

        print(f"\n✅ Scan Complete!")
        print(f"   📈 Stocks Found: {len(results)}")
        print(f"   ⚠️  Failed/Skipped: {failed_stocks}")

        return results

    def save_results(self, results, filename="scan_results.json"):
        """Save results to a JSON file"""
        try:
            # Convert results to JSON-serializable format
            json_results = []
            for r in results:
                json_r = {
                    'symbol': r['symbol'],
                    'current_price': float(r['current_price']),
                    'volume_ratio': float(r['volume_ratio']),
                    'rsi': float(r['rsi']),
                    'adx': float(r['adx']),
                    'patterns': [
                        {
                            'type': p['type'],
                            'strength': float(p['strength']),
                            'confidence': p['confidence'],
                            'success_rate': float(p['success_rate']),
                            'pcs_suitability': float(p['pcs_suitability'])
                        }
                        for p in r['patterns']
                    ]
                }
                json_results.append(json_r)

            with open(filename, 'w') as f:
                json.dump(json_results, f, indent=2)

            print(f"💾 Results saved to {filename}")
            return True

        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
            return False

def main():
    """Main entry point"""

    print("=" * 60)
    print("🎯 NSE PCS Scanner - Standalone Mode")
    print("=" * 60)
    print()

    # Check Telegram configuration
    print(get_config_status())
    print()

    try:
        # Initialize and run scanner
        scanner = StandaloneScanner()
        results = scanner.run()

        print()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scan_results_{timestamp}.json"
        scanner.save_results(results, results_file)

        print()

        # Send to Telegram if configured
        if is_configured():
            print("📱 Sending results to Telegram...")
            if results:
                success = send_stock_results(results)
                if success:
                    print("✅ Results sent to Telegram")
                else:
                    print("❌ Failed to send results to Telegram")
            else:
                print("⚠️  No stocks found to send")
        else:
            print("⚠️  Telegram not configured")
            print("   To enable Telegram notifications, set environment variables:")
            print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")

        print()
        print("=" * 60)
        print(f"✅ Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

        # Try to send error notification to Telegram
        if is_configured():
            send_error_notification(str(e))

        return 1

if __name__ == "__main__":
    sys.exit(main())
