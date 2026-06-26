#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner with Telegram Integration
Runs the screening logic and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

try:
    import ta
except ImportError:
    try:
        import pandas_ta as ta
    except ImportError:
        ta = None

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Default filter criteria for professional scanning
DEFAULT_FILTERS = {
    'rsi_min': 45,
    'rsi_max': 75,
    'adx_min': 20,
    'ma_support': True,
    'ma_type': 'SMA',
    'ma_tolerance': 5,
    'volume_breakout_ratio': 2.0,
    'pattern_strength_min': 65,
    'max_stocks': 25
}

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print(f"⚠️ Telegram not configured. Message: {message[:100]}")
            return False

        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False

class StockScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def calculate_rsi(self, data, period=14):
        """Calculate RSI indicator"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_adx(self, high, low, close, period=14):
        """Calculate ADX indicator"""
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        return adx

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch and process stock data"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            if data is None or len(data) < 20:
                return None

            # Calculate technical indicators
            data['RSI'] = self.calculate_rsi(data['Close'])
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['EMA_20'] = data['Close'].ewm(span=20).mean()

            # Bollinger Bands
            sma = data['Close'].rolling(window=20).mean()
            std = data['Close'].rolling(window=20).std()
            data['BB_upper'] = sma + (std * 2)
            data['BB_lower'] = sma - (std * 2)

            # ADX
            data['ADX'] = self.calculate_adx(data['High'], data['Low'], data['Close'])

            # Volume SMA
            data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()

            return data
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check if current volume meets criteria"""
        try:
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume_SMA'].iloc[-1]
            if avg_volume == 0:
                return False
            return (current_volume / avg_volume) >= min_ratio
        except:
            return False

    def apply_filters(self, data, filters):
        """Apply technical filters to data"""
        try:
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            ema_20 = data['EMA_20'].iloc[-1]

            # RSI filter
            if not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
                return False, f"RSI {current_rsi:.1f} outside range {filters['rsi_min']}-{filters['rsi_max']}"

            # ADX filter
            if current_adx < filters['adx_min']:
                return False, f"ADX {current_adx:.1f} below {filters['adx_min']}"

            # MA Support filter
            if filters['ma_support']:
                if filters['ma_type'] == 'SMA':
                    if current_price < sma_20 * (1 - filters['ma_tolerance']/100):
                        return False, f"Price below SMA20 support"
                else:
                    if current_price < ema_20 * (1 - filters['ma_tolerance']/100):
                        return False, f"Price below EMA20 support"

            # Volume filter
            if not self.check_volume_criteria(data, filters['volume_breakout_ratio']):
                return False, f"Volume below ratio {filters['volume_breakout_ratio']}"

            return True, "All filters passed"
        except Exception as e:
            return False, f"Filter error: {str(e)}"

    def scan_stocks(self, stock_list, filters):
        """Scan multiple stocks for filter criteria"""
        results = []

        print(f"🔍 Scanning {len(stock_list)} stocks...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._scan_single_stock, symbol, filters): symbol
                      for symbol in stock_list}

            for i, future in enumerate(as_completed(futures), 1):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"✅ [{i}/{len(stock_list)}] {symbol}: PASS")
                    else:
                        print(f"❌ [{i}/{len(stock_list)}] {symbol}: FAIL")
                except Exception as e:
                    print(f"❌ [{i}/{len(stock_list)}] {symbol}: ERROR - {e}")

        return results

    def _scan_single_stock(self, symbol, filters):
        """Scan a single stock"""
        data = self.get_stock_data(symbol + ".NS")
        if data is None:
            return None

        passed, reason = self.apply_filters(data, filters)
        if not passed:
            return None

        try:
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            volume_ratio = data['Volume'].iloc[-1] / data['Volume_SMA'].iloc[-1]

            return {
                'symbol': symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return None

def get_nse_stocks():
    """Get list of major NSE F&O stocks"""
    return [
        'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
        'SBIN', 'LT', 'ITC', 'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI',
        'ASIANPAINT', 'BHARTIARTL', 'SUNPHARMA', 'TATAMOTORS', 'ADANIENT',
        'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN'
    ]

def format_telegram_message(results, filters):
    """Format results for Telegram"""
    if not results:
        return "🔴 <b>Stock Scan Results</b>\n\nNo stocks met the filter criteria today.\n\n" \
               f"<code>Filters: RSI {filters['rsi_min']}-{filters['rsi_max']}, ADX>{filters['adx_min']}, " \
               f"Volume>{filters['volume_breakout_ratio']}x</code>\n\n" \
               f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}"

    message = f"✅ <b>Stock Scan Results</b>\n" \
              f"Found <b>{len(results)}</b> stocks meeting criteria\n\n"

    for i, stock in enumerate(results[:15], 1):  # Limit to 15 for Telegram message size
        message += f"<b>{i}. {stock['symbol']}</b>\n"
        message += f"   Price: ₹{stock['price']:.2f}\n"
        message += f"   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
        message += f"   Vol Ratio: {stock['volume_ratio']:.2f}x\n\n"

    if len(results) > 15:
        message += f"... and {len(results) - 15} more stocks\n\n"

    message += f"<code>Filters: RSI {filters['rsi_min']}-{filters['rsi_max']}, ADX>{filters['adx_min']}, " \
              f"Volume>{filters['volume_breakout_ratio']}x</code>\n"
    message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M IST')}"

    return message

def main():
    print("=" * 60)
    print("NSE F&O Stock Scanner with Telegram Integration")
    print("=" * 60)

    # Check if Telegram is configured
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️  WARNING: Telegram not configured")
        print("Set environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nContinuing with local output only...\n")

    # Initialize components
    scanner = StockScanner()
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

    # Get stock list
    stocks = get_nse_stocks()
    print(f"\n📊 Stock Universe: {len(stocks)} stocks")
    print(f"📋 Filter Settings: {json.dumps(DEFAULT_FILTERS, indent=2)}\n")

    # Run scan
    results = scanner.scan_stocks(stocks, DEFAULT_FILTERS)

    # Format and send results
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"✅ Stocks matching criteria: {len(results)}")

    if results:
        print("\n📈 Results:")
        for i, stock in enumerate(results[:10], 1):
            print(f"  {i}. {stock['symbol']:12} | Price: ₹{stock['price']:8.2f} | "
                  f"RSI: {stock['rsi']:6.1f} | ADX: {stock['adx']:6.1f}")
        if len(results) > 10:
            print(f"  ... and {len(results) - 10} more")

    # Send Telegram message
    message = format_telegram_message(results, DEFAULT_FILTERS)
    if notifier.send_message(message):
        print("\n✅ Results sent to Telegram")
    else:
        print("\n⚠️  Results NOT sent to Telegram (configure credentials)")

    print("\n" + "=" * 60)
    return 0 if results else 1

if __name__ == "__main__":
    sys.exit(main())
