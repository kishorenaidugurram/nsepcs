#!/usr/bin/env python3
"""
Simple Stock Scanner - Core logic without ta library dependency
"""

import sys
import os
import logging
from datetime import datetime
import json

# Check if we can import required modules
try:
    import pandas as pd
    import numpy as np
    import yfinance as yf
    print("✓ All basic imports successful")
except ImportError as e:
    print(f"Missing module: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# F&O stocks list (first 50 for quick test)
F_O_STOCKS_SAMPLE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS'
]

def calculate_rsi(data, period=14):
    """Calculate RSI"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def simple_scan(symbol, min_price_change=0.5):
    """Simple scan for stocks with positive movement"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")

        if len(hist) < 20:
            return None

        # Get basic metrics
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100

        # Calculate RSI
        rsi = calculate_rsi(hist['Close'])
        current_rsi = rsi.iloc[-1]

        # Simple volume check
        avg_volume = hist['Volume'].tail(20).mean()
        current_volume = hist['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume

        # Filter logic
        if change_pct < 0:  # Only positive movers
            return None
        if current_rsi > 80:  # Overbought
            return None
        if volume_ratio < 1.0:  # Need volume
            return None

        return {
            'symbol': symbol,
            'price': current_price,
            'change': change_pct,
            'rsi': current_rsi,
            'volume_ratio': volume_ratio
        }

    except Exception as e:
        logger.debug(f"Error scanning {symbol}: {e}")
        return None

def main():
    logger.info("=" * 60)
    logger.info("Simple NSE Stock Scanner")
    logger.info("=" * 60)
    logger.info(f"Scanning {len(F_O_STOCKS_SAMPLE)} stocks...")

    results = []
    for i, symbol in enumerate(F_O_STOCKS_SAMPLE, 1):
        logger.info(f"[{i}/{len(F_O_STOCKS_SAMPLE)}] Scanning {symbol}...")
        result = simple_scan(symbol)
        if result:
            results.append(result)
            logger.info(f"  ✓ Found: {symbol} @ ₹{result['price']:.2f} (+{result['change']:.2f}%)")

    # Save results
    if results:
        output_dir = "/tmp/claude-0/-home-user-nsepcs/0f821919-47d0-5372-aa4d-845b71125a7a/scratchpad"
        os.makedirs(output_dir, exist_ok=True)

        # Save as CSV
        df = pd.DataFrame(results)
        csv_file = os.path.join(output_dir, f"scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(csv_file, index=False)
        logger.info(f"Results saved to: {csv_file}")

        # Save as JSON
        json_file = os.path.join(output_dir, f"scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"JSON saved to: {json_file}")

    logger.info("=" * 60)
    logger.info(f"SCAN COMPLETE: Found {len(results)} qualifying stocks")
    logger.info("=" * 60)

    # Print results to stdout
    if results:
        print("\n" + "=" * 60)
        print("QUALIFYING STOCKS:")
        print("=" * 60)
        for r in results:
            print(f"{r['symbol']:15} | Price: ₹{r['price']:8.2f} | Change: {r['change']:6.2f}% | RSI: {r['rsi']:6.1f}")

    return len(results)

if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
