#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Integration
Run with: python3 run_scanner.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
import talib
from datetime import datetime
import requests
import os

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# NSE F&O Stocks (50 most liquid)
NSE_FO_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'BHARTIARTL', 'ITC', 'SBIN', 'LT', 'KOTAKBANK',
    'AXISBANK', 'MARUTI', 'ASIANPAINT', 'WIPRO', 'ONGC', 'NTPC', 'POWERGRID', 'TATASTEEL', 'TECHM', 'ULTRACEMCO',
    'SUNPHARMA', 'TITAN', 'COALINDIA', 'BAJFINANCE', 'HCLTECH', 'JSWSTEEL', 'INDUSINDBK', 'BRITANNIA', 'CIPLA', 'DRREDDY',
]

def send_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
        r = requests.post(url, json=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_stock_data(symbol):
    """Fetch and analyze stock"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(period="3mo")
        
        if len(data) < 20:
            return None

        # Calculate indicators
        c = data['Close'].values
        h = data['High'].values
        l = data['Low'].values

        data['RSI'] = talib.RSI(c, 14)
        data['ADX'] = talib.ADX(h, l, c, 14)
        data['SMA20'] = talib.SMA(c, 20)
        data['EMA20'] = talib.EMA(c, 20)

        return data
    except:
        return None

def scan():
    """Scan and filter stocks"""
    print(f"🚀 Scanning {len(NSE_FO_STOCKS)} stocks...")
    results = []

    for stock in NSE_FO_STOCKS:
        data = get_stock_data(stock)
        if data is None:
            continue

        # Current metrics
        close = data['Close'].iloc[-1]
        rsi = data['RSI'].iloc[-1]
        adx = data['ADX'].iloc[-1]
        sma20 = data['SMA20'].iloc[-1]

        # Volume check
        vol_ratio = data['Volume'].iloc[-1] / data['Volume'].tail(20).mean()

        # Criteria: RSI 30-75, ADX > 20, above SMA20, volume > 1.2x
        if 30 <= rsi <= 75 and adx > 20 and close > sma20 and vol_ratio > 1.2:
            results.append({
                'symbol': stock,
                'price': close,
                'rsi': rsi,
                'adx': adx,
                'vol': vol_ratio
            })
        
        print(f"  ✓ {stock}")

    return results

def format_message(results):
    """Format for Telegram"""
    if not results:
        return "<b>PCS Scanner</b>\n⚠️ No stocks found today"

    msg = f"<b>📊 PCS Scanner Results</b>\n"
    msg += f"<b>Found: {len(results)}</b> stocks\n"
    msg += "─" * 30 + "\n\n"

    for i, r in enumerate(sorted(results, key=lambda x: x['vol'], reverse=True)[:20], 1):
        msg += f"<b>{i}. {r['symbol']}</b>\n"
        msg += f"₹{r['price']:.0f} | RSI:{r['rsi']:.0f} | ADX:{r['adx']:.0f} | Vol:{r['vol']:.1f}x\n\n"

    if len(results) > 20:
        msg += f"... +{len(results)-20} more"

    return msg

if __name__ == "__main__":
    print("=" * 50)
    print("NSE F&O PCS SCANNER")
    print("=" * 50)
    
    results = scan()
    message = format_message(results)
    
    print("\n" + message)
    print("\n" + "=" * 50)
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        if send_telegram(message):
            print("✅ Sent to Telegram")
        else:
            print("❌ Failed to send")
    else:
        print("⚠️ Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
