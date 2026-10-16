#!/usr/bin/env python3.11
"""
NSE F&O PCS Scanner - Run Scan and Send to Telegram
Simplified standalone runner that works without Streamlit
"""

import os
import sys
import subprocess
import json
from datetime import datetime
import pytz
import pandas as pd
import yfinance as yf
from telegram_scanner import send_scan_results, get_telegram_config

def get_nse_stocks():
    """Get list of NSE F&O stocks"""
    # Core liquid stocks
    return [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
        'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
        'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
        'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS',
        'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS',
        'TATASTEEL.NS', 'HINDALCO.NS', 'NIFTYIT.NS', 'BANKNIFTY.NS'
    ]

def get_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period:
        return None

    deltas = prices.diff()
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    if down == 0:
        return 100.0

    rs = up / down
    rsi = 100. - 100. / (1. + rs)
    return rsi

def analyze_stock(symbol, period="3mo"):
    """Analyze a stock for buy signals"""
    try:
        # Fetch data
        data = yf.download(symbol, period=period, progress=False)

        if data is None or len(data) < 30:
            return None

        # Get latest values
        close_prices = data['Close']
        high_prices = data['High']
        low_prices = data['Low']
        volume = data['Volume']

        # Calculate indicators
        sma_20 = close_prices.rolling(20).mean()
        sma_50 = close_prices.rolling(50).mean()
        ema_20 = close_prices.ewm(span=20).mean()

        # Latest values
        latest_close = close_prices.iloc[-1]
        latest_high = high_prices.iloc[-1]
        latest_low = low_prices.iloc[-1]
        latest_sma20 = sma_20.iloc[-1]
        latest_sma50 = sma_50.iloc[-1]
        latest_ema20 = ema_20.iloc[-1]
        latest_volume = volume.iloc[-1]
        avg_volume = volume.iloc[-50:].mean()

        # RSI
        rsi = get_rsi(close_prices.values)

        # Volume ratio
        volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0

        # Bollinger Bands
        bb_sma = close_prices.rolling(20).mean()
        bb_std = close_prices.rolling(20).std()
        bb_upper = bb_sma + (bb_std * 2)
        bb_lower = bb_sma - (bb_std * 2)

        latest_bb_upper = bb_upper.iloc[-1]
        latest_bb_lower = bb_lower.iloc[-1]
        latest_bb_mid = bb_sma.iloc[-1]

        # Pattern detection score
        score = 0
        patterns = []

        # Check for support near price
        if latest_close > latest_sma20 * 0.97:  # Within 3% of SMA20
            score += 20
            patterns.append("Close to MA support")

        # Check RSI strength
        if 45 <= rsi <= 70:
            score += 20
            patterns.append(f"RSI optimal ({rsi:.1f})")

        # Check volume
        if volume_ratio > 1.2:
            score += 15
            patterns.append(f"High volume ({volume_ratio:.2f}x)")

        # Check trend alignment
        if latest_close > latest_sma20 > latest_sma50:
            score += 20
            patterns.append("Uptrend (Close > SMA20 > SMA50)")

        # Check for breakout potential
        if latest_close > latest_bb_mid and latest_close < latest_bb_upper:
            score += 15
            patterns.append("Near upper BB")

        # Check recent momentum
        recent_change = ((latest_close - close_prices.iloc[-5]) / close_prices.iloc[-5]) * 100
        if 0.5 <= recent_change <= 10:
            score += 10
            patterns.append(f"Momentum up {recent_change:.1f}%")

        if score >= 50:  # Threshold for qualifying
            return {
                'symbol': symbol.replace('.NS', ''),
                'pattern': ' + '.join(patterns[:3]) if patterns else 'Multi-factor setup',
                'strength': min(100, score),
                'current_price': latest_close,
                'rsi': rsi if rsi is not None else 0,
                'adx': 0,  # Simplified for this version
                'volume_ratio': volume_ratio,
                'sma_dist': ((latest_close - latest_sma20) / latest_sma20) * 100 if latest_sma20 > 0 else 0
            }

        return None

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        return None

def main():
    """Main scanner function"""
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    print("\n" + "="*70)
    print(f"🚀 NSE F&O PCS Scanner")
    print(f"   {current_time.strftime('%A, %Y-%m-%d %H:%M:%S IST')}")
    print("="*70)

    # Check Telegram config
    telegram_config = get_telegram_config()
    if not telegram_config['configured']:
        print("\n⚠️  Telegram not configured!")
        print("   See TELEGRAM_SETUP.md for setup instructions")
        print("   Or run: python3.11 telegram_scanner.py test")
    else:
        print(f"\n✅ Telegram configured (Chat ID: {telegram_config['chat_id']})")

    # Get stocks
    stocks = get_nse_stocks()
    print(f"\n📊 Analyzing {len(stocks)} stocks...")
    print("-"*70)

    results = []

    for i, symbol in enumerate(stocks, 1):
        clean_symbol = symbol.replace('.NS', '')
        print(f"[{i:2d}/{len(stocks)}] {clean_symbol:12s}", end=" ", flush=True)

        stock_result = analyze_stock(symbol)

        if stock_result:
            results.append(stock_result)
            strength = stock_result['strength']
            pattern = stock_result['pattern'][:30]
            print(f"✅ {pattern} ({strength:.0f}%)")
        else:
            print("⏭️  Skipped")

    # Print results
    print("\n" + "="*70)
    print(f"📈 SCAN COMPLETE - Found {len(results)} qualifying stocks")
    print("="*70)

    if results:
        print("\n🏆 Top 10 Results:")
        results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)
        for i, stock in enumerate(results_sorted[:10], 1):
            print(f"  {i:2d}. {stock['symbol']:12s} - {stock['pattern']:35s} ({stock['strength']:6.1f}%)")
    else:
        print("\nNo stocks found meeting criteria today")

    # Send to Telegram
    print("\n📤 Sending results to Telegram...")
    if send_scan_results(results):
        print("✅ Successfully sent to Telegram!")
    elif telegram_config['configured']:
        print("❌ Failed to send to Telegram (check credentials)")
    else:
        print("⚠️  Telegram not configured - skipping notification")

    print("\n" + "="*70)
    return len(results)

if __name__ == "__main__":
    try:
        count = main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
