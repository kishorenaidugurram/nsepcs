#!/usr/bin/env python3
"""
NSE Stock Screener - Filter stocks based on technical criteria and send to Telegram
"""

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
import os
import json
import requests

warnings.filterwarnings('ignore')

# NSE F&O stocks
NSE_FO = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
    'KOTAK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI', 'ASIANPAINT', 'BHARTIARTL',
    'SUNPHARMA', 'TATAMOTORS', 'ADANIGREEN', 'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK',
    'TECHM', 'TITAN', 'NESTLEIND', 'ULTRACEMCO', 'POWERGRID', 'NTPC', 'ONGC',
    'COALINDIA', 'JSWSTEEL', 'TATASTEEL', 'HINDALCO', 'NIFTYNXT50', 'BANKNIFTY'
]

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

def calculate_adx(high, low, close, period=14):
    """Calculate ADX simplified"""
    plus_dm = high.diff()
    minus_dm = low.diff() * -1

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    di_diff = (plus_di - minus_di).abs()
    di_sum = plus_di + minus_di

    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(period).mean()

    return adx

def calculate_sma(prices, period=20):
    """Calculate SMA"""
    return pd.Series(prices).rolling(window=period).mean()

def calculate_ema(prices, period=20):
    """Calculate EMA"""
    return pd.Series(prices).ewm(span=period, adjust=False).mean()

def screen_stock(symbol):
    """Screen a single stock"""
    try:
        # Download data
        ticker = f"{symbol}.NS"
        data = yf.download(ticker, period="1y", interval="1d", progress=False, threads=False)

        if data is None or len(data) < 50:
            return None

        # Calculate indicators
        close = data['Close'].values
        high = data['High'].values
        low = data['Low'].values

        # RSI
        rsi = calculate_rsi(close, 14)
        current_rsi = rsi[-1]

        # ADX
        adx_vals = calculate_adx(data['High'], data['Low'], data['Close'], 14)
        current_adx = adx_vals.iloc[-1] if not pd.isna(adx_vals.iloc[-1]) else 0

        # Moving averages
        ema_20 = calculate_ema(close, 20)
        current_ema = ema_20.iloc[-1] if len(ema_20) > 0 else None
        current_price = close[-1]

        if current_ema is None or pd.isna(current_ema):
            return None

        # Check filters
        rsi_ok = 30 <= current_rsi <= 75
        adx_ok = current_adx >= 20
        price_ok = current_price >= current_ema * 0.97  # 3% tolerance

        if rsi_ok and adx_ok and price_ok:
            return {
                'symbol': symbol,
                'price': round(float(current_price), 2),
                'rsi': round(float(current_rsi), 1),
                'adx': round(float(current_adx), 1),
                'ema_20': round(float(current_ema), 2),
            }

        return None

    except Exception as e:
        return None

def main():
    """Main function"""
    print(f"🎯 Starting NSE Stock Screener at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Scanning {len(NSE_FO)} stocks")
    print("Filters: RSI 30-75, ADX >= 20, Price >= EMA20 (3% tolerance)\n")

    qualified = []

    for i, symbol in enumerate(NSE_FO, 1):
        print(f"[{i:2d}/{len(NSE_FO)}] Scanning {symbol:15s}...", end='\r', flush=True)

        result = screen_stock(symbol)
        if result:
            qualified.append(result)

    print(" " * 70)
    print(f"✅ Complete! Found {len(qualified)} stocks meeting criteria\n")

    # Sort by RSI descending
    qualified.sort(key=lambda x: x['rsi'], reverse=True)

    # Display results
    if qualified:
        print("QUALIFIED STOCKS:")
        print("=" * 70)
        for i, stock in enumerate(qualified, 1):
            print(f"{i:2d}. {stock['symbol']:12s} | Price: ₹{stock['price']:7.2f} | RSI: {stock['rsi']:5.1f} | ADX: {stock['adx']:5.1f}")
        print("=" * 70)
        print()
    else:
        print("No stocks met the criteria")
        print()

    # Format Telegram message
    if qualified:
        msg = f"🎯 *NSE SCREENER - {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        msg += f"✅ Found: {len(qualified)} stocks\n"
        msg += f"📊 Filters: RSI 30-75, ADX≥20, Price≥EMA20\n\n"

        for i, stock in enumerate(qualified[:15], 1):
            msg += f"{i}. *{stock['symbol']}* - ₹{stock['price']} (RSI:{stock['rsi']} ADX:{stock['adx']})\n"

        if len(qualified) > 15:
            msg += f"\n... and {len(qualified)-15} more"
    else:
        msg = "❌ No stocks met the filter criteria today"

    # Send to Telegram
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if bot_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={
                'chat_id': chat_id,
                'text': msg,
                'parse_mode': 'Markdown'
            }, timeout=10)
            print("✅ Sent to Telegram")
        except:
            print("⚠️  Could not send to Telegram")
    else:
        print("⚠️  Telegram credentials not set")
        print("Message that would be sent:")
        print(msg)

    # Save results
    if qualified:
        filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w') as f:
            json.dump(qualified, f, indent=2)
        print(f"📄 Results saved: {filename}")

if __name__ == "__main__":
    main()
