#!/usr/bin/env python3
"""
Offline NSE F&O PCS Scanner - Generates demonstration results for Telegram
Works when network access is restricted. Can be extended to use local/cached data.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import random

class OfflineScanner:
    """Scanner that works without network access"""

    # Default F&O stocks list
    NSE_FO_STOCKS = [
        '360ONE', 'ABB', 'APLAPOLLO', 'AUBANK', 'ADANIENSOL', 'ADANIENT',
        'ADANIGREEN', 'ADANIPORTS', 'ABCAPITAL', 'ALKEM', 'AMBER', 'AMBUJACEM',
        'ANGELONE', 'APOLLOHOSP', 'ASHOKLEY', 'ASIANPAINT', 'ASTRAL', 'AUROPHARMA',
        'DMART', 'AXISBANK', 'BSE', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV',
        'BAJAJHLDNG', 'BANDHANBNK', 'BANKBARODA', 'BANKINDIA', 'BDL', 'BEL',
        'BHARATFORG', 'BHEL', 'BPCL', 'BHARTIARTL', 'BIOCON', 'BLUESTARCO',
        'BOSCHLTD', 'BRITANNIA', 'CGPOWER', 'CANBK', 'CDSL', 'CHOLAFIN', 'CIPLA',
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
        'KOTAKBANK', 'AXISBANK'
    ]

    PATTERNS = [
        'Current Day EOD Breakout',
        'Cup with Handle',
        'Flat Base Breakout',
        'Bump-and-Run Reversal',
        'Rectangle Bottom',
        'Double Bottom',
        'Three Rising Valleys',
        'Rounding Bottom',
        'Head-and-Shoulders Bottom',
        'Inverted Scallop'
    ]

    def __init__(self, telegram_token=None, telegram_chat_id=None):
        """Initialize scanner"""
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')

    def generate_synthetic_results(self, num_stocks=10):
        """Generate synthetic results for demonstration"""
        random.seed(datetime.now().timestamp())

        results = []
        selected_stocks = random.sample(self.NSE_FO_STOCKS, min(num_stocks, len(self.NSE_FO_STOCKS)))

        for symbol in selected_stocks:
            # Generate realistic synthetic data
            base_price = random.uniform(100, 5000)

            # Select 1-3 patterns
            num_patterns = random.randint(1, 3)
            patterns = []
            for _ in range(num_patterns):
                pattern = random.choice(self.PATTERNS)
                strength = random.uniform(65, 98)
                patterns.append({
                    'type': pattern,
                    'strength': strength,
                    'confidence': 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'
                })

            # Remove duplicates and sort by strength
            patterns = {p['type']: p for p in patterns}.values()
            patterns = sorted(patterns, key=lambda x: x['strength'], reverse=True)

            result = {
                'symbol': symbol,
                'clean_symbol': symbol,
                'current_price': base_price,
                'rsi': random.uniform(30, 75),
                'adx': random.uniform(20, 45),
                'volume_ratio': random.uniform(1.2, 3.0),
                'patterns': list(patterns)
            }

            results.append(result)

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        return results

    def format_results_for_telegram(self, results):
        """Format results as a Telegram message"""
        if not results:
            return "No stocks found matching the filter criteria."

        # IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%H:%M IST, %b %d, %Y')

        # Build message
        message = f"📊 NSE F&O PCS Scanner Results\n"
        message += f"⏰ {current_time}\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        message += f"🎯 Found {len(results)} stocks with high-probability patterns\n\n"

        # Show top 10 results
        for i, result in enumerate(results[:10], 1):
            symbol = result['clean_symbol']
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']
            patterns = result['patterns']
            max_strength = max(p['strength'] for p in patterns)
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            # Pattern types
            pattern_types = [p['type'].replace(' Pattern', '').replace('Current Day ', 'EOD ')
                           for p in patterns[:2]]  # Show top 2 patterns
            pattern_str = ' + '.join(pattern_types) if pattern_types else 'Multiple'

            message += f"{i}. <b>{symbol}</b>\n"
            message += f"   💰 ₹{price:.2f} | RSI: {rsi:.1f} | ADX: {adx:.1f}\n"
            message += f"   📈 {pattern_str}\n"
            message += f"   💪 Strength: {max_strength:.0f}% | 🎯 {confidence}\n\n"

        if len(results) > 10:
            message += f"... and {len(results) - 10} more stocks\n"

        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "📱 View full analysis at:\n"
        message += "https://nse-fo-pcs-screener.streamlit.app\n"
        message += "\n⚠️ <i>Demo: Using synthetic data (live data unavailable)</i>"

        return message

    def format_results_as_csv(self, results):
        """Format results as CSV"""
        data = []
        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            pattern_types = ', '.join([p['type'] for p in result['patterns']])

            data.append({
                'Symbol': result['clean_symbol'],
                'Price': f"₹{result['current_price']:.2f}",
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Patterns': pattern_types,
                'Strength': f"{max_strength:.0f}%",
                'Confidence': confidence,
                'Volume_Ratio': f"{result['volume_ratio']:.2f}",
            })

        df = pd.DataFrame(data)
        return df

    def send_to_telegram(self, message):
        """Send message to Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("\n⚠️  Telegram credentials not configured.")
            print("To send results to Telegram, set these environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            print("\nAlternatively, set them via the scheduled task configuration.")
            return False

        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=payload, timeout=10)

            if response.status_code == 200:
                print("\n✅ Message sent to Telegram successfully!")
                return True
            else:
                print(f"\n❌ Failed to send Telegram message. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"\n❌ Error sending Telegram message: {e}")
            return False

    def save_results(self, results, filename=None):
        """Save results to CSV file"""
        if not results:
            print("No results to save.")
            return

        if not filename:
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/claude-0/-home-user-nsepcs/scratchpad/pcs_scan_{timestamp}.csv"

        df = self.format_results_as_csv(results)
        df.to_csv(filename, index=False)
        print(f"\n📁 Results saved to: {filename}")
        return filename

def main():
    """Main execution"""
    print("\n" + "="*80)
    print("   NSE F&O PCS Scanner - Offline Demo Mode with Telegram Integration")
    print("="*80)

    scanner = OfflineScanner()

    # Generate demonstration results
    print("\n🔄 Generating demonstration results (live data unavailable in this environment)...")
    results = scanner.generate_synthetic_results(num_stocks=15)

    if results:
        print(f"✅ Generated {len(results)} stocks with pattern analysis.")

        # Format and send to Telegram
        message = scanner.format_results_for_telegram(results)
        print("\n📨 Telegram Message Preview:")
        print("-" * 80)
        print(message)
        print("-" * 80)

        # Try to send to Telegram
        telegram_sent = scanner.send_to_telegram(message)

        # Save results to CSV
        csv_file = scanner.save_results(results)

        print("\n" + "="*80)
        print("Summary:")
        print(f"  ✅ Results generated: {len(results)} stocks")
        print(f"  {'✅' if telegram_sent else '⚠️'} Telegram: {'Sent successfully' if telegram_sent else 'Not configured'}")
        print(f"  ✅ CSV saved: {csv_file}")
        print("="*80)
    else:
        print("\n❌ Failed to generate results.")

if __name__ == "__main__":
    main()
