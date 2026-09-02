#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner - Simplified version
Sends qualified stocks to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
import requests
import pandas as pd
import numpy as np
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Stock universe - Nifty 50 + liquid F&O stocks
LIQUID_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TECHM.NS', 'ULTRACEMCO.NS', 'SUNPHARMA.NS',
    'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS', 'JSWSTEEL.NS',
    'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'EICHERMOT.NS',
    'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS', 'BPCL.NS',
    'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS',
    'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS', 'HDFCLIFE.NS'
]


class TelegramNotifier:
    """Handle sending messages to Telegram"""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message):
        """Send a message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("✅ Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"❌ Failed to send Telegram message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {str(e)}")
            return False


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    try:
        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
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
    except:
        return np.full(len(prices), 50)


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    try:
        ema_fast = pd.Series(prices).ewm(span=fast).mean().values
        ema_slow = pd.Series(prices).ewm(span=slow).mean().values
        macd = ema_fast - ema_slow
        signal_line = pd.Series(macd).ewm(span=signal).mean().values
        histogram = macd - signal_line
        return macd, signal_line, histogram
    except:
        return np.zeros(len(prices)), np.zeros(len(prices)), np.zeros(len(prices))


def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Add technical indicators
        data['RSI'] = calculate_rsi(data['Close'].values)
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()

        macd, signal, histogram = calculate_macd(data['Close'].values)
        data['MACD'] = macd
        data['MACD_signal'] = signal
        data['MACD_hist'] = histogram

        return data
    except Exception as e:
        logger.warning(f"Error fetching {symbol}: {str(e)}")
        return None


def analyze_stock(symbol):
    """Analyze a single stock for trading opportunities"""
    try:
        data = fetch_stock_data(symbol)
        if data is None or len(data) < 20:
            return None

        # Get latest values
        latest = data.iloc[-1]
        current_price = latest['Close']
        current_rsi = latest['RSI']
        current_macd = latest['MACD']
        current_signal = latest['MACD_signal']
        sma_20 = latest['SMA_20']
        sma_50 = latest['SMA_50']

        # Filter criteria
        filters_passed = {
            'rsi': 30 < current_rsi < 80,
            'price_above_sma20': current_price > sma_20 if pd.notna(sma_20) else False,
            'bullish_macd': current_macd > current_signal,
            'volume_today': latest['Volume'] > data['Volume'].mean(),
            'recent_uptrend': latest['Close'] > data['Close'].iloc[-10]
        }

        # Check if passes majority of filters
        passed_filters = sum(filters_passed.values())
        if passed_filters < 3:
            return None

        # Calculate score
        score = passed_filters * 20

        return {
            'symbol': symbol,
            'clean_symbol': symbol.replace('.NS', ''),
            'price': current_price,
            'rsi': current_rsi,
            'macd': current_macd,
            'signal': current_signal,
            'sma_20': sma_20,
            'volume': latest['Volume'],
            'avg_volume': data['Volume'].mean(),
            'score': score,
            'filters_passed': filters_passed,
            'current_price': current_price
        }

    except Exception as e:
        logger.debug(f"Error analyzing {symbol}: {str(e)}")
        return None


def load_config():
    """Load configuration from environment"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables")
        return None

    return {
        'bot_token': bot_token,
        'chat_id': chat_id
    }


def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "🔍 No stocks found matching filter criteria today."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""🎯 *NSE Stock Scan Results*
━━━━━━━━━━━━━━━━━━━━
📅 {current_time}
📊 Stocks Found: {len(results)}
━━━━━━━━━━━━━━━━━━━━

"""

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    for idx, result in enumerate(results[:15], 1):
        score_stars = '⭐' * min(5, int(result['score'] / 20))
        filters = result['filters_passed']
        filter_status = f"✓{sum(filters.values())}/5"

        message += f"""`{idx}. {result['clean_symbol']}`
💰 ₹{result['price']:.0f} | RSI: {result['rsi']:.0f} | {filter_status}
{score_stars} Score: {result['score']:.0f}%

"""

    message += """━━━━━━━━━━━━━━━━━━━━
*Filters:* RSI (30-80), Price > SMA20, Bullish MACD, High Volume
*⚠️ Educational purposes only* - Always do your own research!
"""

    return message


def main():
    logger.info("=" * 60)
    logger.info("🚀 NSE Stock Scanner - Telegram Edition")
    logger.info("=" * 60)

    # Load configuration
    config = load_config()
    if not config:
        logger.error("❌ Configuration failed. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    # Initialize Telegram
    telegram = TelegramNotifier(config['bot_token'], config['chat_id'])

    # Send start message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%H:%M:%S IST')
    telegram.send_message(f"🚀 Starting NSE stock scan at {current_time}...")

    # Scan stocks
    logger.info(f"📊 Scanning {len(LIQUID_STOCKS)} stocks...")
    results = []

    for i, symbol in enumerate(LIQUID_STOCKS, 1):
        clean_symbol = symbol.replace('.NS', '')
        logger.info(f"[{i}/{len(LIQUID_STOCKS)}] Analyzing {clean_symbol}...")

        result = analyze_stock(symbol)
        if result:
            results.append(result)
            logger.info(f"✅ {clean_symbol} - Score: {result['score']:.0f}%")

    logger.info(f"✅ Scan complete! Found {len(results)} qualified stocks")

    # Send results
    telegram_message = format_telegram_message(results)
    telegram.send_message(telegram_message)

    # Send summary
    top_candidate = results[0]['clean_symbol'] if len(results) > 0 else 'None'
    top_score = results[0]['score'] if len(results) > 0 else 0

    telegram.send_message(f"""✅ *Scan Complete!*

*Summary:*
• Analyzed: {len(LIQUID_STOCKS)} stocks
• Qualified: {len(results)} stocks
• Time: {ist.localize(datetime.now()).strftime('%Y-%m-%d %H:%M IST')}

💡 Top Candidate: {top_candidate} (Score: {top_score:.0f}%)""")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        sys.exit(1)
