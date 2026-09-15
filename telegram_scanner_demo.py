#!/usr/bin/env python3
"""
Telegram Stock Scanner - DEMO VERSION
This version uses synthetic data to demonstrate the scanning and Telegram integration
Useful for testing and development when network access is unavailable
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import time

import pandas as pd
import numpy as np
import requests

warnings_import_ok = True
try:
    import warnings
    warnings.filterwarnings('ignore')
except:
    warnings_import_ok = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/nsepcs_scanner_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Sample NSE F&O stocks
SAMPLE_STOCKS = {
    "RELIANCE": {"price": 3200, "volatility": 0.02},
    "TCS": {"price": 3900, "volatility": 0.015},
    "HDFCBANK": {"price": 1850, "volatility": 0.018},
    "INFY": {"price": 2100, "volatility": 0.016},
    "ICICIBANK": {"price": 950, "volatility": 0.022},
    "SBIN": {"price": 550, "volatility": 0.025},
    "LT": {"price": 2450, "volatility": 0.017},
    "ITC": {"price": 470, "volatility": 0.019},
    "KOTAKBANK": {"price": 480, "volatility": 0.020},
    "AXISBANK": {"price": 1125, "volatility": 0.021},
    "HCLTECH": {"price": 1540, "volatility": 0.018},
    "WIPRO": {"price": 520, "volatility": 0.024},
    "MARUTI": {"price": 10200, "volatility": 0.019},
    "ASIANPAINT": {"price": 2850, "volatility": 0.016},
    "BHARTIARTL": {"price": 1480, "volatility": 0.023},
}


def generate_synthetic_ohlcv(symbol: str, days: int = 180) -> pd.DataFrame:
    """Generate synthetic OHLCV data for demonstration"""
    np.random.seed(hash(symbol) % 2**32)

    base_price = SAMPLE_STOCKS[symbol]["price"]
    volatility = SAMPLE_STOCKS[symbol]["volatility"]

    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    data_dict = {'Date': dates}

    # Generate price movements
    returns = np.random.normal(0, volatility, days)
    prices = base_price * np.exp(np.cumsum(returns))

    data_dict['Close'] = prices
    data_dict['High'] = prices * (1 + np.abs(np.random.normal(0, volatility * 0.5, days)))
    data_dict['Low'] = prices * (1 - np.abs(np.random.normal(0, volatility * 0.5, days)))
    data_dict['Open'] = np.roll(prices, 1)
    data_dict['Open'][0] = prices[0]
    data_dict['Volume'] = np.random.uniform(1e6, 10e6, days)

    df = pd.DataFrame(data_dict)
    df.set_index('Date', inplace=True)

    # Calculate indicators
    df['RSI'] = calculate_rsi(df)
    df['ADX'] = calculate_adx(df)
    df['MACD'], df['MACD_SIGNAL'], _ = calculate_macd(df)

    return df


def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(data: pd.DataFrame) -> tuple:
    """Calculate MACD"""
    ema12 = data['Close'].ewm(span=12).mean()
    ema26 = data['Close'].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    hist = macd - signal
    return macd, signal, hist


def calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate simplified ADX"""
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

    return dx.rolling(window=period).mean()


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
    """Telegram notification handler"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram"""
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


class DemoScanner:
    """Demo stock scanner using synthetic data"""

    def __init__(self, config: Config):
        self.config = config
        self.results = []

    def score_stock(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Score stock on technical indicators"""
        current = data.iloc[-1]

        rsi = current['RSI']
        adx = current['ADX']
        volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].iloc[-20:].mean()
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # Filter checks
        if pd.isna(rsi) or pd.isna(adx):
            return None

        if adx < self.config.MIN_ADX:
            return None

        if not (self.config.MIN_RSI <= rsi <= self.config.MAX_RSI):
            return None

        if volume_ratio < self.config.MIN_VOLUME_RATIO:
            return None

        # Calculate score
        score = 0

        # Trend (40%)
        if adx > 30:
            score += 40
        elif adx > 25:
            score += 30
        elif adx > 20:
            score += 20

        # Momentum (40%)
        if 45 <= rsi <= 65:
            score += 40
        elif 40 <= rsi <= 70:
            score += 30
        else:
            score += 20

        # MACD (20%)
        if current['MACD'] > current['MACD_SIGNAL']:
            score += 20
        else:
            score += 10

        return {
            'symbol': symbol,
            'price': float(current['Close']),
            'rsi': float(rsi),
            'adx': float(adx),
            'volume_ratio': float(volume_ratio),
            'score': score,
            'macd': 'BULLISH' if current['MACD'] > current['MACD_SIGNAL'] else 'BEARISH',
        }

    def scan(self, stocks: List[str]) -> List[Dict]:
        """Scan stocks"""
        self.results = []
        logger.info(f"Scanning {len(stocks)} stocks (DEMO MODE with synthetic data)...")

        for i, symbol in enumerate(stocks):
            if (i + 1) % 5 == 0:
                logger.info(f"Progress: {i + 1}/{len(stocks)}")

            # Generate synthetic data
            data = generate_synthetic_ohlcv(symbol)

            # Score stock
            score_result = self.score_stock(symbol, data)
            if score_result is None:
                continue

            self.results.append(score_result)

        # Sort by score
        self.results.sort(key=lambda x: x['score'], reverse=True)
        logger.info(f"Found {len(self.results)} qualifying stocks")

        return self.results


def format_message(results: List[Dict]) -> str:
    """Format results for output"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    message = f"""
📊 <b>NSE Stock Scanner - DEMO MODE</b>
🕐 {timestamp}

<b>Results Summary:</b>
🎯 Total Stocks: <b>{len(results)}</b>
📈 Avg Score: <b>{np.mean([r['score'] for r in results]):.1f}/100</b>

<b>Filters Applied:</b>
• RSI Range: {Config.MIN_RSI}-{Config.MAX_RSI}
• ADX Minimum: {Config.MIN_ADX}
• Volume Ratio: ≥{Config.MIN_VOLUME_RATIO}x

<b>━━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>TOP RECOMMENDATIONS:</b>

"""

    for i, r in enumerate(results[:10], 1):
        macd_emoji = "🟢" if r['macd'] == 'BULLISH' else "🔴"

        message += f"""
<b>#{i} {r['symbol']}</b>
💰 Price: ₹{r['price']:.2f}
📊 RSI: {r['rsi']:.1f} | ADX: {r['adx']:.1f}
📈 Volume: {r['volume_ratio']:.1f}x
🎯 Score: <b>{r['score']:.0f}/100</b>
{macd_emoji} Signal: {r['macd']}
━━━━━━━━━━━━━━━━━━━━

"""

    message += """
<b>NOTE:</b> This is a DEMO using synthetic data for demonstration.
In production, connect to your Telegram bot:
• Set TELEGRAM_BOT_TOKEN env var
• Set TELEGRAM_CHAT_ID env var
"""

    return message


def main():
    """Main execution"""
    logger.info("="*70)
    logger.info("NSE Stock Scanner - DEMO Edition (Synthetic Data)")
    logger.info("="*70)

    config = Config()
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    if notifier.enabled:
        logger.info("✅ Telegram configured - will send results to Telegram")
    else:
        logger.info("⚠️  Telegram not configured - displaying results locally")
        logger.info("   To enable: export TELEGRAM_BOT_TOKEN=... && export TELEGRAM_CHAT_ID=...")

    # Run scanner
    scanner = DemoScanner(config)
    stocks_to_scan = list(SAMPLE_STOCKS.keys())
    results = scanner.scan(stocks_to_scan)

    # Check minimum threshold
    if len(results) < config.MIN_RESULTS:
        logger.warning(f"Only {len(results)} stocks found, minimum: {config.MIN_RESULTS}")
        msg = f"⚠️ Scan complete: Only {len(results)}/{len(stocks_to_scan)} stocks qualified"
        if notifier.enabled:
            notifier.send_message(msg)
        return

    # Format and send
    message = format_message(results)

    if notifier.enabled:
        logger.info("Sending results to Telegram...")
        # Split large messages
        parts = message.split("━━━━━━━━━━━━━━━━━━━━━━━━━")

        for part in parts:
            if part.strip():
                notifier.send_message(part)
                time.sleep(0.3)

        logger.info("✅ Results sent to Telegram!")
    else:
        print("\n" + message)

    # Save results
    results_file = f"/tmp/scan_results_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results saved to {results_file}")
    logger.info("="*70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)
