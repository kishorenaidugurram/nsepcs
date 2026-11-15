#!/usr/bin/env python3
"""
Simple NSE F&O Scanner - Minimal dependencies
Analyzes stocks and sends results to Telegram
"""

import os
import sys
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import requests
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    logger.info("Install with: pip install yfinance pandas numpy requests")
    sys.exit(1)

# NSE F&O Stocks - Core list
NSE_FO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'BHARTIARTL.NS', 'ITC.NS',
    'LT.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
]

class SimpleScanner:
    """Minimal PCS scanner"""

    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    def get_stock_data(self, symbol, period='3mo'):
        """Fetch stock data"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            if len(data) < 20:
                return None
            return data
        except Exception as e:
            logger.debug(f"Error fetching {symbol}: {e}")
            return None

    def calculate_rsi(self, data, period=14):
        """Calculate RSI"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def analyze_stock(self, symbol):
        """Analyze a single stock"""
        try:
            data = self.get_stock_data(symbol)
            if data is None:
                return None

            # Calculate indicators
            data['RSI'] = self.calculate_rsi(data)
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['SMA50'] = data['Close'].rolling(window=50).mean()

            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            volume_today = data['Volume'].iloc[-1]
            volume_avg = data['Volume'].iloc[-20:].mean()

            # Skip if NaN
            if pd.isna(current_rsi) or pd.isna(current_price):
                return None

            # Basic filter criteria
            rsi_ok = 30 <= current_rsi <= 75
            support_ok = current_price > data['SMA20'].iloc[-1] * 0.97
            volume_ok = volume_today > volume_avg * 1.2

            if not (rsi_ok and support_ok and volume_ok):
                return None

            # Calculate pattern strength (0-100)
            strength = 50  # Base strength

            # RSI scoring
            if 45 <= current_rsi <= 65:
                strength += 20
            elif 35 <= current_rsi <= 75:
                strength += 10

            # Price vs MA
            if current_price > data['SMA50'].iloc[-1]:
                strength += 15

            if current_price > data['SMA20'].iloc[-1]:
                strength += 10

            # Volume scoring
            volume_ratio = volume_today / volume_avg
            if volume_ratio > 2:
                strength += 15
            elif volume_ratio > 1.5:
                strength += 10

            strength = min(100, strength)

            return {
                'symbol': symbol.replace('.NS', ''),
                'price': current_price,
                'rsi': current_rsi,
                'volume_ratio': volume_ratio,
                'strength': strength,
                'volume_avg': volume_avg,
            }
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def scan(self, stocks=None, max_stocks=20):
        """Scan stocks"""
        if stocks is None:
            stocks = NSE_FO_STOCKS

        stocks = stocks[:max_stocks]
        logger.info(f"Scanning {len(stocks)} stocks...")

        results = []
        for i, symbol in enumerate(stocks, 1):
            logger.info(f"[{i}/{len(stocks)}] Analyzing {symbol.replace('.NS', '')}...")
            result = self.analyze_stock(symbol)
            if result:
                results.append(result)
                logger.info(f"✓ Found: {result['symbol']} - Strength: {result['strength']:.0f}%")

        # Sort by strength
        results.sort(key=lambda x: x['strength'], reverse=True)
        return results

    def format_for_telegram(self, results):
        """Format results for Telegram"""
        if not results:
            return "📊 NSE F&O Scanner\n\nNo stocks found today meeting the criteria."

        msg = f"📊 *NSE F&O PCS Scanner Results*\n"
        msg += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n\n"
        msg += f"🎯 Found *{len(results)}* stocks\n"
        msg += "=" * 40 + "\n\n"

        for i, r in enumerate(results[:15], 1):
            strength_bar = "█" * int(r['strength']/10) + "░" * (10 - int(r['strength']/10))
            msg += f"{i}. *{r['symbol']}*\n"
            msg += f"   💰 ₹{r['price']:.2f} | RSI: {r['rsi']:.1f}\n"
            msg += f"   📊 Vol: {r['volume_ratio']:.2f}x\n"
            msg += f"   {strength_bar} {r['strength']:.0f}%\n\n"

        if len(results) > 15:
            msg += f"... and {len(results) - 15} more stocks\n\n"

        msg += "=" * 40 + "\n"
        msg += "✅ Trade Smart. Trade Safe.\n"

        return msg

    def send_telegram(self, message):
        """Send message via Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram credentials not configured.")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                logger.info("✓ Message sent to Telegram!")
                return True
            else:
                logger.error(f"Telegram error: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def run(self, max_stocks=20):
        """Run complete scan and send to Telegram"""
        logger.info("Starting NSE F&O Scanner...")

        results = self.scan(max_stocks=max_stocks)
        message = self.format_for_telegram(results)

        print("\n" + "=" * 60)
        print(message)
        print("=" * 60 + "\n")

        if self.telegram_token and self.telegram_chat_id:
            self.send_telegram(message)
        else:
            logger.warning("Telegram not configured. Skipping Telegram send.")

        # Save results
        try:
            with open('/tmp/scan_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info("Results saved to /tmp/scan_results.json")
        except:
            pass

        return len(results) > 0


if __name__ == '__main__':
    scanner = SimpleScanner()
    success = scanner.run(max_stocks=20)
    sys.exit(0 if success else 1)
