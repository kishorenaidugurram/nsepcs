#!/usr/bin/env python3
"""
Simplified Standalone Stock Scanner with Telegram Integration
Runs NSE F&O stock screening without Streamlit dependencies
"""

import os
import sys
import json
import warnings
from datetime import datetime, timedelta
import pytz
import numpy as np
import pandas as pd
import yfinance as yf
import requests

warnings.filterwarnings('ignore')

# Default NSE F&O stocks
NSE_FO_STOCKS = [
    'NIFTY', 'BANKNIFTY', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS',
    'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS',
    'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS',
    'TATASTEEL.NS', 'HINDALCO.NS'
]


def calculate_rsi(data, period=14):
    """Calculate RSI indicator"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_adx(data, period=14):
    """Calculate ADX indicator"""
    high_low = data['High'] - data['Low']
    high_close = abs(data['High'] - data['Close'].shift())
    low_close = abs(data['Low'] - data['Close'].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_dm = data['High'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm = -data['Low'].diff()
    minus_dm[minus_dm < 0] = 0

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    di_diff = abs(plus_di - minus_di)
    di_sum = plus_di + minus_di
    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(period).mean()

    return adx


def get_stock_data(symbol, period="3mo"):
    """Fetch and process stock data"""
    try:
        data = yf.download(symbol, period=period, progress=False, threads=False)

        if data is None or len(data) < 20:
            return None

        # Calculate indicators
        data['RSI'] = calculate_rsi(data, 14)
        data['ADX'] = calculate_adx(data, 14)
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        data['EMA_20'] = data['Close'].ewm(span=20).mean()

        # Bollinger Bands
        bb_sma = data['Close'].rolling(20).mean()
        bb_std = data['Close'].rolling(20).std()
        data['BB_upper'] = bb_sma + (bb_std * 2)
        data['BB_lower'] = bb_sma - (bb_std * 2)

        return data
    except Exception as e:
        return None


class SimpleTelegramReporter:
    """Send scan results to Telegram"""

    def __init__(self):
        """Initialize Telegram reporter"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.ist = pytz.timezone('Asia/Kolkata')

    def validate_credentials(self):
        """Validate that Telegram credentials are set"""
        if not self.bot_token or not self.chat_id:
            return False
        return True

    def send_message(self, message, parse_mode="HTML"):
        """Send a message to Telegram"""
        if not self.api_url:
            return False

        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(f"{self.api_url}/sendMessage", data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False

    def send_scan_results(self, results, config):
        """Format and send scan results to Telegram"""
        if not self.api_url:
            print("⚠️ Telegram not configured - results not sent")
            return

        if not results:
            message = "⚠️ <b>NSE F&O PCS Scan Complete</b>\n\n"
            message += "No stocks matched the filter criteria.\n"
            message += f"Scan time: {datetime.now(self.ist).strftime('%H:%M IST')}"
            self.send_message(message)
            return

        # Send header
        current_time = datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')
        header = f"<b>📊 NSE F&O PCS Scan Results</b>\n"
        header += f"<i>{current_time}</i>\n\n"
        header += f"<b>✅ Stocks Found: {len(results)}</b>\n"
        header += f"<b>RSI Range:</b> {config['rsi_min']}-{config['rsi_max']}\n"
        header += f"<b>ADX Min:</b> {config['adx_min']}\n"
        header += "─" * 40 + "\n\n"

        self.send_message(header)

        # Send results in batches
        batch_message = ""
        for i, result in enumerate(results[:30], 1):
            symbol = result.get('Symbol', 'N/A')
            price = result.get('Price', 0)
            rsi = result.get('RSI', 0)
            adx = result.get('ADX', 0)

            stock_info = f"<b>{i}. {symbol}</b>\n"
            stock_info += f"   ₹{price:.2f} | RSI: {rsi:.1f} | ADX: {adx:.1f}\n"

            if len(batch_message) + len(stock_info) > 3500:
                self.send_message(batch_message)
                batch_message = stock_info
            else:
                batch_message += stock_info

        if batch_message:
            self.send_message(batch_message)

        # Send footer
        footer = f"\n{'─' * 40}\n"
        footer += f"✅ Scan completed at {datetime.now(self.ist).strftime('%H:%M IST')}\n"
        footer += f"<b>Total matches: {len(results)}</b>"
        self.send_message(footer)


def run_simple_scan(stocks_to_scan=None, rsi_min=30, rsi_max=75, adx_min=20):
    """Run a simple stock scan"""

    if stocks_to_scan is None:
        stocks_to_scan = NSE_FO_STOCKS[:20]  # Limit for faster testing

    results = []
    ist = pytz.timezone('Asia/Kolkata')

    print(f"🚀 Starting NSE F&O PCS Scan...")
    print(f"📊 Scanning {len(stocks_to_scan)} stocks")
    print(f"⚙️ Filter: RSI {rsi_min}-{rsi_max}, ADX Min {adx_min}")
    print()

    for idx, symbol in enumerate(stocks_to_scan, 1):
        try:
            if idx % 5 == 0:
                print(f"  Progress: {idx}/{len(stocks_to_scan)}")

            # Get data
            data = get_stock_data(symbol)
            if data is None or len(data) < 20:
                continue

            # Get latest values
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Apply filters
            if pd.isna(current_rsi) or pd.isna(current_adx):
                continue

            if not (rsi_min <= current_rsi <= rsi_max):
                continue

            if current_adx < adx_min:
                continue

            # Stock matches criteria
            result = {
                'Symbol': symbol.replace('.NS', ''),
                'Price': float(current_price),
                'RSI': float(current_rsi),
                'ADX': float(current_adx),
                'Timestamp': datetime.now(ist).isoformat()
            }

            results.append(result)
            print(f"  ✓ {result['Symbol']}: RSI={result['RSI']:.1f}, ADX={result['ADX']:.1f}")

        except Exception as e:
            pass

    return results


def main():
    """Main entry point"""
    try:
        # Run scan
        print("\n" + "="*50)
        results = run_simple_scan()
        print("\n✅ Scan complete!\n")

        # Initialize Telegram
        telegram = SimpleTelegramReporter()

        config = {
            'rsi_min': 30,
            'rsi_max': 75,
            'adx_min': 20
        }

        if telegram.validate_credentials():
            print("📱 Sending results to Telegram...")
            telegram.send_scan_results(results, config)
            print("✅ Results sent to Telegram!\n")
        else:
            print("⚠️ Telegram credentials not configured")
            print("Set environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'\n")

        # Save results locally
        output_file = '/tmp/nsepcs_scan_results.json'
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                'config': config,
                'results': results
            }, f, indent=2)

        print(f"💾 Results saved to {output_file}")
        print(f"📊 Found {len(results)} matching stocks\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
