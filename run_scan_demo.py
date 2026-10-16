#!/usr/bin/env python3.11
"""
NSE F&O PCS Scanner - Demo Mode
Uses realistic synthetic data when live data isn't available
Perfect for testing Telegram integration and scheduled tasks
"""

import os
import sys
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
from telegram_scanner import send_scan_results, get_telegram_config

def generate_demo_stock_data():
    """Generate realistic demo stock data"""
    np.random.seed(42)

    stocks = {
        'RELIANCE': {'base': 3240, 'volatility': 0.02, 'trend': 0.001},
        'TCS': {'base': 4125, 'volatility': 0.015, 'trend': 0.0005},
        'HDFCBANK': {'base': 1850, 'volatility': 0.02, 'trend': 0.0008},
        'INFY': {'base': 2680, 'volatility': 0.018, 'trend': 0.0006},
        'ICICIBANK': {'base': 980, 'volatility': 0.025, 'trend': -0.0002},
        'KOTAKBANK': {'base': 4520, 'volatility': 0.02, 'trend': 0.0007},
        'AXISBANK': {'base': 1110, 'volatility': 0.022, 'trend': 0.0005},
        'SBIN': {'base': 810, 'volatility': 0.03, 'trend': 0.0009},
        'LT': {'base': 2840, 'volatility': 0.016, 'trend': 0.0003},
        'WIPRO': {'base': 510, 'volatility': 0.02, 'trend': 0.0004},
        'HCLTECH': {'base': 1680, 'volatility': 0.018, 'trend': 0.0002},
        'MARUTI': {'base': 9850, 'volatility': 0.025, 'trend': 0.0001},
        'SUNPHARMA': {'base': 850, 'volatility': 0.03, 'trend': -0.0005},
        'ASIANPAINT': {'base': 3450, 'volatility': 0.02, 'trend': 0.0006},
        'TATAMOTORS': {'base': 1320, 'volatility': 0.035, 'trend': 0.001},
    }

    results = []
    for symbol, params in stocks.items():
        # Generate price series
        prices = [params['base']]
        for _ in range(49):  # 50 days
            change = np.random.normal(params['trend'], params['volatility'])
            prices.append(prices[-1] * (1 + change))

        # Calculate indicators
        closes = np.array(prices)
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else np.mean(closes)
        latest_close = closes[-1]

        # Simple RSI calculation
        deltas = np.diff(closes[-15:])
        gains = np.where(deltas > 0, deltas, 0).sum() / 14
        losses = np.where(deltas < 0, -deltas, 0).sum() / 14
        rs = gains / losses if losses > 0 else 100
        rsi = 100 - (100 / (1 + rs))

        # Volume simulation
        volume = np.random.randint(500000, 5000000)
        avg_volume = np.random.randint(1000000, 3000000)
        volume_ratio = volume / avg_volume

        # Calculate score
        score = 0
        patterns = []

        # Support test
        if latest_close > sma_20 * 0.97:
            score += 20
            patterns.append("Support near SMA20")

        # RSI strength
        if 45 <= rsi <= 70:
            score += 20
            patterns.append(f"RSI: {rsi:.0f}")

        # Volume
        if volume_ratio > 1.1:
            score += 15
            patterns.append(f"Vol: {volume_ratio:.1f}x")

        # Trend
        if latest_close > sma_20 > sma_50:
            score += 20
            patterns.append("Uptrend align")

        # Momentum
        momentum = ((closes[-1] - closes[-5]) / closes[-5]) * 100
        if 0.5 <= momentum <= 10:
            score += 10
            patterns.append(f"Mom: {momentum:.1f}%")

        if score >= 50:
            results.append({
                'symbol': symbol,
                'pattern': ' + '.join(patterns[:2]),
                'strength': min(100, score),
                'current_price': latest_close,
                'rsi': rsi,
                'adx': np.random.randint(15, 35),
                'volume_ratio': volume_ratio
            })

    return results

def main():
    """Main function"""
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    print("\n" + "="*70)
    print(f"🚀 NSE F&O PCS Scanner - DEMO MODE")
    print(f"   {current_time.strftime('%A, %Y-%m-%d %H:%M:%S IST')}")
    print(f"   Using synthetic data (for Telegram integration testing)")
    print("="*70)

    # Check Telegram config
    telegram_config = get_telegram_config()
    if not telegram_config['configured']:
        print("\n⚠️  Telegram NOT configured")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to send results")
        print("   See TELEGRAM_SETUP.md for setup instructions")
    else:
        print(f"\n✅ Telegram configured")
        print(f"   Sending results to Chat ID: {telegram_config['chat_id']}")

    # Generate demo data
    print(f"\n📊 Generating demo stock analysis...")
    results = generate_demo_stock_data()

    # Print results
    print("\n" + "="*70)
    print(f"📈 SCAN COMPLETE - Found {len(results)} stocks with setups")
    print("="*70)

    if results:
        results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)
        print(f"\n🏆 Top 10 Stocks:")
        for i, stock in enumerate(results_sorted[:10], 1):
            print(f"  {i:2d}. {stock['symbol']:12s} - {stock['pattern']:35s} ({stock['strength']:5.1f}%)")

    # Send to Telegram
    print("\n📤 Sending results to Telegram...")
    if telegram_config['configured']:
        if send_scan_results(results):
            print("✅ Successfully sent to Telegram!")
        else:
            print("❌ Failed to send to Telegram")
            print("   Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    else:
        print("⚠️  Skipped (Telegram not configured)")
        print("   Run: TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3.11 run_scan_demo.py")

    print("\n" + "="*70)
    return len(results)

if __name__ == "__main__":
    try:
        count = main()
        print(f"\n✅ Demo scan complete - {count} stocks found")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
