#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Simple Telegram Notification Service
Lightweight version without complex dependencies
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import requests
import yfinance as yf
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NSE F&O stocks list
COMPLETE_NSE_FO_UNIVERSE = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS',
    'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS',
    'BHARTIARTL.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS',
    'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS',
    'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS',
    'BANKNIFTY.NS', 'NIFTY.NS'
]


class SimpleTelegramScanner:
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize scanner with Telegram credentials"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

        # Default filter configuration
        self.min_volume_ratio = 1.2
        self.lookback_days = 20

    def calculate_rsi(self, data, period=14):
        """Calculate RSI indicator"""
        try:
            close = data['Close']
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return None

    def calculate_adx(self, data, period=14):
        """Simplified ADX calculation"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']

            tr = np.maximum(
                high - low,
                np.maximum(
                    np.abs(high - close.shift()),
                    np.abs(low - close.shift())
                )
            )
            atr = pd.Series(tr).rolling(window=period).mean()

            up = high - high.shift()
            down = low.shift() - low

            pos_dm = np.where((up > down) & (up > 0), up, 0)
            neg_dm = np.where((down > up) & (down > 0), down, 0)

            pos_di = 100 * (pd.Series(pos_dm).rolling(window=period).mean() / atr)
            neg_di = 100 * (pd.Series(neg_dm).rolling(window=period).mean() / atr)

            di_diff = np.abs(pos_di - neg_di)
            di_sum = pos_di + neg_di
            dx = 100 * (di_diff / di_sum)

            adx = pd.Series(dx).rolling(window=period).mean()
            return adx
        except:
            return None

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch stock data from Yahoo Finance"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            if data is None or len(data) == 0:
                return None
            return data
        except Exception as e:
            logger.warning(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def analyze_stock(self, symbol):
        """Analyze a single stock"""
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')

            # Get data
            data = self.get_stock_data(symbol, period="6mo")
            if data is None or len(data) < 30:
                return None

            # Calculate indicators
            rsi = self.calculate_rsi(data)
            adx = self.calculate_adx(data)

            if rsi is None or adx is None:
                return None

            current_price = data['Close'].iloc[-1]
            current_rsi = rsi.iloc[-1]
            current_adx = adx.iloc[-1]

            # Volume analysis
            avg_volume = data['Volume'].tail(20).mean()
            current_volume = data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            # Simple pattern detection - check if stock shows strength
            # Look for: price above 20-day MA, RSI between 40-70, ADX > 20, volume above average
            sma_20 = data['Close'].tail(20).mean()
            price_above_ma = current_price > sma_20

            # Filter criteria
            rsi_ok = 40 <= current_rsi <= 70
            adx_ok = current_adx >= 20
            volume_ok = volume_ratio >= self.min_volume_ratio
            trend_ok = price_above_ma

            if rsi_ok and adx_ok and volume_ok and trend_ok:
                strength = min(
                    (current_rsi - 40) * 2,  # RSI component
                    (current_adx / 50) * 100,  # ADX component
                    (volume_ratio / 2) * 100,  # Volume component
                    100  # Cap at 100
                )

                return {
                    'symbol': symbol,
                    'clean_symbol': clean_symbol,
                    'price': current_price,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'volume_ratio': volume_ratio,
                    'strength': strength,
                    'sma_20': sma_20,
                    'price_above_ma': price_above_ma
                }

            return None

        except Exception as e:
            logger.warning(f"Error analyzing {symbol}: {str(e)}")
            return None

    def run_scan(self):
        """Run scan on all stocks"""
        results = []
        total = len(COMPLETE_NSE_FO_UNIVERSE)

        logger.info(f"Starting scan of {total} stocks...")

        for i, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE, 1):
            logger.info(f"[{i}/{total}] Analyzing {symbol}...")
            result = self.analyze_stock(symbol)
            if result:
                results.append(result)
                logger.info(f"  ✓ {result['clean_symbol']} - Strength: {result['strength']:.0f}%")

        # Sort by strength
        results.sort(key=lambda x: x['strength'], reverse=True)
        logger.info(f"Found {len(results)} qualifying stocks")

        return results

    def format_telegram_message(self, results):
        """Format results for Telegram"""
        if not results:
            return "❌ No stocks met the filter criteria today."

        message = f"""📊 <b>NSE F&O PCS Scan Results</b>
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 <b>Found {len(results)} Qualifying Stocks</b>

<b>Summary Metrics:</b>
• Average Strength: {np.mean([r['strength'] for r in results]):.1f}%
• Highest Strength: {results[0]['strength']:.1f}%
• Average Volume Ratio: {np.mean([r['volume_ratio'] for r in results]):.2f}x

<b>Top Stocks:</b>
"""

        for idx, stock in enumerate(results[:10], 1):
            confidence = '🟢' if stock['strength'] >= 80 else '🟡' if stock['strength'] >= 60 else '🔴'
            message += f"""
{idx}. <b>{stock['clean_symbol']}</b> {confidence}
   Price: ₹{stock['price']:.2f} | SMA20: ₹{stock['sma_20']:.2f}
   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}
   Strength: {stock['strength']:.0f}% | Volume: {stock['volume_ratio']:.1f}x"""

        if len(results) > 10:
            message += f"\n\n... and {len(results) - 10} more stocks"

        message += f"""

⚠️ <b>Disclaimer:</b> For educational purposes only. Not financial advice."""

        return message

    def send_telegram_message(self, text):
        """Send message to Telegram"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✓ Message sent to Telegram")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                logger.error(response.text)
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False

    def run(self):
        """Run complete scan and send notification"""
        try:
            logger.info("=" * 60)
            logger.info("NSE F&O Simple Telegram Scanner")
            logger.info("=" * 60)

            # Test connection
            logger.info("Testing Telegram connection...")
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            if response.status_code != 200:
                raise Exception("Telegram connection failed")
            logger.info("✓ Telegram connection OK")

            # Run scan
            logger.info("Running stock analysis...")
            results = self.run_scan()

            # Format and send
            logger.info("Formatting message...")
            message = self.format_telegram_message(results)

            logger.info("Sending Telegram notification...")
            self.send_telegram_message(message)

            logger.info("=" * 60)
            logger.info("✓ Scan completed successfully")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            try:
                error_msg = f"❌ <b>NSE F&O Scan Error</b>\n\n{str(e)}"
                self.send_telegram_message(error_msg)
            except:
                pass
            return False


def main():
    """Main entry point"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Missing environment variables:")
        logger.error("  TELEGRAM_BOT_TOKEN - Telegram bot token")
        logger.error("  TELEGRAM_CHAT_ID - Telegram chat ID")
        sys.exit(1)

    scanner = SimpleTelegramScanner(bot_token, chat_id)
    success = scanner.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
