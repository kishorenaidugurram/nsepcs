#!/usr/bin/env python3
"""
Simplified NSE F&O Scanner with Telegram Integration
Uses manual calculations for technical indicators
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

import yfinance as yf


def calculate_rsi(prices, period=14):
    """Calculate RSI manually"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def calculate_macd(prices):
    """Calculate MACD"""
    ema_12 = prices.ewm(span=12, adjust=False).mean()
    ema_26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram


def calculate_bollinger_bands(prices, period=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper, sma, lower


# NSE F&O Stocks List
STOCKS_TO_SCAN = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'DRREDDY.NS', 'SUNPHARMA.NS', 'CIPLA.NS',
    'GAIL.NS', 'BPCL.NS', 'IOC.NS', 'HDFC.NS', 'NTPC.NS',
    'TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'COALINDIA.NS', 'ADANIPORTS.NS',
    'ADANIGREEN.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'CUMMINSIND.NS', 'EICHERMOT.NS',
    'BHARATFORG.NS', 'CONCOR.NS', 'GMRAIRPORT.NS', 'APOLLOHOSP.NS', 'FORTIS.NS',
    'BRITANNIA.NS', 'COLPAL.NS', 'HINDUSTAN.NS', 'HDFCLIFE.NS', 'ICICIGI.NS'
]


class TelegramNotifier:
    """Handle Telegram notifications"""

    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def is_configured(self):
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text, parse_mode="HTML"):
        """Send message to Telegram"""
        if not self.is_configured():
            print(f"\n⚠️  Telegram not configured.")
            print(f"Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
            print(f"\nMessage preview:\n{text}\n")
            return False

        try:
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = requests.post(self.api_url, json=data, timeout=10)
            if response.status_code == 200:
                print("✅ Message sent to Telegram successfully!")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False


class SimpleStockScanner:
    """Simple stock scanner using manual calculations"""

    def __init__(self):
        self.notifier = TelegramNotifier()
        self.ist = pytz.timezone('Asia/Kolkata')

    def fetch_stock_data(self, symbol, period="3mo"):
        """Fetch stock data using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            if data.empty or len(data) < 20:
                return None
            return data
        except Exception as e:
            print(f"  ❌ Error fetching {symbol}: {e}")
            return None

    def calculate_indicators(self, data):
        """Calculate technical indicators manually"""
        try:
            # RSI
            data['RSI'] = calculate_rsi(data['Close'])

            # MACD
            data['MACD'], data['MACD_signal'], data['MACD_hist'] = calculate_macd(data['Close'])

            # Bollinger Bands
            data['BB_upper'], data['BB_middle'], data['BB_lower'] = calculate_bollinger_bands(data['Close'])

            # SMA
            data['SMA_20'] = calculate_sma(data['Close'], 20)
            data['SMA_50'] = calculate_sma(data['Close'], 50)

            return data
        except Exception as e:
            print(f"  ❌ Error calculating indicators: {e}")
            return None

    def check_bullish_setup(self, data, symbol):
        """Check for bullish trading setup"""
        try:
            if data is None or len(data) < 50:
                return None

            # Get latest values
            close = data['Close'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]

            # Check volume trend
            avg_volume = data['Volume'].iloc[-20:].mean()
            current_volume = data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            signals = []
            score = 0

            # Price above moving averages (bullish)
            if pd.notna(sma_20) and pd.notna(sma_50) and close > sma_20 > sma_50:
                signals.append("✅ Price > SMA20 > SMA50 (Strong Uptrend)")
                score += 25
            elif pd.notna(sma_20) and close > sma_20:
                signals.append("✅ Price > SMA20 (Weak Uptrend)")
                score += 15

            # RSI - not overbought but bullish
            if pd.notna(rsi):
                if 40 < rsi < 80:
                    signals.append(f"✅ RSI {rsi:.1f} (Bullish Zone)")
                    score += 15
                elif rsi > 70:
                    signals.append(f"⚠️ RSI {rsi:.1f} (Overbought)")
                    score += 5

            # Volume confirmation
            if volume_ratio > 1.2:
                signals.append(f"✅ Volume {volume_ratio:.1f}x (Above Average)")
                score += 15
            elif volume_ratio > 1.0:
                signals.append(f"✅ Volume {volume_ratio:.1f}x (Normal)")
                score += 5

            # Check for recent uptrend (last 5 days)
            recent_closes = data['Close'].iloc[-5:].tolist()
            if len(recent_closes) >= 5:
                is_trending_up = sum(recent_closes[i] > recent_closes[i-1] for i in range(1, len(recent_closes))) >= 3
                if is_trending_up:
                    signals.append("✅ Recent Uptrend (Last 5 Days)")
                    score += 20

            # Additional check - Price near support
            if len(data) >= 50:
                low_50 = data['Low'].iloc[-50:].min()
                pct_from_low = ((close - low_50) / low_50) * 100
                if 0 < pct_from_low < 15:
                    signals.append(f"✅ Price near support (Distance: {pct_from_low:.1f}%)")
                    score += 10

            if score >= 40 and len(signals) >= 3:
                return {
                    'symbol': symbol,
                    'price': close,
                    'score': score,
                    'rsi': rsi if pd.notna(rsi) else 0,
                    'sma_20': sma_20 if pd.notna(sma_20) else 0,
                    'sma_50': sma_50 if pd.notna(sma_50) else 0,
                    'volume_ratio': volume_ratio,
                    'signals': signals
                }

            return None
        except Exception as e:
            print(f"  ❌ Error checking setup for {symbol}: {e}")
            return None

    def scan_stock(self, symbol):
        """Scan a single stock"""
        try:
            # Fetch data
            data = self.fetch_stock_data(symbol)
            if data is None:
                return None

            # Calculate indicators
            data = self.calculate_indicators(data)
            if data is None:
                return None

            # Check setup
            result = self.check_bullish_setup(data, symbol)
            return result

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            return None

    def run_scan(self, stocks, max_workers=3):
        """Run scan on multiple stocks"""
        print(f"\n🚀 Starting scan of {len(stocks)} stocks...")
        print(f"⏰ Time: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scan_stock, symbol): symbol
                for symbol in stocks
            }

            completed = 0
            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"✅ {completed}/{len(stocks)} - {symbol}: Score {result['score']} (Found!)")
                    else:
                        print(f"⏭️  {completed}/{len(stocks)} - {symbol}: No setup")
                except Exception as e:
                    print(f"❌ {completed}/{len(stocks)} - {symbol}: Error - {e}")

        return results

    def format_telegram_message(self, results):
        """Format results for Telegram"""
        if not results:
            return f"""<b>📊 NSE F&O Scan Results</b>
<b>⏰ {datetime.now(self.ist).strftime('%d-%b-%Y %H:%M:%S')}</b>

<b>❌ No stocks meeting criteria found</b>

Scanned {len(STOCKS_TO_SCAN)} stocks. Try adjusting filters if needed."""

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        message = f"""<b>📊 NSE F&O Scan Results</b>
<b>⏰ {datetime.now(self.ist).strftime('%d-%b-%Y %H:%M:%S')}</b>

<b>✅ Found {len(results)} stocks with bullish setups!</b>

<b>📈 Top Picks:</b>
"""

        for i, result in enumerate(results[:15], 1):
            symbol = result['symbol'].replace('.NS', '')
            message += f"""
<b>{i}. {symbol}</b>
   💰 Price: ₹{result['price']:.2f} | Score: {result['score']}/100
   📊 RSI: {result['rsi']:.1f} | Vol Ratio: {result['volume_ratio']:.1f}x
"""
            for signal in result['signals'][:3]:  # Show top 3 signals
                message += f"   {signal}\n"

        if len(results) > 15:
            message += f"\n... and {len(results) - 15} more stocks"

        return message

    def run(self):
        """Main execution"""
        print("=" * 60)
        print("NSE F&O STOCK SCANNER")
        print("=" * 60)

        # Check Telegram configuration
        if self.notifier.is_configured():
            print("✅ Telegram is configured")
        else:
            print("⚠️  Telegram not configured for this session")

        # Run scan
        results = self.run_scan(STOCKS_TO_SCAN, max_workers=3)

        # Format message
        message = self.format_telegram_message(results)

        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        print(message)

        # Send to Telegram
        if self.notifier.is_configured():
            print("\n📤 Sending to Telegram...")
            self.notifier.send_message(message)
        else:
            print("\n💡 To enable Telegram notifications, set:")
            print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")

        return results


def main():
    """Main entry point"""
    scanner = SimpleStockScanner()
    results = scanner.run()
    print(f"\n✅ Scan complete! Found {len(results)} stocks.")


if __name__ == "__main__":
    main()
