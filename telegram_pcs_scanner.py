#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Integration
Runs PCS analysis and sends qualifying stocks to Telegram
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram integration
try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Install with: pip install python-telegram-bot")

# Default filter criteria
# Technical indicator helper functions
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr


def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
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


DEFAULT_FILTERS = {
    'min_pattern_strength': 60,  # Minimum pattern strength (0-100)
    'min_pcs_suitability': 80,   # Minimum PCS suitability (0-100)
    'rsi_min': 45,
    'rsi_max': 70,
    'adx_min': 20,
    'ma_support': True,
    'ma_type': 'SMA',
    'ma_tolerance': 2,
    'lookback_days': 20,
    'volume_breakout_ratio': 2.0,
    'pattern_strength_min': 60,
}

# Stock universe
STOCK_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
]


class PCSScanner:
    def __init__(self, filters: Dict = None):
        self.filters = filters or DEFAULT_FILTERS.copy()
        self.ist = pytz.timezone('Asia/Kolkata')
        self.results = []

    def fetch_stock_data(self, symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """Fetch and process stock data"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")

            if data is None or len(data) < 20:
                return None

            # Calculate technical indicators
            data['RSI'] = calculate_rsi(data['Close'])
            data['SMA_20'] = calculate_sma(data['Close'], 20)
            data['SMA_50'] = calculate_sma(data['Close'], 50)
            data['EMA_20'] = calculate_ema(data['Close'], 20)

            # Bollinger Bands
            sma_20 = data['SMA_20']
            std_20 = data['Close'].rolling(20).std()
            data['BB_upper'] = sma_20 + (std_20 * 2)
            data['BB_lower'] = sma_20 - (std_20 * 2)

            # MACD
            data['MACD'], data['MACD_signal'], data['MACD_hist'] = calculate_macd(data['Close'])

            # ADX
            data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])

            return data
        except Exception as e:
            logger.warning(f"Error fetching data for {symbol}: {e}")
            return None

    def detect_current_day_breakout(self, data: pd.DataFrame) -> tuple:
        """Detect breakouts on current day with volume confirmation"""
        if len(data) < 21:
            return False, 0, {}

        try:
            current_day = data.iloc[-1]
            lookback_data = data.iloc[-21:-1]

            resistance = lookback_data['High'].max()
            support = lookback_data['Low'].min()

            current_close = current_day['Close']
            current_volume = current_day['Volume']
            avg_volume = lookback_data['Volume'].mean()

            # Breakout conditions
            price_breakout = current_close > resistance * 1.005
            volume_breakout = current_volume > (avg_volume * self.filters['volume_breakout_ratio'])
            consolidation_range = ((resistance - support) / support) * 100
            tight_consolidation = consolidation_range < 15

            if not (price_breakout and volume_breakout and tight_consolidation):
                return False, 0, {}

            # Calculate strength
            strength = 0
            breakout_percentage = ((current_close - resistance) / resistance) * 100

            if breakout_percentage >= 3:
                strength += 35
            elif breakout_percentage >= 2:
                strength += 25
            elif breakout_percentage >= 1:
                strength += 20
            else:
                strength += 15

            volume_ratio = current_volume / avg_volume
            if volume_ratio >= 4:
                strength += 30
            elif volume_ratio >= 3:
                strength += 25
            elif volume_ratio >= 2:
                strength += 20

            if consolidation_range <= 8:
                strength += 25
            elif consolidation_range <= 12:
                strength += 20
            elif consolidation_range <= 15:
                strength += 15

            details = {
                'date': str(current_day.name.date()),
                'close': round(current_close, 2),
                'volume': int(current_volume),
                'resistance': round(resistance, 2),
                'breakout_pct': round(breakout_percentage, 2),
                'volume_ratio': round(volume_ratio, 1),
            }

            return True, strength, details
        except Exception as e:
            logger.warning(f"Error detecting breakout: {e}")
            return False, 0, {}

    def check_filters(self, data: pd.DataFrame) -> bool:
        """Check if stock meets basic filter criteria"""
        if data is None or len(data) < 20:
            return False

        try:
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]

            # Check RSI
            if not (self.filters['rsi_min'] <= current_rsi <= self.filters['rsi_max']):
                return False

            # Check ADX
            if current_adx < self.filters['adx_min']:
                return False

            # Check MA support
            if self.filters['ma_support']:
                if current_price < sma_20 * (1 - self.filters['ma_tolerance']/100):
                    return False

            return True
        except Exception:
            return False

    def analyze_stock(self, symbol: str) -> Optional[Dict]:
        """Analyze single stock and return result if it meets criteria"""
        try:
            data = self.fetch_stock_data(symbol)

            if not self.check_filters(data):
                return None

            # Check for breakout
            breakout_detected, breakout_strength, breakout_details = self.detect_current_day_breakout(data)

            if not breakout_detected:
                return None

            # Calculate PCS suitability (mock calculation)
            pcs_suitability = min(100, int(breakout_strength * 0.9))  # Simplified

            # Filter by strength and suitability
            if breakout_strength < self.filters['pattern_strength_min']:
                return None

            if pcs_suitability < self.filters['min_pcs_suitability']:
                return None

            return {
                'symbol': symbol,
                'strength': breakout_strength,
                'pcs_suitability': pcs_suitability,
                'pattern_type': 'Current Day Breakout',
                'price': round(data['Close'].iloc[-1], 2),
                'rsi': round(data['RSI'].iloc[-1], 1),
                'adx': round(data['ADX'].iloc[-1], 1),
                'details': breakout_details
            }
        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            return None

    def scan_stocks(self, stock_list: List[str] = None, max_workers: int = 5) -> List[Dict]:
        """Scan multiple stocks for PCS opportunities"""
        stock_list = stock_list or STOCK_LIST

        logger.info(f"Starting PCS scan of {len(stock_list)} stocks...")
        self.results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.analyze_stock, symbol): symbol for symbol in stock_list}

            completed = 0
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                        logger.info(f"✓ {symbol}: Strength={result['strength']:.0f}, PCS={result['pcs_suitability']}%")
                except Exception as e:
                    logger.warning(f"✗ {symbol}: {e}")

                completed += 1
                if completed % 5 == 0:
                    logger.info(f"Progress: {completed}/{len(stock_list)}")

        # Sort by strength
        self.results.sort(key=lambda x: x['strength'], reverse=True)
        logger.info(f"✓ Found {len(self.results)} qualifying stocks")

        return self.results

    def format_telegram_message(self, results: List[Dict] = None) -> str:
        """Format results for Telegram message"""
        results = results or self.results

        if not results:
            return "📊 NSE PCS Scanner\nNo qualifying stocks found in this scan."

        message = "📊 NSE F&O PCS Scanner Results\n"
        message += f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')}\n"
        message += f"📈 Found: {len(results)} stocks\n\n"

        for i, stock in enumerate(results[:10], 1):  # Top 10
            message += f"{i}. {stock['symbol']}\n"
            message += f"   💪 Strength: {stock['strength']:.0f}/100\n"
            message += f"   🎯 PCS Fit: {stock['pcs_suitability']}%\n"
            message += f"   💹 Price: ₹{stock['price']}\n"
            message += f"   📊 RSI: {stock['rsi']}, ADX: {stock['adx']}\n\n"

        if len(results) > 10:
            message += f"... and {len(results) - 10} more stocks\n"

        message += "\n⚠️ Not financial advice. Trade at your own risk."

        return message

    async def send_telegram_message(self, message: str, token: str, chat_id: str) -> bool:
        """Send message to Telegram"""
        if not TELEGRAM_AVAILABLE:
            logger.error("python-telegram-bot not installed")
            return False

        try:
            bot = Bot(token=token)
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"✓ Message sent to Telegram chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to send Telegram message: {e}")
            return False


def main():
    """Main entry point"""
    # Get Telegram credentials from environment
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    # Parse arguments for custom stock list
    custom_stocks = None
    if len(sys.argv) > 1:
        # Allow passing custom stock symbols as arguments
        custom_stocks = sys.argv[1:]

    # Initialize scanner
    scanner = PCSScanner(filters=DEFAULT_FILTERS)

    # Run scan
    results = scanner.scan_stocks(stock_list=custom_stocks or STOCK_LIST)

    # Format message
    message = scanner.format_telegram_message(results)

    # Print to console
    print("\n" + message)
    print("\n" + "="*60)

    # Save results to JSON
    with open('/tmp/pcs_scan_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    logger.info("Results saved to /tmp/pcs_scan_results.json")

    # Send to Telegram if credentials available
    if telegram_token and telegram_chat_id:
        asyncio.run(scanner.send_telegram_message(message, telegram_token, telegram_chat_id))
    else:
        logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping Telegram notification.")
        if not telegram_token:
            logger.info("Set TELEGRAM_BOT_TOKEN environment variable")
        if not telegram_chat_id:
            logger.info("Set TELEGRAM_CHAT_ID environment variable")

    # Print summary
    logger.info("\n" + "="*60)
    logger.info(f"Scan complete. Found {len(results)} qualifying stocks.")
    logger.info(f"Full results available in /tmp/pcs_scan_results.json")


if __name__ == "__main__":
    main()
