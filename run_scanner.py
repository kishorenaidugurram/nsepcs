#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Standalone Script
Runs the PCS analysis and sends results to Telegram
"""

import sys
import os
import json
import argparse
from datetime import datetime
import pytz
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup IST timezone
ist = pytz.timezone('Asia/Kolkata')

def create_default_config():
    """Create default filter configuration"""
    return {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:50],  # Start with top 50 for speed
        'rsi_min': 35,
        'rsi_max': 75,
        'adx_min': 18,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.0,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 65,
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
            'inverted_scallop': True,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': True,
        'export_results': True,
        'stocks_limit': 50,
        'enhancements': {
            'delivery_volume': False,
            'fno_consolidation': False,
            'breakout_pullback': False,
            'enhanced_sr': False,
        }
    }

def send_to_telegram(results, telegram_token=None, telegram_chat_id=None):
    """Send results to Telegram"""
    if not telegram_token or not telegram_chat_id:
        logger.info("Telegram credentials not provided. Skipping Telegram notification.")
        return False

    try:
        import requests

        # Format message
        message = f"🎯 NSE F&O PCS Scanner Results\n"
        message += f"📅 {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
        message += f"✅ Found {len(results)} stocks meeting filter criteria\n\n"

        # Add top stocks
        message += "📋 Top Stocks:\n"
        for i, result in enumerate(results[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            price = result['current_price']
            message += f"{i}. {symbol} - {confidence} ({max_strength:.0f}%) @ ₹{price:.2f}\n"

        if len(results) > 10:
            message += f"\n... and {len(results) - 10} more stocks"

        # Send to Telegram
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            logger.info(f"✅ Results sent to Telegram successfully!")
            return True
        else:
            logger.error(f"❌ Failed to send Telegram message: {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Error sending to Telegram: {str(e)}")
        return False

def save_results_to_file(results, output_file):
    """Save results to JSON and CSV files"""
    try:
        # Prepare data for export
        export_data = []

        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            pattern_types = ', '.join([p['type'] for p in result['patterns']])

            export_data.append({
                'Symbol': result['symbol'].replace('.NS', ''),
                'Current Price': f"₹{result['current_price']:.2f}",
                'Confidence': overall_confidence,
                'Max Strength': f"{max_strength:.1f}%",
                'Volume Ratio': f"{result['volume_ratio']:.2f}x",
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Patterns': pattern_types,
                'Number of Patterns': len(result['patterns'])
            })

        # Save to CSV
        df = pd.DataFrame(export_data)
        csv_file = output_file.replace('.json', '.csv')
        df.to_csv(csv_file, index=False)
        logger.info(f"✅ Results saved to {csv_file}")

        # Save to JSON (raw data)
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(ist).isoformat(),
                'total_stocks_found': len(results),
                'results': export_data
            }, f, indent=2)
        logger.info(f"✅ Results saved to {output_file}")

    except Exception as e:
        logger.error(f"❌ Error saving results: {str(e)}")

def run_scan(num_stocks=50, telegram_token=None, telegram_chat_id=None, output_dir='/tmp/claude-0'):
    """Run the main scanner"""
    logger.info("=" * 60)
    logger.info("🚀 NSE F&O PCS Scanner - Starting Analysis")
    logger.info("=" * 60)

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Create config
    config = create_default_config()
    config['stocks_limit'] = min(num_stocks, len(COMPLETE_NSE_FO_UNIVERSE))
    config['stocks_to_scan'] = COMPLETE_NSE_FO_UNIVERSE[:config['stocks_limit']]

    logger.info(f"📊 Scanning {len(config['stocks_to_scan'])} stocks...")
    logger.info(f"⚙️  Filter Settings:")
    logger.info(f"   - RSI Range: {config['rsi_min']}-{config['rsi_max']}")
    logger.info(f"   - ADX Min: {config['adx_min']}")
    logger.info(f"   - Pattern Strength Min: {config['pattern_strength_min']}%")
    logger.info(f"   - Min Volume Ratio: {config['min_volume_ratio']}x")

    results = []

    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            logger.info(f"[{i}/{len(config['stocks_to_scan'])}] Analyzing {clean_symbol}...")

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                logger.debug(f"   ⚠️  Insufficient data for {clean_symbol}")
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                config['min_volume_ratio']
            )
            if not volume_ok:
                logger.debug(f"   ⚠️  Volume criteria not met for {clean_symbol}")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                logger.debug(f"   ⚠️  No patterns detected for {clean_symbol}")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Store result
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_details': volume_details,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data,
            }

            results.append(stock_result)
            max_strength = max(p['strength'] for p in patterns)
            logger.info(f"   ✅ Found {len(patterns)} pattern(s) - Max Strength: {max_strength:.0f}%")

        except Exception as e:
            logger.debug(f"   ❌ Error analyzing {clean_symbol}: {str(e)}")
            continue

    # Sort by pattern strength
    if results:
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    logger.info("=" * 60)
    logger.info(f"🎉 Scan Complete!")
    logger.info(f"📈 Found {len(results)} stocks meeting filter criteria")
    logger.info("=" * 60)

    # Display top results
    if results:
        logger.info("\n📋 Top 10 Results:")
        for i, result in enumerate(results[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            price = result['current_price']
            patterns_text = ', '.join([p['type'] for p in result['patterns'][:2]])
            logger.info(f"{i}. {symbol:12s} | {confidence:6s} ({max_strength:5.0f}%) | ₹{price:8.2f} | {patterns_text}")

    # Save results
    output_file = os.path.join(output_dir, 'scanner_results.json')
    os.makedirs(output_dir, exist_ok=True)
    save_results_to_file(results, output_file)

    # Send to Telegram
    if results and (telegram_token and telegram_chat_id):
        send_to_telegram(results, telegram_token, telegram_chat_id)
    elif results:
        logger.info("ℹ️  To send results to Telegram, set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID env vars")

    return results

def main():
    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner - Standalone Mode')
    parser.add_argument('--stocks', type=int, default=50, help='Number of stocks to scan (default: 50)')
    parser.add_argument('--telegram-token', type=str, help='Telegram bot token')
    parser.add_argument('--telegram-chat-id', type=str, help='Telegram chat ID')
    parser.add_argument('--output-dir', type=str, default='/tmp/claude-0', help='Output directory for results')

    args = parser.parse_args()

    # Check for environment variables
    telegram_token = args.telegram_token or os.environ.get('TELEGRAM_TOKEN')
    telegram_chat_id = args.telegram_chat_id or os.environ.get('TELEGRAM_CHAT_ID')

    # Run scan
    results = run_scan(
        num_stocks=args.stocks,
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
        output_dir=args.output_dir
    )

    return 0 if results else 1

if __name__ == "__main__":
    sys.exit(main())
