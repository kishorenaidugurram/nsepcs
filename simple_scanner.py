#!/usr/bin/env python3
"""
Simplified NSE Stock Scanner with Telegram Integration
Extracts only necessary technical indicators without external TA library
"""

import os
import sys
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import warnings
warnings.filterwarnings('ignore')

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - 100.0 / (1.0 + rs)

    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.0
        else:
            upval = 0.0
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        rs = up / down if down != 0 else 0
        rsi[i] = 100.0 - 100.0 / (1.0 + rs)

    return rsi[-1]

def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return np.mean(prices[-period:])

def calculate_ema(prices, period=20):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = np.mean(prices[:period])

    for price in prices[period:]:
        ema = price * multiplier + ema * (1 - multiplier)

    return ema

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    if len(prices) < slow:
        return None, None

    ema_fast = prices.ewm(span=fast).mean().iloc[-1]
    ema_slow = prices.ewm(span=slow).mean().iloc[-1]

    macd = ema_fast - ema_slow
    return macd, ema_slow

class SimpleScanner:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def fetch_stock_data(self, symbol, period='3mo'):
        """Fetch stock data using yfinance"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data if len(data) >= 20 else None
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            return None

    def analyze_stock(self, symbol, data):
        """Analyze single stock"""
        if data is None or len(data) < 20:
            return None

        try:
            closes = data['Close'].values
            highs = data['High'].values
            lows = data['Low'].values
            volumes = data['Volume'].values

            # Get current day data
            current_price = closes[-1]
            current_high = highs[-1]
            current_low = lows[-1]
            current_volume = volumes[-1]

            # Calculate indicators
            rsi = calculate_rsi(closes, 14)
            sma_20 = calculate_sma(closes, 20)
            ema_20 = calculate_ema(closes, 20)
            macd, macd_signal = calculate_macd(data['Close'], 12, 26, 9)

            # Volume analysis
            avg_volume_20 = np.mean(volumes[-20:])
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0

            # Volatility (Average True Range approximation)
            tr = np.maximum(
                highs[-1] - lows[-1],
                np.maximum(
                    abs(highs[-1] - closes[-2]),
                    abs(lows[-1] - closes[-2])
                )
            )
            atr = tr

            # Trend strength
            trend_up = (current_price > sma_20) if sma_20 else False
            near_resistance = ((current_price / highs[-20:].max()) > 0.97) if len(highs) >= 20 else False

            return {
                'symbol': symbol.replace('.NS', ''),
                'price': float(current_price),
                'rsi': float(rsi) if rsi else None,
                'sma_20': float(sma_20) if sma_20 else None,
                'ema_20': float(ema_20) if ema_20 else None,
                'macd': float(macd) if macd else None,
                'volume_ratio': float(volume_ratio),
                'avg_volume': float(avg_volume_20),
                'current_volume': float(current_volume),
                'atr': float(atr),
                'trend_up': trend_up,
                'near_resistance': near_resistance,
                'high_52w': float(max(highs[-252:] if len(highs) >= 252 else highs)),
                'low_52w': float(min(lows[-252:] if len(lows) >= 252 else lows))
            }

        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return None

    def filter_stocks(self, analysis, filters):
        """Check if stock meets filter criteria"""
        # Basic filters
        if analysis is None:
            return False, []

        signals = []
        score = 0

        # RSI filter (30-75 is healthy)
        if analysis['rsi']:
            if 30 <= analysis['rsi'] <= 75:
                signals.append(f"✓ Healthy RSI ({analysis['rsi']:.1f})")
                score += 20
            elif 40 <= analysis['rsi'] <= 60:
                signals.append(f"✓ Balanced RSI ({analysis['rsi']:.1f})")
                score += 25

        # Volume filter
        if analysis['volume_ratio'] > 1.0:
            signals.append(f"✓ Above avg volume ({analysis['volume_ratio']:.2f}x)")
            score += 15
            if analysis['volume_ratio'] > 2.0:
                score += 10

        # Trend strength
        if analysis['trend_up']:
            signals.append("✓ Above SMA20 (Uptrend)")
            score += 20

        # Near resistance (breakout potential)
        if analysis['near_resistance']:
            signals.append("✓ Near resistance (Breakout potential)")
            score += 25

        # MACD bullish
        if analysis['macd'] and analysis['macd'] > 0:
            signals.append("✓ MACD bullish")
            score += 15

        # Minimum score threshold
        if score >= filters.get('min_score', 30):
            return True, signals

        return False, signals

    def scan_stocks(self, stock_list, filters=None):
        """Scan list of stocks"""
        if filters is None:
            filters = {'min_score': 50}

        print(f"\n🚀 Starting scan of {len(stock_list)} stocks...")
        print(f"⏰ Time: {datetime.now(self.ist).strftime('%H:%M IST')}\n")

        results = []
        success_count = 0
        failed_count = 0

        for i, symbol in enumerate(stock_list, 1):
            clean_symbol = symbol.replace('.NS', '')

            # Fetch data
            data = self.fetch_stock_data(symbol)
            if data is None:
                failed_count += 1
                print(f"[{i}/{len(stock_list)}] ❌ {clean_symbol} - No data")
                continue

            # Analyze
            analysis = self.analyze_stock(symbol, data)
            if analysis is None:
                failed_count += 1
                print(f"[{i}/{len(stock_list)}] ❌ {clean_symbol} - Analysis failed")
                continue

            success_count += 1

            # Filter
            meets_criteria, signals = self.filter_stocks(analysis, filters)

            if meets_criteria:
                analysis['signals'] = signals
                analysis['score'] = sum([20, 15, 20, 25, 15] if len(signals) == 5 else 30)
                results.append(analysis)
                print(f"[{i}/{len(stock_list)}] ✅ {clean_symbol} - MATCH!")
                for signal in signals:
                    print(f"       {signal}")
            else:
                if i % 10 == 0:
                    print(f"[{i}/{len(stock_list)}] ⏳ Scanning... ({len(results)} matches so far)")

        print(f"\n{'='*60}")
        print(f"✅ Scan Complete!")
        print(f"Scanned: {success_count} | Failed: {failed_count} | Matches: {len(results)}")
        print(f"{'='*60}\n")

        return results

    def send_telegram_message(self, message, bot_token=None, chat_id=None):
        """Send message to Telegram"""
        bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            print("⚠️ Telegram credentials not set")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error sending telegram: {e}")
            return False

    def format_telegram_message(self, results):
        """Format results for Telegram"""
        if not results:
            return "<b>⚠️ No stocks found matching the criteria.</b>"

        # Sort by signals count
        results.sort(key=lambda x: len(x.get('signals', [])), reverse=True)

        message = f"<b>📈 Stock Scanner Results</b>\n"
        message += f"<i>Generated: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"
        message += f"<b>🎯 Found: {len(results)} stocks</b> matching criteria\n"
        message += "=" * 50 + "\n\n"

        for i, stock in enumerate(results[:15], 1):
            message += f"<b>{i}. {stock['symbol']}</b>\n"
            message += f"   Price: <code>₹{stock['price']:.2f}</code>\n"
            message += f"   RSI: {stock['rsi']:.1f} | Vol: {stock['volume_ratio']:.2f}x\n"

            for signal in stock.get('signals', [])[:3]:
                message += f"   {signal}\n"

            message += "\n"

        if len(results) > 15:
            message += f"\n<i>... and {len(results) - 15} more stocks</i>"

        return message

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Simple NSE Stock Scanner')
    parser.add_argument('--telegram', action='store_true', help='Send results to Telegram')
    parser.add_argument('--limit', type=int, default=50, help='Number of stocks to scan')
    parser.add_argument('--file', help='Output to file')

    args = parser.parse_args()

    # Stock list - using top 100 from NSE F&O universe
    stock_list = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
        'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
        'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
        'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
        'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
        'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
        'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS',
        'HDFCLIFE.NS', 'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS'
    ][:args.limit]

    scanner = SimpleScanner()

    # Run scan
    results = scanner.scan_stocks(stock_list, filters={'min_score': 40})

    if results:
        print(f"\n✅ Found {len(results)} qualifying stocks:\n")
        for stock in results:
            print(f"  {stock['symbol']}: ₹{stock['price']:.2f}")

        # Save to file if requested
        if args.file:
            with open(args.file, 'w') as f:
                for stock in results:
                    f.write(f"{stock['symbol']},₹{stock['price']:.2f},RSI:{stock['rsi']:.1f}\n")
            print(f"\n📁 Results saved to {args.file}")

        # Send to Telegram if requested
        if args.telegram:
            message = scanner.format_telegram_message(results)
            if scanner.send_telegram_message(message):
                print("✅ Message sent to Telegram!")
            else:
                print("❌ Failed to send to Telegram")
                print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")

    else:
        print("⚠️ No stocks found matching criteria")


if __name__ == "__main__":
    main()
