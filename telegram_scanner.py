#!/usr/bin/env python3
"""
Telegram Stock Scanner - Background task to scan stocks and send results to Telegram
Uses environment variables: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz
import warnings

import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Default NSE F&O stocks
COMPLETE_NSE_FO_UNIVERSE = [
    'NIFTY.NS', 'BANKNIFTY.NS', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS',
    'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS',
    'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS',
    'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS',
    'NESTLEIND.NS', 'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS',
    'COALINDIA.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS', 'DRREDDY.NS',
    'CIPLA.NS', 'PHARMEASY.NS', 'APOLLOHOSP.NS', 'BIOCON.NS', 'LUPIN.NS'
]

class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    def send_message(self, message):
        """Send message to Telegram"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

class StockScanner:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
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

    def _calculate_sma(self, prices, period=20):
        """Calculate Simple Moving Average"""
        return pd.Series(prices).rolling(window=period).mean().values

    def _calculate_ema(self, prices, period=20):
        """Calculate Exponential Moving Average"""
        return pd.Series(prices).ewm(span=period).mean().values

    def _calculate_adx(self, high, low, close, period=14):
        """Calculate ADX indicator"""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
        atr = pd.Series(tr).rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = pd.Series(dx).rolling(window=period).mean()
        return adx.values

    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data with technical indicators"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")

            if data is None or len(data) < 20:
                return None

            # Calculate technical indicators using pandas/numpy only
            close = data['Close'].values
            high = data['High'].values
            low = data['Low'].values

            data['RSI'] = self._calculate_rsi(close, period=14)
            data['SMA_20'] = self._calculate_sma(close, period=20)
            data['SMA_50'] = self._calculate_sma(close, period=50)
            data['EMA_20'] = self._calculate_ema(close, period=20)
            data['ADX'] = self._calculate_adx(data['High'], data['Low'], data['Close'], period=14)

            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def check_volume_criteria(self, data, min_ratio=1.2):
        """Check if current day volume meets criteria"""
        try:
            if len(data) < 2:
                return False, 0, {}

            # Compare today's volume with 20-day average
            today_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].iloc[-21:-1].mean()

            volume_ratio = today_volume / avg_volume if avg_volume > 0 else 0

            volume_ok = volume_ratio >= min_ratio

            return volume_ok, volume_ratio, {
                'today': today_volume,
                'average': avg_volume,
                'ratio': volume_ratio
            }
        except Exception as e:
            return False, 0, {}

    def check_technical_criteria(self, data, rsi_min=30, rsi_max=75, adx_min=20):
        """Check basic technical criteria"""
        try:
            if len(data) < 1:
                return False, {}

            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            current_ema20 = data['EMA_20'].iloc[-1]
            current_sma20 = data['SMA_20'].iloc[-1]

            rsi_ok = rsi_min <= current_rsi <= rsi_max
            adx_ok = current_adx >= adx_min
            trend_ok = current_price > current_ema20  # Price above EMA20

            all_ok = rsi_ok and adx_ok and trend_ok

            return all_ok, {
                'rsi': current_rsi,
                'adx': current_adx,
                'price': current_price,
                'ema20': current_ema20,
                'sma20': current_sma20
            }
        except Exception as e:
            return False, {}

    def detect_current_day_breakout(self, data, lookback_days=20):
        """Detect if stock broke out today"""
        try:
            if len(data) < lookback_days + 1:
                return False, {}

            # Get historical data
            historical = data.iloc[:-1].tail(lookback_days)
            today = data.iloc[-1]

            # Check if today's high is above 20-day high
            historical_high = historical['High'].max()
            historical_low = historical['Low'].min()

            breakout = today['High'] > historical_high * 1.01  # Allow 1% tolerance
            volume_confirmation = today['Volume'] > historical['Volume'].mean() * 1.5

            is_breakout = breakout and volume_confirmation

            return is_breakout, {
                'breakout': breakout,
                'volume_confirmed': volume_confirmation,
                'historical_high': historical_high,
                'today_high': today['High'],
                'breakout_percent': ((today['High'] - historical_high) / historical_high * 100) if historical_high > 0 else 0
            }
        except Exception as e:
            return False, {}

    def scan_stocks(self, symbols, rsi_min=30, rsi_max=75, adx_min=20,
                    min_volume_ratio=1.2, enable_breakout=True):
        """Scan multiple stocks and return qualifying ones"""
        results = []

        for symbol in symbols:
            try:
                clean_symbol = symbol.replace('.NS', '')

                # Get data
                data = self.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue

                # Check volume
                vol_ok, vol_ratio, vol_details = self.check_volume_criteria(data, min_volume_ratio)
                if not vol_ok:
                    continue

                # Check technical criteria
                tech_ok, tech_data = self.check_technical_criteria(data, rsi_min, rsi_max, adx_min)
                if not tech_ok:
                    continue

                # Check for breakout
                if enable_breakout:
                    breakout_ok, breakout_data = self.detect_current_day_breakout(data)
                    if not breakout_ok:
                        continue
                else:
                    breakout_data = {}

                # Stock qualifies
                result = {
                    'symbol': clean_symbol,
                    'price': data['Close'].iloc[-1],
                    'rsi': tech_data.get('rsi', 0),
                    'adx': tech_data.get('adx', 0),
                    'volume_ratio': vol_ratio,
                    'breakout_percent': breakout_data.get('breakout_percent', 0),
                    'timestamp': data.index[-1]
                }
                results.append(result)

            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue

        return results

def main():
    try:
        # Initialize
        telegram = TelegramSender()
        scanner = StockScanner()

        # Send start message
        start_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        telegram.send_message(f"🔍 <b>Stock Scan Started</b>\nTime: {start_time.strftime('%H:%M:%S IST')}")

        # Scan stocks with default filters
        print("Starting stock scan...")
        results = scanner.scan_stocks(
            COMPLETE_NSE_FO_UNIVERSE[:40],  # First 40 F&O stocks for speed
            rsi_min=30,
            rsi_max=75,
            adx_min=20,
            min_volume_ratio=1.2,
            enable_breakout=True
        )

        # Format results for Telegram
        if results:
            # Sort by volume ratio
            results.sort(key=lambda x: x['volume_ratio'], reverse=True)

            # Build message
            message = "<b>📈 Stocks Meeting Filter Criteria 📈</b>\n\n"
            message += f"Found: <b>{len(results)} stocks</b>\n"
            message += f"Time: {start_time.strftime('%H:%M IST')}\n\n"

            for i, stock in enumerate(results[:15], 1):  # Limit to top 15
                message += (
                    f"<b>{i}. {stock['symbol']}</b>\n"
                    f"   Price: ₹{stock['price']:.2f}\n"
                    f"   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
                    f"   Volume: {stock['volume_ratio']:.2f}x | Breakout: {stock['breakout_percent']:.2f}%\n\n"
                )

            if len(results) > 15:
                message += f"\n... and {len(results) - 15} more stocks"

            # Send to Telegram
            success = telegram.send_message(message)

            if success:
                print(f"✅ Successfully sent {len(results)} stocks to Telegram")
            else:
                print("❌ Failed to send message to Telegram")
        else:
            telegram.send_message("❌ No stocks meeting the filter criteria found.")
            print("No stocks found meeting criteria")

    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            telegram.send_message(f"❌ <b>Scan Failed</b>\nError: {str(e)[:100]}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
