#!/usr/bin/env python3
"""
Standalone stock scanner that sends results to Telegram
Extracts the scanning logic from streamlit_app.py and runs it independently
"""

import sys
import os
import json
import requests
from datetime import datetime
import pytz
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Import from streamlit app
from streamlit_app import (
    COMPLETE_NSE_FO_UNIVERSE,
    ProfessionalPCSScanner,
    get_nse_non_fno_stocks
)

def get_default_config():
    """Get default scanner configuration"""
    return {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 65,
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
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': True,
        'export_results': False,
        'stocks_limit': len(COMPLETE_NSE_FO_UNIVERSE),
        'enhancements': {
            'delivery_volume': True,
            'fno_consolidation': True,
            'breakout_pullback': True,
            'enhanced_sr': True
        }
    }

def run_scan(config):
    """Run the scanner with given configuration"""
    scanner = ProfessionalPCSScanner()
    results = []

    total_stocks = len(config['stocks_to_scan'])
    print(f"🚀 Starting scan of {total_stocks} stocks...")

    for i, symbol in enumerate(config['stocks_to_scan']):
        progress = (i + 1) / total_stocks * 100
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"  [{progress:.0f}%] Analyzing {clean_symbol}... ({i+1}/{total_stocks})")

        try:
            # Get data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
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

            # Get news if enabled
            news_data = None
            if config['show_news']:
                try:
                    stock_name = clean_symbol
                    news_data = scanner.get_fundamental_news(symbol, stock_name)
                except:
                    news_data = None

            # Process enhancements
            enhancement_results = {}

            if config.get('enhancements', {}).get('delivery_volume', False):
                try:
                    delivery_analysis = scanner.analyze_delivery_volume_percentage(symbol)
                    enhancement_results['delivery_volume'] = delivery_analysis
                except Exception as e:
                    enhancement_results['delivery_volume'] = {
                        'delivery_percentage': None,
                        'delivery_analysis': f'Error: {str(e)}',
                        'delivery_signals': [],
                        'confidence': 'Low'
                    }

            if config.get('enhancements', {}).get('fno_consolidation', False):
                try:
                    consolidation_analysis = scanner.detect_fno_consolidation_near_resistance(
                        data, symbol, lookback_days=20
                    )
                    enhancement_results['fno_consolidation'] = consolidation_analysis
                except Exception as e:
                    enhancement_results['fno_consolidation'] = {
                        'consolidation_detected': False,
                        'analysis': f'Error: {str(e)}',
                        'signals': []
                    }

            if config.get('enhancements', {}).get('breakout_pullback', False):
                try:
                    breakout_pullback_analysis = scanner.detect_breakout_pullback_strong_green(
                        data, lookback_days=30
                    )
                    enhancement_results['breakout_pullback'] = breakout_pullback_analysis
                except Exception as e:
                    enhancement_results['breakout_pullback'] = {
                        'pattern_detected': False,
                        'analysis': f'Error: {str(e)}',
                        'signals': []
                    }

            if config.get('enhancements', {}).get('enhanced_sr', False):
                try:
                    sr_analysis = scanner.enhanced_support_resistance_analysis(
                        data, lookback_days=50
                    )
                    enhancement_results['enhanced_sr'] = sr_analysis
                except Exception as e:
                    enhancement_results['enhanced_sr'] = {
                        'analysis_available': False,
                        'message': f'Error: {str(e)}',
                        'support_levels': [],
                        'resistance_levels': []
                    }

            # Create stock result
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_details': volume_details,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data,
                'news_data': news_data
            }

            if enhancement_results:
                stock_result['enhancements'] = enhancement_results

            results.append(stock_result)

        except Exception as e:
            continue

    # Sort by pattern strength
    if results:
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    return results

def format_results_for_telegram(results):
    """Format results as a message for Telegram"""
    if not results:
        return "No stocks found meeting the filter criteria."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"🚀 *NSE F&O PCS Scan Results*\n"
    message += f"__{current_time.strftime('%Y-%m-%d %H:%M IST')}__\n\n"

    message += f"📊 *Found {len(results)} stocks*\n\n"

    # Summary metrics
    total_patterns = sum(len(r['patterns']) for r in results)
    avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])
    high_confidence = sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')

    message += f"📈 Total Patterns: {total_patterns}\n"
    message += f"💪 Avg Strength: {avg_strength:.1f}%\n"
    message += f"🏆 High Confidence: {high_confidence}\n\n"

    message += "---\n\n"

    # Stock details
    for i, result in enumerate(results[:20], 1):  # Limit to top 20 for Telegram message size
        clean_symbol = result['symbol'].replace('.NS', '').replace('^', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

        message += f"*{i}. {clean_symbol}*\n"
        message += f"   💰 Price: ₹{result['current_price']:.2f}\n"
        message += f"   📊 Volume: {result['volume_ratio']:.1f}x\n"
        message += f"   📈 RSI: {result['rsi']:.1f}\n"
        message += f"   ⚡ ADX: {result['adx']:.1f}\n"
        message += f"   🎯 Confidence: {confidence} ({max_strength:.0f}%)\n"
        message += f"   📋 Patterns: {len(result['patterns'])}\n"
        message += "\n"

    if len(results) > 20:
        message += f"_... and {len(results) - 20} more stocks_\n\n"

    message += "---\n"
    message += f"📌 Full results saved to results.json\n"
    message += "#NSE #FO #Scanner #TechnicalAnalysis"

    return message

def save_results_to_file(results, filename='scan_results.json'):
    """Save detailed results to JSON file"""
    if not results:
        return

    # Prepare data for JSON serialization
    json_results = []
    for result in results:
        # Convert data DataFrame to dict
        data_dict = result['data'].to_dict() if hasattr(result['data'], 'to_dict') else {}

        json_results.append({
            'symbol': result['symbol'],
            'current_price': float(result['current_price']),
            'volume_ratio': float(result['volume_ratio']),
            'rsi': float(result['rsi']),
            'adx': float(result['adx']),
            'patterns': [
                {
                    'type': p['type'],
                    'strength': float(p['strength']),
                    'confidence': p['confidence'],
                    'description': p.get('description', '')
                }
                for p in result['patterns']
            ],
            'enhancements': result.get('enhancements', {}),
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
        })

    with open(filename, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)

    print(f"✅ Detailed results saved to {filename}")

def send_to_telegram(message):
    """Send message to Telegram"""
    # Get credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not found in environment variables")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to send messages")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("NSE F&O PCS Scanner - Standalone Mode")
    print("=" * 60)
    print()

    # Get configuration
    config = get_default_config()
    print(f"📋 Configuration:")
    print(f"   Stocks to scan: {len(config['stocks_to_scan'])}")
    print(f"   RSI Range: {config['rsi_min']}-{config['rsi_max']}")
    print(f"   Min ADX: {config['adx_min']}")
    print(f"   Min Volume Ratio: {config['min_volume_ratio']}")
    print()

    # Run scan
    results = run_scan(config)

    print()
    print("=" * 60)
    print(f"✅ Scan Complete: Found {len(results)} stocks")
    print("=" * 60)
    print()

    if results:
        # Save detailed results
        save_results_to_file(results)

        # Format message
        message = format_results_for_telegram(results)

        # Print preview
        print("📱 Message preview (first 500 chars):")
        print(message[:500])
        print()

        # Send to Telegram
        send_to_telegram(message)

        # Also save message to file
        with open('telegram_message.txt', 'w') as f:
            f.write(message)
        print("💾 Message saved to telegram_message.txt")

    else:
        print("❌ No stocks found meeting the filter criteria")

if __name__ == '__main__':
    main()
