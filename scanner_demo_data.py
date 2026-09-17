#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Demo with Synthetic Data
Shows how the scanner works with sample data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# Filter configuration
MIN_PCS_SCORE = 50
MIN_VOLUME_RATIO = 0.7

# Sample stock data
SAMPLE_STOCKS = {
    'RELIANCE': {
        'price': 2850.50,
        'rsi': 52.3,
        'adx': 28.5,
        'macd_hist': 12.5,
        'vol_ratio': 0.85,
        'above_sma20': True
    },
    'TCS': {
        'price': 3620.00,
        'rsi': 48.7,
        'adx': 22.3,
        'macd_hist': 8.2,
        'vol_ratio': 0.92,
        'above_sma20': True
    },
    'HDFCBANK': {
        'price': 1820.25,
        'rsi': 61.5,
        'adx': 32.1,
        'macd_hist': 15.3,
        'vol_ratio': 1.12,
        'above_sma20': True
    },
    'INFY': {
        'price': 1865.00,
        'rsi': 45.2,
        'adx': 18.9,
        'macd_hist': -5.2,
        'vol_ratio': 0.78,
        'above_sma20': False
    },
    'ICICIBANK': {
        'price': 1105.50,
        'rsi': 55.8,
        'adx': 25.7,
        'macd_hist': 10.1,
        'vol_ratio': 0.95,
        'above_sma20': True
    },
    'SBIN': {
        'price': 580.75,
        'rsi': 58.3,
        'adx': 24.2,
        'macd_hist': 7.8,
        'vol_ratio': 0.88,
        'above_sma20': True
    },
    'LT': {
        'price': 3265.00,
        'rsi': 52.9,
        'adx': 29.5,
        'macd_hist': 18.5,
        'vol_ratio': 0.81,
        'above_sma20': True
    },
    'ITC': {
        'price': 442.25,
        'rsi': 49.5,
        'adx': 20.1,
        'macd_hist': 2.3,
        'vol_ratio': 0.76,
        'above_sma20': True
    }
}


def calculate_pcs_score(stock_data):
    """Calculate PCS score from sample data"""
    score = 60  # Base score
    details = []

    # RSI (35-75 optimal)
    rsi = stock_data['rsi']
    if 35 <= rsi <= 75:
        score += 10
    details.append(f"RSI: {rsi:.1f}")

    # Trend (ADX > 20)
    if stock_data['adx'] > 20:
        score += 10
        details.append(f"Trend: {stock_data['adx']:.1f}")

    # Price position
    if stock_data['above_sma20']:
        score += 10
        details.append("Above SMA20")
    else:
        score += 5
        details.append("Near SMA20")

    # MACD
    if stock_data['macd_hist'] > 0:
        score += 10
        details.append("MACD +")
    else:
        score += 5
        details.append("MACD -")

    # Volume
    if stock_data['vol_ratio'] >= 0.7:
        score += 5
        details.append("Good Vol")

    return min(score, 100), details


def main():
    """Main function"""
    print("=" * 70)
    print("🚀 NSE F&O PCS Scanner - Demo with Synthetic Data")
    print("=" * 70)
    print(f"📊 Filter: PCS Score ≥ {MIN_PCS_SCORE}, Vol Ratio ≥ {MIN_VOLUME_RATIO}")
    print(f"📈 Analyzing {len(SAMPLE_STOCKS)} sample stocks...\n")

    results = []

    for i, (symbol, data) in enumerate(SAMPLE_STOCKS.items(), 1):
        print(f"[{i}/{len(SAMPLE_STOCKS)}] {symbol}...", end='\r')

        # Check volume
        if data['vol_ratio'] < MIN_VOLUME_RATIO:
            continue

        # Calculate score
        score, details = calculate_pcs_score(data)

        # Filter by score
        if score >= MIN_PCS_SCORE:
            results.append({
                'Symbol': symbol,
                'Price': data['price'],
                'PCS Score': score,
                'RSI': data['rsi'],
                'Vol Ratio': data['vol_ratio'],
                'Details': ' | '.join(details)
            })

    print(" " * 70, end='\r')

    if not results:
        print("\n❌ No stocks meeting criteria")
        return

    # Display results
    df = pd.DataFrame(results).sort_values('PCS Score', ascending=False)

    print("\n" + "=" * 70)
    print("RESULTS - Stocks Meeting Filter Criteria")
    print("=" * 70)
    print(df[['Symbol', 'Price', 'PCS Score', 'RSI', 'Vol Ratio']].to_string(index=False))

    print("\n" + "=" * 70)
    print("DETAILED VIEW")
    print("=" * 70)
    for idx, row in df.iterrows():
        print(f"\n{idx+1}. {row['Symbol']}  [Score: {row['PCS Score']}/100]")
        print(f"   Price: ₹{row['Price']:.2f}")
        print(f"   RSI: {row['RSI']:.1f}")
        print(f"   Volume Ratio: {row['Vol Ratio']:.2f}")
        print(f"   Analysis: {row['Details']}")

    # Save to CSV
    csv_file = f"pcs_results_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_file, index=False)
    print(f"\n💾 Results saved to {csv_file}")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Set up Telegram credentials (see TELEGRAM_SETUP.md)")
    print("2. Run the live scanner: python scanner_telegram.py")
    print("   Environment variables:")
    print("   - TELEGRAM_BOT_TOKEN: Your bot token from @BotFather")
    print("   - TELEGRAM_CHAT_ID: Your Telegram user ID")
    print("   - MIN_PCS_SCORE: Minimum score threshold (default: 50)")
    print("   - MIN_VOLUME_RATIO: Min volume ratio (default: 0.7)")
    print("\n3. Example:")
    print("   export TELEGRAM_BOT_TOKEN='...'")
    print("   export TELEGRAM_CHAT_ID='...'")
    print("   python scanner_telegram.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
