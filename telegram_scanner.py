#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Integration
Standalone script to scan stocks and send results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import pytz
import requests
import pandas as pd
import numpy as np
import warnings

# Add the app directory to path
sys.path.insert(0, '/home/user/nsepcs')

# Import the scanner class from the streamlit app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

warnings.filterwarnings('ignore')

class TelegramScanner:
    def __init__(self):
        """Initialize Telegram scanner with environment variables"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

        if not self.bot_token or not self.chat_id:
            print("⚠️  WARNING: Telegram credentials not set!")
            print("Set environment variables: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            print("Running in dry-run mode - results will be saved to file only")
            self.telegram_enabled = False
        else:
            self.telegram_enabled = True

    def send_telegram_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.telegram_enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False

    def format_result_for_telegram(self, results):
        """Format scan results for Telegram message"""
        if not results:
            return "❌ No stocks found matching the filter criteria."

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        lines = []
        lines.append(f"🎯 <b>NSE F&O PCS Scan Results</b>")
        lines.append(f"📅 {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}")
        lines.append("")
        lines.append(f"📊 Found <b>{len(results)} stocks</b> matching criteria")
        lines.append("")

        # Group by confidence level
        high_conf = [r for r in results if max(p['strength'] for p in r['patterns']) >= 85]
        med_conf = [r for r in results if 70 <= max(p['strength'] for p in r['patterns']) < 85]
        low_conf = [r for r in results if max(p['strength'] for p in r['patterns']) < 70]

        # HIGH Confidence
        if high_conf:
            lines.append("<b>🟢 HIGH CONFIDENCE (85%+)</b>")
            for result in high_conf[:5]:  # Show top 5
                symbol = result['symbol'].replace('.NS', '')
                price = result['current_price']
                strength = max(p['strength'] for p in result['patterns'])
                pattern_type = result['patterns'][0]['type'] if result['patterns'] else 'Unknown'
                lines.append(f"  • {symbol} @ ₹{price:.2f} ({strength:.0f}%) - {pattern_type}")
            if len(high_conf) > 5:
                lines.append(f"  ... and {len(high_conf) - 5} more")
            lines.append("")

        # MEDIUM Confidence
        if med_conf:
            lines.append("<b>🟡 MEDIUM CONFIDENCE (70-84%)</b>")
            for result in med_conf[:5]:  # Show top 5
                symbol = result['symbol'].replace('.NS', '')
                price = result['current_price']
                strength = max(p['strength'] for p in result['patterns'])
                pattern_type = result['patterns'][0]['type'] if result['patterns'] else 'Unknown'
                lines.append(f"  • {symbol} @ ₹{price:.2f} ({strength:.0f}%) - {pattern_type}")
            if len(med_conf) > 5:
                lines.append(f"  ... and {len(med_conf) - 5} more")
            lines.append("")

        # LOW Confidence
        if low_conf:
            lines.append("<b>🔴 LOW CONFIDENCE (<70%)</b>")
            for result in low_conf[:3]:  # Show top 3
                symbol = result['symbol'].replace('.NS', '')
                price = result['current_price']
                strength = max(p['strength'] for p in result['patterns'])
                pattern_type = result['patterns'][0]['type'] if result['patterns'] else 'Unknown'
                lines.append(f"  • {symbol} @ ₹{price:.2f} ({strength:.0f}%) - {pattern_type}")
            if len(low_conf) > 3:
                lines.append(f"  ... and {len(low_conf) - 3} more")
            lines.append("")

        # Summary stats
        total_patterns = sum(len(r['patterns']) for r in results)
        avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])

        lines.append("<b>📈 Summary Stats</b>")
        lines.append(f"  Total Patterns: {total_patterns}")
        lines.append(f"  Avg Strength: {avg_strength:.1f}%")

        return "\n".join(lines)

    def run_scan(self, limit=50):
        """Run the PCS scanner with default filters"""
        print(f"🚀 Starting NSE F&O PCS Scan...")
        print(f"📊 Scanning up to {limit} stocks from {len(COMPLETE_NSE_FO_UNIVERSE)} available")

        # Default configuration matching Streamlit defaults
        config = {
            'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:limit],
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
                'inverted_scallop': True
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'show_charts': False,
            'show_news': False,
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False
            }
        }

        results = []
        scanned = 0

        for i, symbol in enumerate(config['stocks_to_scan']):
            scanned += 1
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            print(f"  [{i+1}/{len(config['stocks_to_scan'])}] Analyzing {clean_symbol}...", end='', flush=True)

            try:
                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    print(" ❌ No data")
                    continue

                # Check volume
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, config['min_volume_ratio']
                )
                if not volume_ok:
                    print(" ❌ Volume")
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    print(" ❌ No patterns")
                    continue

                # Get metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Store result
                result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data
                }

                results.append(result)
                max_strength = max(p['strength'] for p in patterns)
                print(f" ✅ ({max_strength:.0f}%)")

            except Exception as e:
                print(f" ⚠️  Error: {str(e)[:20]}")
                continue

        print(f"\n✅ Scan completed! Found {len(results)} qualifying stocks")
        return results, config

    def save_results_to_file(self, results):
        """Save results to CSV for reference"""
        if not results:
            return None

        summary_data = []
        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            summary_data.append({
                'Symbol': result['symbol'].replace('.NS', ''),
                'Price': f"₹{result['current_price']:.2f}",
                'Strength': f"{max_strength:.0f}%",
                'Confidence': overall_confidence,
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Volume_Ratio': f"{result['volume_ratio']:.2f}x",
                'Pattern_Type': result['patterns'][0]['type'] if result['patterns'] else 'Unknown'
            })

        df = pd.DataFrame(summary_data)
        filename = f"scan_results_{datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"📁 Results saved to {filename}")
        return filename

    def execute(self, limit=50):
        """Execute complete scan and send to Telegram"""
        print("\n" + "="*60)
        print("NSE F&O PCS SCANNER - TELEGRAM MODE")
        print("="*60 + "\n")

        # Run scan
        results, config = self.run_scan(limit)

        # Save results to file
        csv_file = self.save_results_to_file(results)

        # Format message
        message = self.format_result_for_telegram(results)

        # Send to Telegram
        if self.telegram_enabled:
            print(f"\n📱 Sending results to Telegram...")
            if self.send_telegram_message(message):
                print("✅ Message sent successfully!")
            else:
                print("❌ Failed to send message")
                print("Message content:")
                print(message)
        else:
            print(f"\n📝 Telegram disabled - showing message preview:")
            print("="*60)
            print(message)
            print("="*60)

        # Print summary
        print(f"\n📊 SCAN SUMMARY")
        print(f"  Total Found: {len(results)}")
        if results:
            high_conf = sum(1 for r in results if max(p['strength'] for p in r['patterns']) >= 85)
            med_conf = sum(1 for r in results if 70 <= max(p['strength'] for p in r['patterns']) < 85)
            print(f"  HIGH Confidence: {high_conf}")
            print(f"  MEDIUM Confidence: {med_conf}")
            if csv_file:
                print(f"  Results File: {csv_file}")

        print("\n✨ Scan complete!")
        return results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner with Telegram Integration')
    parser.add_argument('--limit', type=int, default=50, help='Number of stocks to scan (default: 50)')
    parser.add_argument('--all', action='store_true', help='Scan all available stocks')

    args = parser.parse_args()

    limit = len(COMPLETE_NSE_FO_UNIVERSE) if args.all else args.limit

    scanner = TelegramScanner()
    results = scanner.execute(limit)

    return 0 if results else 1


if __name__ == '__main__':
    sys.exit(main())
