#!/usr/bin/env python3
"""
NSE F&O PCS Scanner CLI - Standalone version for scheduled runs
Extracts and runs the core scanner logic without Streamlit
Sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import warnings
warnings.filterwarnings('ignore')

# Import scanner class from streamlit app
# We'll extract the essential parts here to avoid Streamlit dependency
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    STOCK_CATEGORIES
)

def send_to_telegram(message: str, bot_token: str = None, chat_id: str = None) -> bool:
    """
    Send message to Telegram

    Args:
        message: Message text to send
        bot_token: Telegram bot token (from env if not provided)
        chat_id: Telegram chat ID (from env if not provided)

    Returns:
        True if sent successfully, False otherwise
    """
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not found in environment variables")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable notifications")
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
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {str(e)}")
        return False

def run_scan(
    stocks_to_scan=None,
    min_volume_ratio=1.2,
    min_pattern_strength=65,
    categories=None,
    rsi_min=30,
    rsi_max=75,
    adx_min=20,
    ma_support=True,
    ma_type='EMA',
    ma_tolerance=3,
    volume_breakout_ratio=2.0,
    lookback_days=20
):
    """
    Run the PCS scanner on specified stocks

    Args:
        stocks_to_scan: List of stock symbols (uses Nifty 50 if None)
        min_volume_ratio: Minimum volume ratio threshold
        min_pattern_strength: Minimum pattern strength threshold
        categories: Stock categories to scan (uses Nifty 50 if None)
        rsi_min: Minimum RSI value
        rsi_max: Maximum RSI value
        adx_min: Minimum ADX value
        ma_support: Whether to check MA support
        ma_type: Type of moving average (EMA or SMA)
        ma_tolerance: MA tolerance percentage
        volume_breakout_ratio: Volume ratio for breakout confirmation
        lookback_days: Number of days to look back for patterns

    Returns:
        Tuple of (List of qualifying stocks, Summary dict)
    """

    print("🚀 Starting PCS Scanner CLI...")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Determine stocks to scan
    if stocks_to_scan is None:
        if categories:
            stocks_to_scan = []
            for cat in categories:
                if cat in STOCK_CATEGORIES:
                    stocks_to_scan.extend(STOCK_CATEGORIES[cat])
            stocks_to_scan = list(set(stocks_to_scan))  # Remove duplicates
        else:
            # Use Nifty 50 by default for faster results
            stocks_to_scan = STOCK_CATEGORIES.get('Nifty 50', COMPLETE_NSE_FO_UNIVERSE[:50])

    print(f"📊 Scanning {len(stocks_to_scan)} stocks...")
    print(f"📈 Filters: RSI {rsi_min}-{rsi_max}, ADX>{adx_min}, Volume>{min_volume_ratio}x, Strength>{min_pattern_strength}%")

    qualifying_stocks = []
    results_summary = {
        'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_scanned': len(stocks_to_scan),
        'qualifying_stocks': [],
        'stats': {
            'high_confidence': 0,
            'medium_confidence': 0,
            'current_day_breakouts': 0
        }
    }

    # Build filter dictionary for detect_patterns
    filters = {
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'adx_min': adx_min,
        'ma_support': ma_support,
        'ma_type': ma_type,
        'ma_tolerance': ma_tolerance,
        'min_volume_ratio': min_volume_ratio,
        'volume_breakout_ratio': volume_breakout_ratio,
        'lookback_days': lookback_days,
        'pattern_strength_min': min_pattern_strength,
        'pattern_filters': {
            'current_day_breakout': True,
            'cup_and_handle': True,
            'flat_base': True,
            'bump_and_run': True,
            'rectangle_bottom': True,
            'rectangle_top': True,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': True,
            'inverted_scallop': True,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True
    }

    for i, symbol in enumerate(stocks_to_scan):
        try:
            clean_symbol = symbol.replace('.NS', '')
            print(f"  [{i+1}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...", end='\r')

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 30:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, min_volume_ratio)
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)

            if not patterns:
                continue

            # Calculate metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            max_strength = max(p['strength'] for p in patterns)
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            has_current_breakout = any('Current Day' in p['type'] for p in patterns)

            stock_data = {
                'symbol': clean_symbol,
                'price': f"₹{current_price:.2f}",
                'volume_ratio': f"{volume_ratio:.2f}x",
                'rsi': f"{current_rsi:.1f}",
                'adx': f"{current_adx:.1f}",
                'strength': f"{max_strength:.0f}%",
                'confidence': confidence,
                'has_breakout': has_current_breakout,
                'patterns': [p['type'] for p in patterns]
            }

            qualifying_stocks.append(stock_data)
            results_summary['qualifying_stocks'].append(stock_data)

            # Update stats
            if confidence == 'HIGH':
                results_summary['stats']['high_confidence'] += 1
            elif confidence == 'MEDIUM':
                results_summary['stats']['medium_confidence'] += 1

            if has_current_breakout:
                results_summary['stats']['current_day_breakouts'] += 1

        except Exception as e:
            continue

    print(f"\n✅ Scan complete! Found {len(qualifying_stocks)} qualifying stocks")

    # Sort by confidence and strength
    qualifying_stocks.sort(
        key=lambda x: (
            {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(x['confidence'], 0),
            float(x['strength'].rstrip('%'))
        ),
        reverse=True
    )

    results_summary['qualifying_stocks'] = qualifying_stocks
    return qualifying_stocks, results_summary

def format_telegram_message(stocks, summary):
    """
    Format scan results for Telegram

    Args:
        stocks: List of qualifying stocks
        summary: Summary statistics

    Returns:
        Formatted HTML message for Telegram
    """

    message = "<b>📊 NSE F&O PCS Scanner Results</b>\n"
    message += f"<i>{summary['scan_date']}</i>\n"
    message += "━" * 40 + "\n\n"

    # Summary stats
    message += f"<b>📈 Summary:</b>\n"
    message += f"  • Total Scanned: <code>{summary['total_scanned']}</code>\n"
    message += f"  • Qualifying: <code>{len(stocks)}</code>\n"
    message += f"  • High Confidence: <code>{summary['stats']['high_confidence']}</code>\n"
    message += f"  • Medium Confidence: <code>{summary['stats']['medium_confidence']}</code>\n"
    message += f"  • Current Day Breakouts: <code>{summary['stats']['current_day_breakouts']}</code>\n\n"

    if not stocks:
        message += "<i>No stocks met the filter criteria today.</i>\n"
        return message

    # Stocks list
    message += "<b>🎯 Qualifying Stocks:</b>\n"
    message += "━" * 40 + "\n"

    for i, stock in enumerate(stocks[:10], 1):  # Limit to first 10 for message size
        breakout_emoji = "🔥" if stock['has_breakout'] else ""
        confidence_emoji = "🟢" if stock['confidence'] == 'HIGH' else "🟡" if stock['confidence'] == 'MEDIUM' else "🔴"

        message += f"\n<b>{i}. {stock['symbol']} {breakout_emoji}</b> {confidence_emoji}\n"
        message += f"  Price: {stock['price']}\n"
        message += f"  Strength: {stock['strength']} | RSI: {stock['rsi']} | ADX: {stock['adx']}\n"
        message += f"  Volume: {stock['volume_ratio']} | Confidence: {stock['confidence']}\n"

    if len(stocks) > 10:
        message += f"\n<i>... and {len(stocks) - 10} more stocks</i>\n"

    message += "\n━" * 40 + "\n"
    message += "<i>⚠️ This is not financial advice. Always do your own research.</i>"

    return message

def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='NSE F&O PCS Scanner - CLI Version'
    )
    parser.add_argument(
        '--categories',
        nargs='+',
        default=['Nifty 50'],
        help='Stock categories to scan (default: Nifty 50)'
    )
    parser.add_argument(
        '--min-volume',
        type=float,
        default=1.0,
        help='Minimum volume ratio (default: 1.0)'
    )
    parser.add_argument(
        '--min-strength',
        type=float,
        default=70,
        help='Minimum pattern strength % (default: 70)'
    )
    parser.add_argument(
        '--no-telegram',
        action='store_true',
        help='Skip Telegram notification'
    )
    parser.add_argument(
        '--bot-token',
        help='Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)'
    )
    parser.add_argument(
        '--chat-id',
        help='Telegram chat ID (or set TELEGRAM_CHAT_ID env var)'
    )

    args = parser.parse_args()

    # Run scan
    stocks, summary = run_scan(
        min_volume_ratio=args.min_volume,
        min_pattern_strength=args.min_strength,
        categories=args.categories
    )

    # Print results to console
    print("\n" + "="*50)
    print("SCAN RESULTS")
    print("="*50)
    print(json.dumps(summary, indent=2))

    # Save results to file
    results_file = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")

    # Send to Telegram if enabled
    if not args.no_telegram:
        message = format_telegram_message(stocks, summary)
        if send_to_telegram(message, args.bot_token, args.chat_id):
            print("✅ Telegram notification sent successfully!")
        else:
            print("⚠️  Telegram notification not configured or failed")

    return 0 if stocks else 1

if __name__ == '__main__':
    sys.exit(main())
