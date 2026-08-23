#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Standalone Analysis & Telegram Integration
Works without ta library by implementing core indicators manually
"""

import os
import json
import logging
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
IST = pytz.timezone('Asia/Kolkata')

# NSE F&O Stocks List
NSE_FO_STOCKS = [
    "NIFTY.NS", "BANKNIFTY.NS", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS",
    "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS",
    "ASIANPAINT.NS", "BHARTIARTL.NS", "SUNPHARMA.NS", "TATAMOTORS.NS",
    "ADANIENT.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "INDUSINDBK.NS",
    "TECHM.NS", "TITAN.NS", "NESTLEIND.NS", "ULTRACEMCO.NS", "POWERGRID.NS",
    "NTPC.NS", "ONGC.NS", "COALINDIA.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "HINDALCO.NS"
]


class SimpleIndicatorCalculator:
    """Calculate technical indicators without ta library"""

    @staticmethod
    def calculate_rsi(data, period=14):
        """Calculate RSI"""
        close = data['Close'].values
        delta = np.diff(close)
        seed = delta[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(close)
        rsi[:period] = 100 - 100 / (1 + rs)

        for i in range(period, len(close)):
            delta_up = delta[i] if delta[i] >= 0 else 0
            delta_down = -delta[i] if delta[i] < 0 else 0
            up = (up * (period - 1) + delta_up) / period
            down = (down * (period - 1) + delta_down) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100 - 100 / (1 + rs)

        return pd.Series(rsi, index=data.index)

    @staticmethod
    def calculate_sma(data, period=20):
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()

    @staticmethod
    def calculate_ema(data, period=20):
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_bollinger_bands(data, period=20, num_std=2):
        """Calculate Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, sma, lower

    @staticmethod
    def calculate_macd(data, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    @staticmethod
    def calculate_adx(high, low, close, period=14):
        """Calculate ADX (Simplified)"""
        plus_dm = np.zeros(len(high))
        minus_dm = np.zeros(len(high))
        tr = np.zeros(len(high))

        for i in range(1, len(high)):
            plus_dm[i] = high.iloc[i] - high.iloc[i-1] if high.iloc[i] > high.iloc[i-1] else 0
            minus_dm[i] = low.iloc[i-1] - low.iloc[i] if low.iloc[i-1] > low.iloc[i] else 0
            tr[i] = max(high.iloc[i] - low.iloc[i],
                       abs(high.iloc[i] - close.iloc[i-1]),
                       abs(low.iloc[i] - close.iloc[i-1]))

        plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / pd.Series(tr).rolling(period).mean()
        minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / pd.Series(tr).rolling(period).mean()

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()

        return adx


def get_stock_data(symbol, period="3mo"):
    """Fetch stock data and calculate indicators"""
    try:
        logger.info(f"  Fetching data for {symbol}...")
        data = yf.download(symbol, period=period, progress=False)

        if data is None or len(data) < 20:
            return None

        # Calculate indicators
        data['RSI'] = SimpleIndicatorCalculator.calculate_rsi(data['Close'])
        data['SMA_20'] = SimpleIndicatorCalculator.calculate_sma(data['Close'], 20)
        data['SMA_50'] = SimpleIndicatorCalculator.calculate_sma(data['Close'], 50)
        data['EMA_20'] = SimpleIndicatorCalculator.calculate_ema(data['Close'], 20)

        bb_upper, bb_mid, bb_lower = SimpleIndicatorCalculator.calculate_bollinger_bands(data['Close'])
        data['BB_upper'] = bb_upper
        data['BB_middle'] = bb_mid
        data['BB_lower'] = bb_lower

        macd, signal, hist = SimpleIndicatorCalculator.calculate_macd(data['Close'])
        data['MACD'] = macd
        data['MACD_signal'] = signal
        data['MACD_hist'] = hist

        data['ADX'] = SimpleIndicatorCalculator.calculate_adx(data['High'], data['Low'], data['Close'])

        return data

    except Exception as e:
        logger.warning(f"  Error fetching {symbol}: {e}")
        return None


def analyze_stock(symbol, data):
    """Analyze stock for PCS opportunities"""
    try:
        if data is None or len(data) < 20:
            return None

        # Get latest values
        latest = data.iloc[-1]
        current_price = latest['Close']
        current_rsi = latest['RSI']
        current_adx = latest['ADX']
        current_close = latest['Close']
        sma_20 = latest['SMA_20']
        ema_20 = latest['EMA_20']

        # Filter criteria
        rsi_ok = 30 <= current_rsi <= 75
        adx_ok = current_adx >= 20
        support_ok = current_close >= sma_20 * 0.97  # 3% below SMA20

        if not (rsi_ok and adx_ok and support_ok):
            return None

        # Check for bullish patterns (simplified)
        macd_signal_ok = data['MACD'].iloc[-1] > data['MACD_signal'].iloc[-1]
        volume_increase = data['Volume'].iloc[-1] > data['Volume'].iloc[-20:].mean() * 1.2

        if not (macd_signal_ok or volume_increase):
            return None

        # Calculate confidence score
        score = 0
        if current_rsi > 45 and current_rsi < 65:
            score += 20
        if current_adx > 25:
            score += 20
        if current_close > sma_20:
            score += 15
        if macd_signal_ok:
            score += 20
        if volume_increase:
            score += 25

        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': current_rsi,
            'adx': current_adx,
            'score': min(score, 100),
            'data': data
        }

    except Exception as e:
        logger.warning(f"  Error analyzing {symbol}: {e}")
        return None


def send_telegram_notification(message, html=False):
    """Send notification to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not set. Skipping notification.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML" if html else "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Telegram notification sent")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram: {e}")
        return False


def format_results_message(results):
    """Format results for Telegram message"""
    if not results:
        return "🔍 NSE F&O PCS Scan\n\n❌ No stocks found meeting filter criteria"

    results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)[:10]

    message = []
    message.append("🎯 <b>NSE F&O PCS Scan Results</b>")
    message.append(f"📅 {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}")
    message.append("")
    message.append(f"✅ Found <b>{len(results)}</b> stocks with bullish patterns")
    message.append("")

    if results_sorted:
        message.append("<b>🏆 Top Opportunities:</b>")
        for i, result in enumerate(results_sorted, 1):
            symbol = result['symbol'].replace('.NS', '')
            message.append(
                f"{i}. <b>{symbol}</b>\n"
                f"   💰 ₹{result['price']:.2f} | "
                f"RSI: {result['rsi']:.0f} | "
                f"ADX: {result['adx']:.0f} | "
                f"Score: {result['score']:.0f}%"
            )

    message.append("")
    message.append("<i>For detailed analysis, run: streamlit run streamlit_app.py</i>")

    return "\n".join(message)


def run_scan(max_stocks=None):
    """Run PCS screening scan"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Screener - Standalone Analysis")
    logger.info("=" * 60)

    stocks_to_scan = NSE_FO_STOCKS[:max_stocks] if max_stocks else NSE_FO_STOCKS
    logger.info(f"Scanning {len(stocks_to_scan)} stocks...")

    results = []

    for i, symbol in enumerate(stocks_to_scan, 1):
        logger.info(f"[{i}/{len(stocks_to_scan)}] Analyzing {symbol}...")

        data = get_stock_data(symbol, period="3mo")
        if data is None:
            continue

        result = analyze_stock(symbol, data)
        if result:
            results.append(result)
            logger.info(f"  ✅ {symbol} passed filters (Score: {result['score']:.0f}%)")

    logger.info("=" * 60)
    logger.info(f"Scan complete: Found {len(results)} qualifying stocks")
    logger.info("=" * 60)

    return results


def main():
    """Main execution"""
    # Check Telegram config
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info("✅ Telegram configured")
    else:
        logger.warning("⚠️  Telegram not configured")
        logger.info("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")

    # Run scan
    results = run_scan(max_stocks=30)

    # Format and send message
    message = format_results_message(results)
    print("\n" + "=" * 60)
    print(message.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""))
    print("=" * 60 + "\n")

    # Send via Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_notification(message, html=True)

    # Save results
    results_data = {
        'timestamp': datetime.now(IST).isoformat(),
        'total_found': len(results),
        'top_10': [
            {
                'symbol': r['symbol'],
                'price': round(r['price'], 2),
                'rsi': round(r['rsi'], 1),
                'adx': round(r['adx'], 1),
                'score': round(r['score'], 1)
            }
            for r in sorted(results, key=lambda x: x['score'], reverse=True)[:10]
        ]
    }

    with open('/tmp/scan_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    logger.info("Results saved to /tmp/scan_results.json")

    return len(results) > 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
