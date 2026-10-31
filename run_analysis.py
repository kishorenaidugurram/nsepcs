#!/usr/bin/env python3
"""
Standalone analysis script for NSE F&O PCS screening
Runs analysis and saves results
"""

import sys
import os
sys.path.insert(0, '/home/user/nsepcs')

# Import from streamlit_app
from streamlit_app import (
    COMPLETE_NSE_FO_UNIVERSE,
    ProfessionalPCSScanner
)

import json
from datetime import datetime
import requests

def run_analysis():
    """Run the PCS analysis with default settings"""

    # Default filter settings (from sidebar defaults)
    config = {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:20],  # Test with first 20 stocks
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'show_news': False,
        'enhancements': {}
    }

    # Pattern filters
    pattern_filters = {
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
    }
    config['pattern_filters'] = pattern_filters
    config['analysis_mode'] = 'Daily Only (V6.0 Style)'
    config['pattern_priority'] = 'All Patterns (Comprehensive)'

    scanner = ProfessionalPCSScanner()
    results = []

    print(f"Starting analysis of {len(config['stocks_to_scan'])} stocks...")
    print(f"Time: {datetime.now().isoformat()}")

    for i, symbol in enumerate(config['stocks_to_scan']):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"[{i+1}/{len(config['stocks_to_scan'])}] Analyzing {clean_symbol}...", end=' ', flush=True)

        try:
            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                print("❌ No data")
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                print("❌ Volume filter")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                print("❌ No patterns")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            stock_result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': float(current_price),
                'rsi': float(current_rsi),
                'adx': float(current_adx),
                'volume_ratio': float(volume_ratio),
                'patterns': [
                    {
                        'type': p['type'],
                        'strength': float(p['strength']),
                        'confidence': p['confidence']
                    }
                    for p in patterns
                ]
            }

            results.append(stock_result)
            print(f"✅ {len(patterns)} patterns")

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            continue

    # Sort by pattern strength
    if results:
        for r in results:
            r['max_pattern_strength'] = max([p['strength'] for p in r['patterns']], default=0)
        results.sort(key=lambda x: x['max_pattern_strength'], reverse=True)

    print(f"\n{'='*60}")
    print(f"Analysis Complete - {len(results)} stocks found with patterns")
    print(f"{'='*60}\n")

    return results, config

def format_results_for_telegram(results, config):
    """Format results as Telegram message"""

    if not results:
        return "❌ No stocks found matching filter criteria."

    message = "📊 NSE F&O PCS Analysis Results\n"
    message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    message += f"✅ Found {len(results)} stocks with patterns\n\n"

    for idx, stock in enumerate(results[:20], 1):  # Top 20
        max_strength = stock['max_pattern_strength']
        symbol = stock['clean_symbol']
        price = stock['current_price']
        rsi = stock['rsi']
        pattern_count = len(stock['patterns'])
        confidence_list = [p['confidence'] for p in stock['patterns']]
        high_conf = confidence_list.count('HIGH')

        message += f"{idx}. {symbol}\n"
        message += f"   Price: ₹{price:.2f} | RSI: {rsi:.1f} | Strength: {max_strength:.1f}%\n"
        message += f"   Patterns: {pattern_count} (HIGH: {high_conf})\n"
        message += "\n"

    return message

def save_results_to_file(results, config):
    """Save results to JSON file"""

    output_file = f"/home/user/nsepcs/analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_data = {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'stocks_scanned': len(config['stocks_to_scan']),
            'rsi_range': [config['rsi_min'], config['rsi_max']],
            'adx_min': config['adx_min'],
            'min_volume_ratio': config['min_volume_ratio']
        },
        'results': results,
        'summary': {
            'total_stocks_found': len(results),
            'high_confidence_count': sum(
                1 for r in results
                for p in r['patterns']
                if p['confidence'] == 'HIGH'
            )
        }
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to: {output_file}")
    return output_file

def send_to_telegram(message, token=None, chat_id=None):
    """Send message to Telegram if credentials are available"""

    if not token or not chat_id:
        print("\n⚠️  Telegram credentials not configured")
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

if __name__ == "__main__":
    print("🚀 NSE F&O PCS Analysis - Standalone Script\n")

    # Run analysis
    results, config = run_analysis()

    # Format for output
    formatted_message = format_results_for_telegram(results, config)
    print(formatted_message)

    # Save to file
    results_file = save_results_to_file(results, config)

    # Try to send to Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if telegram_token and telegram_chat_id:
        print("\n📱 Attempting to send to Telegram...")
        send_to_telegram(formatted_message, telegram_token, telegram_chat_id)
    else:
        print("\n📝 To send results to Telegram, set these environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        print(f"\n📄 Results saved to: {results_file}")
