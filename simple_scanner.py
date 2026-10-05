#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Simplified Standalone Version
Uses basic technical indicators with pandas/numpy only
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
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Import yfinance
import yfinance as yf

# Stock universe from the main app
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS'
]

class SimpleIndicators:
    """Simple technical indicator calculations using pandas/numpy"""

    @staticmethod
    def rsi(series, period=14):
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def sma(series, period):
        """Calculate Simple Moving Average"""
        return series.rolling(window=period).mean()

    @staticmethod
    def ema(series, period):
        """Calculate Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(series, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    @staticmethod
    def adx(high, low, close, period=14):
        """Simplified ADX calculation"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        up_move = high.diff()
        down_move = -low.diff()

        pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        tr_sum = pd.Series(tr).rolling(period).sum()
        pos_di = 100 * pd.Series(pos_dm).rolling(period).sum() / tr_sum
        neg_di = 100 * pd.Series(neg_dm).rolling(period).sum() / tr_sum

        di_diff = abs(pos_di - neg_di)
        di_sum = pos_di + neg_di
        dx = 100 * di_diff / di_sum

        return dx.rolling(period).mean()


class SimplePCSScanner:
    """Simplified PCS Scanner without ta library dependency"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.indicators = SimpleIndicators()

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch and calculate indicators for stock"""
        try:
            data = yf.download(symbol, period=period, interval="1d", progress=False)
            if data is None or len(data) < 20:
                return None

            # Calculate indicators
            data['RSI'] = self.indicators.rsi(data['Close'])
            data['SMA_20'] = self.indicators.sma(data['Close'], 20)
            data['SMA_50'] = self.indicators.sma(data['Close'], 50)
            data['EMA_20'] = self.indicators.ema(data['Close'], 20)

            macd, signal, hist = self.indicators.macd(data['Close'])
            data['MACD'] = macd
            data['MACD_signal'] = signal
            data['MACD_hist'] = hist

            data['ADX'] = self.indicators.adx(data['High'], data['Low'], data['Close'])

            return data
        except Exception as e:
            print(f"    Error fetching {symbol}: {str(e)[:50]}")
            return None

    def check_basic_criteria(self, data, symbol):
        """Check if stock meets basic criteria"""
        if data is None or len(data) < 20:
            return False, {}

        try:
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].tail(21).mean()

            # Filter criteria (matching defaults from Streamlit app)
            rsi_ok = 30 <= current_rsi <= 75
            adx_ok = current_adx >= 20
            volume_ok = current_volume >= (avg_volume * 1.2)

            return (rsi_ok and adx_ok and volume_ok), {
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': current_volume / avg_volume
            }
        except:
            return False, {}

    def detect_breakout(self, data):
        """Simple breakout detection"""
        if len(data) < 22:
            return False, 0

        try:
            # Current day
            current_day = data.iloc[-1]
            lookback_data = data.iloc[:-1].tail(20)

            # Resistance from last 20 days
            resistance = lookback_data['High'].max()
            support = lookback_data['Low'].min()

            # Check if current day broke resistance
            if current_day['Close'] > resistance * 1.005:  # 0.5% above
                breakout_strength = ((current_day['Close'] - resistance) / resistance) * 100
                strength = min(100, 50 + (breakout_strength * 5))
                return True, strength

            return False, 0
        except:
            return False, 0


class TelegramScanner:
    """Main scanner with Telegram integration"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.scanner = SimplePCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')
        self.telegram_enabled = bool(self.bot_token and self.chat_id)

        if not self.telegram_enabled:
            print("⚠️  Telegram credentials not set (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
            print("   Running in dry-run mode - results shown in terminal and saved to file")

    def send_telegram_message(self, message):
        """Send message to Telegram"""
        if not self.telegram_enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False

    def format_message(self, results):
        """Format results for Telegram"""
        if not results:
            return "❌ No stocks found matching criteria."

        lines = []
        lines.append("🎯 <b>NSE F&O PCS Scan Results</b>")
        lines.append(f"📅 {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}")
        lines.append("")
        lines.append(f"📊 Found <b>{len(results)} stocks</b>")
        lines.append("")

        # Sort by strength
        results.sort(key=lambda x: x['strength'], reverse=True)

        for i, result in enumerate(results, 1):
            symbol = result['symbol'].replace('.NS', '')
            price = result['metrics']['price']
            strength = result['strength']
            rsi = result['metrics']['rsi']
            lines.append(f"{i}. <b>{symbol}</b> @ ₹{price:.2f} (Strength: {strength:.0f}%, RSI: {rsi:.1f})")

        lines.append("")
        lines.append(f"📈 Avg Strength: {np.mean([r['strength'] for r in results]):.1f}%")

        return "\n".join(lines)

    def run_scan(self, stocks, limit=None):
        """Run the scanner"""
        stocks_to_scan = stocks[:limit] if limit else stocks
        results = []

        print(f"🚀 Scanning {len(stocks_to_scan)} stocks...")

        for i, symbol in enumerate(stocks_to_scan, 1):
            clean_symbol = symbol.replace('.NS', '')
            print(f"  [{i:2d}/{len(stocks_to_scan)}] {clean_symbol:12s}", end=' ', flush=True)

            try:
                # Get data and check criteria
                data = self.scanner.get_stock_data(symbol)
                if data is None:
                    print("❌ No data")
                    continue

                criteria_met, metrics = self.scanner.check_basic_criteria(data, symbol)
                if not criteria_met:
                    print(f"❌ Criteria")
                    continue

                # Detect breakout
                breakout, strength = self.scanner.detect_breakout(data)
                if not breakout or strength < 50:
                    print(f"❌ Breakout")
                    continue

                # Add to results
                results.append({
                    'symbol': symbol,
                    'strength': strength,
                    'metrics': metrics
                })
                print(f"✅ ({strength:.0f}%)")

            except Exception as e:
                print(f"⚠️  Error")

        print(f"\n✅ Found {len(results)} qualifying stocks\n")
        return results

    def save_results(self, results):
        """Save results to CSV"""
        if not results:
            return None

        df = pd.DataFrame([{
            'Symbol': r['symbol'].replace('.NS', ''),
            'Price': f"₹{r['metrics']['price']:.2f}",
            'Strength': f"{r['strength']:.0f}%",
            'RSI': f"{r['metrics']['rsi']:.1f}",
            'ADX': f"{r['metrics'].get('adx', 0):.1f}",
            'Volume_Ratio': f"{r['metrics']['volume_ratio']:.1f}x"
        } for r in sorted(results, key=lambda x: x['strength'], reverse=True)])

        filename = f"scan_results_{datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"📁 Results saved to: {filename}")
        return filename

    def execute(self, limit=30):
        """Execute complete scan"""
        print("\n" + "="*70)
        print("NSE F&O PCS SCANNER - STANDALONE MODE")
        print("="*70 + "\n")

        results = self.run_scan(COMPLETE_NSE_FO_UNIVERSE, limit)

        # Format message
        message = self.format_message(results)

        # Show in terminal
        print("📋 SCAN RESULTS:")
        print("="*70)
        print(message.replace('<b>', '').replace('</b>', '').replace('<br>', '\n'))
        print("="*70 + "\n")

        # Save to file
        csv_file = self.save_results(results)

        # Send to Telegram
        if self.telegram_enabled and results:
            print("📱 Sending to Telegram...", end=' ', flush=True)
            if self.send_telegram_message(message):
                print("✅ Sent!")
            else:
                print("❌ Failed")

        return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner')
    parser.add_argument('--limit', type=int, default=30, help='Number of stocks to scan')
    parser.add_argument('--all', action='store_true', help='Scan all stocks')

    args = parser.parse_args()
    limit = len(COMPLETE_NSE_FO_UNIVERSE) if args.all else args.limit

    scanner = TelegramScanner()
    results = scanner.execute(limit)

    sys.exit(0 if results else 1)
