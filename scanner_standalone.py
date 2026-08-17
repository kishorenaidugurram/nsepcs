#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Standalone CLI Version
Simplified scanner without ta module dependency
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import requests
import warnings
warnings.filterwarnings('ignore')

# Default stock lists
NIFTY_50 = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
    'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
    'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS',
    'HDFCLIFE.NS', 'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS'
]

def calculate_rsi(data, period=14):
    """Calculate RSI indicator"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
    atr = calculate_atr(high, low, close, period)

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    di_diff = abs(plus_di - minus_di)
    di_sum = plus_di + minus_di
    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(period).mean()

    return adx.fillna(0)

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval="1d")

        if len(data) < 30:
            return None

        # Calculate technical indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        data['EMA_20'] = data['Close'].ewm(span=20).mean()

        return data.dropna()
    except Exception as e:
        print(f"Error fetching {symbol}: {str(e)}", file=sys.stderr)
        return None

def check_volume(data, min_ratio=1.2):
    """Check if current volume is above average"""
    current_volume = data['Volume'].iloc[-1]
    avg_volume = data['Volume'].tail(20).mean()

    ratio = current_volume / avg_volume if avg_volume > 0 else 0
    return ratio >= min_ratio, ratio

def check_technical_filters(data, rsi_min=30, rsi_max=75, adx_min=20):
    """Check if stock meets technical filters"""
    if len(data) < 30:
        return False

    current_rsi = data['RSI'].iloc[-1]
    current_adx = data['ADX'].iloc[-1]
    current_price = data['Close'].iloc[-1]
    sma_20 = data['SMA_20'].iloc[-1]

    # Check filters
    rsi_ok = rsi_min <= current_rsi <= rsi_max
    adx_ok = current_adx >= adx_min
    support_ok = current_price >= sma_20 * 0.97  # Within 3% of SMA20

    return rsi_ok and adx_ok and support_ok

def detect_bullish_pattern(data):
    """Detect simple bullish patterns"""
    if len(data) < 20:
        return False, 0

    # Get recent data
    recent = data.tail(20)
    current_price = data['Close'].iloc[-1]
    current_rsi = data['RSI'].iloc[-1]

    # Pattern 1: Close at 20-day high
    high_20 = data['High'].tail(20).max()
    is_near_high = current_price >= high_20 * 0.98

    # Pattern 2: Price above moving averages
    sma_20 = data['SMA_20'].iloc[-1]
    sma_50 = data['SMA_50'].iloc[-1]
    is_above_mas = current_price > sma_20 > sma_50

    # Pattern 3: RSI bullish (not overbought but rising)
    is_rsi_bullish = 40 < current_rsi < 70

    # Pattern 4: Volume above average
    current_vol = data['Volume'].iloc[-1]
    avg_vol = data['Volume'].tail(20).mean()
    is_volume_bullish = current_vol > avg_vol * 1.2

    pattern_count = sum([is_near_high, is_above_mas, is_rsi_bullish, is_volume_bullish])
    strength = (pattern_count / 4) * 100

    detected = pattern_count >= 2

    return detected, strength

def send_to_telegram(message: str, bot_token: str = None, chat_id: str = None) -> bool:
    """Send message to Telegram"""
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not found in environment")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {str(e)}", file=sys.stderr)
        return False

def run_scan(stocks=None, min_volume_ratio=1.2):
    """Run the scanner"""
    print("🚀 Starting NSE F&O Scanner...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")

    if stocks is None:
        stocks = NIFTY_50

    print(f"📊 Scanning {len(stocks)} stocks...")

    qualifying = []

    for i, symbol in enumerate(stocks):
        try:
            clean = symbol.replace('.NS', '')
            print(f"  [{i+1}/{len(stocks)}] {clean}...", end='\r')

            # Fetch data
            data = fetch_stock_data(symbol)
            if data is None:
                continue

            # Check volume
            vol_ok, vol_ratio = check_volume(data, min_volume_ratio)
            if not vol_ok:
                continue

            # Check technical filters
            tech_ok = check_technical_filters(data)
            if not tech_ok:
                continue

            # Detect patterns
            pattern_ok, strength = detect_bullish_pattern(data)
            if not pattern_ok:
                continue

            # Get metrics
            price = data['Close'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            adx = data['ADX'].iloc[-1]

            # Determine confidence
            if strength >= 80:
                conf = "HIGH"
            elif strength >= 65:
                conf = "MEDIUM"
            else:
                conf = "LOW"

            qualifying.append({
                'symbol': clean,
                'price': price,
                'rsi': rsi,
                'adx': adx,
                'volume_ratio': vol_ratio,
                'strength': strength,
                'confidence': conf
            })

        except Exception as e:
            continue

    print(f"\n✅ Scan complete! Found {len(qualifying)} stocks\n")
    return qualifying

def format_message(stocks):
    """Format results for Telegram"""
    msg = "<b>📊 NSE F&O Scanner Results</b>\n"
    msg += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</i>\n"
    msg += "━" * 40 + "\n\n"

    if not stocks:
        msg += "<i>No stocks met the criteria today.</i>"
        return msg

    msg += f"<b>Found {len(stocks)} qualifying stocks:</b>\n━" * 40 + "\n"

    for i, stock in enumerate(stocks[:15], 1):
        conf_emoji = "🟢" if stock['confidence'] == 'HIGH' else "🟡"
        msg += f"\n{i}. <b>{stock['symbol']}</b> {conf_emoji}\n"
        msg += f"   💰 ₹{stock['price']:.2f} | "
        msg += f"📊 RSI: {stock['rsi']:.1f} | "
        msg += f"⚡ ADX: {stock['adx']:.1f}\n"
        msg += f"   📈 Strength: {stock['strength']:.0f}% | "
        msg += f"📊 Volume: {stock['volume_ratio']:.1f}x\n"

    if len(stocks) > 15:
        msg += f"\n<i>... and {len(stocks) - 15} more</i>"

    msg += "\n\n" + "━" * 40 + "\n"
    msg += "<i>⚠️ Not financial advice. Do your own research.</i>"

    return msg

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner')
    parser.add_argument('--no-telegram', action='store_true', help='Skip Telegram')
    parser.add_argument('--bot-token', help='Telegram bot token')
    parser.add_argument('--chat-id', help='Telegram chat ID')
    parser.add_argument('--min-volume', type=float, default=1.2, help='Min volume ratio')

    args = parser.parse_args()

    # Run scan
    stocks = run_scan(min_volume_ratio=args.min_volume)

    # Print results
    print("="*50)
    print("RESULTS")
    print("="*50)
    for stock in stocks:
        print(f"{stock['symbol']:12} ₹{stock['price']:8.2f} RSI:{stock['rsi']:5.1f} "
              f"ADX:{stock['adx']:5.1f} Vol:{stock['volume_ratio']:4.1f}x "
              f"Strength:{stock['strength']:5.1f}% {stock['confidence']}")

    # Save results
    results_file = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_scanned': len(NIFTY_50),
            'qualifying_stocks': stocks
        }, f, indent=2)
    print(f"\n💾 Saved to: {results_file}")

    # Send to Telegram
    if not args.no_telegram:
        msg = format_message(stocks)
        if send_to_telegram(msg, args.bot_token, args.chat_id):
            print("✅ Telegram notification sent!")
        else:
            print("⚠️  Telegram not configured")

    return 0 if stocks else 1

if __name__ == '__main__':
    sys.exit(main())
