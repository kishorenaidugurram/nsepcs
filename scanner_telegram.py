#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Notifier
Runs the PCS scanner and sends filtered results to Telegram
"""

import os
import sys
import asyncio
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
import warnings

warnings.filterwarnings('ignore')

# Try to import telegram bot, but make it optional
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️  python-telegram-bot not installed. Install with: pip install python-telegram-bot")

# ====== CONFIGURATION ======
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Filter configuration
MIN_PCS_SCORE = float(os.getenv('MIN_PCS_SCORE', '50'))
MIN_VOLUME_RATIO = float(os.getenv('MIN_VOLUME_RATIO', '0.7'))
MAX_STOCKS = int(os.getenv('MAX_STOCKS', '40'))

# Stock list (subset of NSE F&O universe)
DEMO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS',
    'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS',
    'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS'
]


def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period + 1:
        return np.full(len(prices), 50)

    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed>=0].sum()/period
    down = -seed[seed<0].sum()/period
    rs = up/down if down != 0 else 0
    rsi = np.full(len(prices), 50.0)
    rsi[:period+1] = 100. - 100./(1.+rs)

    for i in range(period+1, len(prices)):
        delta = deltas[i-1]
        upval = delta if delta > 0 else 0
        downval = -delta if delta < 0 else 0
        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1.+rs)

    return rsi


def calculate_sma(prices, period=20):
    """Calculate SMA"""
    return pd.Series(prices).rolling(window=period).mean().fillna(method='bfill').values


def calculate_macd(prices):
    """Calculate MACD"""
    series = pd.Series(prices)
    ema_12 = series.ewm(span=12).mean()
    ema_26 = series.ewm(span=26).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9).mean()
    hist = macd - signal
    return macd.fillna(method='bfill').values, signal.fillna(method='bfill').values, hist.fillna(method='bfill').values


def calculate_adx_simple(high, low, close):
    """Calculate simplified ADX"""
    try:
        tr = np.maximum(high - low, np.maximum(abs(high - np.roll(close, 1)), abs(low - np.roll(close, 1))))
        atr = pd.Series(tr).rolling(14).mean().fillna(method='bfill').values

        di_up = np.where(high - np.roll(high, 1) > 0, high - np.roll(high, 1), 0)
        di_down = np.where(np.roll(low, 1) - low > 0, np.roll(low, 1) - low, 0)

        di_up = pd.Series(di_up).rolling(14).mean().fillna(method='bfill').values
        di_down = pd.Series(di_down).rolling(14).mean().fillna(method='bfill').values

        di_up_pct = (di_up / (atr + 1e-6)) * 100
        di_down_pct = (di_down / (atr + 1e-6)) * 100

        dx = np.abs(di_up_pct - di_down_pct) / (di_up_pct + di_down_pct + 1e-6) * 100
        adx = pd.Series(dx).rolling(14).mean().fillna(method='bfill').values

        return adx
    except:
        return np.full(len(close), 20)


class TelegramNotifier:
    """Send messages to Telegram"""

    def __init__(self, token, chat_id):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot not available")
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def send_message(self, message: str, parse_mode='HTML') -> bool:
        """Send a message to Telegram chat"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            print(f"Telegram error: {e}")
            return False


class PCSScanner:
    """PCS Scanner for filtering stocks"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch and process stock data"""
        try:
            data = yf.download(symbol, period=period, progress=False, quiet=True)

            if data is None or len(data) < 30:
                return None

            # Calculate technical indicators
            data['RSI'] = calculate_rsi(data['Close'].values)
            data['SMA_20'] = calculate_sma(data['Close'].values, 20)
            data['SMA_50'] = calculate_sma(data['Close'].values, 50)
            macd, macd_sig, macd_hist = calculate_macd(data['Close'].values)
            data['MACD'] = macd
            data['MACD_hist'] = macd_hist
            data['ADX'] = calculate_adx_simple(data['High'].values, data['Low'].values, data['Close'].values)

            return data
        except Exception as e:
            return None

    def calculate_pcs_score(self, data, symbol):
        """Calculate PCS score - More lenient scoring"""
        try:
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_macd_hist = data['MACD_hist'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]

            score = 60  # Higher base score
            details = []

            # RSI Analysis
            if 35 <= current_rsi <= 75:
                score += 10
                details.append(f"RSI: {current_rsi:.0f}")
            elif current_rsi < 35:
                score += 5
                details.append(f"RSI Oversold: {current_rsi:.0f}")

            # Trend
            if current_adx > 20:
                score += 10
                details.append(f"ADX Trend: {current_adx:.0f}")

            # Price vs SMA
            if current_price > sma_20:
                score += 10
                details.append("Above SMA20")
            else:
                score += 5
                details.append("Near SMA20")

            # MACD
            if current_macd_hist > 0:
                score += 10
                details.append("MACD Positive")
            else:
                score += 5
                details.append("MACD Neutral")

            # Volume check
            avg_vol = data['Volume'].tail(20).mean()
            if data['Volume'].iloc[-1] > avg_vol * 0.8:
                score += 5
                details.append("Good Volume")

            return min(score, 100), details

        except Exception as e:
            return 60, ["Standard metrics"]

    def check_volume_criteria(self, data, min_ratio=0.7):
        """Check volume criteria"""
        try:
            recent_vol = data['Volume'].tail(5).mean()
            hist_vol = data['Volume'].tail(50).mean()
            ratio = recent_vol / hist_vol if hist_vol > 0 else 0
            return ratio >= min_ratio, ratio
        except:
            return True, 1.0

    def scan_stocks(self, stocks, min_score=50, min_volume_ratio=0.7):
        """Scan and filter stocks"""
        results = []

        for i, symbol in enumerate(stocks, 1):
            clean = symbol.replace('.NS', '')
            print(f"[{i}/{len(stocks)}] {clean}...", end='\r')

            data = self.get_stock_data(symbol)
            if data is None:
                continue

            vol_ok, vol_ratio = self.check_volume_criteria(data, min_volume_ratio)
            if not vol_ok:
                continue

            score, details = self.calculate_pcs_score(data, symbol)

            if score >= min_score:
                price = data['Close'].iloc[-1]
                rsi = data['RSI'].iloc[-1]

                results.append({
                    'Symbol': clean,
                    'Price': round(price, 2),
                    'PCS Score': int(score),
                    'RSI': round(rsi, 1),
                    'Vol Ratio': round(vol_ratio, 2),
                    'Details': ' | '.join(details)
                })

        print(" " * 60, end='\r')
        if results:
            return pd.DataFrame(results).sort_values('PCS Score', ascending=False)
        return pd.DataFrame()


async def send_to_telegram(results):
    """Send results to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials not set")
        return False

    try:
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

        message = "<b>📊 NSE F&O PCS Scanner</b>\n"
        message += f"<i>{datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"
        message += f"<b>Found {len(results)} stocks</b>\n\n"

        message += "<b>Results:</b>\n<code>"
        for idx, row in results.head(10).iterrows():
            message += f"{row['Symbol']:<10} {row['PCS Score']:>3} {row['RSI']:>5.1f}\n"
        message += "</code>"

        return await notifier.send_message(message)
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False


async def main():
    """Main function"""
    print("=" * 60)
    print("🚀 NSE F&O PCS Scanner with Telegram")
    print("=" * 60)
    print(f"Filter: Score ≥ {MIN_PCS_SCORE}, Vol Ratio ≥ {MIN_VOLUME_RATIO}")
    print(f"Scanning {min(len(DEMO_STOCKS), MAX_STOCKS)} stocks...\n")

    scanner = PCSScanner()
    results = scanner.scan_stocks(
        DEMO_STOCKS[:MAX_STOCKS],
        min_score=MIN_PCS_SCORE,
        min_volume_ratio=MIN_VOLUME_RATIO
    )

    if results.empty:
        print("\n❌ No stocks found")
        print("Try lowering MIN_PCS_SCORE or MIN_VOLUME_RATIO")
        return

    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(results[['Symbol', 'Price', 'PCS Score', 'RSI']].to_string(index=False))

    # Save to CSV
    csv_file = f"pcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results.to_csv(csv_file, index=False)
    print(f"\n💾 Saved to {csv_file}")

    # Send to Telegram if configured
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        if await send_to_telegram(results):
            print("✅ Sent to Telegram")
        else:
            print("❌ Failed to send to Telegram")
    else:
        print("\n📱 To enable Telegram:")
        print("  export TELEGRAM_BOT_TOKEN='your_token'")
        print("  export TELEGRAM_CHAT_ID='your_id'")


if __name__ == "__main__":
    asyncio.run(main())
