#!/usr/bin/env python3
"""
Simple Stock Scanner with Telegram Integration
Runs the NSE F&O PCS scanner without streamlit dependencies
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# NSE F&O Complete Universe (top 100 liquid stocks)
NSE_FO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS',
    'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS',
    'TATASTEEL.NS', 'HINDALCO.NS', 'HEROMOTOCO.NS', 'BOSCHIND.NS', 'CIPLA.NS',
    'DRREDDY.NS', 'GRASIM.NS', 'SHREECEM.NS', 'TATA_STEEL.NS', 'SIEMENS.NS',
    'BHEL.NS', 'IPCALAB.NS', 'VOLTAS.NS', 'APLLTD.NS', 'SBICARD.NS',
]

class SimpleScanner:
    """Simple stock scanner with technical indicators"""

    def __init__(self):
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.results = []

    def calculate_rsi(self, data, period=14):
        """Calculate RSI indicator"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_sma(self, data, period):
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()

    def calculate_ema(self, data, period):
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()

    def calculate_adx(self, high, low, close, period=14):
        """Calculate ADX indicator"""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

        di_diff = abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        dx = 100 * (di_diff / di_sum)
        adx = dx.rolling(period).mean()

        return adx

    def get_stock_data(self, symbol, period='3mo'):
        """Fetch stock data from Yahoo Finance"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            if data.empty:
                return None

            # Calculate indicators
            data['RSI'] = self.calculate_rsi(data['Close'])
            data['SMA_20'] = self.calculate_sma(data['Close'], 20)
            data['EMA_20'] = self.calculate_ema(data['Close'], 20)
            data['ADX'] = self.calculate_adx(data['High'], data['Low'], data['Close'])

            return data
        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
            return None

    def detect_simple_patterns(self, data, symbol):
        """Detect simple technical patterns"""
        patterns = []

        if len(data) < 30:
            return patterns

        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]

        # Check for oversold bounce (RSI < 40 and bouncing back)
        if not np.isnan(current_rsi) and current_rsi < 40:
            prev_rsi = data['RSI'].iloc[-5:-1].mean()
            if current_rsi > prev_rsi and current_price > sma_20:
                patterns.append({
                    'type': 'Oversold Bounce',
                    'strength': 65 + (40 - current_rsi),
                    'confidence': 'MEDIUM',
                    'success_rate': 72
                })

        # Check for strong trend (ADX > 25)
        if not np.isnan(current_adx) and current_adx > 25:
            if current_price > ema_20:
                patterns.append({
                    'type': 'Strong Uptrend',
                    'strength': min(95, 60 + (current_adx - 20) * 2),
                    'confidence': 'HIGH',
                    'success_rate': 75
                })

        # Check for support level bounce
        lowest_20 = data['Close'].iloc[-20:].min()
        if current_price > lowest_20 * 1.02 and current_price < lowest_20 * 1.05:
            patterns.append({
                'type': 'Support Level Bounce',
                'strength': 70,
                'confidence': 'MEDIUM',
                'success_rate': 68
            })

        return patterns

    def send_telegram_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Telegram message sent successfully")
                return True
            else:
                print(f"❌ Failed to send: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending message: {str(e)}")
            return False

    def run_scan(self, max_stocks=50):
        """Run the stock scanner"""
        stocks_to_scan = NSE_FO_STOCKS[:max_stocks]

        print(f"\n🚀 Starting scan of {len(stocks_to_scan)} stocks...")
        print(f"⏰ Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}\n")

        results = []

        for i, symbol in enumerate(stocks_to_scan):
            progress = (i + 1) / len(stocks_to_scan)
            clean_symbol = symbol.replace('.NS', '')
            print(f"[{progress*100:3.0f}%] 🔍 Analyzing {clean_symbol}...", end='\r')

            try:
                # Get stock data
                data = self.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 30:
                    continue

                # Basic volume check
                avg_volume = data['Volume'].iloc[-20:].mean()
                current_volume = data['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

                if volume_ratio < 1.0:  # Need at least average volume
                    continue

                # Get metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Skip if indicators are NaN
                if np.isnan(current_rsi) or np.isnan(current_adx):
                    continue

                # Detect patterns
                patterns = self.detect_simple_patterns(data, symbol)
                if not patterns:
                    continue

                # Create result
                stock_result = {
                    'symbol': clean_symbol,
                    'price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'max_strength': max(p['strength'] for p in patterns)
                }

                results.append(stock_result)

            except Exception as e:
                continue

        print(f"\n✅ Scan complete! Found {len(results)} stocks.\n")

        # Sort by strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)
        self.results = results
        return results

    def format_results_for_telegram(self, limit=15):
        """Format results for Telegram"""
        if not self.results:
            return "📊 No stocks found matching the criteria today."

        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

        message = f"""
<b>📊 NSE F&O Stock Scanner Results</b>
<i>{timestamp}</i>

<b>Summary:</b>
• Total stocks found: {len(self.results)}
• Stocks scanned: {len(NSE_FO_STOCKS[:50])}

"""

        # Add top stocks
        message += "<b>🏆 Top Performing Stocks:</b>\n"

        for idx, result in enumerate(self.results[:limit], 1):
            strength = result['max_strength']
            confidence = 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'
            emoji = '🟢' if confidence == 'HIGH' else '🟡' if confidence == 'MEDIUM' else '🔴'

            pattern_types = ", ".join([p['type'] for p in result['patterns']])

            message += f"\n{idx}. <b>{result['symbol']}</b> {emoji}\n"
            message += f"   💰 ₹{result['price']:.2f} | RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
            message += f"   📈 Volume: {result['volume_ratio']:.1f}x | Strength: {strength:.0f}%\n"
            message += f"   🎯 {pattern_types}\n"

        message += "\n<i>View full analysis at: https://nse-fo-pcs-screener.streamlit.app</i>"

        return message

    def run_and_send(self, max_stocks=50):
        """Run scan and send to Telegram"""
        print("=" * 60)
        print("NSE F&O STOCK SCANNER - TELEGRAM INTEGRATION")
        print("=" * 60)

        # Run scan
        self.run_scan(max_stocks=max_stocks)

        # Format results
        message = self.format_results_for_telegram()

        # Send to Telegram if configured
        if self.telegram_token and self.telegram_chat_id:
            print(f"\n📤 Sending to Telegram Chat: {self.telegram_chat_id}")
            self.send_telegram_message(message)
        else:
            print("\n⚠️  Telegram credentials not configured.")
            print("\nTo enable Telegram notifications:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            print("\nResults preview:")
            print(message)

        print("\n" + "=" * 60)


if __name__ == "__main__":
    scanner = SimpleScanner()
    max_stocks = int(os.environ.get('MAX_STOCKS', '50'))
    scanner.run_and_send(max_stocks=max_stocks)
