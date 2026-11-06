#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner with Telegram Integration
Runs the stock scanner and sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Import from streamlit_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from streamlit_app import (
        ProfessionalPCSScanner,
        COMPLETE_NSE_FO_UNIVERSE,
        fetch_stock_data_cached
    )
except ImportError as e:
    print(f"Error importing from streamlit_app: {e}")
    sys.exit(1)


class TelegramNotifier:
    """Handle Telegram notifications"""
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def is_configured(self):
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text, parse_mode="HTML"):
        """Send message to Telegram"""
        if not self.is_configured():
            print(f"⚠️ Telegram not configured. Message not sent:")
            print(text)
            return False

        try:
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = requests.post(self.api_url, json=data, timeout=10)
            if response.status_code == 200:
                print("✅ Message sent to Telegram")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False


class StockScannerRunner:
    """Run the stock scanner and collect results"""

    def __init__(self):
        self.scanner = ProfessionalPCSScanner()
        self.notifier = TelegramNotifier()
        self.ist = pytz.timezone('Asia/Kolkata')

    def run_scan(self, stocks_to_scan, max_workers=5):
        """Run scan on multiple stocks"""
        print(f"\n🚀 Starting scan of {len(stocks_to_scan)} stocks...")
        print(f"⏰ Time: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")

        results = []
        config = {
            'min_volume_ratio': 1.5,
            'show_news': False,
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False
            }
        }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._scan_stock, symbol, config): symbol
                for symbol in stocks_to_scan
            }

            completed = 0
            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"✅ {completed}/{len(stocks_to_scan)} - Found pattern for {result['symbol']}")
                    else:
                        print(f"⏭️  {completed}/{len(stocks_to_scan)} - No pattern for {symbol}")
                except Exception as e:
                    print(f"❌ {completed}/{len(stocks_to_scan)} - Error scanning {symbol}: {e}")

        return results

    def _scan_stock(self, symbol, config):
        """Scan individual stock"""
        try:
            # Get stock data
            data = self.scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                return None

            # Check volume
            volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
            if not volume_ok:
                return None

            # Detect patterns
            patterns = self.scanner.detect_patterns(data, symbol, config)
            if not patterns:
                return None

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            return {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data
            }
        except Exception as e:
            return None

    def format_results_for_telegram(self, results):
        """Format results as Telegram message"""
        if not results:
            return "📊 Scan Complete: No stocks meeting criteria found."

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        # Calculate summary
        total_patterns = sum(len(r['patterns']) for r in results)
        avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])
        high_confidence = sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')

        message = f"""<b>🎯 NSE F&O PCS Scan Results</b>
<b>⏰ {datetime.now(self.ist).strftime('%d-%b-%Y %H:%M:%S')}</b>

<b>📈 Summary:</b>
• Stocks Found: <b>{len(results)}</b>
• Total Patterns: <b>{total_patterns}</b>
• Avg Strength: <b>{avg_strength:.1f}%</b>
• High Confidence: <b>{high_confidence}</b>

<b>📋 Top Stocks:</b>
"""

        for i, result in enumerate(results[:10], 1):
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            symbol = result['symbol'].replace('.NS', '')

            message += f"""
<b>{i}. {symbol}</b>
   💰 Price: ₹{result['current_price']:.2f}
   📊 Strength: {max_strength:.0f}% | Confidence: {confidence}
   📈 RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}
   📦 Volume: {result['volume_ratio']:.1f}x"""

        if len(results) > 10:
            message += f"\n\n... and {len(results) - 10} more stocks"

        return message

    def format_results_for_csv(self, results):
        """Format results as CSV"""
        data = []
        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            pattern_types = ', '.join([p['type'] for p in result['patterns']])

            data.append({
                'Symbol': result['symbol'].replace('.NS', ''),
                'Price': f"₹{result['current_price']:.2f}",
                'Strength': f"{max_strength:.1f}%",
                'Confidence': confidence,
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Volume_Ratio': f"{result['volume_ratio']:.1f}x",
                'Patterns': pattern_types
            })

        df = pd.DataFrame(data)
        return df

    def run(self):
        """Main execution"""
        print("=" * 60)
        print("NSE F&O PCS SCANNER WITH TELEGRAM INTEGRATION")
        print("=" * 60)

        # Check Telegram configuration
        if self.notifier.is_configured():
            print("✅ Telegram is configured")
        else:
            print("⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

        # Run scan
        results = self.run_scan(COMPLETE_NSE_FO_UNIVERSE, max_workers=5)

        # Format and send results
        telegram_message = self.format_results_for_telegram(results)
        print("\n" + "=" * 60)
        print("TELEGRAM MESSAGE PREVIEW:")
        print("=" * 60)
        print(telegram_message)

        # Send to Telegram
        if self.notifier.is_configured():
            print("\n📤 Sending to Telegram...")
            self.notifier.send_message(telegram_message)

        # Save CSV
        csv_filename = f"/tmp/nse_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if results:
            df = self.format_results_for_csv(results)
            df.to_csv(csv_filename, index=False)
            print(f"💾 Results saved to: {csv_filename}")

        print("\n✅ Scan complete!")
        return results


def main():
    """Main entry point"""
    runner = StockScannerRunner()
    results = runner.run()

    # Print summary
    print(f"\n📊 Found {len(results)} stocks meeting criteria")
    if results:
        df = runner.format_results_for_csv(results)
        print("\nTop 5 Results:")
        print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
