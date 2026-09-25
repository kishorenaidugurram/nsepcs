#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Simple Version (without ta package)
Scans stocks for PCS opportunities and sends results to Telegram
"""

import os
import json
import sys
from datetime import datetime
import pytz
import requests

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"Error: Required package not found: {e}")
    sys.exit(1)

def send_telegram_message(bot_token, chat_id, message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def calculate_rsi(data, period=14):
    """Calculate RSI manually"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(data, period=14):
    """Simplified ADX calculation"""
    high_diff = data['High'].diff()
    low_diff = -data['Low'].diff()

    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

    tr = np.maximum(
        data['High'] - data['Low'],
        np.maximum(
            abs(data['High'] - data['Close'].shift()),
            abs(data['Low'] - data['Close'].shift())
        )
    )

    atr = tr.rolling(period).mean()
    di_plus = 100 * (plus_dm.rolling(period).mean() / atr)
    di_minus = 100 * (minus_dm.rolling(period).mean() / atr)

    di_diff = abs(di_plus - di_minus)
    di_sum = di_plus + di_minus

    adx = 100 * (di_diff / di_sum).rolling(period).mean()
    return adx.fillna(0)

def get_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval="1d")

        if len(data) < 30:
            return None

        # Add technical indicators
        data['RSI'] = calculate_rsi(data)
        data['ADX'] = calculate_adx(data)
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()

        return data
    except Exception as e:
        return None

def check_volume_criteria(data, min_ratio=1.2):
    """Check if volume meets criteria"""
    if len(data) < 21:
        return False, 0

    current_volume = data['Volume'].iloc[-1]
    avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()

    volume_ratio = current_volume / avg_20_volume

    return volume_ratio >= min_ratio, volume_ratio

def detect_breakout(data, lookback_days=20):
    """Detect if stock broke out from recent resistance"""
    if len(data) < lookback_days + 2:
        return False, 0

    # Get current day
    current = data.iloc[-1]

    # Get lookback period
    lookback = data.iloc[-(lookback_days + 1):-1]

    # Find resistance
    resistance = lookback['High'].max()
    support = lookback['Low'].min()

    # Check if broke above resistance
    price_breakout = current['Close'] > resistance * 1.005
    high_breakout = current['High'] > resistance * 1.01

    if not (price_breakout or high_breakout):
        return False, 0

    # Check volume
    avg_volume = lookback['Volume'].mean()
    volume_ratio = current['Volume'] / avg_volume

    if volume_ratio < 1.5:
        return False, 0

    # Calculate strength score
    strength = 0
    breakout_pct = ((current['Close'] - resistance) / resistance) * 100

    if breakout_pct >= 3:
        strength = 85
    elif breakout_pct >= 2:
        strength = 75
    elif breakout_pct >= 1:
        strength = 65

    if volume_ratio >= 3:
        strength += 10
    elif volume_ratio >= 2:
        strength += 5

    return True, min(strength, 100)

def scan_stocks(symbols, config):
    """Scan stocks and return qualifying results"""
    print(f"\nScanning {len(symbols)} stocks...")
    results = []

    for idx, symbol in enumerate(symbols, 1):
        if idx % 30 == 0:
            print(f"  Progress: {idx}/{len(symbols)}")

        try:
            # Get data
            data = get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Get latest indicators
            rsi = data['RSI'].iloc[-1]
            adx = data['ADX'].iloc[-1]

            # Check filters
            if not (config['rsi_min'] <= rsi <= config['rsi_max']):
                continue

            if adx < config['adx_min']:
                continue

            # Check volume
            volume_ok, volume_ratio = check_volume_criteria(
                data, min_ratio=config['min_volume_ratio']
            )

            if not volume_ok:
                continue

            # Check for breakout
            breakout, strength = detect_breakout(
                data, lookback_days=config['lookback_days']
            )

            if breakout and strength >= config['pattern_strength_min']:
                current_price = data['Close'].iloc[-1]

                results.append({
                    'symbol': symbol.replace('.NS', ''),
                    'score': strength,
                    'rsi': rsi,
                    'adx': adx,
                    'price': current_price,
                    'pattern': 'Current Day Breakout',
                    'volume_ratio': volume_ratio,
                    'sma_20': data['SMA_20'].iloc[-1],
                    'sma_50': data['SMA_50'].iloc[-1]
                })

        except Exception as e:
            continue

    return results

def main():
    """Main function"""
    print("=" * 70)
    print("NSE F&O PCS Scanner (Simplified Version)")
    print("=" * 70)

    # Get Telegram credentials
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

    telegram_available = bool(bot_token and chat_id)

    if telegram_available:
        print("\n[+] Telegram credentials found")
    else:
        print("\n[i] Telegram not configured - results will be displayed and saved to file")

    # Configuration
    config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'min_volume_ratio': 1.2,
        'lookback_days': 20,
        'pattern_strength_min': 65
    }

    print("\n[*] Filter Configuration:")
    print(f"    RSI Range: {config['rsi_min']}-{config['rsi_max']}")
    print(f"    ADX Min: {config['adx_min']}")
    print(f"    Min Volume Ratio: {config['min_volume_ratio']}x")
    print(f"    Lookback Days: {config['lookback_days']}")
    print(f"    Pattern Strength Min: {config['pattern_strength_min']}%")

    # Stock list - NSE F&O stocks
    stocks = [
        '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
        'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
        'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
        'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
        'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
        'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
        'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
        'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
        'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
        'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS'
    ]

    # Scan
    results = scan_stocks(stocks, config)
    results.sort(key=lambda x: x['score'], reverse=True)

    # Prepare message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    timestamp_str = current_time.strftime('%Y-%m-%d %H:%M IST')

    message = f"[PCS SCANNER RESULTS]\n"
    message += f"Time: {timestamp_str}\n\n"
    message += f"Found: {len(results)} qualifying stocks\n"
    message += f"(Pattern Strength >= {config['pattern_strength_min']}%)\n\n"

    if results:
        message += "TOP 10 PICKS:\n"
        message += "=" * 60 + "\n"

        for i, r in enumerate(results[:10], 1):
            message += f"{i:2d}. {r['symbol']:12s} Score: {r['score']:3.0f}  RSI: {r['rsi']:6.1f}  ADX: {r['adx']:6.1f}\n"

        # Save results
        json_file = '/tmp/pcs_scanner_results.json'
        with open(json_file, 'w') as f:
            json.dump({
                'timestamp': timestamp_str,
                'total_results': len(results),
                'top_10_stocks': [
                    {
                        'rank': i + 1,
                        'symbol': r['symbol'],
                        'score': round(r['score'], 2),
                        'rsi': round(r['rsi'], 2),
                        'adx': round(r['adx'], 2),
                        'price': round(r['price'], 2)
                    }
                    for i, r in enumerate(results[:10])
                ]
            }, f, indent=2)

        print(f"\n[+] Results saved to {json_file}")

        # Send to Telegram
        if telegram_available:
            print("[*] Sending to Telegram...")
            telegram_msg = f"<b>PCS Scanner Results</b>\n"
            telegram_msg += f"<i>{timestamp_str}</i>\n\n"
            telegram_msg += f"<b>{len(results)} stocks found</b>\n\n"
            telegram_msg += "<b>Top 10 Picks:</b>\n"

            for i, r in enumerate(results[:10], 1):
                telegram_msg += f"{i}. <b>{r['symbol']}</b> ({r['score']:.0f})\n"

            if send_telegram_message(bot_token, chat_id, telegram_msg):
                print("[+] Sent to Telegram")
            else:
                print("[-] Failed to send to Telegram")
    else:
        message += "No qualifying stocks found.\n"
        if telegram_available:
            if send_telegram_message(bot_token, chat_id, message):
                print("[+] Notification sent to Telegram")

    # Print results
    print("\n" + "=" * 70)
    print(message)
    print("=" * 70)

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
