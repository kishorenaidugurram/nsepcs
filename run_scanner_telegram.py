#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Telegram Reporter
Runs the PCS scanner and sends results to Telegram
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import requests
import warnings
import time

warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Simple technical analysis functions
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i-1]
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

def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(window=period).mean().values

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = pd.Series(prices).ewm(span=fast).mean().values
    ema_slow = pd.Series(prices).ewm(span=slow).mean().values
    macd = ema_fast - ema_slow
    macd_signal = pd.Series(macd).ewm(span=signal).mean().values
    return macd, macd_signal

def get_stock_data(symbol, period="3mo"):
    """Fetch stock data and calculate technical indicators"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Calculate indicators
        close_prices = data['Close'].values

        data['RSI'] = calculate_rsi(close_prices)
        data['SMA_20'] = calculate_sma(close_prices, 20)
        data['SMA_50'] = calculate_sma(close_prices, 50)

        macd, macd_signal = calculate_macd(close_prices)
        data['MACD'] = macd
        data['MACD_signal'] = macd_signal

        # Simplified ADX (use fixed value based on volatility)
        data['ADX'] = 20 + np.std(np.diff(close_prices) / close_prices[:-1]) * 200

        # Volume ratio
        data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(window=20).mean()

        return data
    except Exception as e:
        return None

class SimplePCSScanner:
    """Simplified PCS Scanner"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def analyze_stock(self, symbol, data, filters):
        """Analyze a stock for PCS opportunities"""
        if data is None or len(data) < 20:
            return None

        try:
            current = data.iloc[-1]
            price = current['Close']
            rsi = current['RSI']
            adx = current['ADX']
            volume_ratio = current.get('Volume_Ratio', 1.0)

            # Check filters
            if pd.isna(rsi) or not (filters['rsi_min'] <= rsi <= filters['rsi_max']):
                return None

            if pd.isna(adx) or adx < filters['adx_min']:
                return None

            if volume_ratio < filters['min_volume_ratio']:
                return None

            # Calculate pattern strength
            strength = self._calculate_pattern_strength(data, rsi, adx)

            if strength < filters['pattern_strength_min']:
                return None

            result = {
                'symbol': symbol,
                'price': price,
                'rsi': rsi,
                'adx': adx,
                'volume_ratio': volume_ratio,
                'strength': strength,
                'confidence': 'HIGH' if strength >= 80 else 'MEDIUM' if strength >= 60 else 'LOW',
                'data': data
            }

            return result
        except Exception as e:
            return None

    def _calculate_pattern_strength(self, data, rsi, adx):
        """Calculate overall pattern strength score (0-100)"""
        score = 0

        # RSI component (0-30 points)
        if 40 <= rsi <= 70:
            score += 30 * (1 - abs(rsi - 55) / 30)
        elif rsi > 30:
            score += 20

        # ADX component (0-25 points)
        if adx >= 25:
            score += 25
        elif adx >= 15:
            score += 15

        # Trend component (0-25 points)
        try:
            close = data['Close'].iloc[-1]
            sma20 = data['SMA_20'].iloc[-1]
            sma50 = data['SMA_50'].iloc[-1]

            if not pd.isna(sma20) and not pd.isna(sma50):
                if close > sma20 > sma50:
                    score += 25
                elif close > sma20:
                    score += 20
                elif close > sma50:
                    score += 10
        except:
            pass

        # Volume component (0-20 points)
        try:
            volume_ratio = data['Volume_Ratio'].iloc[-1]
            if not pd.isna(volume_ratio):
                if volume_ratio >= 2.0:
                    score += 20
                elif volume_ratio >= 1.5:
                    score += 15
                elif volume_ratio >= 1.2:
                    score += 10
        except:
            pass

        return min(100, max(0, score))

class TelegramReporter:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text, parse_mode='HTML'):
        """Send message to Telegram"""
        try:
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(f"{self.api_url}/sendMessage", data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    def send_document(self, file_path, caption=""):
        """Send file to Telegram"""
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(f"{self.api_url}/sendDocument", files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send document: {e}")
            return False

def run_pcs_scan(stocks_to_scan=None, min_strength=65, filters=None):
    """Run the PCS scanner with specified criteria"""

    if filters is None:
        filters = {
            'min_volume_ratio': 1.2,
            'rsi_min': 40,
            'rsi_max': 75,
            'adx_min': 15,
            'pattern_strength_min': min_strength,
        }

    if stocks_to_scan is None:
        stocks_to_scan = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS',
            'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS',
            'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS',
            'MARUTI.NS', 'ASIANPAINT.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS'
        ]

    scanner = SimplePCSScanner()
    results = []
    failed_stocks = []

    print(f"\n📊 Starting PCS Scan for {len(stocks_to_scan)} stocks...")
    print(f"⚙️  Filter Settings:")
    print(f"   - Min Pattern Strength: {min_strength}%")
    print(f"   - Min Volume Ratio: {filters['min_volume_ratio']}x")
    print(f"   - RSI Range: {filters['rsi_min']}-{filters['rsi_max']}")
    print(f"   - Min ADX: {filters['adx_min']}")
    print("-" * 50)

    for idx, symbol in enumerate(stocks_to_scan, 1):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            print(f"[{idx}/{len(stocks_to_scan)}] {clean_symbol}...", end=' ', flush=True)

            data = get_stock_data(symbol, period="3mo")
            if data is None:
                print("❌ No data")
                failed_stocks.append((clean_symbol, "No data"))
                continue

            result = scanner.analyze_stock(clean_symbol, data, filters)

            if result is None:
                print("❌")
                continue

            results.append(result)
            print(f"✅ {result['strength']:.0f}% ({result['confidence']})")

        except Exception as e:
            print(f"⚠️")
            failed_stocks.append((clean_symbol, str(e)))

    results.sort(key=lambda x: x['strength'], reverse=True)

    print("-" * 50)
    print(f"\n✨ Found {len(results)} matching stocks | ⚠️ {len(failed_stocks)} failed")

    return results

def format_results_for_telegram(results):
    """Format results as Telegram message"""

    if not results:
        return "❌ <b>No stocks found meeting the filter criteria.</b>"

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"""<b>📊 NSE F&O PCS Screener</b>
<b>🕐 {current_time.strftime('%Y-%m-%d %H:%M IST')}</b>

<b>📈 {len(results)} High-Quality Opportunities Found:</b>
"""

    for idx, result in enumerate(results[:15], 1):
        symbol = result['symbol']
        price = result['price']
        strength = result['strength']
        confidence = "🟢 HIGH" if strength >= 80 else "🟡 MED" if strength >= 60 else "🔴 LOW"
        rsi = result['rsi']
        vol = result['volume_ratio']

        message += f"""
<b>{idx}. {symbol}</b> | 💰₹{price:.0f}
   {confidence} ({strength:.0f}%) | RSI:{rsi:.0f} | Vol:{vol:.1f}x
"""

    message += f"""
<b>⚙️ Filters:</b> Strength≥65% | Vol≥1.2x | RSI:40-75 | ADX≥15

<i>Not financial advice • Do your own research</i>"""

    return message

def create_csv_export(results):
    """Create CSV file of results"""

    data = []
    for result in results:
        data.append({
            'Symbol': result['symbol'],
            'Price': f"₹{result['price']:.2f}",
            'Strength': f"{result['strength']:.0f}%",
            'Confidence': result['confidence'],
            'RSI': f"{result['rsi']:.1f}",
            'ADX': f"{result['adx']:.1f}",
            'Volume_Ratio': f"{result['volume_ratio']:.2f}x"
        })

    if not data:
        return None

    df = pd.DataFrame(data)
    csv_path = f"/tmp/pcs_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_path, index=False)

    return csv_path

def main():
    print("\n" + "="*50)
    print("🚀 NSE F&O PCS SCREENER - TELEGRAM REPORTER")
    print("="*50)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️  Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")

    # Define filter criteria
    filters = {
        'min_volume_ratio': 1.2,
        'rsi_min': 40,
        'rsi_max': 75,
        'adx_min': 15,
        'pattern_strength_min': 65,
    }

    # Run scanner
    results = run_pcs_scan(min_strength=65, filters=filters)

    # Format results
    message = format_results_for_telegram(results)

    # Create CSV export
    csv_path = create_csv_export(results)

    # Send to Telegram if configured
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("\n📤 Sending to Telegram...")
        reporter = TelegramReporter(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

        if reporter.send_message(message):
            print("✅ Message sent")
        else:
            print("❌ Failed to send message")

        if csv_path and os.path.exists(csv_path):
            time.sleep(0.5)
            if reporter.send_document(csv_path, "📊 Detailed Results"):
                print("✅ CSV sent")
    else:
        print("\n📋 Results (Telegram not configured):")
        print(message)
        if csv_path:
            print(f"\n📊 CSV: {csv_path}")

    print("\n" + "="*50)
    return len(results)

if __name__ == "__main__":
    try:
        result_count = main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
