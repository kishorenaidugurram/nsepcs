#!/usr/bin/env python3
"""
Lightweight NSE F&O PCS Scanner with Telegram Integration
Runs pattern detection and sends results to Telegram
"""

import os
import sys
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# NSE F&O Stock Universe
NSE_FO_STOCKS = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS',
    'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS', 'DIVISLAB.NS',
    'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS',
    'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS',
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS',
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS',
    'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS',
    'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS',
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS',
    'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS', 'INFY.NS',
    'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS',
    'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS',
    'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS',
    'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS',
    'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS',
    'MAXHEALTH.NS', 'MAZDOCK.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS',
    'NBCC.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS',
    'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS',
    'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS',
    'PATANJALI.NS', 'PERSISTENT.NS'
]

def calculate_rsi(data, period=14):
    """Calculate RSI"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(high, low, close, period=14):
    """Calculate ADX"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

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

    return adx

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        data = yf.download(symbol, period=period, progress=False, threads=False)
        if data.empty or len(data) < 20:
            return None

        # Calculate technical indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])
        data['SMA20'] = data['Close'].rolling(20).mean()
        data['EMA20'] = data['Close'].ewm(span=20).mean()

        return data.dropna()
    except Exception as e:
        return None

def detect_current_day_breakout(data, lookback_days=20, min_volume_ratio=2.0):
    """Detect current day breakout"""
    if len(data) < lookback_days:
        return False, 0

    # Historical resistance
    lookback_data = data.iloc[-lookback_days-1:-1]
    resistance_level = lookback_data['High'].max()

    # Current day
    current = data.iloc[-1]
    current_close = current['Close']
    current_volume = current['Volume']
    avg_volume = lookback_data['Volume'].mean()

    # Breakout criteria
    price_breakout = current_close > resistance_level * 1.01
    volume_breakout = current_volume > avg_volume * min_volume_ratio if avg_volume > 0 else False

    if not (price_breakout and volume_breakout):
        return False, 0

    breakout_percentage = ((current_close - resistance_level) / resistance_level) * 100
    strength = min(100, 30 + (breakout_percentage * 5) + ((current_volume / avg_volume - min_volume_ratio) * 15))

    return True, strength

def detect_cup_and_handle(data):
    """Detect cup and handle pattern"""
    if len(data) < 60:
        return False, 0

    recent = data.iloc[-60:]
    cup_data = recent.iloc[-50:-15]
    handle_data = recent.iloc[-15:]

    cup_high = cup_data['High'].max()
    cup_low = cup_data['Low'].min()
    cup_depth = ((cup_high - cup_low) / cup_high) * 100

    handle_high = handle_data['High'].max()
    current_close = data['Close'].iloc[-1]

    valid_cup = 15 <= cup_depth <= 40
    handle_breakout = current_close > handle_high * 1.01

    if not (valid_cup and handle_breakout):
        return False, 0

    strength = min(100, 35 + (valid_cup * 30) + (handle_breakout * 35))
    return True, strength

def detect_flat_base(data):
    """Detect flat base breakout"""
    if len(data) < 40:
        return False, 0

    recent = data.iloc[-40:]
    base_data = recent.iloc[-30:]

    base_range = base_data['High'].max() - base_data['Low'].min()
    base_avg_price = base_data['Close'].mean()
    volatility = (base_range / base_avg_price) * 100

    current_close = data['Close'].iloc[-1]
    breakout = current_close > base_data['High'].max() * 1.01

    valid_base = 2 <= volatility <= 8
    if not (valid_base and breakout):
        return False, 0

    strength = min(100, 40 + (breakout * 30) + ((8 - volatility) * 5))
    return True, strength

def detect_patterns(symbol, data):
    """Detect all patterns"""
    patterns = []

    # Current day breakout
    breakout_detected, breakout_strength = detect_current_day_breakout(data)
    if breakout_detected and breakout_strength >= 65:
        patterns.append({
            'type': 'Current Day Breakout',
            'strength': breakout_strength,
            'confidence': 'HIGH' if breakout_strength >= 85 else 'MEDIUM',
            'success_rate': 72,
            'pcs_suitability': 88
        })

    # Cup and handle
    cup_detected, cup_strength = detect_cup_and_handle(data)
    if cup_detected and cup_strength >= 65:
        patterns.append({
            'type': 'Cup with Handle',
            'strength': cup_strength,
            'confidence': 'HIGH' if cup_strength >= 85 else 'MEDIUM',
            'success_rate': 68,
            'pcs_suitability': 75
        })

    # Flat base
    flat_detected, flat_strength = detect_flat_base(data)
    if flat_detected and flat_strength >= 65:
        patterns.append({
            'type': 'Flat Base Breakout',
            'strength': flat_strength,
            'confidence': 'HIGH' if flat_strength >= 85 else 'MEDIUM',
            'success_rate': 70,
            'pcs_suitability': 82
        })

    return patterns

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    if not bot_token:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not chat_id:
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def run_scan(max_stocks=50):
    """Run the scanner"""
    print("=" * 70)
    print("🚀 NSE F&O PCS Scanner - Automated Scan")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"Stocks to scan: {min(max_stocks, len(NSE_FO_STOCKS))}")
    print("-" * 70)

    results = []
    stocks_to_scan = NSE_FO_STOCKS[:max_stocks]

    for i, symbol in enumerate(stocks_to_scan, 1):
        try:
            clean_symbol = symbol.replace('.NS', '')
            print(f"[{i:3d}/{len(stocks_to_scan)}] {clean_symbol:12s} ", end='', flush=True)

            # Fetch data
            data = fetch_stock_data(symbol)
            if data is None:
                print("❌")
                continue

            # Check basic filters
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            if not (30 <= current_rsi <= 75 and current_adx >= 20):
                print("❌")
                continue

            # Detect patterns
            patterns = detect_patterns(symbol, data)
            if not patterns:
                print("❌")
                continue

            # Get current price
            current_price = data['Close'].iloc[-1]

            result = {
                'symbol': clean_symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'strength': max(p['strength'] for p in patterns),
                'confidence': 'HIGH' if max(p['strength'] for p in patterns) >= 85 else 'MEDIUM'
            }
            results.append(result)
            print(f"✅ ({len(patterns)} pattern(s))")

        except Exception as e:
            print(f"⚠️")

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    print("\n" + "=" * 70)
    print(f"📈 Results: {len(results)} stocks found")
    print("=" * 70)

    return results

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found meeting filter criteria"

    msg = "<b>📊 NSE F&O PCS Scan Results</b>\n"
    msg += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"

    for i, r in enumerate(results[:12], 1):
        confidence_emoji = "🟢" if r['confidence'] == 'HIGH' else "🟡"
        pattern_list = " | ".join([p['type'][:15] for p in r['patterns'][:2]])

        msg += f"{i}. <b>{r['symbol']}</b> {confidence_emoji}\n"
        msg += f"   💰 ₹{r['price']:.2f} | 📊 {r['strength']:.0f}% | RSI: {r['rsi']:.1f} | ADX: {r['adx']:.1f}\n"
        msg += f"   {pattern_list}\n\n"

    if len(results) > 12:
        msg += f"... and <b>{len(results) - 12}</b> more stocks found\n\n"

    msg += f"<b>Total: {len(results)} stocks</b> meeting criteria today"

    return msg

def main():
    """Main function"""
    # Run scan
    results = run_scan(max_stocks=80)

    if not results:
        print("\n❌ No stocks meeting criteria")
        msg = "❌ No stocks met today's PCS scan criteria"
    else:
        # Display top results
        print("\n📊 TOP 10 STOCKS:\n")
        for i, r in enumerate(results[:10], 1):
            print(f"{i:2d}. {r['symbol']:<12s} ₹{r['price']:>8.2f} | Strength: {r['strength']:>5.0f}% | {r['confidence']}")

        msg = format_telegram_message(results)

    # Send to Telegram
    print("\n📱 Sending to Telegram...")
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if send_to_telegram(msg, bot_token, chat_id):
        print("✅ Message sent to Telegram successfully!")
    else:
        if not bot_token or not chat_id:
            print("⚠️  Telegram credentials not found")
            print("   Set: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        else:
            print("⚠️  Failed to send to Telegram (network error)")

    print("\n✅ Scan completed")

if __name__ == "__main__":
    main()
