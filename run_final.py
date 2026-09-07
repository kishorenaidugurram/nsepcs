#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Final Minimal Implementation
No external technical analysis library needed
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

def send_to_telegram(message_text):
    """Send message to Telegram"""
    try:
        import requests
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def calculate_rsi(prices, period=14):
    """Calculate RSI without ta library"""
    if len(prices) < period + 1:
        return 50.0

    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_stock(symbol, data_df):
    """Analyze a stock for patterns"""
    try:
        if data_df is None or len(data_df) < 20:
            return None

        prices = data_df['Close'].values
        volumes = data_df['Volume'].values
        highs = data_df['High'].values
        lows = data_df['Low'].values

        # Current metrics
        current_price = prices[-1]
        current_volume = volumes[-1]
        current_rsi = calculate_rsi(prices)

        # Volume analysis
        avg_volume_20 = sum(volumes[-20:]) / 20
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1

        # Support/Resistance
        high_20 = max(highs[-20:])
        low_20 = min(lows[-20:])

        # Pattern detection - simplified
        patterns = []

        # Pattern 1: Volume surge + price near resistance
        if volume_ratio >= 1.5:
            distance_to_high = ((high_20 - current_price) / high_20) * 100
            if distance_to_high < 3:
                patterns.append({
                    'type': 'Resistance Breakout',
                    'strength': 70 + (volume_ratio * 10),
                    'confidence': 'MEDIUM'
                })

        # Pattern 2: Price near 20-day high with volume
        if current_price > high_20 * 0.98 and volume_ratio >= 1.2:
            patterns.append({
                'type': 'High Volume Thrust',
                'strength': 65 + (volume_ratio * 8),
                'confidence': 'MEDIUM'
            })

        # Pattern 3: Volume surge without price confirmation
        if volume_ratio >= 2.0:
            patterns.append({
                'type': 'Volume Confirmation',
                'strength': 60,
                'confidence': 'LOW'
            })

        if patterns:
            return {
                'symbol': symbol,
                'price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'patterns': patterns,
                'high_20': high_20,
                'low_20': low_20
            }

        return None

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def main():
    """Main function"""
    print("🚀 NSE F&O PCS Screener - Final Run")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")

    # Try to import yfinance
    try:
        import yfinance as yf
        import pandas as pd
        print("✅ Dependencies ready\n")
    except ImportError as e:
        print(f"❌ Missing: {e}")
        print("Install with: pip install yfinance pandas numpy requests\n")
        return 1

    # Nifty 50 stocks
    stocks = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    ]

    print(f"🔍 Scanning {len(stocks)} stocks...\n")

    results = []
    for i, symbol in enumerate(stocks, 1):
        try:
            clean_symbol = symbol.replace('.NS', '')
            print(f"  [{i:2d}/{len(stocks)}] {clean_symbol}...", end=' ', flush=True)

            # Fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="3mo")

            if len(data) < 20:
                print("❌ No data")
                continue

            # Analyze
            analysis = analyze_stock(symbol, data)

            if analysis:
                results.append(analysis)
                best_pattern = max(analysis['patterns'], key=lambda p: p['strength'])
                print(f"✅ ({best_pattern['type']}, {best_pattern['strength']:.0f}%)")
            else:
                print("⚠️  No patterns")

        except Exception as e:
            print(f"⚠️  Error")
            continue

    # Generate report
    print(f"\n{'='*70}")
    print(f"✅ RESULTS: Found {len(results)} stocks with patterns")
    print(f"{'='*70}\n")

    if results:
        # Sort by best pattern strength
        for result in sorted(results, key=lambda r: max(p['strength'] for p in r['patterns']), reverse=True):
            symbol = result['symbol'].replace('.NS', '')
            price = result['price']
            volume = result['volume_ratio']
            rsi = result['rsi']
            best_pattern = max(result['patterns'], key=lambda p: p['strength'])

            print(f"🎯 {symbol}")
            print(f"   💰 ₹{price:.2f} | 📊 {volume:.1f}x | RSI: {rsi:.1f}")
            print(f"   📈 {best_pattern['type']} ({best_pattern['strength']:.0f}% strength)")
            print()

    # Send to Telegram
    telegram_enabled = os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID')

    if telegram_enabled:
        print("📤 Sending to Telegram...")

        message = f"📊 <b>NSE F&O PCS Screener</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n\n"

        if results:
            message += f"✅ <b>Found {len(results)} stocks</b>\n\n"
            for result in sorted(results, key=lambda r: max(p['strength'] for p in r['patterns']), reverse=True)[:10]:
                symbol = result['symbol'].replace('.NS', '')
                price = result['price']
                volume = result['volume_ratio']
                best_pattern = max(result['patterns'], key=lambda p: p['strength'])

                message += f"<b>{symbol}</b> ₹{price:.2f}\n"
                message += f"📊 {volume:.1f}x | 📈 {best_pattern['type']}\n"
                message += f"💪 {best_pattern['strength']:.0f}%\n\n"
        else:
            message += "❌ No qualifying stocks found today"

        if send_to_telegram(message):
            print("✅ Sent successfully\n")
        else:
            print("⚠️  Failed to send\n")
    else:
        print("ℹ️  Telegram not configured\n")
        print("To enable:")
        print("  export TELEGRAM_BOT_TOKEN='...'")
        print("  export TELEGRAM_CHAT_ID='...'\n")

    print(f"✅ Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
