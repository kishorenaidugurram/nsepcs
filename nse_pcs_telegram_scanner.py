#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Integration
Runs the professional PCS scanner and sends results to Telegram

Usage:
    python3 nse_pcs_telegram_scanner.py

Environment Variables:
    TELEGRAM_BOT_TOKEN: Your Telegram bot token (from BotFather)
    TELEGRAM_CHAT_ID: Your Telegram chat ID (target recipient)

Example:
    export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'
    export TELEGRAM_CHAT_ID='YOUR_CHAT_ID'
    python3 nse_pcs_telegram_scanner.py
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import standard libraries first
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
import json
import yfinance as yf
from bs4 import BeautifulSoup
import re
from io import BytesIO
import openpyxl
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema
from concurrent.futures import ThreadPoolExecutor, as_completed

# Create a minimal ta module implementation
class _TAMomentum:
    @staticmethod
    def RSIIndicator(close, **kwargs):
        window = kwargs.get('window', 14)
        deltas = close.diff()
        seed = deltas[:window + 1]
        up = seed[seed >= 0].sum() / window
        down = -seed[seed < 0].sum() / window
        rs = up / down if down != 0 else 100
        rsi = np.zeros_like(close, dtype=float)
        rsi[:window] = 100.0 - 100.0 / (1.0 + rs)
        for i in range(window, len(close)):
            delta = deltas.iloc[i]
            upval = delta if delta > 0 else 0.
            downval = -delta if delta < 0 else 0.
            up = (up * (window - 1) + upval) / window
            down = (down * (window - 1) + downval) / window
            rs = up / down if down != 0 else 100
            rsi[i] = 100.0 - 100.0 / (1.0 + rs)
        class RSI:
            def __init__(self, v): self._v = pd.Series(rsi, index=close.index)
            def rsi(self): return self._v
        return RSI(None)

    @staticmethod
    def StochasticOscillator(high, low, close, **kwargs):
        window = kwargs.get('window', 14)
        low_min = low.rolling(window=window).min()
        high_max = high.rolling(window=window).max()
        k = 100 * (close - low_min) / (high_max - low_min)
        k = k.rolling(window=3).mean()
        class Stoch:
            def __init__(self, v): self._v = k.fillna(method='bfill').fillna(method='ffill')
            def stoch(self): return self._v
        return Stoch(None)

    @staticmethod
    def WilliamsRIndicator(high, low, close, **kwargs):
        window = kwargs.get('window', 14)
        high_max = high.rolling(window=window).max()
        low_min = low.rolling(window=window).min()
        wr = -100 * (high_max - close) / (high_max - low_min)
        class WR:
            def __init__(self, v): self._v = wr.fillna(method='bfill').fillna(method='ffill')
            def williams_r(self): return self._v
        return WR(None)

class _TATrend:
    @staticmethod
    def SMAIndicator(close, window=20):
        class SMA:
            def __init__(self, v): self._v = v.rolling(window=window).mean()
            def sma_indicator(self): return self._v
        return SMA(close)

    @staticmethod
    def EMAIndicator(close, window=20):
        class EMA:
            def __init__(self, v): self._v = v.ewm(span=window, adjust=False).mean()
            def ema_indicator(self): return self._v
        return EMA(close)

    @staticmethod
    def MACD(close, **kwargs):
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal
        class MACD:
            def macd(self): return macd_line
            def macd_signal(self): return signal
            def macd_diff(self): return hist
        return MACD()

    @staticmethod
    def ADXIndicator(high, low, close):
        window = 14
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
        atr = pd.Series(tr).rolling(window=window).mean()
        plus_di = 100 * pd.Series(plus_dm).rolling(window=window).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=window).mean() / atr
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=window).mean()
        class ADX:
            def adx(self): return adx.fillna(method='bfill').fillna(method='ffill')
        return ADX()

class _TAVolatility:
    @staticmethod
    def BollingerBands(close, **kwargs):
        window = 20
        middle = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        class BB:
            def bollinger_hband(self): return upper
            def bollinger_lband(self): return lower
            def bollinger_mavg(self): return middle
        return BB()

    @staticmethod
    def AverageTrueRange(high, low, close):
        window = 14
        tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
        atr = pd.Series(tr).rolling(window=window).mean()
        class ATR:
            def average_true_range(self): return atr.fillna(method='bfill').fillna(method='ffill')
        return ATR()

class ta:
    momentum = _TAMomentum
    trend = _TATrend
    volatility = _TAVolatility

sys.modules['ta'] = ta

# Load the scanner
with open(os.path.join(os.path.dirname(__file__), 'streamlit_app.py'), 'r') as f:
    content = f.read()

import_section = content.split('if __name__ == "__main__":')[0]
namespace = {
    'yf': yf, 'pd': pd, 'np': np, 'datetime': datetime, 'timedelta': timedelta,
    'pytz': pytz, 'requests': requests, 'json': json, 'ta': ta,
    'BeautifulSoup': BeautifulSoup, 're': re, 'warnings': warnings,
    'ThreadPoolExecutor': ThreadPoolExecutor, 'as_completed': as_completed,
    'KMeans': KMeans, 'argrelextrema': argrelextrema, 'BytesIO': BytesIO,
    'openpyxl': openpyxl,
    'st': type('st', (), {'set_page_config': lambda *a, **k: None, 'markdown': lambda *a, **k: None})(),
}

try:
    exec(import_section, namespace)
except Exception as e:
    print(f"Error loading scanner: {e}")
    sys.exit(1)

ProfessionalPCSScanner = namespace.get('ProfessionalPCSScanner')
COMPLETE_NSE_FO_UNIVERSE = namespace.get('COMPLETE_NSE_FO_UNIVERSE', [])

if not ProfessionalPCSScanner:
    print("Error: Could not load ProfessionalPCSScanner")
    sys.exit(1)


class TelegramNotifier:
    """Send scan results to Telegram"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def is_configured(self):
        """Check if Telegram credentials are set"""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text):
        """Send a message to Telegram"""
        if not self.is_configured():
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def send_results(self, results):
        """Send scan results to Telegram"""
        if not results:
            self.send_message("🔴 NSE PCS Scanner: No stocks found matching filter criteria")
            return

        ist = pytz.timezone('Asia/Kolkata')
        header = f"""
🎯 <b>NSE F&O PCS Scan Results</b>
📅 {datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')}

📊 Found <b>{len(results)} stocks</b> with confirmed patterns
"""
        self.send_message(header)

        # Send top 15 stocks
        for i, result in enumerate(results[:15], 1):
            symbol = result['symbol'].replace('.NS', '').replace('^', '')
            strength = max(p['strength'] for p in result['patterns'])
            pattern = max(result['patterns'], key=lambda x: x['strength'])['type']

            msg = f"<b>{i}. {symbol}</b>\n"
            msg += f"💰 ₹{result['current_price']:.2f} | RSI:{result['rsi']:.0f} | ADX:{result['adx']:.0f}\n"
            msg += f"📊 Vol:{result['volume_ratio']:.1f}x | 🎯 {pattern} ({strength:.0f}%)"
            self.send_message(msg)

        if len(results) > 15:
            self.send_message(f"<i>... and {len(results) - 15} more stocks available</i>")


def run_scanner(num_stocks=50):
    """Run the PCS scanner"""
    ist = pytz.timezone('Asia/Kolkata')
    print("\n" + "="*100)
    print(f"🚀 NSE F&O PCS Scanner | {datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')}")
    print("="*100 + "\n")

    scanner = ProfessionalPCSScanner()

    # Recommended filter configuration
    config = {
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
            'inverted_scallop': True,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
    }

    print(f"Filter Configuration:")
    print(f"  • RSI Range: {config['rsi_min']} to {config['rsi_max']}")
    print(f"  • ADX Minimum: {config['adx_min']}")
    print(f"  • Min Volume Ratio: {config['min_volume_ratio']}x")
    print(f"  • Pattern Strength Min: {config['pattern_strength_min']}%")
    print(f"  • Analysis Mode: {config['analysis_mode']}\n")

    results = []
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:num_stocks]
    total = len(stocks_to_scan)

    print(f"Scanning {total} stocks from F&O universe...")
    print("-" * 100)

    for i, symbol in enumerate(stocks_to_scan, 1):
        clean = symbol.replace('.NS', '').replace('^', '')
        print(f"[{i:2d}/{total}] {clean:12s} ", end='', flush=True)

        try:
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or data.empty:
                print("❌ No data")
                continue

            vol_ok, vol_ratio, vol_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not vol_ok:
                print("❌ Low volume")
                continue

            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                print("❌ No patterns")
                continue

            result = {
                'symbol': symbol,
                'current_price': data['Close'].iloc[-1],
                'volume_ratio': vol_ratio,
                'rsi': data['RSI'].iloc[-1],
                'adx': data['ADX'].iloc[-1],
                'patterns': patterns,
                'data': data,
            }

            results.append(result)
            strength = max(p['strength'] for p in patterns)
            print(f"✅ {len(patterns)} pattern(s) ({strength:.0f}%)")

        except Exception as e:
            print(f"❌ Error")
            continue

    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    print("-" * 100)
    print(f"\n✅ Scan Complete: Found {len(results)} stocks with patterns\n")

    return results


def format_results(results):
    """Format results as text"""
    if not results:
        return "No stocks found matching filter criteria"

    ist = pytz.timezone('Asia/Kolkata')
    lines = ["\n" + "="*110]
    lines.append(f"NSE F&O PCS SCAN RESULTS")
    lines.append(f"Time: {datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')}")
    lines.append(f"Stocks Found: {len(results)}")
    lines.append("="*110 + "\n")

    for i, r in enumerate(results, 1):
        symbol = r['symbol'].replace('.NS', '').replace('^', '')
        strength = max(p['strength'] for p in r['patterns'])
        pattern = max(r['patterns'], key=lambda x: x['strength'])['type']

        line = f"{i:3d}. {symbol:12s} | ₹{r['current_price']:8.2f} | "
        line += f"RSI:{r['rsi']:5.1f} | ADX:{r['adx']:5.1f} | "
        line += f"Vol:{r['volume_ratio']:5.2f}x | {pattern[:30]:30s} ({strength:3.0f}%)"
        lines.append(line)

    return "\n".join(lines)


def main():
    """Main execution"""
    try:
        print("\n✅ Scanner initialized successfully")
        print(f"✅ Stock universe: {len(COMPLETE_NSE_FO_UNIVERSE)} F&O stocks\n")

        results = run_scanner(num_stocks=50)

        # Display results
        text = format_results(results)
        print(text)

        # Save to file
        ist = pytz.timezone('Asia/Kolkata')
        ts = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        results_file = f'pcs_scan_results_{ts}.txt'

        with open(results_file, 'w') as f:
            f.write(text)
        print(f"\n💾 Results saved to: {results_file}")

        # Export to CSV
        if results:
            csv_file = f'pcs_scan_results_{ts}.csv'
            data = []
            for r in results:
                strength = max(p['strength'] for p in r['patterns'])
                pattern = max(r['patterns'], key=lambda x: x['strength'])['type']
                data.append({
                    'Symbol': r['symbol'].replace('.NS', '').replace('^', ''),
                    'Price': f"{r['current_price']:.2f}",
                    'RSI': f"{r['rsi']:.1f}",
                    'ADX': f"{r['adx']:.1f}",
                    'Volume': f"{r['volume_ratio']:.2f}x",
                    'Pattern': pattern,
                    'Strength': f"{strength:.0f}%",
                    'NumPatterns': len(r['patterns']),
                })

            pd.DataFrame(data).to_csv(csv_file, index=False)
            print(f"📊 CSV exported to: {csv_file}")

        # Send to Telegram
        notifier = TelegramNotifier()
        if notifier.is_configured():
            print("\n📤 Sending results to Telegram...")
            notifier.send_results(results)
            print("✅ Telegram notification sent!")
        else:
            print("\n⚠️  Telegram not configured")
            print("   To enable Telegram notifications, set these environment variables:")
            print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")

        print(f"\n✅ Process completed successfully!")
        print(f"   Scanned: 50 stocks")
        print(f"   Found: {len(results)} stocks with patterns")

        return results

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    main()
