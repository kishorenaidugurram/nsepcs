#!/usr/bin/env python3
"""
Simple stock scanner runner
Extracts and runs core scanning logic with minimal dependencies
"""

import sys
import os
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

def main():
    logger.info("=" * 60)
    logger.info("NSE F&O Stock Scanner - Starting Scan")
    logger.info("=" * 60)

    # Try importing the scanner
    try:
        sys.path.insert(0, '/home/user/nsepcs')
        from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
        logger.info(f"✅ Scanner imported successfully")
        logger.info(f"📊 Stock universe: {len(COMPLETE_NSE_FO_UNIVERSE)} stocks")
    except ImportError as e:
        logger.error(f"❌ Failed to import scanner: {e}")
        logger.info("Please ensure all dependencies are installed:")
        logger.info("  pip install -r requirements.txt")
        return 1

    # Scanner configuration (defaults from UI)
    config = {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:100],  # Start with first 100 for speed
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
        'show_news': False,
    }

    logger.info(f"🔍 Scanning {len(config['stocks_to_scan'])} stocks...")
    logger.info(f"📈 Filters: RSI({config['rsi_min']}-{config['rsi_max']}), ADX≥{config['adx_min']}, Volume≥{config['min_volume_ratio']:.1f}x")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []

    # Run scan
    for i, symbol in enumerate(config['stocks_to_scan']):
        try:
            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {i + 1}/{len(config['stocks_to_scan'])}")

            # Get data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                continue

            # Check volume
            volume_ok, volume_ratio, _ = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            results.append({
                'symbol': symbol.replace('.NS', ''),
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': len(patterns),
                'max_strength': max(p['strength'] for p in patterns),
                'pattern_types': [p['type'] for p in patterns[:2]]
            })

        except Exception as e:
            continue

    logger.info(f"\n✅ Scan Complete!")
    logger.info(f"📊 Found {len(results)} stocks matching filter criteria\n")

    # Display results
    if results:
        # Sort by strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)

        print("\n" + "=" * 80)
        print("FILTERED STOCKS - NSE F&O")
        print("=" * 80)
        print(f"{'Symbol':<10} {'Price':<12} {'RSI':<8} {'ADX':<8} {'Vol':<8} {'Strength':<10} {'Patterns'}")
        print("-" * 80)

        for result in results[:20]:
            patterns_str = ", ".join(result['pattern_types'][:2])
            print(f"{result['symbol']:<10} ₹{result['price']:<11.2f} {result['rsi']:<7.1f} "
                  f"{result['adx']:<7.1f} {result['volume_ratio']:<7.1f}x {result['max_strength']:<9.0f}% {patterns_str}")

        if len(results) > 20:
            print(f"\n... and {len(results) - 20} more stocks")

        print("=" * 80)

        # Save results to JSON
        output_file = f"/tmp/scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Results saved to: {output_file}")

        return 0

    else:
        logger.warning("⚠️ No stocks found matching the criteria.")
        logger.info("Try adjusting filters:")
        logger.info("  - Lower pattern strength threshold")
        logger.info("  - Increase RSI range")
        logger.info("  - Reduce volume ratio requirement")
        return 1


if __name__ == "__main__":
    sys.exit(main())
