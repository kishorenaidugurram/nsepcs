#!/usr/bin/env python3
"""
Simple NSE F&O Scanner - No external TA library required
Screens stocks based on basic technical criteria
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
import pytz
import warnings
warnings.filterwarnings('ignore')

# Manual installation check with helpful message
def check_dependencies():
    """Check and install dependencies"""
    packages = {
        'yfinance': 'yfinance',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'requests': 'requests'
    }

    missing = []
    for import_name, package_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        print(f"⚠️ Missing packages: {', '.join(missing)}")
        print(f"\nInstall with: pip install --user {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

import yfinance as yf
import pandas as pd
import numpy as np
import requests

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# NSE F&O Stock Universe (Top 50 for quick testing)
TOP_NSE_FO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATASTEEL.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'M&M.NS',
    'BPCL.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS',
    'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS', 'HDFCLIFE.NS',
    'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS', 'ADANIGREEN.NS'
]

class SimpleScanner:
    """Simple stock scanner without complex TA indicators"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def calculate_sma(self, data, window):
        """Calculate Simple Moving Average"""
        return data['Close'].rolling(window=window).mean()

    def calculate_rsi(self, data, window=14):
        """Calculate Relative Strength Index"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, data):
        """Calculate MACD indicator"""
        ema_12 = data['Close'].ewm(span=12).mean()
        ema_26 = data['Close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        return macd, signal

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch stock data"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)

            if len(data) < 30:
                return None

            return data
        except Exception as e:
            return None

    def analyze_stock(self, symbol, filters):
        """Analyze a single stock"""
        try:
            data = self.get_stock_data(symbol)
            if data is None:
                return None

            # Get latest values
            current_price = data['Close'].iloc[-1]
            sma_20 = self.calculate_sma(data, 20).iloc[-1]
            sma_50 = self.calculate_sma(data, 50).iloc[-1]
            rsi = self.calculate_rsi(data).iloc[-1]
            macd, macd_signal = self.calculate_macd(data)

            current_macd = macd.iloc[-1]
            current_signal = macd_signal.iloc[-1]

            # Volume analysis
            current_volume = data['Volume'].iloc[-1]
            avg_volume_20 = data['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume_20

            # Score calculation
            score = 0
            signals = []

            # Check filters
            if filters['rsi_min'] <= rsi <= filters['rsi_max']:
                score += 25
                signals.append(f"RSI: {rsi:.1f}")

            if current_price > sma_20:
                score += 20
                signals.append("Price > SMA20")

            if sma_20 > sma_50:
                score += 20
                signals.append("SMA20 > SMA50")

            if current_macd > current_signal:
                score += 15
                signals.append("MACD Bullish")

            if volume_ratio >= filters['volume_ratio']:
                score += 20
                signals.append(f"Volume: {volume_ratio:.2f}x")

            if score >= filters['min_score']:
                return {
                    'symbol': symbol,
                    'price': current_price,
                    'rsi': rsi,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'macd': current_macd,
                    'volume_ratio': volume_ratio,
                    'score': score,
                    'signals': signals
                }

            return None

        except Exception as e:
            print(f"  ❌ Error analyzing {symbol}: {str(e)}")
            return None

    def send_telegram(self, message):
        """Send message to Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return False

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram error: {str(e)}")
            return False

    def format_message(self, stocks):
        """Format results for Telegram"""
        if not stocks:
            return """<b>📊 NSE F&O Scanner Results</b>
<i>Generated: {}</i>

❌ No stocks met today's criteria.""".format(
                datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST'))

        stocks_sorted = sorted(stocks, key=lambda x: x['score'], reverse=True)

        message = f"""<b>📊 NSE F&O Scanner Results</b>
<i>Generated: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')}</i>

<b>✅ Found {len(stocks)} qualifying stocks</b>

"""

        for stock in stocks_sorted[:10]:
            message += f"""<code>{stock['symbol'].replace('.NS', '')}</code>
  💰 ₹{stock['price']:.2f}
  📈 Score: {stock['score']}/100
  📊 RSI: {stock['rsi']:.1f}
  📍 SMA20: ₹{stock['sma_20']:.2f}
  🔊 Volume: {stock['volume_ratio']:.2f}x
  ✨ {', '.join(stock['signals'][:3])}

"""

        if len(stocks) > 10:
            message += f"\n📌 ... and {len(stocks) - 10} more stocks\n"

        return message

    def run(self, filters=None):
        """Run scanner"""
        if filters is None:
            filters = {
                'rsi_min': 35,
                'rsi_max': 70,
                'volume_ratio': 1.2,
                'min_score': 60
            }

        print(f"\n{'='*60}")
        print(f"🚀 NSE F&O Stock Scanner")
        print(f"{'='*60}")
        print(f"📋 Scanning {len(TOP_NSE_FO_STOCKS)} stocks...")
        print(f"Filters: RSI({filters['rsi_min']}-{filters['rsi_max']}), "
              f"Volume(≥{filters['volume_ratio']}x), Score(≥{filters['min_score']})")
        print(f"{'='*60}\n")

        qualified_stocks = []

        for idx, symbol in enumerate(TOP_NSE_FO_STOCKS, 1):
            print(f"[{idx:2d}/{len(TOP_NSE_FO_STOCKS)}] Analyzing {symbol:15s} ...", end=' ')

            result = self.analyze_stock(symbol, filters)

            if result:
                print(f"✅ Score: {result['score']}")
                qualified_stocks.append(result)
            else:
                print("⏭️")

            time.sleep(0.3)  # Rate limiting

        print(f"\n{'='*60}")
        print(f"📈 RESULTS")
        print(f"{'='*60}")
        print(f"✅ Qualified stocks: {len(qualified_stocks)}\n")

        if qualified_stocks:
            qualified_stocks.sort(key=lambda x: x['score'], reverse=True)

            print("Top stocks by score:")
            for stock in qualified_stocks[:5]:
                print(f"  {stock['symbol']:15s} - Score: {stock['score']:3.0f}, "
                      f"RSI: {stock['rsi']:5.1f}, Vol: {stock['volume_ratio']:4.2f}x")

            print("\nAll qualified stocks:")
            for stock in qualified_stocks:
                print(f"  • {stock['symbol']}")

        # Save to file
        self.save_results(qualified_stocks)

        # Send to Telegram
        message = self.format_message(qualified_stocks)

        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            print(f"\n📱 Sending results to Telegram...")
            if self.send_telegram(message):
                print("✅ Results sent to Telegram!")
            else:
                print("❌ Failed to send to Telegram")
        else:
            print("\n⚠️  Telegram not configured")
            print("    Set: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

        return qualified_stocks

    def save_results(self, stocks):
        """Save results to CSV"""
        if not stocks:
            return

        df = pd.DataFrame([
            {
                'Symbol': s['symbol'],
                'Price': s['price'],
                'RSI': s['rsi'],
                'SMA20': s['sma_20'],
                'SMA50': s['sma_50'],
                'Volume_Ratio': s['volume_ratio'],
                'Score': s['score'],
                'Signals': ', '.join(s['signals'])
            }
            for s in stocks
        ])

        df = df.sort_values('Score', ascending=False)
        filename = f"scanner_results_{datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Results saved to: {filename}")


def main():
    """Main entry point"""
    scanner = SimpleScanner()

    # Run with default filters
    scanner.run()


if __name__ == "__main__":
    main()
