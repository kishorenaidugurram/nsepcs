#!/usr/bin/env python3
"""
NSE F&O Stock Analyzer - Non-Streamlit version
Runs the stock analysis and sends results to Telegram
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Import the scanner class
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    STOCK_CATEGORIES
)

# ============ TELEGRAM CONFIGURATION ============
def get_telegram_credentials():
    """Get Telegram bot token and chat ID from environment or config"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("WARNING: Telegram credentials not found in environment variables")
        print("  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable Telegram notifications")
        return None, None

    return token, chat_id


def send_to_telegram(message, token, chat_id, parse_mode='HTML'):
    """Send message to Telegram"""
    if not token or not chat_id:
        print("Telegram not configured, skipping notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Break message into chunks if too long (Telegram limit is 4096 chars)
    max_length = 4096
    if len(message) > max_length:
        messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    else:
        messages = [message]

    for msg in messages:
        try:
            payload = {
                'chat_id': chat_id,
                'text': msg,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Telegram send failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
            return False

    return True


# ============ ANALYSIS CONFIGURATION ============
class AnalysisConfig:
    """Default analysis configuration for automated runs"""
    def __init__(self):
        self.min_volume_ratio = 1.5
        self.min_pattern_strength = 70  # Minimum strength for patterns
        self.lookback_days = 20
        self.volume_breakout_ratio = 2.0
        self.enable_weekly_validation = True
        self.min_rsi = 30
        self.max_rsi = 80
        self.min_adx = 15
        self.ma_support = True
        self.ma_tolerance = 5

        # Filter for more qualified stocks
        self.focus_on_current_day_breakouts = True  # Prioritize recent breakouts

    def to_dict(self):
        """Convert to dictionary for scanner"""
        return {
            'stocks_to_scan': [],  # Will be set during analysis
            'min_volume_ratio': self.min_volume_ratio,
            'lookback_days': self.lookback_days,
            'volume_breakout_ratio': self.volume_breakout_ratio,
            'rsi_min': self.min_rsi,
            'rsi_max': self.max_rsi,
            'adx_min': self.min_adx,
            'ma_support': self.ma_support,
            'ma_tolerance': self.ma_tolerance,
            'pattern_strength_min': self.min_pattern_strength,
            'enable_weekly_validation': self.enable_weekly_validation,
            'show_news': False,
            'pattern_filters': {
                'current_day_breakout': True,
                'cup_and_handle': True,
                'double_bottom': True,
                'rectangle_bottom': True,
                'flat_base': True,
                'head_and_shoulders': True
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enhancements': {}
        }


def analyze_stocks(scanner, config_dict, stock_list):
    """Analyze a list of stocks and return results"""
    config_dict['stocks_to_scan'] = stock_list
    results = []

    print(f"Analyzing {len(stock_list)} stocks...")

    for idx, symbol in enumerate(stock_list, 1):
        try:
            print(f"  [{idx}/{len(stock_list)}] Analyzing {symbol.replace('.NS', '')}", end='\r')

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                config_dict['min_volume_ratio']
            )
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config_dict)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_high = data['High'].iloc[-1]
            current_low = data['Low'].iloc[-1]

            # Get weekly data for validation
            weekly_data = scanner.get_weekly_stock_data(symbol, period="6mo")

            # Process patterns and calculate best strength
            max_strength = max(p['strength'] for p in patterns) if patterns else 0

            if max_strength >= config_dict['pattern_strength_min']:
                stock_result = {
                    'symbol': symbol,
                    'clean_symbol': symbol.replace('.NS', '').replace('^', ''),
                    'current_price': current_price,
                    'current_high': current_high,
                    'current_low': current_low,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'max_strength': max_strength,
                    'patterns': patterns,
                    'pattern_types': [p['type'] for p in patterns],
                    'has_current_day_breakout': any('Current Day' in p['type'] for p in patterns),
                    'weekly_validation': weekly_data is not None
                }
                results.append(stock_result)

        except Exception as e:
            continue

    print(f"\n✓ Analyzed {len(stock_list)} stocks, found {len(results)} matches")
    return results


def filter_results(results, min_strength=70, priority='current_day_breakouts'):
    """Filter and sort results based on criteria"""
    filtered = [r for r in results if r['max_strength'] >= min_strength]

    if priority == 'current_day_breakouts':
        # Sort: Current day breakouts first, then by strength
        filtered.sort(key=lambda x: (not x['has_current_day_breakout'], -x['max_strength']))
    else:
        filtered.sort(key=lambda x: -x['max_strength'])

    return filtered


def format_telegram_message(results, min_stocks=3):
    """Format results for Telegram message"""
    if not results:
        return "❌ No stocks found meeting the criteria today."

    # Group by pattern type
    current_day_stocks = [r for r in results if r['has_current_day_breakout']]
    other_stocks = [r for r in results if not r['has_current_day_breakout']]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M IST")

    message = f"""
<b>🎯 NSE F&O Stock Screener Results</b>
<i>{timestamp}</i>

<b>📊 Summary:</b>
• Total qualified: {len(results)}
• Current Day Breakouts: {len(current_day_stocks)}
• Other Patterns: {len(other_stocks)}

"""

    # Current day breakouts
    if current_day_stocks:
        message += "<b>🔥 CURRENT DAY BREAKOUTS (High Confidence):</b>\n"
        for i, stock in enumerate(current_day_stocks[:10], 1):  # Top 10
            patterns_str = ", ".join(set(stock['pattern_types']))
            message += f"{i}. <b>{stock['clean_symbol']}</b> - ₹{stock['current_price']:.2f} | Strength: {stock['max_strength']:.0f}% | RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
        message += "\n"

    # Other patterns
    if other_stocks:
        message += "<b>📈 OTHER PATTERNS (Medium Confidence):</b>\n"
        for i, stock in enumerate(other_stocks[:10], 1):  # Top 10
            patterns_str = ", ".join(set(stock['pattern_types']))
            message += f"{i}. <b>{stock['clean_symbol']}</b> - ₹{stock['current_price']:.2f} | Strength: {stock['max_strength']:.0f}% | RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"

    # Export list as plain text
    message += "\n<b>📋 Stock Symbols for Quick Access:</b>\n<code>"
    all_symbols = [r['clean_symbol'] for r in results[:20]]
    message += ", ".join(all_symbols)
    message += "</code>"

    message += "\n\n<i>Scan completed successfully</i>"

    return message


def main():
    """Main analysis function"""
    print("=" * 60)
    print("NSE F&O Stock Analyzer - Telegram Integration")
    print("=" * 60)

    # Get Telegram credentials
    telegram_token, telegram_chat_id = get_telegram_credentials()

    # Initialize scanner and config
    scanner = ProfessionalPCSScanner()
    config = AnalysisConfig()
    config_dict = config.to_dict()

    # Select stocks to scan (top liquid ones)
    stocks_to_scan = STOCK_CATEGORIES['Nifty 50'][:30] + STOCK_CATEGORIES['Bank Nifty'][:10]
    stocks_to_scan = list(dict.fromkeys(stocks_to_scan))  # Remove duplicates

    print(f"\n📈 Starting analysis of {len(stocks_to_scan)} liquid stocks...\n")

    # Run analysis
    results = analyze_stocks(scanner, config_dict, stocks_to_scan)

    # Filter results
    filtered_results = filter_results(results, min_strength=70, priority='current_day_breakouts')

    print(f"\n✓ Found {len(filtered_results)} stocks meeting criteria")

    # Format and send Telegram message
    message = format_telegram_message(filtered_results)

    print("\n" + "=" * 60)
    print("MESSAGE PREVIEW:")
    print("=" * 60)
    # Show message without HTML tags in console
    preview = message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<code>', '').replace('</code>', '')
    print(preview)
    print("=" * 60)

    if telegram_token and telegram_chat_id:
        print("\n📤 Sending to Telegram...")
        if send_to_telegram(message, telegram_token, telegram_chat_id, parse_mode='HTML'):
            print("✅ Message sent successfully to Telegram!")
        else:
            print("❌ Failed to send message to Telegram")
    else:
        print("\n⚠️  Telegram credentials not configured")
        print("   To enable, set environment variables:")
        print("   - TELEGRAM_BOT_TOKEN")
        print("   - TELEGRAM_CHAT_ID")

    # Save results to CSV for reference
    if filtered_results:
        df = pd.DataFrame(filtered_results)
        csv_file = f"/tmp/nse_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n💾 Results saved to: {csv_file}")

    print("\n✓ Analysis complete!")


if __name__ == "__main__":
    main()
