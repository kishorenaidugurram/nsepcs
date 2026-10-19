#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Automated Telegram Reporter
Runs the stock scanner and sends filtered results to Telegram
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
import pytz
import numpy as np
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Simple technical indicator implementations
def calculate_rsi(prices, window=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper, sma, lower

def calculate_adx(high, low, close, window=14):
    """Calculate ADX indicator (simplified)"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()

    # For simplicity, return a simple momentum indicator
    return close.pct_change().rolling(window=window).std() * 100

def calculate_macd(prices, fast=12, slow=26):
    """Calculate MACD"""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    return macd

# Import the scanner class from the main app
sys.path.insert(0, '/home/user/nsepcs')

# Configuration
DEFAULT_CONFIG = {
    'min_pcs_score': 55,
    'min_volume_ratio': 1.5,
    'liquidity_tier': 1,
    'max_stocks': 40,
    'pattern_strength_threshold': 65,
    'min_rsi': 30,
    'max_rsi': 80,
}

# NSE F&O Stocks (Tier 1 - Ultra High Liquidity)
TIER1_STOCKS = ['NIFTY', 'BANKNIFTY', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
                 'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS']

# Read Telegram credentials from environment or config
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

class SimpleStockScanner:
    """Simplified scanner for standalone operation"""

    def __init__(self):
        self.cache = {}

    def get_stock_data(self, symbol, period="3mo", interval="1d"):
        """Fetch stock data from Yahoo Finance"""
        try:
            if symbol in self.cache:
                return self.cache[symbol]

            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data is None or len(data) == 0:
                return None

            # Calculate technical indicators
            data['RSI'] = calculate_rsi(data['Close'])
            data['MACD'] = calculate_macd(data['Close'])
            data['BB_High'], data['BB_Mid'], data['BB_Low'] = calculate_bollinger_bands(data['Close'])
            data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['SMA50'] = data['Close'].rolling(window=50).mean()
            data['Volume_MA'] = data['Volume'].rolling(window=20).mean()

            self.cache[symbol] = data
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def check_volume_criteria(self, data, min_ratio=1.5):
        """Check if current day volume meets criteria"""
        try:
            current_volume = data['Volume'].iloc[-1]
            volume_ma = data['Volume_MA'].iloc[-2]

            if volume_ma == 0:
                return False, 0, {}

            volume_ratio = current_volume / volume_ma
            volume_ok = volume_ratio >= min_ratio

            return volume_ok, volume_ratio, {
                'current_volume': int(current_volume),
                'average_volume': int(volume_ma),
                'ratio': volume_ratio
            }
        except Exception as e:
            return False, 0, {}

    def detect_simple_patterns(self, data, config):
        """Detect simple bullish patterns"""
        patterns = []
        try:
            close = data['Close']
            rsi = data['RSI']

            # Current day metrics
            current_close = close.iloc[-1]
            current_rsi = rsi.iloc[-1]
            prev_close = close.iloc[-2]

            # Pattern 1: Bullish momentum with good RSI
            if current_rsi > config['min_rsi'] and current_rsi < config['max_rsi']:
                if current_close > prev_close:
                    strength = (current_rsi - config['min_rsi']) / (config['max_rsi'] - config['min_rsi']) * 100
                    patterns.append({
                        'type': 'Bullish Momentum',
                        'strength': min(strength, 100),
                        'confidence': 'HIGH' if strength > 80 else 'MEDIUM' if strength > 60 else 'LOW'
                    })

            # Pattern 2: Support bounce
            sma20 = data['SMA20'].iloc[-1]
            if current_close > sma20 and close.iloc[-2] <= sma20:
                patterns.append({
                    'type': 'Support Bounce',
                    'strength': 75,
                    'confidence': 'HIGH'
                })

            # Pattern 3: Volume breakout
            vol_ma = data['Volume_MA'].iloc[-1]
            if data['Volume'].iloc[-1] > vol_ma * 1.5:
                patterns.append({
                    'type': 'Volume Breakout',
                    'strength': 80,
                    'confidence': 'HIGH'
                })

            return patterns
        except Exception as e:
            return []

    def analyze_stock(self, symbol, config):
        """Analyze a single stock"""
        try:
            # Get data
            data = self.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            # Check volume
            volume_ok, volume_ratio, _ = self.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                return None

            # Detect patterns
            patterns = self.detect_simple_patterns(data, config)
            if not patterns:
                return None

            # Get current metrics
            max_strength = max(p['strength'] for p in patterns)
            if max_strength < config['pattern_strength_threshold']:
                return None

            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            return {
                'symbol': symbol,
                'current_price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': patterns,
                'max_strength': max_strength
            }
        except Exception as e:
            return None

def send_telegram_message(text, parse_mode='HTML'):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured. Results won't be sent.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def format_results_for_telegram(results):
    """Format scan results for Telegram message"""
    if not results:
        return "🔴 No stocks met the criteria in today's scan."

    message = f"<b>📈 NSE F&O PCS Scanner Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b>\n\n"
    message += f"✅ Found <b>{len(results)}</b> stocks meeting filter criteria\n\n"

    # Group by confidence
    high_conf = [r for r in results if max(p['strength'] for p in r['patterns']) >= 80]
    med_conf = [r for r in results if 60 <= max(p['strength'] for p in r['patterns']) < 80]

    if high_conf:
        message += "<b>🔥 HIGH CONFIDENCE ({}):</b>\n".format(len(high_conf))
        for result in sorted(high_conf, key=lambda x: x['max_strength'], reverse=True)[:5]:
            symbol = result['symbol'].replace('.NS', '')
            message += f"• <code>{symbol}</code> - ₹{result['current_price']:.2f} | RSI: {result['rsi']:.1f} | Vol: {result['volume_ratio']:.1f}x\n"
        message += "\n"

    if med_conf:
        message += "<b>🟡 MEDIUM CONFIDENCE ({}):</b>\n".format(len(med_conf))
        for result in sorted(med_conf, key=lambda x: x['max_strength'], reverse=True)[:5]:
            symbol = result['symbol'].replace('.NS', '')
            message += f"• <code>{symbol}</code> - ₹{result['current_price']:.2f} | RSI: {result['rsi']:.1f} | Vol: {result['volume_ratio']:.1f}x\n"
        message += "\n"

    message += "---\n"
    message += "⚠️  <i>This is not financial advice. Always do your own research before trading.</i>"

    return message

def run_scanner(stocks, config):
    """Run the scanner on a list of stocks"""
    scanner = SimpleStockScanner()
    results = []

    print(f"\n🚀 Starting scan of {len(stocks)} stocks...")
    print(f"📊 Filters: Min Pattern Strength = {config['pattern_strength_threshold']}%, Min Volume Ratio = {config['min_volume_ratio']}x")

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_symbol = {executor.submit(scanner.analyze_stock, symbol, config): symbol for symbol in stocks}

        completed = 0
        for future in as_completed(future_to_symbol):
            completed += 1
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    max_strength = result['max_strength']
                    print(f"✅ {symbol.replace('.NS', '')} - Strength: {max_strength:.0f}%")
                else:
                    print(f"⏭️  {symbol.replace('.NS', '')} - No patterns found")
            except Exception as e:
                print(f"❌ {symbol} - Error: {e}")

            # Print progress
            if completed % 5 == 0:
                print(f"Progress: {completed}/{len(stocks)}")

    return results

def save_results_to_file(results):
    """Save scan results to a JSON file"""
    try:
        import json
        from datetime import datetime

        # Create results directory if it doesn't exist
        results_dir = '/tmp/nsepcs_results'
        os.makedirs(results_dir, exist_ok=True)

        # Prepare data
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_stocks_found': len(results),
            'scan_config': DEFAULT_CONFIG,
            'stocks': []
        }

        for result in results:
            output_data['stocks'].append({
                'symbol': result['symbol'],
                'price': float(result['current_price']),
                'rsi': float(result['rsi']),
                'adx': float(result['adx']),
                'volume_ratio': float(result['volume_ratio']),
                'max_strength': float(result['max_strength']),
                'patterns': result['patterns']
            })

        # Save to file
        filename = f"{results_dir}/scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"✅ Results saved to: {filename}")
        return filename
    except Exception as e:
        print(f"⚠️  Could not save results to file: {e}")
        return None

def create_summary_report(results):
    """Create a text summary report"""
    try:
        from datetime import datetime

        # Create results directory if it doesn't exist
        results_dir = '/tmp/nsepcs_results'
        os.makedirs(results_dir, exist_ok=True)

        # Build report
        report = f"""NSE F&O PCS SCANNER REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

SCAN CONFIGURATION:
- Min Pattern Strength: {DEFAULT_CONFIG['pattern_strength_threshold']}%
- Min Volume Ratio: {DEFAULT_CONFIG['min_volume_ratio']}x
- Min RSI: {DEFAULT_CONFIG['min_rsi']}
- Max RSI: {DEFAULT_CONFIG['max_rsi']}

RESULTS SUMMARY:
- Total Stocks Found: {len(results)}

STOCKS MEETING CRITERIA:
"""

        if results:
            for result in sorted(results, key=lambda x: x['max_strength'], reverse=True):
                symbol = result['symbol'].replace('.NS', '')
                report += f"\n{symbol:12} | Price: ₹{result['current_price']:8.2f} | RSI: {result['rsi']:5.1f} | Vol: {result['volume_ratio']:4.1f}x | Strength: {result['max_strength']:5.1f}%\n"
                for pattern in result['patterns']:
                    report += f"              └─ {pattern['type']}: {pattern['strength']:.0f}% ({pattern['confidence']})\n"
        else:
            report += "\nNo stocks met the criteria."

        report += f"\n{'='*60}\nNOTE: This is not financial advice. Always do your own research.\n"

        # Save to file
        filename = f"{results_dir}/scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report)

        print(f"✅ Report saved to: {filename}")
        return filename, report
    except Exception as e:
        print(f"⚠️  Could not create report: {e}")
        return None, None

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("NSE F&O PCS Scanner - Telegram Reporter")
    print("="*60)

    # Check Telegram configuration
    print("\n📋 Configuration Check:")
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("✅ Telegram credentials found")
    else:
        print("⚠️  Telegram not configured. See TELEGRAM_SETUP.md for instructions.")
        print("   Results will be saved locally but not sent to Telegram.")

    # Use Tier 1 stocks for quick scan
    stocks_to_scan = TIER1_STOCKS[:20]  # First 20 stocks for speed

    # Run scanner
    results = run_scanner(stocks_to_scan, DEFAULT_CONFIG)

    # Format results
    message = format_results_for_telegram(results)

    # Save results locally
    print("\n💾 Saving results...")
    save_results_to_file(results)
    report_file, report_text = create_summary_report(results)

    # Print to console
    print("\n" + "="*60)
    print("SCAN RESULTS")
    print("="*60)
    print(message.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', '').replace('<i>', '').replace('</i>', ''))

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        if results:
            print("\n📤 Sending results to Telegram...")
            if send_telegram_message(message):
                print("✅ Results sent to Telegram successfully!")
            else:
                print("⚠️  Could not send to Telegram (network error)")
        else:
            print("\n📤 Sending 'No results' message to Telegram...")
            if send_telegram_message(message):
                print("✅ Message sent to Telegram")
    else:
        print("\n⏭️  Skipping Telegram notification (not configured)")

    print("\n✅ Scan completed!")
    print(f"📂 Check /tmp/nsepcs_results/ for detailed results")
    return results

if __name__ == "__main__":
    results = main()
