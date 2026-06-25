#!/usr/bin/env python3
"""
NSE Stock Scanner - Standalone Runner
Run the stock scanner with default settings and display results
"""

import os
import sys
import logging
from datetime import datetime
import pytz

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_default_config():
    """Create default scanner configuration"""
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
    }


def run_scanner(config, max_stocks=None):
    """Run the stock scanner with given configuration"""
    scanner = ProfessionalPCSScanner()
    results = []

    stocks_to_scan = config['stocks_to_scan']
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    logger.info(f"Starting scan of {len(stocks_to_scan)} stocks...")

    for i, symbol in enumerate(stocks_to_scan):
        try:
            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {i + 1}/{len(stocks_to_scan)}")

            # Get recent data
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

            # Store result
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data,
            }

            results.append(stock_result)

        except Exception as e:
            logger.debug(f"Error processing {symbol}: {str(e)[:50]}")
            continue

    # Sort results by pattern strength
    if results:
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    logger.info(f"Scan complete. Found {len(results)} qualifying stocks.")
    return results


def display_results(results, limit=20):
    """Display results in a nice format"""
    if not results:
        print("\n❌ No stocks found matching the filter criteria.\n")
        return

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%d-%m-%Y %H:%M IST')

    print("\n" + "=" * 90)
    print(f"📊 NSE F&O STOCK SCANNER RESULTS")
    print(f"⏰ {timestamp}")
    print("=" * 90)
    print(f"\n✅ Found {len(results)} stocks matching filter criteria")
    print(f"(Showing top {min(limit, len(results))} results)\n")

    # Create formatted table
    print(f"{'#':<3} {'Symbol':<8} {'Price':<10} {'Volume':<8} {'RSI':<6} {'ADX':<6} {'Pattern':<30} {'Score':<7}")
    print("-" * 90)

    for idx, stock in enumerate(results[:limit], 1):
        symbol = stock['symbol'].replace('.NS', '')
        price = stock['current_price']
        volume = stock['volume_ratio']
        rsi = stock['rsi']
        adx = stock['adx']
        max_strength = max(p['strength'] for p in stock['patterns'])
        pattern_type = stock['patterns'][0]['type']

        # Truncate pattern name if needed
        pattern_display = pattern_type[:28] if len(pattern_type) > 28 else pattern_type

        print(f"{idx:<3} {symbol:<8} ₹{price:<9.2f} {volume:<7.1f}x {rsi:<5.1f} {adx:<5.1f} {pattern_display:<30} {max_strength:<6.0f}%")

    print("-" * 90)

    # Show details for top 5
    print(f"\n📋 DETAILED ANALYSIS OF TOP 5 STOCKS:\n")

    for idx, stock in enumerate(results[:5], 1):
        symbol = stock['symbol'].replace('.NS', '')
        print(f"\n{idx}. {symbol.upper()}")
        print(f"   {'─' * 50}")
        print(f"   💰 Price: ₹{stock['current_price']:.2f}")
        print(f"   📊 Volume: {stock['volume_ratio']:.2f}x (above average)")
        print(f"   📈 RSI: {stock['rsi']:.1f}")
        print(f"   ⚡ ADX: {stock['adx']:.1f}")
        print(f"   🎯 Detected Patterns:")

        for pattern in stock['patterns'][:3]:  # Show top 3 patterns
            confidence_emoji = "🟢" if pattern['confidence'] == 'HIGH' else "🟡" if pattern['confidence'] == 'MEDIUM' else "🔴"
            print(f"      {confidence_emoji} {pattern['type']}")
            print(f"         • Strength: {pattern['strength']:.1f}%")
            print(f"         • Success Rate: {pattern.get('success_rate', 0):.1f}%")
            print(f"         • PCS Suitability: {pattern.get('pcs_suitability', 0):.1f}%")

    print("\n" + "=" * 90)
    print("⚠️  Disclaimer: For educational purpose only. Not investment advice.")
    print("=" * 90 + "\n")


def save_results_to_file(results, filename=None):
    """Save results to CSV file"""
    if not results:
        return None

    import csv
    import pandas as pd

    if filename is None:
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        filename = f"scan_results_{timestamp}.csv"

    # Prepare data
    rows = []
    for stock in results:
        symbol = stock['symbol'].replace('.NS', '')
        for pattern in stock['patterns']:
            rows.append({
                'Symbol': symbol,
                'Price': f"{stock['current_price']:.2f}",
                'Volume_Ratio': f"{stock['volume_ratio']:.2f}",
                'RSI': f"{stock['rsi']:.1f}",
                'ADX': f"{stock['adx']:.1f}",
                'Pattern': pattern['type'],
                'Strength': f"{pattern['strength']:.1f}",
                'Confidence': pattern.get('confidence', 'N/A'),
                'Success_Rate': f"{pattern.get('success_rate', 0):.1f}",
                'PCS_Suitability': f"{pattern.get('pcs_suitability', 0):.1f}"
            })

    # Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    logger.info(f"Results saved to {filename}")
    return filename


def main():
    """Main entry point"""
    print("\n" + "=" * 90)
    print("🚀 NSE F&O STOCK SCANNER - STARTING SCAN")
    print("=" * 90 + "\n")

    # Create config and run scanner
    config = create_default_config()

    logger.info(f"Universe: {len(config['stocks_to_scan'])} F&O stocks")
    logger.info(f"RSI Range: {config['rsi_min']} - {config['rsi_max']}")
    logger.info(f"ADX Minimum: {config['adx_min']}")
    logger.info(f"Volume Ratio: {config['min_volume_ratio']}x minimum")
    logger.info("Patterns: All 12 chart patterns enabled")
    logger.info("")

    # Run scan
    results = run_scanner(config)

    # Display results
    display_results(results, limit=20)

    # Save to file
    if results:
        filename = save_results_to_file(results)
        print(f"\n💾 Full results exported to: {filename}\n")

    return results


if __name__ == "__main__":
    results = main()
