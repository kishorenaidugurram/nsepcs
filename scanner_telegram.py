#!/usr/bin/env python3
"""
NSE PCS Scanner - Demo Mode (generates realistic sample results)
When live data is unavailable, this generates sample results for demonstration
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import pytz
from datetime import datetime
import requests
import os
import random

# Sample stocks with realistic data
SAMPLE_STOCKS = {
    'RELIANCE': {'base_price': 2850, 'volatility': 0.02, 'trend': 0.005},
    'TCS': {'base_price': 3980, 'volatility': 0.018, 'trend': 0.003},
    'HDFCBANK': {'base_price': 1880, 'volatility': 0.022, 'trend': 0.006},
    'INFY': {'base_price': 2240, 'volatility': 0.020, 'trend': 0.004},
    'ICICIBANK': {'base_price': 1050, 'volatility': 0.025, 'trend': 0.007},
    'SBIN': {'base_price': 580, 'volatility': 0.028, 'trend': 0.008},
    'MARUTI': {'base_price': 11850, 'volatility': 0.035, 'trend': 0.005},
    'ASIANPAINT': {'base_price': 3420, 'volatility': 0.032, 'trend': 0.003},
    'WIPRO': {'base_price': 445, 'volatility': 0.024, 'trend': 0.002},
    'KOTAKBANK': {'base_price': 1485, 'volatility': 0.026, 'trend': 0.006},
    'AXISBANK': {'base_price': 1125, 'volatility': 0.030, 'trend': 0.008},
    'LT': {'base_price': 3280, 'volatility': 0.021, 'trend': 0.005},
    'BHARTIARTL': {'base_price': 1635, 'volatility': 0.027, 'trend': 0.004},
    'SUNPHARMA': {'base_price': 825, 'volatility': 0.033, 'trend': 0.006},
    'TATASTEEL': {'base_price': 135, 'volatility': 0.038, 'trend': 0.009},
    'JSWSTEEL': {'base_price': 945, 'volatility': 0.036, 'trend': 0.007},
    'POWERGRID': {'base_price': 375, 'volatility': 0.019, 'trend': 0.002},
    'NTPC': {'base_price': 385, 'volatility': 0.020, 'trend': 0.003},
    'ONGC': {'base_price': 385, 'volatility': 0.034, 'trend': 0.005},
    'BPCL': {'base_price': 385, 'volatility': 0.031, 'trend': 0.004},
}

def generate_stock_data(symbol, config):
    """Generate realistic stock data for demo"""
    base_price = config['base_price']
    volatility = config['volatility']
    trend = config['trend']

    # Generate 60 days of data
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    prices = []

    current_price = base_price
    for i, date in enumerate(dates):
        # Add trend and random walk
        daily_change = trend + np.random.normal(0, volatility)
        current_price *= (1 + daily_change)
        prices.append(current_price)

    # Calculate current metrics
    current_price = prices[-1]
    rsi = 45 + np.random.uniform(-15, 25)  # Between 30-70
    adx = 20 + np.random.uniform(0, 30)    # Between 20-50

    # Volume data
    current_vol = np.random.uniform(100000, 5000000)
    avg_vol = np.random.uniform(50000, 3000000)
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0

    return {
        'price': current_price,
        'rsi': rsi,
        'adx': adx,
        'vol_ratio': vol_ratio,
        'trend': 'Bullish' if trend > 0 else 'Neutral'
    }

def generate_patterns(symbol, stock_data):
    """Generate realistic patterns for a stock"""
    patterns = []

    # Pattern likelihood based on RSI and ADX
    rsi = stock_data['rsi']
    adx = stock_data['adx']

    # Pattern 1: Near Support (when RSI is low)
    if 25 <= rsi <= 40:
        patterns.append({
            'name': 'Near Support',
            'strength': int(50 + (40 - rsi) * 2),
            'confidence': 'MEDIUM'
        })

    # Pattern 2: Bullish Trend
    if rsi > 50 and adx > 20:
        patterns.append({
            'name': 'Bullish Trend',
            'strength': int(60 + (rsi - 50) * 0.5),
            'confidence': 'MEDIUM'
        })

    # Pattern 3: Volume Increase
    if stock_data['vol_ratio'] > 1.5:
        patterns.append({
            'name': 'Volume Increase',
            'strength': int(50 + (stock_data['vol_ratio'] - 1.5) * 10),
            'confidence': 'LOW'
        })

    # Pattern 4: Strong ADX (Trend Strength)
    if adx > 25:
        patterns.append({
            'name': 'Strong Trend',
            'strength': int(55 + (adx - 25) * 1.2),
            'confidence': 'MEDIUM'
        })

    # Pattern 5: Oversold Bounce
    if rsi < 35:
        patterns.append({
            'name': 'Oversold Bounce',
            'strength': int(40 + (35 - rsi) * 2),
            'confidence': 'LOW'
        })

    return patterns

def send_to_telegram(message, bot_token, chat_id):
    """Send message to Telegram"""
    if not bot_token or not chat_id:
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
    except:
        return False

def main():
    print("\n" + "="*60)
    print("🚀 NSE F&O PCS Scanner - Demo Mode")
    print("="*60 + "\n")
    print("📌 Note: Using simulated data (live data unavailable)\n")

    # Get Telegram credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not found")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable Telegram delivery\n")

    results = []

    print(f"🔍 Scanning {len(SAMPLE_STOCKS)} sample stocks...\n")

    for i, (symbol, config) in enumerate(SAMPLE_STOCKS.items()):
        try:
            # Generate realistic data
            stock_data = generate_stock_data(symbol, config)

            # Detect patterns
            patterns = generate_patterns(symbol, stock_data)

            if patterns:
                results.append({
                    'symbol': symbol,
                    'price': stock_data['price'],
                    'rsi': stock_data['rsi'],
                    'adx': stock_data['adx'],
                    'vol_ratio': stock_data['vol_ratio'],
                    'patterns': patterns
                })

                print(f"✅ {symbol}: {len(patterns)} pattern(s) | RSI:{stock_data['rsi']:.1f} ADX:{stock_data['adx']:.1f}")
            else:
                print(f"❌ {symbol}: No patterns")

        except Exception as e:
            print(f"⚠️  {symbol}: Error - {str(e)[:40]}")

    print("\n" + "="*60)
    print(f"📊 RESULTS: Found {len(results)} stocks with patterns\n")

    if results:
        # Sort by max pattern strength
        results_sorted = sorted(results, key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        print("🏆 TOP RESULTS:\n")
        for i, result in enumerate(results_sorted[:10], 1):
            max_strength = max(p['strength'] for p in result['patterns'])
            patterns_str = ', '.join([p['name'][:18] for p in result['patterns'][:2]])

            print(f"{i:2}. {result['symbol']:12} | ₹{result['price']:9.2f} | RSI:{result['rsi']:5.1f} | Vol:{result['vol_ratio']:4.2f}x")
            print(f"      {patterns_str}")

        if len(results) > 10:
            print(f"\n    ... and {len(results) - 10} more stocks")

        # Format for Telegram
        message = "🔍 <b>NSE PCS Scanner - Daily Results</b>\n"
        message += "<i>(Demo Mode - Simulated Data)</i>\n\n"
        message += f"📊 Found <b>{len(results)} stocks</b> meeting criteria:\n\n"

        for i, result in enumerate(results_sorted[:10], 1):
            max_strength = max(p['strength'] for p in result['patterns'])
            pattern_main = result['patterns'][0]['name']
            message += f"{i}. <b>{result['symbol']}</b> - ₹{result['price']:.2f}\n"
            message += f"   📈 RSI: {result['rsi']:.0f} | ADX: {result['adx']:.0f}\n"
            message += f"   🎯 {pattern_main} ({max_strength:.0f}%)\n"

        if len(results) > 10:
            message += f"\n✨ ...and {len(results) - 10} more stocks\n"

        message += f"\n⏰ Scan: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}"
        message += "\n\n<i>Data: Simulated - For demo purposes only</i>"

        # Send to Telegram
        if bot_token and chat_id:
            print("\n" + "="*60)
            print("📱 Sending to Telegram...")
            if send_to_telegram(message, bot_token, chat_id):
                print("✅ Message sent to Telegram!")
            else:
                print("❌ Failed to send Telegram message")
                print("\nMessage content:")
                print(message)
        else:
            print("\n" + "="*60)
            print("📱 Message that would be sent to Telegram:\n")
            print(message)

    print("\n" + "="*60)
    print("✅ Scan complete!\n")

    return len(results)

if __name__ == "__main__":
    main()
