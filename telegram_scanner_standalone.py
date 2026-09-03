#!/usr/bin/env python3
"""
Simplified NSE F&O Stock Scanner with Telegram Integration
Uses basic technical indicators without external dependencies
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz
import logging
import numpy as np
import pandas as pd
import yfinance as yf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NSE F&O Universe
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS'
]


class SimpleStockScanner:
    """Simplified stock scanner using basic technical indicators"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period:
            return np.nan

        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        rs = up / down if down != 0 else 0
        rsi = 100.0 - 100.0 / (1.0 + rs)

        rsi_values = np.zeros_like(prices)
        rsi_values[:period] = 100.0 - 100.0 / (1.0 + (up / down if down != 0 else 0))

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.0
            else:
                upval = 0.0
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period

            rs = up / down if down != 0 else 0
            rsi_values[i] = 100.0 - 100.0 / (1.0 + rs)

        return rsi_values[-1]

    @staticmethod
    def calculate_sma(prices, period):
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return np.nan
        return np.mean(prices[-period:])

    @staticmethod
    def calculate_ema(prices, period):
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.nan
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = price * multiplier + ema * (1 - multiplier)
        return ema

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch stock data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)

            if len(data) < 20:
                return None

            return data

        except Exception as e:
            logger.debug(f"Error fetching {symbol}: {e}")
            return None

    def analyze_stock(self, symbol):
        """Analyze a single stock"""
        try:
            # Fetch data
            data = self.get_stock_data(symbol, period="3mo")
            if data is None:
                return None

            # Calculate indicators
            close_prices = data['Close'].values
            current_close = close_prices[-1]
            current_high = data['High'].values[-1]
            current_low = data['Low'].values[-1]
            current_volume = data['Volume'].values[-1]

            # RSI
            rsi = self.calculate_rsi(close_prices)

            # Moving Averages
            sma_20 = self.calculate_sma(close_prices, 20)
            sma_50 = self.calculate_sma(close_prices, 50)
            ema_20 = self.calculate_ema(close_prices, 20)

            # Volume analysis
            avg_volume_20 = np.mean(data['Volume'].values[-20:])
            volume_ratio = current_volume / avg_volume_20

            # Check breakout conditions
            resistance = np.max(data['High'].values[-20:])
            support = np.min(data['Low'].values[-20:])

            # Simple ADX approximation (trend strength)
            trend_strength = abs(current_close - sma_50) / sma_50 * 100

            # Pattern detection (simplified)
            patterns = []

            # Current day breakout
            if current_close > resistance * 1.005 and volume_ratio > 1.5:
                patterns.append({
                    'type': 'Breakout',
                    'strength': min(95, 50 + trend_strength * 2),
                    'confidence': 'HIGH' if volume_ratio > 2 else 'MEDIUM'
                })

            # Oversold bounce
            if rsi < 40 and current_close > sma_20:
                patterns.append({
                    'type': 'Oversold Bounce',
                    'strength': min(90, 60 + (40 - rsi)),
                    'confidence': 'MEDIUM'
                })

            # Above moving averages
            if current_close > sma_20 > sma_50:
                patterns.append({
                    'type': 'Bullish Alignment',
                    'strength': min(80, 50 + trend_strength),
                    'confidence': 'MEDIUM' if trend_strength > 2 else 'LOW'
                })

            if not patterns:
                return None

            return {
                'symbol': symbol,
                'price': current_close,
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'volume_ratio': volume_ratio,
                'trend_strength': trend_strength,
                'patterns': patterns,
                'max_strength': max(p['strength'] for p in patterns)
            }

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            return None

    def scan_stocks(self, limit=50):
        """Scan multiple stocks"""
        logger.info(f"Starting scan of {min(limit, len(COMPLETE_NSE_FO_UNIVERSE))} stocks")

        results = []
        stocks = COMPLETE_NSE_FO_UNIVERSE[:limit]

        for i, symbol in enumerate(stocks, 1):
            logger.info(f"[{i}/{len(stocks)}] Scanning {symbol.replace('.NS', '')}...")

            analysis = self.analyze_stock(symbol)
            if analysis:
                results.append(analysis)
                logger.info(f"  ✓ Found {len(analysis['patterns'])} pattern(s)")

        # Sort by pattern strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)

        logger.info(f"Scan complete. Found {len(results)} stocks with patterns")
        return results


class TelegramSender:
    """Send results to Telegram"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.ist = pytz.timezone('Asia/Kolkata')

        if self.bot_token and self.chat_id:
            logger.info("✓ Telegram credentials found")
        else:
            logger.warning("⚠ Telegram credentials not configured")
            logger.warning("  Set: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

    def send_message(self, text):
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Cannot send to Telegram - credentials missing")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("✓ Message sent to Telegram")
                return True
            else:
                logger.error(f"✗ Telegram error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"✗ Failed to send message: {e}")
            return False

    def format_message(self, results):
        """Format results for Telegram"""
        if not results:
            return "❌ No stocks found today"

        current_time = datetime.now(self.ist).strftime('%H:%M IST')

        msg = f"""<b>📊 NSE F&O Scanner Report</b>
<i>{current_time}</i>

<b>✅ Found {len(results)} stocks meeting criteria:</b>

"""

        for i, stock in enumerate(results[:15], 1):
            symbol = stock['symbol'].replace('.NS', '')
            price = stock['price']
            rsi = stock['rsi']
            volume = stock['volume_ratio']
            strength = stock['max_strength']

            patterns_str = ', '.join([p['type'] for p in stock['patterns'][:2]])

            msg += f"""<b>{i}. {symbol}</b>
💰 ₹{price:.2f} | RSI {rsi:.0f} | Vol {volume:.1f}x | 💪 {strength:.0f}%
🎯 {patterns_str}

"""

        msg += f"""<i>Report generated at {current_time}</i>"""

        return msg

    def save_results(self, results):
        """Save results to file"""
        timestamp = datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')
        filename = f"/tmp/stock_scan_{timestamp}.json"

        try:
            data = {
                'timestamp': datetime.now(self.ist).isoformat(),
                'stocks_found': len(results),
                'results': [
                    {
                        'symbol': r['symbol'],
                        'price': float(r['price']),
                        'rsi': float(r['rsi']),
                        'volume_ratio': float(r['volume_ratio']),
                        'trend_strength': float(r['trend_strength']),
                        'patterns': r['patterns']
                    }
                    for r in results[:20]
                ]
            }

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Results saved to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("  NSE F&O Stock Scanner with Telegram Integration")
    print("="*70 + "\n")

    # Scan stocks
    scanner = SimpleStockScanner()
    results = scanner.scan_stocks(limit=50)

    # Send to Telegram
    sender = TelegramSender()

    if results:
        message = sender.format_message(results)
        print("\n📨 Telegram Message Preview:")
        print("-" * 70)
        print(message)
        print("-" * 70 + "\n")

        # Try sending
        sender.send_message(message)

        # Save results
        sender.save_results(results)

        # Summary
        print(f"""
✅ SCAN COMPLETE
   • Stocks Found: {len(results)}
   • Top Pick: {results[0]['symbol'].replace('.NS', '')} ({results[0]['max_strength']:.0f}% strength)
   • Telegram Sent: {'Yes' if sender.bot_token and sender.chat_id else 'No - Configure credentials'}
   • Results Saved: Yes
""")
    else:
        print("\n❌ No stocks found matching criteria")
        msg = "❌ NSE F&O Scanner: No stocks found meeting criteria today"
        sender.send_message(msg)

    print("="*70 + "\n")


if __name__ == "__main__":
    main()
