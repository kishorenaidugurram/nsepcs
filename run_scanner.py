#!/usr/bin/env python3
"""
NSE PCS Scanner - Standalone CLI Version
Runs the stock scanner and optionally sends results to Telegram
"""

import sys
import os
import time
import json
from datetime import datetime
import pytz
from typing import List, Dict, Tuple

# Core imports
import numpy as np
import pandas as pd
import yfinance as yf
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try importing talib (installed as alternative to 'ta')
try:
    import talib
    USE_TALIB = True
except ImportError:
    USE_TALIB = False

warnings_filters = [
    'ignore:.*',
]


class StockScanner:
    """Standalone stock scanner"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_stock_data(self, symbol: str, period: str = "3mo") -> pd.DataFrame or None:
        """Fetch stock data from yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval="1d")

            if len(data) < 20:
                return None

            # Calculate basic technical indicators
            self._add_technical_indicators(data)
            return data

        except Exception as e:
            return None

    def _add_technical_indicators(self, data: pd.DataFrame):
        """Add technical indicators to dataframe"""
        try:
            close = data['Close'].values
            high = data['High'].values
            low = data['Low'].values
            volume = data['Volume'].values

            # RSI calculation
            if USE_TALIB:
                data['RSI'] = talib.RSI(close, timeperiod=14)
            else:
                data['RSI'] = self._calculate_rsi(close)

            # SMA
            data['SMA_20'] = pd.Series(close).rolling(20).mean().values
            data['SMA_50'] = pd.Series(close).rolling(50).mean().values
            data['EMA_20'] = pd.Series(close).ewm(span=20).mean().values

            # Bollinger Bands
            bb_mid = pd.Series(close).rolling(20).mean()
            bb_std = pd.Series(close).rolling(20).std()
            data['BB_upper'] = (bb_mid + 2 * bb_std).values
            data['BB_lower'] = (bb_mid - 2 * bb_std).values
            data['BB_middle'] = bb_mid.values

            # MACD
            ema_12 = pd.Series(close).ewm(span=12).mean()
            ema_26 = pd.Series(close).ewm(span=26).mean()
            data['MACD'] = (ema_12 - ema_26).values
            data['MACD_signal'] = pd.Series(data['MACD']).ewm(span=9).mean().values
            data['MACD_hist'] = (data['MACD'] - data['MACD_signal']).values

            # ADX (simplified)
            data['ADX'] = self._calculate_adx(high, low, close)

            # ATR
            data['ATR'] = self._calculate_atr(high, low, close)

            # Stochastic
            data['Stoch_K'] = self._calculate_stochastic(high, low, close)

            # Williams %R
            data['Williams_R'] = self._calculate_williams_r(high, low, close)

        except Exception as e:
            print(f"Error adding indicators: {e}")

    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate RSI"""
        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down else 0
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

            rs = up / down if down else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return rsi

    @staticmethod
    def _calculate_adx(high, low, close, period=14):
        """Calculate ADX (simplified)"""
        h_l = high - low
        h_c = np.abs(high - np.roll(close, 1))
        l_c = np.abs(low - np.roll(close, 1))

        tr = np.maximum(h_l, np.maximum(h_c, l_c))
        atr = pd.Series(tr).rolling(period).mean()

        up = high - np.roll(high, 1)
        down = np.roll(low, 1) - low

        pos_dm = np.where((up > down) & (up > 0), up, 0)
        neg_dm = np.where((down > up) & (down > 0), down, 0)

        pos_di = 100 * pd.Series(pos_dm).rolling(period).mean() / atr
        neg_di = 100 * pd.Series(neg_dm).rolling(period).mean() / atr

        dx = 100 * np.abs(pos_di - neg_di) / (pos_di + neg_di)
        adx = pd.Series(dx).rolling(period).mean()

        return adx.values

    @staticmethod
    def _calculate_atr(high, low, close, period=14):
        """Calculate ATR"""
        h_l = high - low
        h_c = np.abs(high - np.roll(close, 1))
        l_c = np.abs(low - np.roll(close, 1))

        tr = np.maximum(h_l, np.maximum(h_c, l_c))
        atr = pd.Series(tr).rolling(period).mean()

        return atr.values

    @staticmethod
    def _calculate_stochastic(high, low, close, period=14):
        """Calculate Stochastic oscillator"""
        low_min = pd.Series(low).rolling(period).min()
        high_max = pd.Series(high).rolling(period).max()

        k = 100 * (close - low_min.values) / (high_max.values - low_min.values + 1e-10)
        return k

    @staticmethod
    def _calculate_williams_r(high, low, close, period=14):
        """Calculate Williams %R"""
        high_max = pd.Series(high).rolling(period).max()
        low_min = pd.Series(low).rolling(period).min()

        wr = -100 * (high_max.values - close) / (high_max.values - low_min.values + 1e-10)
        return wr

    def check_volume_criteria(self, data: pd.DataFrame, min_ratio: float = 1.0) -> Tuple[bool, float, Dict]:
        """Check if current day volume meets criteria"""
        if len(data) < 21:
            return False, 0, {}

        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()

        volume_ratio = current_volume / avg_20_volume

        details = {
            'current_volume': current_volume,
            'avg_20_volume': avg_20_volume,
            'ratio': volume_ratio
        }

        return volume_ratio >= min_ratio, volume_ratio, details

    def detect_breakout_pattern(self, data: pd.DataFrame, symbol: str) -> Dict or None:
        """Detect if there's a current day breakout pattern"""
        if len(data) < 22:
            return None

        try:
            current_day = data.iloc[-1]
            lookback_data = data.iloc[-22:-1]

            resistance = lookback_data['High'].max()
            current_close = current_day['Close']

            # Check if close is above resistance
            breakout_pct = ((current_close - resistance) / resistance) * 100

            if breakout_pct > 0.5:
                return {
                    'type': 'Current Day Breakout',
                    'strength': min(100, 50 + (breakout_pct * 5)),
                    'resistance': resistance,
                    'current_close': current_close,
                    'breakout_pct': breakout_pct,
                    'confidence': 'HIGH' if breakout_pct > 2 else 'MEDIUM'
                }

        except Exception:
            pass

        return None

    def scan_stock(self, symbol: str, min_volume_ratio: float = 1.2,
                   pattern_strength_min: int = 50) -> Dict or None:
        """Scan a single stock"""
        try:
            # Get data
            data = self.get_stock_data(symbol)
            if data is None:
                return None

            # Check volume
            volume_ok, volume_ratio, _ = self.check_volume_criteria(data, min_volume_ratio)
            if not volume_ok:
                return None

            # Detect patterns
            pattern = self.detect_breakout_pattern(data, symbol)
            if not pattern:
                return None

            if pattern['strength'] < pattern_strength_min:
                return None

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            return {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'pattern': pattern
            }

        except Exception:
            return None

    def scan_stocks(self, stocks: List[str], max_workers: int = 5, max_stocks: int = None) -> List[Dict]:
        """Scan multiple stocks in parallel"""
        if max_stocks:
            stocks = stocks[:max_stocks]

        results = []
        print(f"🚀 Scanning {len(stocks)} stocks...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.scan_stock, symbol): symbol for symbol in stocks}

            for i, future in enumerate(as_completed(futures), 1):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"✅ [{i}/{len(stocks)}] {symbol.replace('.NS', '')} - Pattern found: {result['pattern']['type']}")
                    else:
                        print(f"⏭️  [{i}/{len(stocks)}] {symbol.replace('.NS', '')}")
                except Exception as e:
                    print(f"❌ [{i}/{len(stocks)}] {symbol.replace('.NS', '')}")

        return results


class TelegramReporter:
    """Send results to Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"
        self.ist = pytz.timezone('Asia/Kolkata')

    def send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            url = f"{self.telegram_api}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False

    def send_results(self, results: List[Dict]):
        """Send scan results to Telegram"""
        if not results:
            self.send_message("❌ No stocks found matching the criteria")
            return

        # Sort by pattern strength
        results.sort(key=lambda x: x['pattern']['strength'], reverse=True)

        # Summary message
        summary = f"✅ <b>NSE PCS Scan Results</b>\n"
        summary += f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}\n"
        summary += f"📊 <b>Found {len(results)} stocks</b>\n\n"

        # Top stocks table
        summary += "<b>Top Stocks:</b>\n"
        summary += "<code>"
        for i, r in enumerate(results[:15], 1):
            symbol = r['symbol'].replace('.NS', '')
            summary += f"{i:2d}. {symbol:8s} ₹{r['current_price']:8.2f} "
            summary += f"Vol:{r['volume_ratio']:5.1f}x Str:{r['pattern']['strength']:3.0f}%\n"
        summary += "</code>"

        self.send_message(summary)

        # Send full list
        time.sleep(1)
        stock_list = " | ".join([r['symbol'].replace('.NS', '') for r in results])
        list_msg = f"<b>All {len(results)} Stocks:</b>\n<code>{stock_list}</code>"
        self.send_message(list_msg)


# NSE F&O stocks list (sample)
NSE_FO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TECHM.NS', 'ULTRACEMCO.NS', 'SUNPHARMA.NS',
    'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS', 'JSWSTEEL.NS',
    'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'EICHERMOT.NS',
    'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS', 'BPCL.NS',
    'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS',
    'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS', 'HDFCLIFE.NS',
    'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS', 'ICICIPRULI.NS'
]


def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════╗
    ║   NSE PCS Scanner - CLI Edition        ║
    ║   Telegram Integration Available       ║
    ╚════════════════════════════════════════╝
    """)

    # Check command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python run_scanner.py [OPTIONS]")
        print("\nOptions:")
        print("  --telegram <TOKEN> <CHAT_ID>  Send results to Telegram")
        print("  --stocks N                    Scan first N stocks (default: all)")
        print("  --min-volume RATIO            Minimum volume ratio (default: 1.2)")
        print("  --min-strength N              Minimum pattern strength (default: 50)")
        print("\nExample:")
        print("  python run_scanner.py --stocks 50 --telegram 123456:ABC 987654321")
        sys.exit(0)

    # Parse arguments
    telegram_token = None
    telegram_chat_id = None
    max_stocks = None
    min_volume = 1.2
    min_strength = 50

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--telegram' and i + 2 < len(args):
            telegram_token = args[i + 1]
            telegram_chat_id = args[i + 2]
            i += 3
        elif args[i] == '--stocks' and i + 1 < len(args):
            max_stocks = int(args[i + 1])
            i += 2
        elif args[i] == '--min-volume' and i + 1 < len(args):
            min_volume = float(args[i + 1])
            i += 2
        elif args[i] == '--min-strength' and i + 1 < len(args):
            min_strength = int(args[i + 1])
            i += 2
        else:
            i += 1

    # Run scanner
    scanner = StockScanner()
    results = scanner.scan_stocks(NSE_FO_STOCKS, max_workers=5, max_stocks=max_stocks)

    print(f"\n✅ Scan complete! Found {len(results)} stocks\n")

    # Display results
    if results:
        print("Top Stocks:")
        print("-" * 80)
        for i, r in enumerate(results[:10], 1):
            symbol = r['symbol'].replace('.NS', '')
            print(f"{i:2d}. {symbol:10s} ₹{r['current_price']:8.2f} "
                  f"Vol:{r['volume_ratio']:5.1f}x RSI:{r['rsi']:5.1f} "
                  f"Strength:{r['pattern']['strength']:3.0f}%")
        print("-" * 80)

        # Save to CSV
        csv_path = f"/tmp/scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame([{
            'Symbol': r['symbol'].replace('.NS', ''),
            'Price': r['current_price'],
            'Volume': r['volume_ratio'],
            'RSI': r['rsi'],
            'ADX': r['adx'],
            'Pattern': r['pattern']['type'],
            'Pattern_Strength': r['pattern']['strength']
        } for r in results])
        df.to_csv(csv_path, index=False)
        print(f"\n💾 Results saved to: {csv_path}\n")

        # Send to Telegram if credentials provided
        if telegram_token and telegram_chat_id:
            print("📤 Sending results to Telegram...")
            reporter = TelegramReporter(telegram_token, telegram_chat_id)
            reporter.send_results(results)
            print("✅ Results sent to Telegram!")
    else:
        print("❌ No stocks found matching the criteria")


if __name__ == "__main__":
    main()
