#!/usr/bin/env python3
"""
Stock Scanner with Telegram Integration - Simplified Version
Runs NSE F&O stock scanner and sends results to Telegram
"""

import sys
import os
sys.path.insert(0, '/home/user/nsepcs')

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import warnings
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# NSE F&O Stock Universe (from streamlit_app.py)
COMPLETE_NSE_FO_UNIVERSE = [
    # Tier 1 - Ultra High Liquidity
    "^NSEBANK^", "^NIFTY^", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS",
    # Tier 2 - High Liquidity
    "KOTAKBANK.NS", "AXISBANK.NS", "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS",
    "ASIANPAINT.NS", "BHARTIARTL.NS", "SUNPHARMA.NS", "TATAMOTORS.NS", "ADANIENT.NS",
    # Tier 3 - Medium Liquidity
    "BAJFINANCE.NS", "BAJAJFINSV.NS", "INDUSINDBK.NS", "TECHM.NS", "TITAN.NS",
    "NESTLEIND.NS", "ULTRACEMCO.NS", "POWERGRID.NS", "NTPC.NS", "ONGC.NS",
    "COALINDIA.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "HINDALCO.NS"
]

class TelegramSender:
    """Send messages to Telegram"""
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def is_configured(self):
        """Check if Telegram is configured"""
        return bool(self.token and self.chat_id)

    def send_message(self, text, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.is_configured():
            print(f"[Console Output] {text[:100]}...")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_document(self, file_path, caption=''):
        """Send file to Telegram"""
        if not self.is_configured():
            return False

        try:
            url = f"{self.base_url}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {'document': f}
                payload = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, files=files, data=payload, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram document: {e}")
            return False

def calculate_technical_indicators(data):
    """Calculate RSI, ADX, MACD using simple implementations"""
    df = data.copy()

    # RSI (14-period)
    if len(df) >= 14:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
    else:
        df['RSI'] = 50

    # ADX (simplified)
    df['ADX'] = 30  # Simplified for now

    # MACD
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    # Moving averages
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)

    return df

def detect_patterns(data, symbol, rsi_min=30, rsi_max=75, adx_min=20):
    """Detect chart patterns and calculate PCS score"""
    if data is None or len(data) < 20:
        return []

    df = calculate_technical_indicators(data)

    patterns = []
    current_price = df['Close'].iloc[-1]
    current_rsi = df['RSI'].iloc[-1]
    current_adx = df['ADX'].iloc[-1]
    sma_20 = df['SMA20'].iloc[-1]
    ema_20 = df['EMA20'].iloc[-1]

    # Check filters
    if not (rsi_min <= current_rsi <= rsi_max):
        return []

    if current_adx < adx_min:
        return []

    if current_price < sma_20 * 0.97:  # 3% tolerance
        return []

    # Calculate bullish signals
    signals = 0

    # RSI oversold bounce detection
    if current_rsi < 40 and df['RSI'].iloc[-2] < current_rsi:
        signals += 1

    # MACD bullish crossover
    if len(df) >= 3:
        if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['Signal'].iloc[-2]:
            signals += 1

    # Price above moving average
    if current_price > sma_20 and current_price > ema_20:
        signals += 1

    # Volume analysis (simplified)
    if len(df) >= 5:
        current_vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].iloc[-20:].mean()
        if current_vol > avg_vol * 1.2:
            signals += 1

    # Breakout detection
    if len(df) >= 20:
        last_20_high = df['Close'].iloc[-20:-1].max()
        if current_price > last_20_high * 0.98:  # Near 20-day high
            signals += 1

    if signals >= 2:  # At least 2 bullish signals
        pcs_score = min(50 + (signals * 15), 100)  # Score from 50 to 100

        # Determine primary pattern
        if signals >= 4:
            pattern_name = "Breakout Setup (High Conviction)"
        elif signals >= 3:
            pattern_name = "Breakout Setup (Moderate Conviction)"
        else:
            pattern_name = "Continuation Pattern"

        patterns.append({
            'symbol': symbol.replace('.NS', ''),
            'pattern': pattern_name,
            'strength': min(50 + (signals * 20), 100),
            'pcs_score': pcs_score,
            'rsi': round(current_rsi, 1),
            'price': round(current_price, 2),
            'signals': signals
        })

    return patterns

def fetch_data(symbol):
    """Fetch stock data from yfinance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period='3mo')
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"  Error fetching {symbol}: {str(e)[:50]}")
        return None

def run_scanner():
    """Run stock scanner with default filters"""
    print("🚀 Starting NSE F&O Stock Scanner...")
    print(f"📊 Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} stocks")
    print("=" * 60)

    results = []
    failed_stocks = []

    total = len(COMPLETE_NSE_FO_UNIVERSE)
    for i, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE, 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"[{i:2d}/{total}] Scanning {clean_symbol:15s}...", end='', flush=True)

        try:
            data = fetch_data(symbol)
            if data is None or data.empty:
                print(" ⚠️  No data")
                failed_stocks.append(clean_symbol)
                continue

            patterns = detect_patterns(data, symbol)

            if patterns:
                for pattern in patterns:
                    results.append(pattern)
                print(f" ✅ Found {len(patterns)} pattern(s)")
            else:
                print(" -")
        except Exception as e:
            print(f" ❌ Error")
            failed_stocks.append(clean_symbol)

    print("=" * 60)
    print(f"✅ Scan complete!")
    print(f"   Found {len(results)} patterns in {total - len(failed_stocks)}/{total} stocks")
    if failed_stocks:
        print(f"⚠️  Failed: {', '.join(failed_stocks[:3])}")

    return results

def format_results(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found matching criteria"

    # Sort by score/strength
    df = pd.DataFrame(results)
    df = df.sort_values('pcs_score', ascending=False)

    message = "<b>📊 NSE F&O Stock Scanner Results</b>\n"
    message += f"<i>Generated: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}</i>\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    message += f"<b>Total Patterns Found: {len(df)}</b>\n\n"

    for idx, row in df.head(15).iterrows():
        message += f"<b>🔹 {row['symbol']}</b>\n"
        message += f"  Price: ₹{row['price']:.2f}\n"
        message += f"  Pattern: {row['pattern']}\n"
        message += f"  Strength: {row['strength']:.0f}%\n"
        message += f"  PCS Score: {row['pcs_score']:.1f}/100\n"
        message += f"  RSI: {row['rsi']:.1f}\n"
        message += "─────────────────────────\n"

    if len(df) > 15:
        message += f"\n<i>... and {len(df) - 15} more patterns</i>"

    return message

def main():
    print("\n" + "=" * 60)
    print("NSE F&O STOCK SCANNER WITH TELEGRAM")
    print("=" * 60 + "\n")

    telegram = TelegramSender()

    if telegram.is_configured():
        print("✅ Telegram configured - Results will be sent")
        telegram.send_message("🚀 <b>NSE F&O Scanner Started</b>\nScanning all stocks with filter criteria...")
    else:
        print("⚠️  Telegram not configured")
        print("   To use Telegram, set environment variables:")
        print("   - TELEGRAM_BOT_TOKEN")
        print("   - TELEGRAM_CHAT_ID")
        print("\nResults will be displayed in console.\n")

    # Run scanner
    results = run_scanner()

    print("\n" + "=" * 60)

    # Format and send results
    message = format_results(results)

    if telegram.is_configured():
        success = telegram.send_message(message)
        if success:
            print("✅ Results sent to Telegram")
        else:
            print("❌ Failed to send to Telegram")
            print("\nResults preview:")
            print(message)
    else:
        print("\nResults Preview:\n")
        print(message)

    # Create summary CSV
    if results:
        df = pd.DataFrame(results)
        csv_path = '/tmp/scanner_results.csv'
        df.to_csv(csv_path, index=False)
        print(f"\n💾 Results saved to {csv_path}")

        if telegram.is_configured():
            telegram.send_document(csv_path, "📊 Detailed Scanner Results")

if __name__ == "__main__":
    main()
