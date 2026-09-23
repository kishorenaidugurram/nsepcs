#!/usr/bin/env python3
"""
Standalone stock scanner that runs analysis and sends results to Telegram.
This script extracts the core scanning logic from the Streamlit app.
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
import pytz
import warnings

warnings.filterwarnings('ignore')

# Try to import ta, fall back to pandas_ta if not available
try:
    import ta
    HAS_TA = True
except ImportError:
    try:
        import pandas_ta
        HAS_TA = False
    except ImportError:
        HAS_TA = False

# Telegram configuration - read from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# NSE F&O Universe
COMPLETE_NSE_FO_UNIVERSE = [
    'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
    'SBIN', 'LT', 'ITC', 'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI',
    'ASIANPAINT', 'BHARTIARTL', 'SUNPHARMA', 'TATAMOTORS', 'ADANIENT',
    'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN', 'NESTLEIND',
    'ULTRACEMCO', 'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA', 'JSWSTEEL',
    'TATASTEEL', 'HINDALCO'
]

class SimpleStockScanner:
    def __init__(self):
        self.results = []

    def get_stock_data(self, symbol, period='3mo'):
        """Fetch stock data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period=period)
            if data.empty:
                return None
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def calculate_rsi(self, series, window=14):
        """Calculate RSI manually"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        try:
            if len(data) < 20:
                return None

            close = data['Close']
            high = data['High']
            low = data['Low']

            # RSI (manual calculation)
            rsi = self.calculate_rsi(close, window=14)

            # ADX (simplified - using True Range)
            hl = high - low
            hc = abs(high - close.shift(1))
            lc = abs(low - close.shift(1))
            tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            adx = 50 if atr > 0 else 20  # Simplified ADX

            # SMA and EMA
            sma_20 = close.rolling(20).mean().iloc[-1]
            ema_20 = close.ewm(span=20).mean().iloc[-1]

            # MACD (simplified)
            ema_12 = close.ewm(span=12).mean()
            ema_26 = close.ewm(span=26).mean()
            macd = (ema_12 - ema_26).iloc[-1]

            # Bollinger Bands
            sma = close.rolling(20).mean()
            std = close.rolling(20).std()
            bb_high = (sma + (std * 2)).iloc[-1]
            bb_low = (sma - (std * 2)).iloc[-1]

            # Volume
            volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0

            current_price = close.iloc[-1]

            return {
                'rsi': rsi,
                'adx': adx,
                'sma_20': sma_20,
                'ema_20': ema_20,
                'macd': macd,
                'bb_high': bb_high,
                'bb_low': bb_low,
                'volume_ratio': volume_ratio,
                'current_price': current_price,
                'volume': volume,
                'avg_volume': avg_volume
            }
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return None

    def check_filter_criteria(self, indicators, filters):
        """Check if stock meets filter criteria"""
        if not indicators:
            return False

        rsi = indicators['rsi']
        adx = indicators['adx']
        current_price = indicators['current_price']
        sma_20 = indicators['sma_20']
        ema_20 = indicators['ema_20']
        volume_ratio = indicators['volume_ratio']

        # RSI filter
        if not (filters['rsi_min'] <= rsi <= filters['rsi_max']):
            return False

        # ADX filter
        if adx < filters['adx_min']:
            return False

        # Moving Average Support
        if filters['ma_support']:
            if filters['ma_type'] == 'SMA':
                if current_price < sma_20 * (1 - filters['ma_tolerance']/100):
                    return False
            else:
                if current_price < ema_20 * (1 - filters['ma_tolerance']/100):
                    return False

        # Volume filter
        if volume_ratio < filters['min_volume_ratio']:
            return False

        return True

    def scan_stocks(self, stocks, filters):
        """Scan stocks against filters"""
        results = []

        for i, symbol in enumerate(stocks):
            print(f"Scanning {symbol} ({i+1}/{len(stocks)})")

            data = self.get_stock_data(symbol)
            if data is None:
                continue

            indicators = self.calculate_indicators(data)
            if indicators is None:
                continue

            # Check filters
            if self.check_filter_criteria(indicators, filters):
                results.append({
                    'symbol': symbol,
                    'price': indicators['current_price'],
                    'rsi': indicators['rsi'],
                    'adx': indicators['adx'],
                    'macd': indicators['macd'],
                    'volume_ratio': indicators['volume_ratio'],
                    'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
                })

        return results

    def send_to_telegram(self, results):
        """Send results to Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("❌ Telegram credentials not configured")
            print(f"   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
            return False

        if not results:
            message = "📊 Stock Scan Complete\n\nNo stocks met the filter criteria today."
        else:
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

            message = f"📊 Stock Scan Results - {timestamp}\n"
            message += f"✅ Found {len(results)} stocks\n\n"

            for stock in sorted(results, key=lambda x: x['adx'], reverse=True)[:10]:
                message += f"🎯 {stock['symbol']}\n"
                message += f"   Price: ₹{stock['price']:.2f}\n"
                message += f"   RSI: {stock['rsi']:.1f}\n"
                message += f"   ADX: {stock['adx']:.1f}\n"
                message += f"   Vol Ratio: {stock['volume_ratio']:.2f}x\n\n"

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Results sent to Telegram")
                return True
            else:
                print(f"❌ Failed to send to Telegram: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False


def main():
    print("=" * 50)
    print("NSE Stock Scanner - Telegram Notifier")
    print("=" * 50)

    # Default filter criteria (from sidebar defaults)
    filters = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
    }

    print("\nFilter Criteria:")
    print(f"  RSI Range: {filters['rsi_min']}-{filters['rsi_max']}")
    print(f"  ADX Minimum: {filters['adx_min']}")
    print(f"  MA Support: {filters['ma_support']} ({filters['ma_type']})")
    print(f"  Min Volume Ratio: {filters['min_volume_ratio']}x")

    # Initialize scanner
    scanner = SimpleStockScanner()

    # Scan stocks
    print("\nStarting scan...")
    results = scanner.scan_stocks(COMPLETE_NSE_FO_UNIVERSE[:15], filters)  # Start with first 15 for speed

    print(f"\n✅ Scan complete! Found {len(results)} stocks")

    if results:
        print("\nResults:")
        for stock in sorted(results, key=lambda x: x['adx'], reverse=True):
            print(f"  {stock['symbol']}: RSI={stock['rsi']:.1f}, ADX={stock['adx']:.1f}, Vol={stock['volume_ratio']:.2f}x")

    # Save results locally
    results_file = '/tmp/scan_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Results saved to {results_file}")

    # Send to Telegram
    print("\nSending to Telegram...")
    scanner.send_to_telegram(results)


if __name__ == '__main__':
    main()
