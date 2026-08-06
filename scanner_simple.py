#!/usr/bin/env python3
"""
Simplified stock scanner - sends results to Telegram via environment variables
"""

import os
import json
import requests
from datetime import datetime
import pytz
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# NSE F&O Stock Universe
STOCKS = [
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
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS',
    'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS',
    'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS',
    'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS',
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
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()

    return adx.fillna(20)

def get_stock_data(symbol, period='3mo'):
    """Fetch stock data"""
    try:
        data = yf.download(symbol, period=period, progress=False)
        if data.empty:
            return None
        return data
    except:
        return None

def analyze_stock(symbol):
    """Analyze a single stock"""
    try:
        # Fetch data
        data = get_stock_data(symbol, period='3mo')
        if data is None or len(data) < 30:
            return None

        # Calculate indicators
        data['RSI'] = calculate_rsi(data['Close'], 14)
        data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'], 14)

        # Get latest values
        latest = data.iloc[-1]
        rsi = latest['RSI']
        adx = latest['ADX']
        price = latest['Close']

        # Volume analysis
        avg_volume = data['Volume'].tail(20).mean()
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        # Check if meets criteria
        if pd.isna(rsi) or pd.isna(adx):
            return None

        # Filter criteria
        if rsi < 30 or rsi > 75:  # RSI filter
            return None
        if adx < 20:  # ADX filter
            return None
        if volume_ratio < 1.2:  # Volume filter
            return None

        # Trend check - simple moving averages
        sma20 = data['Close'].tail(20).mean()
        sma50 = data['Close'].tail(50).mean()

        # Price should be above both MAs for uptrend
        if price < sma20 or price < sma50:
            return None

        return {
            'symbol': symbol.replace('.NS', ''),
            'price': price,
            'rsi': rsi,
            'adx': adx,
            'volume_ratio': volume_ratio,
            'sma20': sma20,
            'sma50': sma50
        }

    except Exception as e:
        return None

def send_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print("\n" + "="*60)
    print("🚀 NSE F&O STOCK SCANNER")
    print("="*60)
    print(f"\n📊 Analyzing {len(STOCKS)} stocks...")

    results = []

    # Analyze stocks
    for i, stock in enumerate(STOCKS, 1):
        if i % 20 == 0:
            print(f"  Progress: {i}/{len(STOCKS)}")

        result = analyze_stock(stock)
        if result:
            results.append(result)
            print(f"✅ {result['symbol']}: RSI={result['rsi']:.0f}, ADX={result['adx']:.0f}, Vol={result['volume_ratio']:.1f}x")

    print(f"\n🎯 Found {len(results)} stocks meeting criteria\n")

    # Sort by ADX (trend strength)
    results.sort(key=lambda x: x['adx'], reverse=True)

    # Format message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"📊 <b>NSE F&O Scanner</b>\n"
    message += f"🕐 {current_time.strftime('%Y-%m-%d %H:%M IST')}\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"🎯 <b>Found {len(results)} stocks</b>\n\n"

    # Top 12 stocks
    for i, stock in enumerate(results[:12], 1):
        message += f"{i}. <b>{stock['symbol']}</b>\n"
        message += f"   💰 ₹{stock['price']:.2f} | "
        message += f"📈 RSI: {stock['rsi']:.0f} | "
        message += f"⚡ ADX: {stock['adx']:.0f}\n"
        message += f"   Volume: {stock['volume_ratio']:.1f}x\n\n"

    if len(results) > 12:
        message += f"... and <b>{len(results) - 12} more stocks</b>\n\n"

    message += f"━━━━━━━━━━━━━━━━━━━━━━━━"

    # Print
    print("📨 Message:")
    print("-" * 60)
    print(message.replace('<b>', '').replace('</b>', '').replace('<br>', '\n'))
    print("-" * 60)

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("\n📤 Sending to Telegram...")
        if send_telegram(message):
            print("✅ Sent successfully!")
        else:
            print("❌ Failed to send")
    else:
        print("\n⚠️ Telegram credentials not configured")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")

        # Save results to file
        with open('/tmp/scanner_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("📁 Results saved to /tmp/scanner_results.json")

    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
