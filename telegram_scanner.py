#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner with Telegram integration
Extracts stocks meeting filter criteria and sends to Telegram
"""

import os
import json
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# NSE F&O stocks universe
COMPLETE_NSE_FO_UNIVERSE = [
    # Tier 1 - Ultra High Liquidity
    'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
    # Tier 2 - High Liquidity
    'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI', 'ASIANPAINT', 'BHARTIARTL', 'SUNPHARMA',
    'TATAMOTORS', 'ADANIENT',
    # Tier 3 - Medium Liquidity
    'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN', 'NESTLEIND', 'ULTRACEMCO',
    'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA', 'JSWSTEEL', 'TATASTEEL', 'HINDALCO'
]

class SimpleIndicators:
    """Calculate technical indicators without the `ta` library"""

    @staticmethod
    def rsi(prices, period=14):
        """Calculate RSI"""
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

    @staticmethod
    def sma(prices, period=20):
        """Calculate SMA"""
        return pd.Series(prices).rolling(window=period).mean().values

    @staticmethod
    def ema(prices, period=20):
        """Calculate EMA"""
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values

    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = SimpleIndicators.sma(prices, period)
        std = pd.Series(prices).rolling(window=period).std().values
        bb_upper = sma + (std_dev * std)
        bb_lower = sma - (std_dev * std)
        return bb_upper, sma, bb_lower

    @staticmethod
    def macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
        ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd.values, macd_signal.values, macd_hist.values

class PCSScanner:
    """Simplified PCS Scanner for Telegram reporting"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.indicators = SimpleIndicators()
        self.use_synthetic = False  # Will be set to True if real data unavailable

    def generate_synthetic_data(self, symbol, base_price=100):
        """Generate synthetic OHLCV data for testing"""
        np.random.seed(hash(symbol) % 2**32)
        dates = pd.date_range(end=datetime.now(), periods=60, freq='1D')

        prices = [base_price]
        for _ in range(59):
            change = np.random.normal(0, 2)  # 2% std dev
            prices.append(prices[-1] * (1 + change / 100))

        data = pd.DataFrame({
            'Date': dates,
            'Open': [p * (1 + np.random.normal(0, 0.5)/100) for p in prices],
            'High': [p * (1 + abs(np.random.normal(0.5, 0.5))/100) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0.5, 0.5))/100) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 60)
        }, index=dates)

        return data

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch stock data and calculate indicators"""
        try:
            data = None
            # Add .NS suffix for NSE stocks if not already present
            ticker = f"{symbol}.NS" if '.' not in symbol else symbol

            # Try to fetch data from Yahoo Finance
            try:
                data = yf.download(ticker, period=period, progress=False)
                if data is not None and len(data) >= 20:
                    logger.debug(f"Fetched real data for {symbol}")
            except Exception as e:
                logger.debug(f"Could not fetch real data for {symbol}: {str(e)[:50]}")
                data = None

            # Use synthetic data if real data not available
            if data is None or len(data) < 20:
                logger.info(f"Using synthetic data for {symbol}")
                self.use_synthetic = True
                data = self.generate_synthetic_data(symbol)

            if data is None or len(data) < 20:
                return None

            # Calculate indicators
            close_prices = data['Close'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values

            data['RSI'] = self.indicators.rsi(close_prices)
            data['SMA_20'] = self.indicators.sma(close_prices, 20)
            data['SMA_50'] = self.indicators.sma(close_prices, 50)
            data['EMA_20'] = self.indicators.ema(close_prices, 20)
            bb_upper, bb_mid, bb_lower = self.indicators.bollinger_bands(close_prices)
            data['BB_upper'] = bb_upper
            data['BB_middle'] = bb_mid
            data['BB_lower'] = bb_lower
            data['MACD'], data['MACD_signal'], data['MACD_hist'] = self.indicators.macd(close_prices)

            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def calculate_pcs_score(self, data, symbol):
        """Calculate PCS score based on technical analysis"""
        try:
            if data is None or len(data) < 20:
                return None

            # Get latest values
            current_price = data['Close'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            bb_upper = data['BB_upper'].iloc[-1]
            bb_lower = data['BB_lower'].iloc[-1]
            bb_middle = data['BB_middle'].iloc[-1]
            macd = data['MACD'].iloc[-1]
            macd_signal = data['MACD_signal'].iloc[-1]
            macd_hist = data['MACD_hist'].iloc[-1]

            score = 0

            # 1. Bullish Momentum (30%)
            if 45 <= rsi <= 65:
                score += 30  # Optimal RSI range
            elif 30 < rsi < 70:
                score += 20
            elif rsi > 20:
                score += 10

            # 2. Trend Strength (25%)
            if macd_hist > 0 and macd > macd_signal:
                score += 25
            elif macd > macd_signal:
                score += 15
            elif macd > 0:
                score += 10

            # 3. Support Proximity (20%)
            distance_to_bb_lower = ((current_price - bb_lower) / (bb_middle - bb_lower)) * 100 if (bb_middle - bb_lower) != 0 else 50
            if distance_to_bb_lower > 30:
                score += 20
            elif distance_to_bb_lower > 20:
                score += 15
            elif distance_to_bb_lower > 10:
                score += 10

            # 4. Volatility (15%) - Prefer moderate volatility
            volatility = ((bb_upper - bb_lower) / bb_middle * 100) if bb_middle != 0 else 0
            if 8 <= volatility <= 20:
                score += 15
            elif volatility < 25:
                score += 10

            # 5. Volume Confirmation (10%)
            volume_avg = data['Volume'].tail(20).mean()
            if data['Volume'].iloc[-1] > volume_avg * 1.1:
                score += 10
            elif data['Volume'].iloc[-1] > volume_avg:
                score += 5

            return {
                'score': score,
                'rsi': rsi,
                'price': current_price,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'macd': macd,
                'volatility': volatility
            }
        except Exception as e:
            logger.error(f"Error calculating PCS score for {symbol}: {e}")
            return None

    def scan_stocks(self, stocks=None, min_score=55):
        """Scan stocks and filter by PCS score"""
        if stocks is None:
            stocks = COMPLETE_NSE_FO_UNIVERSE

        results = []

        logger.info(f"Scanning {len(stocks)} stocks...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._scan_single_stock, symbol, min_score): symbol
                      for symbol in stocks}

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")

        # Sort by PCS score
        results.sort(key=lambda x: x['pcs_score'], reverse=True)
        return results

    def _scan_single_stock(self, symbol, min_score):
        """Scan a single stock"""
        try:
            data = self.get_stock_data(symbol)
            if data is None:
                return None

            pcs_data = self.calculate_pcs_score(data, symbol)
            if pcs_data is None:
                return None

            score = pcs_data['score']
            if score >= min_score:
                return {
                    'symbol': symbol,
                    'pcs_score': score,
                    'price': pcs_data['price'],
                    'rsi': pcs_data['rsi'],
                    'macd': pcs_data['macd'],
                    'volatility': pcs_data['volatility']
                }
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")

        return None

class TelegramReporter:
    """Send results to Telegram"""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, message):
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars")
            return False

        try:
            response = requests.post(
                self.api_url,
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def format_results(self, results, use_synthetic=False):
        """Format scan results for Telegram"""
        if not results:
            message = "🔍 <b>NSE F&O PCS Scan Results</b>\n\n"
            message += "No stocks found meeting the filter criteria (PCS Score ≥ 55)\n"
            message += f"<i>Scan completed at {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M UTC')}</i>"
            return message

        message = "🔍 <b>NSE F&O PCS Scan Results</b>\n"
        message += f"<i>Found {len(results)} stocks meeting filter criteria (PCS Score ≥ 55)</i>\n"
        if use_synthetic:
            message += "<i>⚠️  Data: Demo/Synthetic (Network issue)</i>\n"
        message += f"<i>Scan time: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M UTC')}</i>\n\n"

        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for i, result in enumerate(results[:10], 1):  # Limit to top 10 due to message size
            symbol = result['symbol']
            score = result['pcs_score']
            price = result['price']
            rsi = result['rsi']
            volatility = result['volatility']

            # Confidence level based on score
            if score >= 75:
                confidence = "🟢 HIGH"
            elif score >= 60:
                confidence = "🟡 MEDIUM"
            else:
                confidence = "🔴 LOW"

            message += f"\n<b>{i}. {symbol}</b>\n"
            message += f"PCS Score: {score:.0f}/100 {confidence}\n"
            message += f"Price: ₹{price:.2f}\n"
            message += f"RSI: {rsi:.1f}\n"
            message += f"Volatility: {volatility:.1f}%\n"

        if len(results) > 10:
            message += f"\n... and {len(results) - 10} more stocks\n"

        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return message

def main():
    """Main entry point"""
    logger.info("Starting NSE F&O PCS Scanner with Telegram integration...")

    # Initialize scanner
    scanner = PCSScanner()

    # Run scan with default min score of 55
    logger.info("Running scan with min PCS score: 55")
    results = scanner.scan_stocks(min_score=55)

    logger.info(f"Found {len(results)} stocks meeting criteria")

    # Format and send to Telegram
    reporter = TelegramReporter(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    message = reporter.format_results(results, use_synthetic=scanner.use_synthetic)

    # Log results
    logger.info("\n" + "="*50)
    logger.info(message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<br>', '\n'))
    logger.info("="*50)

    # Send to Telegram if credentials are available
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info("Sending results to Telegram...")
        if reporter.send_message(message):
            logger.info("✅ Message sent to Telegram successfully!")
        else:
            logger.error("❌ Failed to send message to Telegram")
    else:
        logger.warning("⚠️  Telegram credentials not configured. Results logged locally only.")
        logger.info("\nTo send results to Telegram, set environment variables:")
        logger.info("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        logger.info("  export TELEGRAM_CHAT_ID='your_chat_id'")

    return results

if __name__ == "__main__":
    main()
