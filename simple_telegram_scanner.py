#!/usr/bin/env python3
"""
Simple Telegram Stock Scanner - Lightweight NSE F&O Analysis
Runs without heavy dependencies, sends qualifying stocks to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import time
import warnings

import yfinance as yf
import pandas as pd
import numpy as np
import requests

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/nsepcs_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# NSE F&O Stocks - Top 40 liquid stocks
NSE_FO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "LT.NS", "ITC.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS", "ASIANPAINT.NS", "BHARTIARTL.NS",
    "SUNPHARMA.NS", "TATAMOTORS.NS", "ADANIENT.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "INDUSINDBK.NS", "TECHM.NS", "TITAN.NS", "NESTLEIND.NS", "ULTRACEMCO.NS",
    "POWERGRID.NS", "NTPC.NS", "ONGC.NS", "COALINDIA.NS", "JSWSTEEL.NS",
    "TATASTEEL.NS", "HINDALCO.NS", "BPCL.NS", "GAIL.NS", "HEROMOTOCO.NS",
    "DIVISLAB.NS", "APOLLOHOSP.NS", "EICHERMOT.NS", "INDUSTOWER.NS", "DRREDDY.NS",
]


def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD"""
    ema_fast = data['Close'].ewm(span=fast).mean()
    ema_slow = data['Close'].ewm(span=slow).mean()

    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal

    return macd, macd_signal, macd_hist


def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands"""
    sma = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()

    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)

    return upper_band, sma, lower_band


def calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ADX (simplified)"""
    high = data['High']
    low = data['Low']
    close = data['Close']

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(window=period).mean()

    plus_dm = high.diff().where(high.diff() > low.diff(), 0).where(high.diff() > 0, 0)
    minus_dm = low.diff().where(low.diff() > high.diff(), 0).where(low.diff() > 0, 0)

    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

    di_diff = (plus_di - minus_di).abs()
    di_sum = plus_di + minus_di

    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(window=period).mean()

    return adx


def detect_breakout(data: pd.DataFrame, lookback: int = 20) -> bool:
    """Detect if price has recently broken out"""
    if len(data) < lookback:
        return False

    recent = data.iloc[-5:]  # Last 5 days
    lookback_high = data['High'].iloc[-lookback:-5].max()

    # Price broke above 20-day high
    return (recent['High'] > lookback_high).any()


def detect_consolidation(data: pd.DataFrame, lookback: int = 20) -> bool:
    """Detect consolidation pattern"""
    if len(data) < lookback:
        return False

    recent = data['Close'].iloc[-lookback:]
    high = recent.max()
    low = recent.min()
    range_pct = ((high - low) / low) * 100

    # Consolidation is when price range is less than 5%
    return range_pct < 5


def calculate_volume_ratio(data: pd.DataFrame) -> float:
    """Calculate volume ratio vs average"""
    if len(data) < 20:
        return 1.0

    avg_volume = data['Volume'].iloc[-20:-1].mean()
    current_volume = data['Volume'].iloc[-1]

    if avg_volume == 0:
        return 1.0

    return current_volume / avg_volume


class Config:
    """Configuration"""
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    MIN_RSI = float(os.getenv('MIN_RSI', '35'))
    MAX_RSI = float(os.getenv('MAX_RSI', '75'))
    MIN_ADX = float(os.getenv('MIN_ADX', '20'))
    MIN_VOLUME_RATIO = float(os.getenv('MIN_VOLUME_RATIO', '1.2'))
    MIN_RESULTS = int(os.getenv('MIN_RESULTS', '3'))


class TelegramNotifier:
    """Handle Telegram notifications"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            return False

        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                },
                timeout=10
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram error: {str(e)}")
            return False


class SimpleScanner:
    """Simple stock scanner"""

    def __init__(self, config: Config):
        self.config = config
        self.results = []

    def fetch_stock_data(self, symbol: str, period: str = "6mo") -> Optional[pd.DataFrame]:
        """Fetch stock data from Yahoo Finance"""
        try:
            data = yf.download(symbol, period=period, progress=False)

            if data.empty or len(data) < 30:
                return None

            # Calculate indicators
            data['RSI'] = calculate_rsi(data)
            data['ADX'] = calculate_adx(data)
            data['MACD'], data['MACD_SIGNAL'], data['MACD_HIST'] = calculate_macd(data)
            data['BB_HIGH'], data['BB_MID'], data['BB_LOW'] = calculate_bollinger_bands(data)

            return data
        except Exception as e:
            logger.debug(f"Error fetching {symbol}: {str(e)}")
            return None

    def score_stock(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Score a stock based on technical indicators"""
        current = data.iloc[-1]

        # Get technical indicators
        rsi = current['RSI']
        adx = current['ADX']
        volume_ratio = calculate_volume_ratio(data)

        # Check filters
        if pd.isna(rsi) or pd.isna(adx):
            return None

        # Filter by ADX
        if adx < self.config.MIN_ADX:
            return None

        # Filter by RSI
        if not (self.config.MIN_RSI <= rsi <= self.config.MAX_RSI):
            return None

        # Filter by volume
        if volume_ratio < self.config.MIN_VOLUME_RATIO:
            return None

        # Calculate score (0-100)
        score = 0

        # Trend strength (30%)
        if current['ADX'] > 25:
            score += 30
        elif current['ADX'] > 20:
            score += 20

        # Momentum (30%)
        if 45 <= rsi <= 65:
            score += 30
        elif 35 <= rsi <= 75:
            score += 20

        # MACD (20%)
        if current['MACD'] > current['MACD_SIGNAL']:
            score += 20

        # Breakout pattern (20%)
        if detect_breakout(data):
            score += 20
        elif not detect_consolidation(data):
            score += 10

        return {
            'symbol': symbol,
            'price': float(current['Close']),
            'rsi': float(rsi),
            'adx': float(adx),
            'volume_ratio': float(volume_ratio),
            'score': score,
            'macd_signal': 'BULLISH' if current['MACD'] > current['MACD_SIGNAL'] else 'BEARISH',
            'breakout': detect_breakout(data),
        }

    def scan(self, stocks: List[str]) -> List[Dict]:
        """Scan stocks and return results"""
        self.results = []
        logger.info(f"Scanning {len(stocks)} stocks...")

        for i, symbol in enumerate(stocks):
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(stocks)}")

            data = self.fetch_stock_data(symbol)
            if data is None:
                continue

            score_result = self.score_stock(symbol, data)
            if score_result is None:
                continue

            self.results.append(score_result)

        # Sort by score
        self.results.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"Found {len(self.results)} qualifying stocks")
        return self.results


def format_results(results: List[Dict]) -> Tuple[str, str]:
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found meeting criteria", ""

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    summary = f"""
📊 <b>NSE Stock Scan Results</b>
🕐 {timestamp}

🎯 Stocks Found: <b>{len(results)}</b>
📈 Avg Score: <b>{np.mean([r['score'] for r in results]):.1f}</b>

Filter Criteria:
• RSI: {Config.MIN_RSI}-{Config.MAX_RSI}
• ADX Min: {Config.MIN_ADX}
• Volume: ≥{Config.MIN_VOLUME_RATIO}x
"""

    details = ""
    for i, r in enumerate(results[:10], 1):
        breakout_emoji = "🔥" if r['breakout'] else "📊"
        macd_emoji = "🟢" if r['macd_signal'] == 'BULLISH' else "🔴"

        detail = f"""
<b>#{i} {r['symbol'].replace('.NS', '')}</b>
💰 ₹{r['price']:.2f}
📈 RSI: {r['rsi']:.1f} | ADX: {r['adx']:.1f}
📊 Vol: {r['volume_ratio']:.1f}x | Score: {r['score']:.0f}
{macd_emoji} MACD: {r['macd_signal']} {breakout_emoji}
━━━━━━━━━━━━━━━━
"""
        details += detail

    return summary, details


def main():
    """Main execution"""
    logger.info("="*60)
    logger.info("Simple NSE Stock Scanner")
    logger.info("="*60)

    # Check Telegram config
    config = Config()
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    if notifier.enabled:
        logger.info("✅ Telegram notifications enabled")
    else:
        logger.info("⚠️  Telegram not configured - local results only")

    # Run scanner
    scanner = SimpleScanner(config)
    results = scanner.scan(NSE_FO_STOCKS)

    # Check minimum results
    if len(results) < config.MIN_RESULTS:
        logger.warning(f"Only {len(results)} stocks found, below minimum of {config.MIN_RESULTS}")
        msg = f"Scan completed but only {len(results)} stocks qualified (minimum: {config.MIN_RESULTS})"
        if notifier.enabled:
            notifier.send_message(msg)
        return

    # Format and send results
    summary, details = format_results(results)

    if notifier.enabled:
        logger.info("Sending results to Telegram...")
        notifier.send_message(summary)
        time.sleep(0.5)
        if details:
            notifier.send_message(details)
    else:
        print(summary)
        print(details)

    # Save to file
    results_file = f"/tmp/scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results saved to {results_file}")
    logger.info("="*60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)
