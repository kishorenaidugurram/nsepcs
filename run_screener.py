#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Screener - For automated analysis without Streamlit UI
"""

import sys
import os

# Mock streamlit before importing streamlit_app
class MockStreamlit:
    def set_page_config(self, **kwargs):
        pass

    def markdown(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['streamlit'] = MockStreamlit()

# Mock 'ta' module
class MockTA:
    def RSI(self, *args, **kwargs):
        return None

    def MACD(self, *args, **kwargs):
        return None, None, None

    def ADX(self, *args, **kwargs):
        return None

    def BBANDS(self, *args, **kwargs):
        return None, None, None

    def SMA(self, *args, **kwargs):
        return None

    def EMA(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['ta'] = MockTA()

# Now we can import the scanner and other components
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import warnings
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import re
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema

try:
    import ta
except ImportError:
    print("Note: 'ta' package not available, some indicators may be unavailable")
    ta = None

warnings.filterwarnings('ignore')

# Import the ProfessionalPCSScanner class by extracting it from the streamlit app
# We'll read the file and execute it in a controlled way
import importlib.util

spec = importlib.util.spec_from_file_location("streamlit_app", "/home/user/nsepcs/streamlit_app.py")
streamlit_app = importlib.util.module_from_spec(spec)
streamlit_app.st = MockStreamlit()
sys.modules['streamlit'] = streamlit_app.st

try:
    spec.loader.exec_module(streamlit_app)
except Exception as e:
    print(f"Note: Some streamlit-specific code skipped: {e}")

# Get the scanner class and stocks list
ProfessionalPCSScanner = streamlit_app.ProfessionalPCSScanner
COMPLETE_NSE_FO_UNIVERSE = streamlit_app.COMPLETE_NSE_FO_UNIVERSE

def run_screener(max_stocks=None, min_pattern_strength=65):
    """
    Run the PCS screener with default filter criteria

    Args:
        max_stocks: Maximum number of stocks to scan (None = all)
        min_pattern_strength: Minimum pattern strength threshold (0-100)

    Returns:
        List of stocks meeting the criteria
    """

    # Default configuration matching the sidebar defaults
    config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': min_pattern_strength,
        'show_news': False,  # Disable news for speed
    }

    # Set up stocks to scan
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    print(f"🚀 Starting scan of {len(stocks_to_scan)} stocks...")
    print(f"Filter criteria: Pattern Strength ≥ {config['pattern_strength_min']}%")
    print(f"RSI: {config['rsi_min']}-{config['rsi_max']}, ADX: ≥{config['adx_min']}")
    print()

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []

    # Scan each stock
    for i, symbol in enumerate(stocks_to_scan):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"[{i+1}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...", end='\r')

        try:
            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Check if RSI is within range
            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                continue

            # Get the strongest pattern
            max_strength = max(p['strength'] for p in patterns)

            # Create result
            stock_result = {
                'symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'pattern_strength': max_strength,
                'pattern_count': len(patterns),
                'main_pattern': max([p for p in patterns], key=lambda x: x['strength'])['type'],
                'confidence': 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            }

            results.append(stock_result)

        except Exception as e:
            continue

    print(" " * 80)  # Clear the line

    # Sort by pattern strength
    results.sort(key=lambda x: x['pattern_strength'], reverse=True)

    print(f"\n✅ Scan complete! Found {len(results)} stocks meeting the criteria.\n")

    return results


def format_results_for_telegram(results, max_results=20):
    """
    Format results for Telegram message

    Args:
        results: List of stock results
        max_results: Maximum number of results to include

    Returns:
        Formatted message string
    """

    if not results:
        return "No stocks found meeting the filter criteria."

    # Limit to top results
    top_results = results[:max_results]

    # Create message
    message = f"📊 NSE F&O PCS Screener Results\n"
    message += f"{'='*40}\n"
    message += f"Stocks Found: {len(results)}\n"
    message += f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"{'='*40}\n\n"

    for i, result in enumerate(top_results, 1):
        message += f"{i}. {result['symbol']}\n"
        message += f"   Price: ₹{result['current_price']:.2f}\n"
        message += f"   Strength: {result['pattern_strength']:.0f}% | Confidence: {result['confidence']}\n"
        message += f"   RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"   Pattern: {result['main_pattern']}\n"
        message += f"   Volume Ratio: {result['volume_ratio']:.1f}x\n\n"

    if len(results) > max_results:
        message += f"\n... and {len(results) - max_results} more stocks"

    return message


if __name__ == "__main__":
    # Run the screener
    results = run_screener(max_stocks=None, min_pattern_strength=65)

    # Display results
    print("Top 10 Stocks:\n")
    for result in results[:10]:
        print(f"{result['symbol']:12} | Strength: {result['pattern_strength']:5.0f}% | "
              f"Price: ₹{result['current_price']:8.2f} | {result['confidence']:6} | "
              f"RSI: {result['rsi']:5.1f} | ADX: {result['adx']:5.1f}")

    # Format for notification
    if results:
        formatted_msg = format_results_for_telegram(results, max_results=10)
        print("\n" + "="*50)
        print("Formatted for Telegram:")
        print("="*50)
        print(formatted_msg)

        # Save results to file for processing
        results_file = "/tmp/screener_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, default=str)
        print(f"\n✅ Results saved to {results_file}")
