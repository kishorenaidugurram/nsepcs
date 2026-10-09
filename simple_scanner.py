#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Scanner - Standalone Edition
No Streamlit dependency, focused on core scanning and Telegram reporting
"""

import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Tuple

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# NSE F&O Universe
NSE_FO_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
    'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI', 'ASIANPAINT', 'BHARTIARTL',
    'SUNPHARMA', 'TATAMOTORS', 'ADANIENT', 'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK',
    'TECHM', 'TITAN', 'NESTLEIND', 'ULTRACEMCO', 'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA',
    'JSWSTEEL', 'TATASTEEL', 'HINDALCO', 'BPCL', 'EICHERMOT', 'MOTHERSON', 'BAJAJFINSV',
    'PEL', 'SBICARD', 'HDFC', 'HEROMOTOCORP', 'BRITANNIA', 'LTIM', 'CIPLA', 'DRREDDY',
    'ZYDUSLIFE', 'SHRIRAMFIN'
]

class SimpleNSEScanner:
    """Simple NSE stock scanner without heavy dependencies"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_stock_data(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
        """Fetch stock data using yfinance"""
        try:
            import yfinance as yf

            # Add NSE extension if needed
            if not symbol.endswith('.NS'):
                symbol = f"{symbol}.NS"

            # Download data
            data = yf.download(symbol, period=period, progress=False)

            if data is None or len(data) < 20:
                return None

            # Calculate RSI
            data['RSI'] = self.calculate_rsi(data['Close'], period=14)

            # Calculate Moving Averages
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()

            # Calculate Bollinger Bands
            data['BB_middle'] = data['Close'].rolling(window=20).mean()
            data['BB_std'] = data['Close'].rolling(window=20).std()
            data['BB_upper'] = data['BB_middle'] + (data['BB_std'] * 2)
            data['BB_lower'] = data['BB_middle'] - (data['BB_std'] * 2)

            # Calculate MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['MACD_signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['MACD_hist'] = data['MACD'] - data['MACD_signal']

            # Calculate ADX (simplified)
            data['ADX'] = self.calculate_adx(data, period=14)

            return data

        except Exception as e:
            print(f"  Error fetching {symbol}: {str(e)}")
            return None

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX indicator (simplified)"""
        try:
            high_low = data['High'] - data['Low']
            high_close = abs(data['High'] - data['Close'].shift())
            low_close = abs(data['Low'] - data['Close'].shift())

            tr = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = tr.rolling(period).mean()

            # Simplified ADX calculation
            di = (high_low / tr * 100).rolling(period).mean()
            adx = di.rolling(period).mean()

            return adx.fillna(20)  # Default value of 20
        except:
            return pd.Series([20] * len(data), index=data.index)

    def analyze_stock(self, symbol: str, min_rsi: int = 30, max_rsi: int = 75,
                     min_adx: float = 20.0) -> Dict:
        """Analyze a single stock for pattern opportunities"""

        clean_symbol = symbol.replace('.NS', '')
        data = self.get_stock_data(symbol, period="3mo")

        if data is None:
            return None

        # Get latest values
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        volume_ratio = data['Volume'].iloc[-1] / data['Volume'].iloc[-20:-1].mean()

        # Check basic criteria
        if current_rsi < min_rsi or current_rsi > max_rsi:
            return None

        if current_adx < min_adx:
            return None

        if volume_ratio < 1.2:
            return None

        # Calculate trend strength
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]

        trend_strength = 0
        if current_price > sma_20 > sma_50:
            trend_strength = 85
        elif current_price > sma_20:
            trend_strength = 70
        elif current_price > sma_50:
            trend_strength = 60
        else:
            return None  # Not a good setup

        # Check MACD
        macd_hist = data['MACD_hist'].iloc[-1]
        if macd_hist > 0:
            trend_strength += 10
        elif macd_hist > -0.5:
            trend_strength += 5

        return {
            'symbol': clean_symbol,
            'price': float(current_price),
            'rsi': float(current_rsi),
            'adx': float(current_adx),
            'volume_ratio': float(volume_ratio),
            'trend_strength': min(100, trend_strength),
            'sma_20': float(sma_20),
            'sma_50': float(sma_50),
            'macd': float(data['MACD'].iloc[-1]),
            'macd_signal': float(data['MACD_signal'].iloc[-1]),
            'bb_upper': float(data['BB_upper'].iloc[-1]),
            'bb_lower': float(data['BB_lower'].iloc[-1]),
        }

    def scan_universe(self, stocks: List[str], max_stocks: int = 50) -> List[Dict]:
        """Scan a universe of stocks"""

        print(f"📊 Scanning {min(max_stocks, len(stocks))} stocks...")
        results = []

        for i, stock in enumerate(stocks[:max_stocks]):
            try:
                result = self.analyze_stock(stock)
                if result:
                    results.append(result)
                    print(f"  ✓ {stock:15} - Strength: {result['trend_strength']:.0f}%")
                else:
                    print(f"  ✗ {stock:15}")
            except Exception as e:
                print(f"  ✗ {stock:15} - Error: {str(e)[:30]}")

        # Sort by trend strength
        results.sort(key=lambda x: x['trend_strength'], reverse=True)

        return results

def send_to_telegram(message: str) -> bool:
    """Send message to Telegram"""

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️  Telegram not configured. Showing results instead:")
        print("─" * 60)
        print(message)
        print("─" * 60)
        print("\n📌 To enable Telegram notifications, set:")
        print("   TELEGRAM_BOT_TOKEN=your_bot_token")
        print("   TELEGRAM_CHAT_ID=your_chat_id")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send to Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False

def format_results(results: List[Dict]) -> str:
    """Format scan results for Telegram"""

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    if not results:
        message = "🚫 <b>NSE F&O Pattern Scanner</b>\n\n"
        message += "No stocks met the filter criteria today.\n\n"
        message += f"<i>Scanned at {current_time.strftime('%H:%M IST')}</i>"
        return message

    # Header
    message = "🎯 <b>NSE F&O Pattern Scanner Results</b>\n"
    message += f"📅 {current_time.strftime('%Y-%m-%d %H:%M IST')}\n\n"

    # Summary
    message += "<b>📊 Summary:</b>\n"
    message += f"✅ Stocks Found: <b>{len(results)}</b>\n"
    avg_strength = np.mean([r['trend_strength'] for r in results])
    message += f"💪 Avg Strength: <b>{avg_strength:.1f}%</b>\n\n"

    # Results
    message += "<b>🏆 Top Opportunities:</b>\n"
    message += "═" * 45 + "\n"

    for i, result in enumerate(results[:10], 1):
        conf_emoji = "🟢" if result['trend_strength'] >= 85 else "🟡" if result['trend_strength'] >= 70 else "🔴"

        message += f"\n{i}. <b>{result['symbol']}</b> {conf_emoji}\n"
        message += f"   💰 ₹{result['price']:.2f}\n"
        message += f"   📊 Strength: {result['trend_strength']:.0f}%\n"
        message += f"   📈 RSI: {result['rsi']:.1f} | ⚡ ADX: {result['adx']:.1f}\n"
        message += f"   📉 Vol: {result['volume_ratio']:.1f}x\n"

    if len(results) > 10:
        message += f"\n... and <b>{len(results) - 10}</b> more stocks\n"

    message += "\n" + "═" * 45 + "\n"
    message += "<i>⚠️  Not financial advice. Always verify before trading.</i>"

    return message

def main():
    """Main execution"""
    print("=" * 60)
    print("NSE F&O Pattern Scanner - Telegram Edition")
    print("=" * 60)
    print()

    # Check dependencies
    try:
        import yfinance
        print("✓ yfinance available")
    except ImportError:
        print("❌ yfinance not installed. Install with: pip install yfinance")
        print("\nAttempting to install yfinance...")
        os.system("pip install -q yfinance requests")
        try:
            import yfinance
            print("✓ yfinance installed successfully")
        except:
            print("Failed to install. Please install manually.")
            return

    print()

    # Create scanner
    scanner = SimpleNSEScanner()

    # Scan top 50 F&O stocks
    results = scanner.scan_universe(NSE_FO_STOCKS, max_stocks=50)

    print()
    print(f"✅ Scan complete. Found {len(results)} qualifying stocks.\n")

    # Format and send results
    message = format_results(results)
    send_to_telegram(message)

    print()
    print("=" * 60)
    print("✓ Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
