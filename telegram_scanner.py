#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Integration Script
Runs stock analysis and sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure SSL for proxy
os.environ['REQUESTS_CA_BUNDLE'] = '/root/.ccr/ca-bundle.crt'
os.environ['SSL_CERT_FILE'] = '/root/.ccr/ca-bundle.crt'

# Configure yfinance to use proxy settings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


class SimpleStockAnalyzer:
    """Simple stock analyzer using basic technical indicators"""

    @staticmethod
    def calculate_rsi(closes, period=14):
        """Calculate RSI"""
        deltas = np.diff(closes)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(closes, dtype=float)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(closes)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return rsi

    @staticmethod
    def calculate_macd(closes, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = pd.Series(closes).ewm(span=fast).mean().values
        ema_slow = pd.Series(closes).ewm(span=slow).mean().values
        macd = ema_fast - ema_slow
        macd_signal = pd.Series(macd).ewm(span=signal).mean().values
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist

    @staticmethod
    def calculate_adx(high, low, close, period=14):
        """Calculate ADX (simplified)"""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = pd.Series(tr).rolling(window=period).mean().values

        up_move = high - np.roll(high, 1)
        down_move = np.roll(low, 1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr

        di_diff = np.abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        dx = 100 * di_diff / di_sum
        adx = pd.Series(dx).rolling(window=period).mean().values

        return adx, atr


class TelegramNotifier:
    """Handle Telegram notifications"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()
        self.session.verify = '/root/.ccr/ca-bundle.crt'

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = self.session.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_document(self, file_path: str, caption: str = "") -> bool:
        """Send a file to Telegram"""
        try:
            url = f"{self.base_url}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {"document": f}
                data = {
                    "chat_id": self.chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                response = self.session.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending file to Telegram: {e}")
            return False


class StockDataFetcher:
    """Fetch stock data from Yahoo Finance"""

    @staticmethod
    def fetch_data(symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """Fetch stock data"""
        try:
            import yfinance as yf

            # Configure session with SSL verification
            session = requests.Session()
            session.verify = '/root/.ccr/ca-bundle.crt'

            df = yf.download(
                symbol,
                period=period,
                progress=False,
                timeout=10,
                session=session
            )

            if df is None or len(df) < 20:
                return None

            return df
        except Exception as e:
            return None


class StockScannerCLI:
    """Command-line interface for stock scanning"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.analyzer = SimpleStockAnalyzer()

        # Default filter criteria
        self.default_filters = {
            'stocks_to_scan': [
                'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
                'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
                'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
                'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
                'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS'
            ],
            'min_rsi': 35,
            'max_rsi': 75,
            'min_adx': 20,
            'min_volume_ratio': 1.2,
            'min_price_change': 1.0,
        }

    def analyze_stock(self, symbol: str, filters: Dict) -> Optional[Dict]:
        """Analyze a single stock"""
        try:
            # Fetch data
            data = StockDataFetcher.fetch_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            # Calculate indicators
            closes = data['Close'].values
            highs = data['High'].values
            lows = data['Low'].values
            volumes = data['Volume'].values

            # RSI
            rsi = self.analyzer.calculate_rsi(closes, 14)
            current_rsi = rsi[-1]

            # ADX
            adx, atr = self.analyzer.calculate_adx(highs, lows, closes, 14)
            current_adx = adx[-1] if not np.isnan(adx[-1]) else 0

            # MACD
            macd, macd_signal, macd_hist = self.analyzer.calculate_macd(closes)
            current_macd_hist = macd_hist[-1]

            # Volume analysis
            avg_volume = volumes[-20:].mean()
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            # Price movement
            current_price = closes[-1]
            prev_close = closes[-2] if len(closes) > 1 else closes[-1]
            price_change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0

            # Filter criteria
            rsi_ok = filters['min_rsi'] <= current_rsi <= filters['max_rsi']
            adx_ok = current_adx >= filters['min_adx']
            volume_ok = volume_ratio >= filters['min_volume_ratio']
            momentum_ok = current_macd_hist > 0

            # Determine if stock passes filters
            passes_filters = rsi_ok and adx_ok and volume_ok and momentum_ok

            if not passes_filters:
                return None

            # Calculate pattern strength score (0-100)
            strength_score = 0
            reasons = []

            if rsi_ok:
                rsi_norm = (current_rsi - filters['min_rsi']) / (filters['max_rsi'] - filters['min_rsi'])
                strength_score += rsi_norm * 25
                reasons.append(f"RSI: {current_rsi:.1f}")

            if adx_ok:
                adx_norm = min(current_adx / 40, 1.0)  # Normalize to 40
                strength_score += adx_norm * 25
                reasons.append(f"ADX: {current_adx:.1f}")

            if volume_ok:
                vol_norm = min(volume_ratio / 2.0, 1.0)
                strength_score += vol_norm * 25
                reasons.append(f"Vol: {volume_ratio:.1f}x")

            if momentum_ok:
                strength_score += 25
                reasons.append("Momentum: Bullish")

            return {
                'symbol': symbol.replace('.NS', ''),
                'current_price': float(current_price),
                'volume_ratio': float(volume_ratio),
                'rsi': float(current_rsi),
                'adx': float(current_adx),
                'price_change_pct': float(price_change_pct),
                'macd_momentum': float(current_macd_hist),
                'strength_score': float(strength_score),
                'reasons': reasons,
                'passes_filters': passes_filters
            }

        except Exception as e:
            return None

    def run_scan(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Run the stock scan with given filters"""
        filters = filters or self.default_filters
        stocks = filters['stocks_to_scan']
        results = []

        print(f"\n{'='*70}")
        print(f"🚀 Starting scan of {len(stocks)} stocks")
        print(f"   Filters: RSI {filters['min_rsi']}-{filters['max_rsi']}, ADX ≥ {filters['min_adx']}")
        print(f"{'='*70}\n")

        for i, symbol in enumerate(stocks):
            progress = (i + 1) / len(stocks)
            percentage = int(progress * 100)

            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            print(f"[{percentage:3d}%] [{i+1:2d}/{len(stocks):2d}] {clean_symbol:<12}", end='', flush=True)

            try:
                result = self.analyze_stock(symbol, filters)

                if result:
                    results.append(result)
                    print(f" ✅ Score: {result['strength_score']:.0f}%")
                else:
                    print(" ⏭️  Filtered")

            except Exception as e:
                print(f" ❌ Error")
                continue

        # Sort by strength score
        results.sort(key=lambda x: x['strength_score'], reverse=True)

        print(f"\n{'='*70}")
        print(f"✅ Scan complete! Found {len(results)} stocks with patterns")
        print(f"{'='*70}\n")

        return results

    def format_results_for_telegram(self, results: List[Dict]) -> str:
        """Format scan results for Telegram message"""
        if not results:
            return "❌ No stocks found matching filter criteria"

        message = f"""
🎯 <b>NSE F&O PCS Scanner Results</b>
📅 {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')}

✅ <b>Found {len(results)} stocks matching filter criteria:</b>

"""

        for i, stock in enumerate(results[:15], 1):  # Limit to 15 for message length
            emoji = "🟢" if stock['strength_score'] >= 75 else "🟡" if stock['strength_score'] >= 60 else "🔴"

            message += f"""<b>{i}. {stock['symbol']}</b> {emoji}
   💰 Price: ₹{stock['current_price']:.2f} ({stock['price_change_pct']:+.2f}%)
   🔥 Score: {stock['strength_score']:.0f}%
   📊 RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f} | Vol: {stock['volume_ratio']:.2f}x

"""

        if len(results) > 15:
            message += f"\n📋 ... and {len(results) - 15} more stocks\n"

        message += "\n<i>📊 For detailed analysis: https://nse-fo-pcs-screener.streamlit.app</i>"
        message += "\n⏰ <i>Next scan in 24 hours</i>"

        return message

    def export_to_csv(self, results: List[Dict], filename: str = "scan_results.csv") -> Optional[str]:
        """Export results to CSV"""
        if not results:
            return None

        data = []
        for stock in results:
            data.append({
                'Symbol': stock['symbol'],
                'Price': f"₹{stock['current_price']:.2f}",
                'Change': f"{stock['price_change_pct']:+.2f}%",
                'Score': f"{stock['strength_score']:.1f}%",
                'RSI': f"{stock['rsi']:.1f}",
                'ADX': f"{stock['adx']:.1f}",
                'Volume_Ratio': f"{stock['volume_ratio']:.2f}x",
                'Timestamp': datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S')
            })

        df = pd.DataFrame(data)
        filepath = f"/tmp/claude-0/-home-user-nsepcs/8007fd3c-094f-5e9f-b77a-44528be2dbb6/scratchpad/{filename}"
        df.to_csv(filepath, index=False)
        return filepath

    def run_and_notify(self, telegram_bot_token: Optional[str] = None,
                      telegram_chat_id: Optional[str] = None):
        """Run scan and send results to Telegram"""

        # Get credentials from environment or parameters
        bot_token = telegram_bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            print("\n⚠️  Telegram credentials not found!")
            print("Please set environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            print("\nOr run with: python telegram_scanner.py --token YOUR_TOKEN --chat-id YOUR_CHAT_ID")
            return False

        # Run scan
        results = self.run_scan()

        if not results:
            print("❌ No stocks found with current filters")
            return False

        # Create notifier
        notifier = TelegramNotifier(bot_token, chat_id)

        # Format and send message
        message = self.format_results_for_telegram(results)
        print("📨 Sending results to Telegram...", end='', flush=True)
        if notifier.send_message(message):
            print(" ✅")
        else:
            print(" ❌")
            return False

        # Export and send CSV
        csv_path = self.export_to_csv(results)
        if csv_path:
            print("📎 Sending detailed CSV...", end='', flush=True)
            if notifier.send_document(csv_path, "📊 Detailed Scan Results"):
                print(" ✅\n")
            else:
                print(" ❌\n")

        print("✨ Scan and notification complete!")
        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner with Telegram integration')
    parser.add_argument('--token', help='Telegram bot token')
    parser.add_argument('--chat-id', help='Telegram chat ID')
    parser.add_argument('--no-telegram', action='store_true', help='Run scan without sending to Telegram')

    args = parser.parse_args()

    scanner = StockScannerCLI()

    if args.no_telegram:
        results = scanner.run_scan()
        if results:
            # Print formatted results to console
            print("="*70)
            print("📊 SCAN RESULTS")
            print("="*70 + "\n")
            for i, stock in enumerate(results, 1):
                emoji = "🟢" if stock['strength_score'] >= 75 else "🟡" if stock['strength_score'] >= 60 else "🔴"
                print(f"{i:2d}. {stock['symbol']:<12} {emoji} Score: {stock['strength_score']:6.1f}% | Price: ₹{stock['current_price']:8.2f} | RSI: {stock['rsi']:5.1f} | ADX: {stock['adx']:5.1f}")

            # Export CSV
            csv_path = scanner.export_to_csv(results)
            print(f"\n✅ Results exported to: {csv_path}")
    else:
        scanner.run_and_notify(args.token, args.chat_id)


if __name__ == "__main__":
    main()
