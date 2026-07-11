#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Telegram Integration
Runs the scanner and sends filtered stocks to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from typing import List, Dict, Optional

warnings.filterwarnings('ignore')


# Technical Indicator Calculations (without ta dependency)
def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_adx(high, low, close, period=14):
    """Calculate ADX (simplified)"""
    # Plus DM and Minus DM
    plus_dm = high.diff()
    plus_dm = plus_dm.where(plus_dm > 0, 0)

    minus_dm = -low.diff()
    minus_dm = minus_dm.where(minus_dm > 0, 0)

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Smoothed values
    plus_di = 100 * (plus_dm.rolling(window=period).sum() / tr.rolling(window=period).sum())
    minus_di = 100 * (minus_dm.rolling(window=period).sum() / tr.rolling(window=period).sum())

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    return adx

# Configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default filter settings
DEFAULT_FILTERS = {
    'rsi_min': 30,
    'rsi_max': 75,
    'adx_min': 20,
    'ma_support': True,
    'ma_type': 'EMA',
    'ma_tolerance': 3,
    'min_volume_ratio': 1.2,
    'volume_breakout_ratio': 2.0,
    'lookback_days': 20,
    'pattern_strength_min': 65,
    'enable_daily_analysis': True,
    'enable_weekly_validation': False,
    'pattern_filters': {
        'current_day_breakout': True,
        'cup_and_handle': True,
        'flat_base': True,
        'bump_and_run': True,
        'rectangle_bottom': True,
        'rectangle_top': True,
        'head_shoulders_bottom': True,
        'double_bottom': True,
        'three_rising_valleys': True,
        'rounding_bottom': True,
        'rounding_top_upside': True,
        'inverted_scallop': True,
    }
}

# NSE F&O Stocks - Tier 1 (most liquid)
TIER1_STOCKS = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC']

# Add .NS suffix
TIER1_STOCKS = [s + '.NS' if not s.endswith('.NS') else s for s in TIER1_STOCKS]

def send_telegram_message(message: str, parse_mode: str = 'HTML') -> bool:
    """Send a message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

class SimplePCSScanner:
    """Simplified PCS Scanner for non-Streamlit usage"""

    def __init__(self):
        self.data_cache = {}

    def get_stock_data(self, symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """Fetch stock data with technical indicators"""
        try:
            # Try fetching data
            data = yf.download(symbol, period=period, progress=False)

            if data.empty or len(data) < 20:
                return None

            # Calculate technical indicators
            data['RSI'] = calculate_rsi(data['Close'], window=14)

            # Simple MACD (without ta library)
            ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = ema_12 - ema_26
            data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

            # Bollinger Bands
            sma20 = data['Close'].rolling(window=20).mean()
            std20 = data['Close'].rolling(window=20).std()
            data['BB_High'] = sma20 + (std20 * 2)
            data['BB_Mid'] = sma20
            data['BB_Low'] = sma20 - (std20 * 2)

            # ADX
            data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])

            # Moving Averages
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()

            # Volume analysis
            data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()

            return data.dropna()

        except Exception as e:
            print(f"⚠️ Error fetching {symbol}: {e}")
            return None

    def check_volume_criteria(self, data: pd.DataFrame, min_ratio: float = 1.2) -> tuple:
        """Check if volume meets criteria"""
        try:
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume_SMA'].iloc[-1]

            if avg_volume == 0:
                return False, 0, {}

            volume_ratio = current_volume / avg_volume

            volume_ok = volume_ratio >= min_ratio
            volume_details = {
                'current': current_volume,
                'average': avg_volume,
                'ratio': volume_ratio
            }

            return volume_ok, volume_ratio, volume_details
        except:
            return False, 0, {}

    def detect_current_day_breakout(self, data: pd.DataFrame, symbol: str, lookback_days: int = 20,
                                   min_volume_ratio: float = 2.0) -> Optional[Dict]:
        """Detect current day breakout pattern"""
        try:
            if len(data) < lookback_days + 1:
                return None

            current_price = data['Close'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]

            # Get lookback range (exclude current day)
            lookback_data = data.iloc[-(lookback_days+1):-1]

            recent_high = lookback_data['High'].max()
            recent_low = lookback_data['Low'].min()
            avg_volume = lookback_data['Volume'].mean()

            # Check if current day broke above resistance
            breakout_detected = current_price > recent_high

            if not breakout_detected:
                return None

            # Check volume confirmation
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            if volume_ratio < min_volume_ratio:
                return None

            # Calculate breakout strength
            breakout_percentage = ((current_price - recent_high) / recent_high) * 100
            strength = min(100, 70 + (volume_ratio - min_volume_ratio) * 5 + breakout_percentage * 2)

            return {
                'type': 'Current Day Breakout',
                'strength': strength,
                'confidence': 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW',
                'breakout_price': recent_high,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'distance_pct': breakout_percentage
            }

        except:
            return None

    def analyze_stock(self, symbol: str, filters: Dict) -> Optional[Dict]:
        """Analyze a single stock"""
        try:
            # Get data
            data = self.get_stock_data(symbol)
            if data is None or len(data) == 0:
                return None

            # Check volume
            volume_ok, volume_ratio, _ = self.check_volume_criteria(data, filters['min_volume_ratio'])
            if not volume_ok:
                return None

            # Get current metrics
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_price = data['Close'].iloc[-1]

            # Check technical filters
            if not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
                return None

            if current_adx < filters['adx_min']:
                return None

            # Check MA support
            if filters['ma_support']:
                sma_20 = data['SMA_20'].iloc[-1]
                ema_20 = data['EMA_20'].iloc[-1]

                if filters['ma_type'] == 'SMA':
                    support_level = sma_20 * (1 - filters['ma_tolerance']/100)
                    if current_price < support_level:
                        return None
                else:
                    support_level = ema_20 * (1 - filters['ma_tolerance']/100)
                    if current_price < support_level:
                        return None

            # Detect patterns
            patterns = []

            if filters['pattern_filters'].get('current_day_breakout', True):
                breakout = self.detect_current_day_breakout(
                    data, symbol,
                    lookback_days=filters.get('lookback_days', 20),
                    min_volume_ratio=filters.get('volume_breakout_ratio', 2.0)
                )
                if breakout and breakout['strength'] >= filters['pattern_strength_min']:
                    patterns.append(breakout)

            if not patterns:
                return None

            # Return stock result
            return {
                'symbol': symbol,
                'symbol_clean': symbol.replace('.NS', ''),
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': patterns,
                'max_strength': max(p['strength'] for p in patterns),
                'data': data
            }

        except Exception as e:
            return None

    def scan(self, stocks: List[str], filters: Dict) -> List[Dict]:
        """Scan multiple stocks"""
        results = []

        for i, symbol in enumerate(stocks):
            print(f"🔍 Scanning {i+1}/{len(stocks)}: {symbol.replace('.NS', '')}")

            result = self.analyze_stock(symbol, filters)
            if result:
                results.append(result)

        # Sort by strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)

        return results

def format_telegram_message(results: List[Dict]) -> str:
    """Format scan results for Telegram"""
    if not results:
        return "❌ No stocks found matching the filter criteria"

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    message = f"""
🎯 <b>NSE F&O PCS Scanner Results</b>
📅 {timestamp}

<b>📊 Summary</b>
✅ Stocks Found: <b>{len(results)}</b>
🔥 Average Strength: <b>{np.mean([r['max_strength'] for r in results]):.1f}%</b>

<b>📈 Top Stocks</b>
"""

    for i, stock in enumerate(results[:10], 1):
        symbol = stock['symbol_clean']
        price = stock['price']
        strength = stock['max_strength']
        rsi = stock['rsi']
        adx = stock['adx']
        vol_ratio = stock['volume_ratio']

        confidence = 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'

        message += f"""
{i}. <b>{symbol}</b>
   💰 Price: ₹{price:.2f}
   ⚡ Strength: {strength:.0f}% ({confidence})
   📊 RSI: {rsi:.1f} | ADX: {adx:.1f}
   📈 Volume: {vol_ratio:.2f}x
"""

    message += f"""

⏱️ Scan completed at {timestamp}
"""

    return message

def main():
    """Main function"""
    print("🚀 Starting NSE F&O PCS Telegram Scanner...")

    # Check credentials
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ WARNING: Telegram not configured!")
        print("Set environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nRunning in demo mode (results will print to console only)")
        has_telegram = False
    else:
        has_telegram = True
        print(f"✅ Telegram configured - Chat ID: {TELEGRAM_CHAT_ID}")

    # Create scanner
    scanner = SimplePCSScanner()

    # Scan Tier 1 stocks by default
    print(f"\n🔍 Scanning {len(TIER1_STOCKS)} stocks...")
    results = scanner.scan(TIER1_STOCKS, DEFAULT_FILTERS)

    # Format message
    message = format_telegram_message(results)

    # Print to console
    print("\n" + "="*60)
    print(message)
    print("="*60)

    # Send to Telegram if configured
    if has_telegram:
        print("\n📤 Sending to Telegram...")
        if send_telegram_message(message):
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")

    return results

if __name__ == '__main__':
    main()
