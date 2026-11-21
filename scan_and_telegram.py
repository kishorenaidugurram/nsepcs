#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner with Telegram Integration
Runs the stock scanning filters and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


class StockScanner:
    """Simplified stock scanner for standalone use"""

    def __init__(self):
        self.ist = __import__('pytz').timezone('Asia/Kolkata')

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        return {'MACD': macd, 'Signal': signal_line}

    def _calculate_adx(self, data, period=14):
        """Calculate ADX (simplified)"""
        high = data['High']
        low = data['Low']
        close = data['Close']

        tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
        atr = tr.rolling(period).mean()

        plus_dm = np.where(high.diff() > low.diff().abs(), high.diff(), 0)
        minus_dm = np.where(low.diff().abs() > high.diff(), low.diff().abs(), 0)

        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

        di_diff = abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        di_ratio = (di_diff / (di_sum + 1e-10)).rolling(period).mean()
        adx = 100 * di_ratio

        return adx.fillna(0)

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch and calculate technical indicators"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")

            if len(data) < 20:
                return None

            # Calculate technical indicators
            data['RSI'] = self._calculate_rsi(data['Close'], 14)
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['ADX'] = self._calculate_adx(data, 14)

            macd_data = self._calculate_macd(data['Close'])
            data['MACD'] = macd_data['MACD']
            data['MACD_signal'] = macd_data['Signal']

            return data
        except Exception as e:
            logger.debug(f"Error fetching data for {symbol}: {e}")
            return None

    def check_volume_criteria(self, data, min_ratio=1.5):
        """Check if volume meets criteria"""
        if len(data) < 21:
            return False, 0

        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_ratio = current_volume / avg_20_volume

        return volume_ratio >= min_ratio, volume_ratio

    def detect_patterns(self, data, symbol):
        """Detect technical patterns"""
        if len(data) < 50:
            return []

        patterns = []

        # Get current values
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]

        # Check basic conditions
        if not pd.isna(current_rsi):
            if current_rsi < 30:
                patterns.append({'type': 'RSI Oversold', 'signal': 'Bullish', 'rsi': current_rsi})
            elif current_rsi > 70:
                patterns.append({'type': 'RSI Overbought', 'signal': 'Bearish', 'rsi': current_rsi})

        if not pd.isna(current_adx) and current_adx > 25:
            patterns.append({'type': 'Strong Trend', 'signal': 'Trend Present', 'adx': current_adx})

        # Check moving average crossovers
        if len(data) >= 50:
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]

            if not pd.isna(sma_20) and not pd.isna(sma_50):
                if current_price > sma_20 > sma_50:
                    patterns.append({'type': 'Moving Average', 'signal': 'Bullish Trend', 'price': current_price})

        # Check MACD
        if not pd.isna(data['MACD'].iloc[-1]) and not pd.isna(data['MACD_signal'].iloc[-1]):
            macd = data['MACD'].iloc[-1]
            macd_signal = data['MACD_signal'].iloc[-1]

            if macd > macd_signal:
                patterns.append({'type': 'MACD', 'signal': 'Bullish', 'macd': macd})

        return patterns

    def scan_stocks(self, symbols, filters):
        """Scan multiple stocks with filters"""
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for symbol in symbols:
                futures[executor.submit(self._analyze_stock, symbol, filters)] = symbol

            completed = 0
            total = len(symbols)

            for future in as_completed(futures):
                completed += 1
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    logger.info(f"Scanned {completed}/{total} stocks - Found {len(results)} so far")
                except Exception as e:
                    logger.debug(f"Error scanning {futures[future]}: {e}")

        return sorted(results, key=lambda x: x.get('strength', 0), reverse=True)

    def _analyze_stock(self, symbol, filters):
        """Analyze individual stock"""
        try:
            data = self.get_stock_data(symbol)
            if data is None:
                return None

            # Check volume criteria
            volume_ok, volume_ratio = self.check_volume_criteria(
                data,
                min_ratio=filters.get('min_volume_ratio', 1.5)
            )

            if not volume_ok:
                return None

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Skip if NaN
            if pd.isna(current_rsi) or pd.isna(current_adx):
                return None

            # Apply filters
            rsi_min = filters.get('rsi_min', 30)
            rsi_max = filters.get('rsi_max', 80)
            adx_min = filters.get('adx_min', 20)

            if not (rsi_min <= current_rsi <= rsi_max):
                return None

            if current_adx < adx_min:
                return None

            # Detect patterns
            patterns = self.detect_patterns(data, symbol)
            if not patterns:
                return None

            # Calculate strength score
            strength = 0
            strength += (current_rsi / 100) * 30  # RSI contribution
            strength += min(max(current_adx / 50, 0), 1) * 30  # ADX contribution
            strength += min(volume_ratio / 3, 1) * 25  # Volume contribution
            strength += len(patterns) * 5  # Pattern count

            return {
                'symbol': symbol.replace('.NS', ''),
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': patterns,
                'strength': min(strength, 100),
                'patterns_count': len(patterns)
            }

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            return None


def send_to_telegram(results, telegram_token, telegram_chat_id):
    """Send scan results to Telegram"""
    if not telegram_token or not telegram_chat_id:
        logger.error("Telegram credentials not provided. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    try:
        # Create message
        message = "📊 **NSE F&O STOCK SCAN RESULTS**\n"
        message += f"🕐 Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n\n"

        if not results:
            message += "No stocks matching criteria found today."
        else:
            message += f"🎯 Found {len(results)} stocks\n\n"

            for i, stock in enumerate(results[:20], 1):  # Limit to top 20
                message += f"**{i}. {stock['symbol']}**\n"
                message += f"   💰 Price: ₹{stock['price']:.2f}\n"
                message += f"   📈 RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
                message += f"   📊 Volume: {stock['volume_ratio']:.1f}x | Strength: {stock['strength']:.0f}%\n"
                message += f"   🎯 Patterns: {stock['patterns_count']}\n\n"

        # Send to Telegram
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Results sent to Telegram successfully")
            return True
        else:
            logger.error(f"❌ Failed to send Telegram message: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending to Telegram: {e}")
        traceback.print_exc()
        return False


def main():
    """Main execution function"""
    logger.info("🚀 Starting NSE F&O Stock Scanner...")

    # Get Telegram credentials from environment
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    # NSE F&O stocks universe (top 60 for quick scanning)
    stocks = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
        'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
        'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
        'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
        'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
        'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
        'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS',
        'HDFCLIFE.NS', 'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS',
        'BANKBARODA.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS', 'IDFCFIRSTB.NS'
    ]

    # Define filters
    filters = {
        'rsi_min': 30,
        'rsi_max': 80,
        'adx_min': 20,
        'min_volume_ratio': 1.5
    }

    try:
        # Scan stocks
        scanner = StockScanner()
        logger.info(f"📊 Scanning {len(stocks)} stocks...")
        results = scanner.scan_stocks(stocks, filters)

        logger.info(f"✅ Scan complete. Found {len(results)} qualifying stocks")

        # Save results to JSON
        output_dir = '/tmp/claude-0/-home-user-nsepcs/scratchpad'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'scan_results.json')

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"📁 Results saved to {output_file}")

        # Print results to console
        if results:
            logger.info("\n" + "="*60)
            logger.info("SCAN RESULTS")
            logger.info("="*60)
            for i, stock in enumerate(results[:20], 1):
                logger.info(f"{i}. {stock['symbol']} - Price: ₹{stock['price']:.2f}, RSI: {stock['rsi']:.1f}, ADX: {stock['adx']:.1f}, Strength: {stock['strength']:.0f}%")
            logger.info("="*60)

        # Send to Telegram if credentials available
        if telegram_token and telegram_chat_id:
            logger.info("📱 Sending results to Telegram...")
            success = send_to_telegram(results, telegram_token, telegram_chat_id)
            return success
        else:
            logger.warning("⚠️  Telegram credentials not set. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to send results")
            return True  # Still success, just no telegram send

    except Exception as e:
        logger.error(f"❌ Error during scanning: {e}")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
