#!/usr/bin/env python3
"""
Standalone PCS Scanner Script
Runs the NSE F&O PCS analysis and sends qualifying stocks to Telegram
"""

import sys
import os
import json
import asyncio
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Import Telegram bot
from telegram import Bot
from telegram.error import TelegramError

# Import scanner from streamlit app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE, STOCK_CATEGORIES

# Configuration - Load from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Default filter criteria
DEFAULT_FILTERS = {
    'rsi_min': 30,
    'rsi_max': 80,
    'adx_min': 15,
    'ma_support': True,
    'ma_type': 'SMA',
    'ma_tolerance': 2.0,
    'pattern_strength_min': 50,  # Minimum pattern strength
    'lookback_days': 20,
    'volume_breakout_ratio': 1.5,
    'analysis_mode': 'Daily + Weekly Combined (Recommended)',
    'enable_daily_analysis': True,
    'enable_weekly_validation': True,
    'pattern_filters': {
        'current_day_breakout': True,
        'cup_and_handle': True,
        'flat_base': True,
        'bump_and_run': True,
        'rectangle_bottom': True,
        'rectangle_top': False,
        'head_shoulders_bottom': True,
        'double_bottom': True,
        'three_rising_valleys': True,
        'rounding_bottom': True,
        'rounding_top_upside': False,
        'inverted_scallop': True
    }
}

def run_scanner(stocks=None, filters=None, max_stocks=50):
    """
    Run the PCS scanner on specified stocks

    Args:
        stocks: List of stock symbols (if None, uses top F&O stocks)
        filters: Filter configuration dictionary
        max_stocks: Maximum number of stocks to analyze

    Returns:
        List of qualifying stocks with their details
    """

    if filters is None:
        filters = DEFAULT_FILTERS

    # Use Nifty 50 stocks if no stocks specified
    if stocks is None:
        stocks = STOCK_CATEGORIES.get('Nifty 50', COMPLETE_NSE_FO_UNIVERSE[:50])

    # Limit to max_stocks
    stocks = stocks[:max_stocks]

    scanner = ProfessionalPCSScanner()
    qualifying_stocks = []

    print(f"🚀 Starting PCS Scanner Analysis")
    print(f"📊 Analyzing {len(stocks)} stocks")
    print(f"⚙️  Minimum Pattern Strength: {filters['pattern_strength_min']}")
    print(f"📈 Filter: RSI {filters['rsi_min']}-{filters['rsi_max']}, ADX > {filters['adx_min']}")
    print(f"{'='*60}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}

        for symbol in stocks:
            future = executor.submit(analyze_stock, scanner, symbol, filters)
            futures[future] = symbol

        completed = 0
        for future in as_completed(futures):
            completed += 1
            symbol = futures[future]
            try:
                result = future.result()
                if result is not None:
                    qualifying_stocks.append(result)
                    print(f"✅ {symbol}: {result['patterns']}")
                else:
                    print(f"⏭️  {symbol}: No patterns detected")
            except Exception as e:
                print(f"❌ {symbol}: Error - {str(e)}")

            # Print progress
            if completed % 5 == 0:
                print(f"   Progress: {completed}/{len(stocks)} analyzed")

    # Sort by pattern strength
    qualifying_stocks.sort(key=lambda x: x['best_strength'], reverse=True)

    print(f"{'='*60}")
    print(f"✅ Scan Complete: {len(qualifying_stocks)} stocks meet criteria")

    return qualifying_stocks

def analyze_stock(scanner, symbol, filters):
    """
    Analyze a single stock for patterns

    Returns:
        Dictionary with stock info and patterns, or None if no patterns
    """
    try:
        # Fetch stock data
        data = scanner.get_stock_data(symbol, period="3mo")
        if data is None or len(data) < 20:
            return None

        # Fetch weekly data for validation
        weekly_data = scanner.get_weekly_stock_data(symbol, period="6mo")

        # Detect patterns
        patterns = scanner.detect_patterns(data, symbol, filters)

        if patterns:
            # Get best pattern and strength
            best_pattern = patterns[0]  # First pattern is usually strongest

            return {
                'symbol': symbol,
                'patterns': best_pattern['type'],
                'best_strength': best_pattern.get('strength', 0),
                'current_price': data['Close'].iloc[-1],
                'current_rsi': data['RSI'].iloc[-1],
                'current_adx': data['ADX'].iloc[-1],
                'pattern_details': best_pattern
            }
    except Exception as e:
        return None

    return None

async def send_results_to_telegram(results):
    """
    Send scan results to Telegram

    Args:
        results: List of qualifying stocks
    """

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        save_results_to_file(results)
        return

    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)

        # Create message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not results:
            message = f"🔍 PCS Scanner Results - {timestamp}\n\n"
            message += "❌ No stocks meet the current filter criteria.\n"
            message += f"Total analyzed: Check logs for details."
        else:
            message = f"✅ PCS Scanner Results - {timestamp}\n\n"
            message += f"📊 Found {len(results)} qualifying stocks:\n\n"

            # Add top 10 results
            for i, stock in enumerate(results[:10], 1):
                message += f"{i}. {stock['symbol']}\n"
                message += f"   Pattern: {stock['patterns']}\n"
                message += f"   Strength: {stock['best_strength']:.0f}/100\n"
                message += f"   Price: ₹{stock['current_price']:.2f}\n"
                message += f"   RSI: {stock['current_rsi']:.1f}, ADX: {stock['current_adx']:.1f}\n\n"

            if len(results) > 10:
                message += f"... and {len(results) - 10} more stocks\n"

            message += f"\n📋 Full results saved and available in scan logs."

        # Send message
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )

        print(f"✅ Results sent to Telegram!")

    except TelegramError as e:
        print(f"❌ Telegram Error: {e}")
        print("   Saving results to file instead...")
        save_results_to_file(results)
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        save_results_to_file(results)

def save_results_to_file(results):
    """
    Save results to a JSON file

    Args:
        results: List of qualifying stocks
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_results_{timestamp}.json"

    # Convert to JSON-serializable format
    data = {
        'timestamp': datetime.now().isoformat(),
        'total_stocks': len(results),
        'stocks': [
            {
                'symbol': stock['symbol'],
                'pattern': stock['patterns'],
                'strength': float(stock['best_strength']),
                'price': float(stock['current_price']),
                'rsi': float(stock['current_rsi']),
                'adx': float(stock['current_adx'])
            }
            for stock in results
        ]
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"📁 Results saved to: {filename}")

def main():
    """
    Main execution function
    """
    print("\n" + "="*60)
    print("🎯 NSE F&O PCS Scanner - Automated Run")
    print("="*60 + "\n")

    # Run scanner
    results = run_scanner(
        stocks=STOCK_CATEGORIES.get('Nifty 50'),  # Use Nifty 50 stocks
        filters=DEFAULT_FILTERS,
        max_stocks=50
    )

    print(f"\n📊 Summary:")
    print(f"   Total Stocks Analyzed: 50 (Nifty 50)")
    print(f"   Stocks Meeting Criteria: {len(results)}")

    if results:
        print(f"\n🏆 Top 5 Results:")
        for i, stock in enumerate(results[:5], 1):
            print(f"   {i}. {stock['symbol']} - {stock['patterns']} (Strength: {stock['best_strength']:.0f}/100)")

    # Send results
    print(f"\n📤 Sending results...")
    asyncio.run(send_results_to_telegram(results))

    print("\n" + "="*60)
    print("✅ Scan Complete")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
